from datetime import datetime
import re

def checkBirthdate(ymd):
    '''校验出生日期。输入8位出生日期字符串，返回：{code, id, age, {year, month, day}}'''
    if len(ymd) != 8:
        return {'code': 'Error', 'id': ymd, 'age': '出生日期长度需要为8位', 'date': ''}
    if ymd.isdigit() == False:
        return {'code': 'Error', 'id': ymd, 'age': '非法出生日期', 'date': ''}
    year = int(ymd[0:4])
    month = int(ymd[4:6])
    day = int(ymd[6:8])
    currentYear = datetime.now().year
    age = currentYear - year
    if age < 0:
        return {'code': 'Error', 'id': ymd, 'age': '未来出生日期', 'date': ''}
    # 年份：[1-9][0-9]{3}
    # 闰年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))
    # 平年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))
    # 使用正则表达式
    if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:
        ereg = re.compile('([1-9][0-9]{3})((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))')
    else: 
        ereg = re.compile('([1-9][0-9]{3})((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))')
    if ereg.match(ymd):
        return {'code': 'OK', 'id': ymd, 'age': age, 'date': {'year': year, 'month': month, 'day': day}}
    return {'code': 'Error', 'id': ymd, 'age': '非法出生日期', 'date': ''}

# if __name__ == '__main__':
#     print(checkBirthdate('20201001')) # 4岁
#     print(checkBirthdate('20200229')) # 4岁
#     print(checkBirthdate('20250229')) # 未来出生日期
#     print(checkBirthdate('20200230')) # 非法出生日期
#     print(checkBirthdate('20000228')) # 24岁