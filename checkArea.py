"""查询六位省/地/县码、九位乡级码或十二位兼容码。"""

import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path


with Path(__file__).with_name('归属地.json').open('r', encoding='utf-8') as file:
    area_dict = json.load(file)
with Path(__file__).with_name('历史归属地.json').open('r', encoding='utf-8') as file:
    historical_dict = json.load(file)
SNAPSHOT_DIR = Path(__file__).with_name('年度数据')


def _town_index(data):
    towns = defaultdict(list)
    for code, item in data.items():
        if len(code) in (9, 12) and item.get('t'):
            towns[code[:6]].append({'code': code, 'name': item['t']})
    return {parent: sorted(rows, key=lambda row: row['code']) for parent, rows in towns.items()}


current_towns = _town_index(area_dict)


@lru_cache(maxsize=2)
def _snapshot_data(path):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    return payload['codes']


def _snapshots():
    if not SNAPSHOT_DIR.exists():
        return []
    return sorted((path for path in SNAPSHOT_DIR.glob('????.json')
                   if path.stem.isdigit()), reverse=True)


def _archived_item(code):
    for path in _snapshots():
        item = _snapshot_data(str(path)).get(code)
        if item:
            return item, int(path.stem)
    return None, None


def _display_towns(rows):
    """Group twelve-digit compatible codes with their nine-digit town."""
    visible = [dict(row) for row in rows if len(row['code']) == 9]
    nine = {(row['code'], row['name']): row for row in visible}
    for row in rows:
        if len(row['code']) != 12:
            continue
        parent = nine.get((row['code'][:9], row['name']))
        if parent is None:
            visible.append(dict(row))
        else:
            parent.setdefault('aliases', []).append(row['code'])
    return sorted(visible, key=lambda row: row['code'])


def get_subdivisions(areaId):
    """Return all available subordinate towns; never infer one from an ID number."""
    code = str(areaId)[:6]
    rows = current_towns.get(code, [])
    if rows:
        return _display_towns(rows), '现行数据'
    for path in _snapshots():
        rows = _town_index({key: value for key, value in _snapshot_data(str(path)).items()
                            if key.startswith(code) and len(key) in (9, 12)}).get(code, [])
        if rows:
            return _display_towns(rows), f'{path.stem}年版历史留存'
    return [], '无可用数据'


def checkArea(areaId):
    """返回原项目的地区校验结构；乡级码额外返回 township。"""
    areaId = str(areaId)
    if len(areaId) not in (6, 9, 12):
        return {'code': 'Error', 'id': areaId, 'area': '区域码长度须为6位、9位或12位'}
    if not areaId.isascii() or not areaId.isdigit():
        return {'code': 'Error', 'id': areaId, 'area': '非法区域码'}
    item = area_dict.get(areaId)
    archived_year = None
    if item is None and len(areaId) in (9, 12):
        item, archived_year = _archived_item(areaId)
    history = historical_dict.get(areaId, []) if len(areaId) == 6 else []
    if item is None and not history:
        return {'code': 'Error', 'id': areaId, 'area': '未知区域码'}

    if item is None:
        # The source can list several past meanings for a reused code. Show
        # the latest one by default and return every recorded meaning below.
        latest = history[0]
        area = {
            'province': latest['p'],
            'city': latest['a'],
            'district': latest['d'],
            'note': (f"民政部行政区划数据（{latest['year']}年版，历史留存）"
                     if 'year' in latest else '历年行政区划资料'),
            'kind': '历史区域',
        }
    else:
        is_supplement = item['i'].startswith('cn-division')
        area = {
            'province': item['p'],
            'city': item['a'],
            'district': item['d'],
            'note': (f'民政部行政区划数据（{archived_year}年版历史留存）' if archived_year else
                     ('补充区划资料' if is_supplement else '民政部行政区划数据')),
            'kind': '历史区域' if archived_year else ('补充代码' if is_supplement else '现行代码'),
        }
        if len(areaId) in (9, 12):
            area['township'] = item['t']
    if history:
        visible_history = (history if item is None else [
            record for record in history
            if 'year' not in record or
            (record['p'], record['a'], record['d']) != (item['p'], item['a'], item['d'])
        ])
        if visible_history:
            area['historical_records'] = visible_history
    if len(areaId) == 6:
        area['subdivisions'], area['subdivision_source'] = get_subdivisions(areaId)
    return {'code': 'OK', 'id': areaId, 'area': area}
