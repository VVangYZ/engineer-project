import win32com.client as win32
import numpy as np

# 连接 cad 文件
acad = win32.Dispatch("AutoCad.Application")
doc = acad.ActiveDocument
ms = doc.ModelSpace
print(doc.name)

# 获取多段线及坐标
all_tendon = []
for i in range(ms.count):
    all_tendon.append(ms.item(i))

sub_tendon = {}

for i in all_tendon:
    i_coordinates = np.array(i.coordinates).reshape(-1, 2)
    i_y = np.average(i_coordinates[:, 1])
    i_dic = {'coordinates': i_coordinates, 'y': i_y, 'length': i.length, }
    sub_tendon.setdefault(i.layer, []).append(i_dic)

for i in sub_tendon:
    sub_tendon[i] = sorted(sub_tendon[i], key=lambda x: x['y'], reverse=True)

tendon_num = {
    'FC2': [[5, 4], [5, 4, 3], [5, 4, 5]],
    'FC1': [[4, 5], [3, 4, 5], [5, 4, 5]],
    'F2': [[5, 4, 5], [5, 4, 5], [4, 5, 4, 5]],
    'F3': [[3, 5], [5, 5]]
}

tendon_type = {
    'FC2': [15, 15, 15],
    'FC1': [15, 15, 15],
    'F2': [15, 17, 17],
    'F3': [15, 15]
}

cap_length = {
    'FC2': [30, 33, 36],
    'FC1': [27.2, 30, 35],
    'F2': [20, 27, 30],
    'F3': [[13.5, 13.5], [18.5, 18.5]]
}

tendon_cal = {}

for i in tendon_num:
    for m, n in enumerate(tendon_num[i]):
        i_tendon = sub_tendon[f'{i}-{m}']
        i_length = [i['length'] for i in i_tendon]
        tendon_cal.setdefault(i, []).append(i_length)

tendon_cal



