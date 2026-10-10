"""从随项目提供的历年区划汇总表生成独立的历史归属地数据。"""

import csv
import json
from collections import defaultdict
from pathlib import Path


DIRECTORY = Path(__file__).resolve().parent
SOURCE_PATH = DIRECTORY / '历史数据源.csv'
CURRENT_PATH = DIRECTORY / '归属地.json'
OUTPUT_PATH = DIRECTORY / '历史归属地.json'
SNAPSHOT_DIR = DIRECTORY / '年度数据'
REQUIRED_COLUMNS = {
    '代码', '一级行政区', '二级行政区', '名称', '级别',
    '启用时间', '变更/弃用时间', '新代码',
}


def build_historical_area(source_path=SOURCE_PATH, current_path=CURRENT_PATH,
                          output_path=OUTPUT_PATH, snapshot_dir=SNAPSHOT_DIR,
                          current_data=None, pending_snapshot=None, write=True):
    current = (current_data if current_data is not None else
               json.loads(Path(current_path).read_text(encoding='utf-8')))
    history = defaultdict(list)
    with Path(source_path).open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        if not REQUIRED_COLUMNS.issubset(reader.fieldnames or []):
            raise ValueError('历史数据源缺少必需列')
        for row in reader:
            code = row['代码']
            if len(code) != 6 or not code.isascii() or not code.isdigit():
                raise ValueError(f'非法六位代码：{code}')
            start = int(row['启用时间'])
            end = int(row['变更/弃用时间']) if row['变更/弃用时间'] else None
            if not 1981 <= start <= 2100 or (end is not None and end <= start):
                raise ValueError(f'历史时间段异常：{code} {start} {end}')
            # Current records belong in the main file. Keep earlier records
            # here even when the six-digit code still exists today.
            if code in current and end is None:
                continue
            level = row['级别']
            if level not in ('省级', '地级', '县级'):
                raise ValueError(f'未知区划级别：{code} {level}')
            record = {
                'p': row['一级行政区'],
                'a': row['二级行政区'] if level == '县级' else (row['名称'] if level == '地级' else ''),
                'd': row['名称'] if level == '县级' else '',
                'level': level,
                'from': start,
                'to': end,
            }
            if row['新代码']:
                record['next'] = row['新代码']
            if record in history[code]:
                raise ValueError(f'重复历史记录：{code} {start}')
            history[code].append(record)

    snapshots = {}
    if Path(snapshot_dir).exists():
        for path in Path(snapshot_dir).glob('*.json'):
            if path.stem.isdigit() and len(path.stem) == 4:
                snapshots[int(path.stem)] = json.loads(path.read_text(encoding='utf-8'))
    if pending_snapshot is not None:
        snapshots[pending_snapshot['version_year']] = pending_snapshot
    for year, snapshot in sorted(snapshots.items()):
        if snapshot.get('version_year') != year or not isinstance(snapshot.get('codes'), dict):
            raise ValueError(f'{year} 年度快照格式异常')
        for code, item in snapshot['codes'].items():
            if len(code) != 6 or not code.isascii() or not code.isdigit():
                continue  # 身份证归属地只使用六位省、地、县代码
            record = {
                'p': item['p'], 'a': item['a'], 'd': item['d'],
                'level': '县级' if item['d'] else ('地级' if item['a'] else '省级'),
                'year': year,
                'source': '年度快照',
            }
            history[code].append(record)

    ordered = {
        code: sorted(records, key=lambda item: (item.get('year', item.get('from', 0)),
                                                bool(item.get('year'))), reverse=True)
        for code, records in sorted(history.items())
    }
    if len(ordered) < 3000 or '142225' not in ordered:
        raise ValueError('历史区划数据数量异常')
    if write:
        Path(output_path).write_text(
            json.dumps(ordered, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )
    return ordered


if __name__ == '__main__':
    records = build_historical_area()
    print(f'已生成 {len(records)} 个历史代码、{sum(map(len, records.values()))} 段归属记录')
