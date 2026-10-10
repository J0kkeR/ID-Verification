"""命令行身份证校验入口。将本文件放在 ID-Verification 项目根目录运行。"""

import argparse
import re
import sys

try:
    from checkArea import checkArea
    from checkBirthdate import checkBirthdate
    from checkGender import checkGender
    from checkNum import checkNum
except ImportError as exc:
    print("导入失败：请将 id_cli.py 放在 ID-Verification 项目根目录后运行。", file=sys.stderr)
    print(f"详细信息：{exc}", file=sys.stderr)
    sys.exit(2)


def historical_note(records):
    """Format all known year-end versions of a six-digit historical code."""
    parts = []
    for record in records:
        if 'year' in record:
            period = f"{record['year']}年版留存"
        else:
            until = record['to'] - 1 if record['to'] else 2025
            period = f"{record['from']}—{until}年末"
        place = record['p'] + ('' if record['a'] == '直辖' else record['a']) + record['d']
        parts.append(f'{period}：{place}')
    return '；'.join(parts)


def verify(identity_number):
    """调用原项目的四项校验，返回供终端显示的结果。"""
    number = identity_number.strip().upper()
    if not re.fullmatch(r"[0-9]{17}[0-9X]", number):
        return {"号码": number, "整体有效性": "〖异常〗", "原因": "身份证号须为18位：前17位为数字，末位为数字或X"}

    area = checkArea(number[:6])
    birthdate = checkBirthdate(number[6:14])
    gender = checkGender(number[16])
    checksum = checkNum(number)

    errors = []
    if area["code"] != "OK" or not (area["area"].get("district") or area["area"].get("subdivisions")):
        errors.append("地区编码无效")
    if birthdate["code"] != "OK":
        errors.append("出生日期无效")
    if gender["code"] != "OK":
        errors.append("性别顺序码无效")
    if checksum["code"] != "OK":
        errors.append("校验码错误")

    area_info = area.get("area", {}) if area["code"] == "OK" else {}
    subdivisions = area_info.get('subdivisions', [])
    date_info = birthdate.get("date", {}) if birthdate["code"] == "OK" else {}
    date_text = "未知"
    if date_info:
        date_text = f"{date_info['year']}年{date_info['month']}月{date_info['day']}日"

    result = {
        "号码": number,
        "整体有效性": "有效" if not errors else "〖异常〗",
        "校验码": checksum["code"],
        "省份": area_info.get("province", "未知"),
        "城市": area_info.get("city", "未知"),
        "区域": (area_info.get("district") or "未设区") if area_info else "未知",
        "区划记录": area_info.get("kind", "未知"),
        "下辖乡镇街道数量": len(subdivisions),
        "下辖乡镇街道": subdivisions,
        "乡镇街道数据版本": area_info.get('subdivision_source', '无'),
        "乡镇街道说明": "身份证只包含县级区划码，无法确定持证人所在的具体乡镇街道",
        "历史备注": historical_note(area_info["historical_records"]) if area_info.get("historical_records") else "无",
        "数据来源": area_info.get("note", "未知"),
        "生日": date_text,
        "性别": gender.get("gender", "未知") if gender["code"] == "OK" else "未知",
    }
    if errors:
        result["原因"] = "、".join(errors)
    return result


def query_area_code(code):
    """Query a six-, nine- or twelve-digit local area code directly."""
    checked = checkArea(code)
    if checked['code'] != 'OK':
        return {'区划代码': code, '查询结果': '未找到', '原因': checked['area']}
    area = checked['area']
    result = {
        '区划代码': code,
        '查询结果': '已找到',
        '区划记录': area['kind'],
        '省份': area['province'],
        '城市': area['city'],
        '区县': area['district'] or '未设区',
        '历史备注': historical_note(area['historical_records']) if area.get('historical_records') else '无',
        '数据来源': area['note'],
    }
    if len(code) == 6:
        result['下辖乡镇街道数量'] = len(area['subdivisions'])
        result['下辖乡镇街道'] = area['subdivisions']
        result['乡镇街道数据版本'] = area['subdivision_source']
    else:
        result['乡镇街道'] = area['township']
        result['乡镇街道数据版本'] = '历史留存' if area['kind'] == '历史区域' else '现行数据'
    return result


def print_result(result):
    for label, value in result.items():
        if label == '下辖乡镇街道':
            print(f'{label}：')
            if value:
                for item in value:
                    aliases = f"（兼容码：{'、'.join(item['aliases'])}）" if item.get('aliases') else ''
                    print(f"  {item['code']}  {item['name']}{aliases}")
            else:
                print('  无可用数据')
        else:
            print(f'{label}：{value}')


def main():
    parser = argparse.ArgumentParser(description="查询18位身份证号或6/9/12位区划代码")
    parser.add_argument("identity_number", nargs="?", help="身份证号或区划代码；省略时会提示输入")
    args = parser.parse_args()

    if args.identity_number is None:
        try:
            number = input("请输入身份证号或区划代码：")
        except EOFError:
            parser.error("未提供身份证号")
    else:
        number = args.identity_number

    try:
        value = number.strip().upper()
        result = (query_area_code(value) if value.isascii() and value.isdigit()
                  and len(value) in (6, 9, 12) else verify(value))
    except Exception as exc:
        print(f"校验失败：原项目校验函数执行出错：{exc}", file=sys.stderr)
        return 2

    print_result(result)
    return 0 if result.get('查询结果') == '已找到' or result.get('整体有效性') == '有效' else 1


if __name__ == "__main__":
    sys.exit(main())
