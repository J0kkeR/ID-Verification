import requests
import csv

url = "https://cdn.uukit.com/data/idCardData.json"
data = requests.get(url).json()

# 创建一个 CSV 文件
with open('身份证归属地查询表.csv', 'w', newline='', encoding='utf-8') as csvfile:
    # 初始化 CSV 写入器
    csv_writer = csv.writer(csvfile)

    # 写入 CSV 文件的表头
    csv_writer.writerow(['编码', '省级行政区', '地级行政区', '县级行政区', '备注'])

    # 遍历 JSON 数据
    for key, value in data.items():
        # 将 JSON 数据写入 CSV 文件
        csv_writer.writerow([key, value['p'], value['a'], value['d'], value['i']])

print("JSON 数据已保存到 身份证归属地查询表.csv 文件中")