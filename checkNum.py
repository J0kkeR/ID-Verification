'''
1、将身份证号码前17位数分别乘以不同的系数。从第一位到第十七位的系数分别为：7 9 10 5 8 4 2 1 6 3 7 9 10 5 8 4 2
2、将这17位数字和系数相乘的结果相加
3、用加出来和除以11，看余数是多少
4、余数只可能有0 1 2 3 4 5 6 7 8 9 10这11个数字。其分别对应的校验码为1 0 X 9 8 7 6 5 4 3 2
'''

coe = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
lastNum = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

def checkNum(id):
    '''校验校验码。输入18位字符串，返回：{code, id, area, age, gender, jym}'''
    if len(id) != 18:
        return {'code': 'Error', 'id': id, 'jym': '身份证号码长度需要为18位'}
    # num是id前17位
    num = id[0:17]
    if num.isdigit() == False:
        return {'code': 'Error', 'id': id, 'jym': '非法身份证号码'}
    sum = 0
    for i in range(17):
        sum += int(num[i]) * coe[i]
    jym = lastNum[sum % 11]
    if id[17] != jym:
        return {'code': 'Error', 'id': id, 'jym': '校验码错误'}
    return {'code': 'OK', 'id': id, 'jym': jym}

