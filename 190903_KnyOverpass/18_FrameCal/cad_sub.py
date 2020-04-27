import win32com.client as win32
import numpy as np
import pandas as pd
import pythoncom

# 种类
my_type = ('F2', 'F3', 'FC2', 'FC1')
hh_type = ('C1', 'C2MAA', 'C2MBA', 'C2SAA', 'C2SAB', 'C2SBA', 'C2XAA')

# 链接 cad 文件
acad = win32.Dispatch("AutoCad.Application")
doc = acad.ActiveDocument
ms = doc.ModelSpace
print(doc.name)


# 通过坐标获得插入点数据
def POINT(x, y, z):
    return win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (x, y, z))


def plot_line(pt0, pts, lyr):
    """
    绘制桥墩示意图
    :param pt0: 参考原点
    :param pts: 坐标点集（顺序相连）
    :param lyr: 图层
    :return:
    """
    pts = [[i[0] + pt0[0], i[1] + pt0[1]] for i in pts]
    pts = [POINT(i[0], i[1], 0) for i in pts]
    for i in range(len(pts)):
        i_line = ms.AddLine(pts[i-1], pts[i])
        i_line.layer = lyr


def add_note(pt0, note):
    """
    添加指定文本
    :param pt0: 文本参考点
    :param note: 文本内容
    :return:
    """
    note_pt = POINT(pt0[0], pt0[1] + 1.5, 0)
    i_text = ms.addtext(note, note_pt, 1.5)
    i_text.alignment = 1
    i_text.TextAlignmentPoint = note_pt


def plot_sub(sub_pd, plot_type=my_type):
    point_o = [0, 0]
    for i in plot_type:
        point_o[0] += 90
        point_o[1] = 0
        add_note(point_o, i)
        i_sub = sub_pd[sub_pd['Type'] == i]
        for m, n in i_sub.iterrows():
            point_o[1] -= 35
            bridge_pt = [[a, b] for a in n['bridge'] for b in [0, -1.6]]
            cap_pt = [[a, b] for a in n['cap'] for b in [-1.9, -4]]
            pier_pt = []
            for x in n['pier']:
                pier_pt.append([[a, b] for b in [-4.2, -4.2 - n['pier_h']] for a in [x - 0.9, x + 0.9]])
            all_pt = pier_pt + [bridge_pt, cap_pt]
            all_lyr = ['pier'] * len(pier_pt) + ['bridge', 'cap']
            if n['ramp'] != [0]:
                ramp_pt = [[a, b] for a in n['ramp'] for b in [0, -1.6]]
                all_pt.append(ramp_pt)
                all_lyr.append('ramp')
            for x, y in zip(all_pt, all_lyr):
                x[2], x[3] = x[3], x[2]
                plot_line(point_o, x, y)
            i_note = '桩号: {:<20}主梁宽: {:<10.3f}盖梁宽: {:<10.3f}墩高: {:<10.3f}' \
                .format(n['Name'], n['bridge'][1] - n['bridge'][0], n['cap'][1] - n['cap'][0], n['pier_h'])
            add_note(point_o, i_note)


def plot_sub_with_joint(sub_pd, plot_type=my_type):
    point_o = [0, 0]
    for i in plot_type:
        point_o[0] += 150
        point_o[1] = 0
        add_note(point_o, i)
        i_sub = sub_pd[sub_pd['Type'] == i]
        for m, n in i_sub.iterrows():
            point_o[1] -= 35
            bridge_pt = [[a, b] for a in n['bridge'] for b in [0, -1.6]]
            cap_pt = [[a, b] for a in n['cap'] for b in [-1.9, -4]]
            pier_pt = []
            for x in n['pier']:
                pier_pt.append([[a, b] for b in [-4.2, -4.2 - n['pier_h']] for a in [x - 0.9, x + 0.9]])
            joint_pt = []
            joint_loc = [0, 0]
            for x in n['block_length'][:-1]:
                joint_loc[0] = joint_loc[1] + x
                joint_loc[1] = joint_loc[0] + 0.3
                joint_pt.append([[n['cap'][0] + a, b] for a in joint_loc for b in [-1.9, -4]])
            block_loc = [n['bridge'][0] + 0.66, n['bridge'][1] - 0.66 - 0.5]
            block_pt = []
            for x in block_loc:
                block_pt.append([[x + a, b] for a in [0, 0.5] for b in [0.65 - 1.9, -1.9]])
            all_pt = pier_pt + [bridge_pt, cap_pt] + joint_pt + block_pt
            all_lyr = ['pier'] * len(pier_pt) + ['bridge', 'cap'] + ['joint'] * len(joint_pt) + ['block'] * 2
            if n['ramp'] != [0]:
                ramp_pt = [[a, b] for a in n['ramp'] for b in [0, -1.6]]
                all_pt.append(ramp_pt)
                all_lyr.append('ramp')
            for x, y in zip(all_pt, all_lyr):
                x[2], x[3] = x[3], x[2]
                plot_line(point_o, x, y)
            i_note = '桩号: {:<20}主梁宽: {:<10.3f}盖梁宽: {:<10.3f}墩高: {:<10.3f}分块: {:<30}' \
                .format(n['span_name'], n['bridge'][1] - n['bridge'][0], n['cap'][1] - n['cap'][0],
                        n['pier_h'], ' - '.join(n['block_type']))
            add_note(point_o, i_note)




# sub_pd = pd.read_json('../IO/sub_df.json', orient='split')
#
# point_o = [0, 0]
# for i in hh_type:
#     point_o[0] += 90
#     point_o[1] = 0
#     add_note(point_o, i)
#     i_sub = sub_pd[sub_pd['type'] == i]
#     for m, n in i_sub.iterrows():
#         point_o[1] -= 35
#         bridge_pt = [[a, b] for a in n['bridge'] for b in [0, -1.6]]
#         cap_pt = [[a, b] for a in n['cap'] for b in [-1.9, -3.9]]
#         pier_pt = []
#         for x in n['pier']:
#             pier_pt.append([[a, b] for b in [-4, -3.9-n['pier_h']] for a in [x-1, x+1]])
#         all_pt = pier_pt + [bridge_pt, cap_pt]
#         all_lyr = ['pier'] * (len(all_pt) - 2) + ['bridge', 'cap']
#         if n['ramp'] == [0]:
#             ramp_pt = [[a, b] for a in n['ramp'] for b in [0, -1.6]]
#             all_pt.append(ramp_pt)
#             all_lyr.append('ramp')
#         for x, y in zip(all_pt, all_lyr):
#             x[2], x[3] = x[3], x[2]
#             plot_line(point_o, x, y)
#         i_note = '桩号: {:<10.0f}主梁宽: {:<10.2f}盖梁宽: {:<10.2f}墩高: {:<10.2f}'\
#             .format(m, n['bridge'][1] - n['bridge'][0], n['cap'][1] - n['cap'][0], n['pier_h'])
#         add_note(point_o, i_note)



# sub_pd_fc2 = sub_pd[sub_pd['type'].isin(my_type)]
# range_dic = {'bridge': [], 'ramp': []}
#
# for i, j in sub_pd_fc2.iterrows():
#     i_bridge_range = j['bridge'][1] - j['bridge'][0]
#     range_dic['bridge'].append(i_bridge_range)
#     if j['ramp'] != 0:
#         i_ramp_range = j['ramp'][1] - j['ramp'][0]
#         range_dic['ramp'].append(i_ramp_range)
#
# for i in range_dic.values():
#     print(min(i), max(i))









