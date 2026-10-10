def checkGender(gender):
    '''校验性别。输入1位性别编码字符串，返回：{code, id, gender}'''
    if len(gender) != 1:
        return {'code': 'Error', 'id': gender, 'gender': '性别编码长度需要为1位'}
    if gender.isdigit() == False:
        return {'code': 'Error', 'id':gender, 'gender': '非法性别编码'}
    genderInt = int(gender)
    if genderInt % 2 == 0:
        return {'code': 'OK', 'id':gender, 'gender': '女'}
    else:
        return {'code': 'OK', 'id':gender, 'gender': '男'}