"""把项目本地 JSON 生成为可直接双击打开网页使用的精简脚本。"""

import json
from collections import defaultdict
from pathlib import Path


DIRECTORY = Path(__file__).resolve().parent


def build_web_data(current_data=None, history_data=None, version_year=None,
                   output_path=DIRECTORY / 'area_data.js', write=True,
                   snapshot_dir=DIRECTORY / '年度数据', pending_snapshot=None):
    if current_data is None:
        current_data = json.loads((DIRECTORY / '归属地.json').read_text(encoding='utf-8'))
    if history_data is None:
        history_data = json.loads((DIRECTORY / '历史归属地.json').read_text(encoding='utf-8'))
    if version_year is None:
        snapshots = sorted((DIRECTORY / '年度数据').glob('????.json'))
        version_year = int(snapshots[-1].stem) if snapshots else None
    current = {
        code: {
            'p': item['p'], 'a': item['a'], 'd': item['d'],
            'kind': '补充代码' if item['i'].startswith('cn-division') else '现行代码',
        }
        for code, item in current_data.items() if len(code) == 6
    }
    towns = defaultdict(list)
    for code, item in current_data.items():
        if len(code) in (9, 12) and item.get('t'):
            towns[code[:6]].append([code, item['t']])
    snapshots = {}
    if Path(snapshot_dir).exists():
        for path in Path(snapshot_dir).glob('????.json'):
            if path.stem.isdigit():
                snapshots[int(path.stem)] = json.loads(path.read_text(encoding='utf-8'))
    if pending_snapshot is not None:
        snapshots[pending_snapshot['version_year']] = pending_snapshot
    archived_towns = defaultdict(list)
    seen = set(current_data)
    for year, snapshot in sorted(snapshots.items(), reverse=True):
        for code, item in snapshot['codes'].items():
            if len(code) in (9, 12) and item.get('t') and code not in seen:
                archived_towns[code[:6]].append([code, item['t'], year])
                seen.add(code)
    payload = {
        'version_year': version_year,
        'current': current,
        'history': history_data,
        'towns': dict(towns),
        'archived_towns': dict(archived_towns),
    }
    script = 'window.IDV_DATA=' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n'
    if write:
        Path(output_path).write_text(script, encoding='utf-8')
    return script


if __name__ == '__main__':
    script = build_web_data()
    print(f'已生成网页本地数据：{len(script)} 字符')
