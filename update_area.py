"""从民政部接口更新现行归属地.json，历史代码单独存放。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time

import requests

from build_historical_area import build_historical_area
from build_web_data import build_web_data


API_URL = 'https://dmfw.mca.gov.cn/9095/xzqh/getList'
VERSION_URL = 'https://dmfw.mca.gov.cn/XzqhVersionPublish.html'
DATA_PATH = Path(__file__).with_name('归属地.json')
THREAD_LOCAL = threading.local()
CODE_PATTERN = re.compile(r'[0-9]{12}\Z')
VERSION_PATTERN = re.compile(r'数据截止日期为\s*(20\d{2})年\s*\d{1,2}月\s*\d{1,2}日')


def discover_latest_year(insecure=False):
    """Use the publisher's stated data cutoff, never the download date."""
    response = get_session().get(VERSION_URL, timeout=(10, 45), verify=not insecure)
    response.raise_for_status()
    response.encoding = 'utf-8'  # 发布页明确声明 UTF-8
    match = VERSION_PATTERN.search(response.text)
    if not match:
        raise ValueError('发布页未给出年版截止日期；请用 --year 明确指定年版')
    return int(match.group(1))


def stage_text(path, content):
    """Stage a UTF-8 file next to its destination for atomic replacement."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                     prefix='.area-stage-', suffix='.tmp',
                                     delete=False) as file:
        file.write(content)
        file.flush()
        os.fsync(file.fileno())
        return Path(file.name)


def get_session():
    if not hasattr(THREAD_LOCAL, 'session'):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'ID-Verification/1.0 (+https://github.com/ifzzh/ID-Verification)',
            'Referer': 'https://dmfw.mca.gov.cn/interface.html',
            'Accept': 'application/json',
        })
        THREAD_LOCAL.session = session
    return THREAD_LOCAL.session


def fetch_node(code, depth, year, cache_dir, resume, insecure):
    """Read one documented API tree, retrying transient network errors."""
    cache_path = cache_dir / f'{code or "root"}-{depth}.json'
    if resume and cache_path.exists():
        payload = json.loads(cache_path.read_text(encoding='utf-8'))
        if payload.get('status') == 200 and isinstance(payload.get('data'), dict):
            return payload['data']

    params = {'code': code, 'maxLevel': depth}
    if year is not None:
        params['year'] = year
    last_error = None
    for attempt in range(5):
        try:
            response = get_session().get(
                API_URL, params=params, timeout=(10, 45), verify=not insecure
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get('status') != 200 or not isinstance(payload.get('data'), dict):
                raise ValueError(f"接口状态异常：{payload.get('status')} {payload.get('message')}")
            data = payload['data']
            if code and str(data.get('code')) != code:
                raise ValueError(f"接口返回了不同代码：请求 {code}，得到 {data.get('code')}")
            cache_dir.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            os.replace(temporary, cache_path)
            return data
        except (requests.RequestException, ValueError, json.JSONDecodeError) as error:
            last_error = error
            if attempt < 4:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f'获取 {code or "全国"} 失败：{last_error}')


def fetch_many(codes, depth, year, cache_dir, resume, insecure, workers, label):
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {
            executor.submit(fetch_node, code, depth, year, cache_dir, resume, insecure): code
            for code in codes
        }
        for future in as_completed(pending):
            code = pending[future]
            results[code] = future.result()
            if len(results) % 100 == 0 or len(results) == len(codes):
                print(f'{label}：{len(results)}/{len(codes)}', flush=True)
    return results


def output_code(node):
    raw = str(node.get('code', ''))
    if not CODE_PATTERN.fullmatch(raw):
        raise ValueError(f'接口代码不是十二位数字：{raw}')
    if node['level'] <= 3:
        if raw[6:] != '000000':
            raise ValueError(f'省地县代码后六位不为零：{raw}')
        return raw[:6]
    if node['level'] == 4:
        return raw[:9] if raw[9:] == '000' else raw
    raise ValueError(f"未知区划层级：{node['level']}")


def add_tree(node, path, result, levels, edition):
    level = node.get('level')
    if level not in (1, 2, 3, 4):
        raise ValueError(f'未知区划层级：{level}')
    name = node.get('name')
    if not isinstance(name, str) or not name:
        raise ValueError(f'区划名称缺失：{node.get("code")}')
    names = dict(path)
    names[level] = name
    key = output_code(node)
    note = (f'省级民政部门（民政部接口{edition}，更新于{date.today().isoformat()}）'
            if level == 4 else
            f'民政部接口（{edition}，更新于{date.today().isoformat()}）')
    value = {
        'p': names.get(1, ''),
        'a': names.get(2, ''),
        'd': names.get(3, ''),
        'i': note,
    }
    if level == 4:
        value['t'] = name
    if key in result and result[key] != value:
        raise ValueError(f'相同代码存在不同区划内容：{key}')
    result[key] = value
    levels[key] = level
    for child in node.get('children') or []:
        if child.get('level') in (1, 2, 3):
            add_tree(child, names, result, levels, edition)


def preserve_additions(current, updated, full_update):
    """Carry forward sourced additions, distinguishing aliases from supplements."""
    for code, old in current.items():
        if code in updated:
            continue
        note = old.get('i', '')
        if note.startswith('历史区划：'):
            continue  # 旧版数据中的历史代码已迁往历史归属地.json
        elif note.startswith('cn-division'):
            if '对应民政部九位代码' in note and full_update:
                official = updated.get(code[:9])
                if official is None or official.get('t') != old.get('t'):
                    continue
                value = official.copy()
                value['i'] = note
                updated[code] = value
            else:
                updated[code] = old
        elif not full_update and len(code) in (9, 12):
            value = old.copy()
            parent = updated.get(code[:6])
            if parent and value.get('d') == current.get(code[:6], {}).get('d'):
                for field in ('p', 'a', 'd'):
                    value[field] = parent[field]
            updated[code] = value


def update_area(year=None, full_update=True, workers=3, resume=False,
                insecure=False, dry_run=False, data_path=DATA_PATH):
    if not data_path.exists():
        raise FileNotFoundError(f'找不到现有数据：{data_path}')
    current = json.loads(data_path.read_text(encoding='utf-8'))
    year = year if year is not None else discover_latest_year(insecure)
    edition = f'{year}年版'
    run_key = str(year)
    cache_dir = data_path.parent / '.area_update_cache' / run_key

    root = fetch_node('', 2, year, cache_dir, resume, insecure)
    if root.get('level') != 0:
        raise ValueError('接口根节点层级异常')
    provinces = [node for node in root.get('children') or [] if node.get('level') == 1]
    if not 31 <= len(provinces) <= 34:
        raise ValueError(f'省级节点数量异常：{len(provinces)}')
    province_codes = [str(node['code']) for node in provinces]
    print(f'正在获取 {len(province_codes)} 个省级分支（{edition}）', flush=True)
    branches = fetch_many(province_codes, 2, year, cache_dir, resume,
                          insecure, workers, '省级分支')

    updated = {}
    levels = {}
    for code in province_codes:
        branch = branches[code]
        if branch.get('name') != next(x['name'] for x in provinces if x['code'] == code):
            raise ValueError(f'省级名称前后不一致：{code}')
        add_tree(branch, {}, updated, levels, edition)

    counts = Counter(levels.values())
    if not (counts[1] >= 31 and counts[2] >= 300 and counts[3] >= 2600):
        raise ValueError(f'省地县数量过低，取消更新：{dict(counts)}')

    # Preserve display labels from cn-division for direct-admin counties.
    for code, value in updated.items():
        if levels[code] == 3 and not value['a']:
            old = current.get(code)
            if old and old.get('d') == value['d'] and old.get('a') and 'cn-division' in old.get('i', ''):
                value['a'] = old['a']
                value['i'] += '；地级显示依据 cn-division 2026.0.1 补全'

    if full_update:
        city_codes = sorted(set(
            str(node['code'])
            for branch in branches.values()
            for node in walk(branch)
            if node.get('level') == 2
        ))
        county_codes = sorted(set(
            str(node['code'])
            for branch in branches.values()
            for node in walk(branch)
            if node.get('level') == 3
        ))
        print(f'正在获取 {len(city_codes)} 个地级、{len(county_codes)} 个县级节点的乡级数据', flush=True)
        # Direct-admin towns are level 4 children of level 2 cities. The API
        # requires maxLevel=2 for those; counties need only maxLevel=1.
        details = fetch_many(city_codes, 2, year, cache_dir, resume,
                             insecure, workers, '地级乡镇分支')
        details.update(fetch_many(county_codes, 1, year, cache_dir, resume,
                                  insecure, workers, '县级乡镇分支'))
        for raw_code, node in details.items():
            parent_key = output_code(node)
            parent = updated.get(parent_key)
            if parent is None:
                raise ValueError(f'乡级记录缺少上级：{raw_code}')
            for child in node.get('children') or []:
                if child.get('level') != 4:
                    continue
                key = output_code(child)
                value = {
                    'p': parent['p'],
                    'a': parent['a'],
                    'd': parent['d'],
                    'i': f'省级民政部门（民政部接口{edition}，更新于{date.today().isoformat()}）',
                    't': child['name'],
                }
                if '地级显示依据 cn-division' in parent['i']:
                    value['i'] += '；地级显示依据 cn-division 2026.0.1 补全'
                if key in updated and updated[key] != value:
                    raise ValueError(f'乡级代码重复且内容不同：{key}')
                updated[key] = value
                levels[key] = 4
        if sum(level == 4 for level in levels.values()) < 35000:
            raise ValueError('乡级代码数量过低，取消更新')

    preserve_additions(current, updated, full_update)
    if len(updated) < 40000:
        raise ValueError(f'最终记录数量过低，取消更新：{len(updated)}')

    lengths = Counter(map(len, updated))
    print(f'校验通过：{len(updated)} 条；长度分布 {dict(sorted(lengths.items()))}', flush=True)
    if dry_run:
        print('预览完成，未替换数据或年度快照', flush=True)
        return updated

    snapshot = {
        'version_year': year,
        'captured_at': date.today().isoformat(),
        'full_update': full_update,
        'codes': dict(sorted(updated.items())),
    }
    snapshot_dir = data_path.parent / '年度数据'
    history = build_historical_area(
        current_data=updated, snapshot_dir=snapshot_dir,
        pending_snapshot=snapshot, write=False,
    )
    web_script = build_web_data(current_data=updated, history_data=history,
                                version_year=year, write=False,
                                snapshot_dir=snapshot_dir, pending_snapshot=snapshot)
    targets = [
        (snapshot_dir / f'{year}.json', json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n'),
        (data_path.parent / '历史归属地.json',
         json.dumps(history, ensure_ascii=False, indent=2) + '\n'),
        (data_path.parent / 'area_data.js', web_script),
        (data_path, json.dumps(dict(sorted(updated.items())), ensure_ascii=False, indent=2) + '\n'),
    ]
    staged = []
    try:
        for path, content in targets:
            staged.append((stage_text(path, content), path))
        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _ in staged:
            if temporary.exists():
                temporary.unlink()
    print(f'已更新：{data_path}；已保存 {year} 年度快照并同步历史库、网页数据', flush=True)
    return updated


def walk(node):
    yield node
    for child in node.get('children') or []:
        yield from walk(child)


def main():
    parser = argparse.ArgumentParser(description='从民政部接口更新归属地.json')
    parser.add_argument('--year', type=int, help='指定年版；省略时读取民政部发布页的数据截止年份')
    parser.add_argument('--county-only', action='store_true',
                        help='只更新省、地、县，原有乡级记录保持旧版')
    parser.add_argument('--workers', type=int, default=3, choices=range(1, 5),
                        metavar='1-4', help='并发请求数，默认 3')
    parser.add_argument('--resume', action='store_true', help='复用本次未完成更新的缓存')
    parser.add_argument('--dry-run', action='store_true', help='获取并校验，但不替换数据文件')
    parser.add_argument('--insecure', action='store_true',
                        help='仅在受信任代理环境中跳过 TLS 证书校验')
    args = parser.parse_args()
    if args.year is not None and not 2000 <= args.year <= 2100:
        parser.error('year 须在 2000 到 2100 之间')
    if args.insecure:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        update_area(year=args.year, full_update=not args.county_only,
                    workers=args.workers, resume=args.resume,
                    insecure=args.insecure, dry_run=args.dry_run)
    except Exception as error:
        parser.exit(2, f'更新失败，原数据未替换：{error}\n')


if __name__ == '__main__':
    main()
