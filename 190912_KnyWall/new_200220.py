import numpy as np
import pandas as pd
import time

# ---------------------------------------- 一些参数 ----------------------------------------

# 文件参数
usual_file = 'usual_data_1215.txt'
filename = 'new_truss'

# 钢架参数
height = 26.5
height_il = 2
thick_1 = 1.2
thick_2 = 2.5

support_h = 14
support_d = 5.3
support_d_2 = 4
support_division = np.r_[0:support_h:height_il, support_h]

# 钢架位置
frame1_x = np.r_[2.75:2.75+35:5, 2.75+35, 2.75+35+6:2.75+35+6+50:5, 2.75+35+6+50]
frame1_y = np.r_[0, -thick_1]
frame2_x = np.r_[0, thick_2]
frame2_y = np.r_[-35:-5:5, -5]
frame_z = np.r_[0:(height - height_il):height_il, height]

frame_super = [2.75+25, 2.75+35+6+15]
frame_brace = 2.75+35+4

frame1_link2_n = 4      # 每节分几小节
frame1_x_add = np.r_[2.75:2.75+35:5/frame1_link2_n, 2.75+35, 2.75+35+6:2.75+35+6+50:5/frame1_link2_n, 2.75+35+6+50]

# 荷载参数
wind_10 = 28    # 10m 高度处基本风速
wind_h = [[3, 5, 10, 15, 20, 30], [0.6, 0.65, 0.74, 0.83, 0.9, 0.97]]   # 随高度变化


# ---------------------------------------- 建立节点 ----------------------------------------

node = pd.DataFrame(columns=['x', 'y', 'z'])
n_num = 0

# 原点
for i in frame_z:
    n_num += 1
    node.loc[n_num] = [0, 0, i]

for i in frame_z:
    n_num += 1
    node.loc[n_num] = [thick_2, -thick_1, i]

# 横排
for i in frame1_x_add:
    for j in frame1_y:
        for k in frame_z:
            n_num += 1
            node.loc[n_num] = [i, j, k]

# 竖排
for j in frame2_y:
    for i in frame2_x:
        for k in frame_z:
            n_num += 1
            node.loc[n_num] = [i, j, k]

# 斜撑
for i in frame1_x:
    for j in support_division[:-1]:
        ny = np.interp(j, [0, support_h], [support_d, 0])
        n_num += 1
        node.loc[n_num] = [i, ny, j]

for i in frame2_y:
    for j in support_division[:-1]:
        nx = np.interp(j, [0, support_h], [-support_d_2, 0])
        n_num += 1
        node.loc[n_num] = [nx, i, j]

# ---------------------------------------- 建立单元 ----------------------------------------

elem = pd.DataFrame(columns=['m', 's', 'b', 'n1', 'n2', 'WHAT'])
enum = 0


def elem_from_node(nodes, s, what, m=1, b=0):
    for i, j in enumerate(nodes[:-1]):
        global enum
        global elem
        enum += 1
        n1 = j
        n2 = nodes[i + 1]
        elem.loc[enum] = [m, s, b, n1, n2, what]


def link_from_loc(loc1, loc2, s, what, m=1, b=0):
    for i in frame_z[1:]:
        n1 = node[(node['x'] == loc1[0]) & (node['y'] == loc1[1]) & (node['z'] == i)].index[0]
        n2 = node[(node['x'] == loc2[0]) & (node['y'] == loc2[1]) & (node['z'] == i)].index[0]
        global enum
        global elem
        enum += 1
        elem.loc[enum] = [m, s, b, n1, n2, what]


# 立柱
n = node[(node['x'] == 0) & (node['y'] == 0)].index
elem_from_node(n, 1, 'Link1', b=-45)

n = node[(node['x'] == thick_2) & (node['y'] == -thick_1)].index
elem_from_node(n, 1, 'Link1', b=-45)

for i in frame1_x:
    for j in frame1_y:
        if frame_super[0]+1 < i < frame_super[1]-1:
            n1 = node[(node['x'] == i) & (node['y'] == j) & (node['z'] <= 10)].index
            elem_from_node(n1, 9, 'Link1', b=90)
            n2 = node[(node['x'] == i) & (node['y'] == j) & (node['z'] >= 10)].index
            elem_from_node(n2, 1, 'Link1', b=90)
        elif frame_super[0]-8 < i < frame_super[1]+8:
            n = node[(node['x'] == i) & (node['y'] == j)].index
            elem_from_node(n, 8, 'Link1', b=90)
        else:
            n = node[(node['x'] == i) & (node['y'] == j)].index
            elem_from_node(n, 1, 'Link1', b=90)

for i in frame2_x:
    for j in frame2_y:
        n1 = node[(node['x'] == i) & (node['y'] == j) & (node['z'] <= 10)].index
        elem_from_node(n1, 9, 'Link1')
        n2 = node[(node['x'] == i) & (node['y'] == j) & (node['z'] >= 10)].index
        elem_from_node(n2, 1, 'Link1')

# 横杆
for i in frame_z[1:]:
    if i in [support_h - height_il, support_h, support_h + height_il]:
        link2_sec = 15
    else:
        link2_sec = 2
    n = node[((node['x'] == 0) | (node['y'] == 0)) & (node['z'] == i)]
    nn = n.sort_values(by=['x', 'y']).index
    elem_from_node(nn, link2_sec, 'Link2')
    n = node[((node['x'] == thick_2) | (node['y'] == -thick_1)) & (node['z'] == i)]
    nn = n.sort_values(by=['x', 'y']).index
    elem_from_node(nn, link2_sec, 'Link2')

# 斜杆
for i in frame1_x[:-1]:
    if i+5 < frame_brace or i > frame_brace:
        for j in np.arange(frame1_link2_n):
            loc_1 = [i + j/frame1_link2_n*5, (j+1) % 2 * (-thick_1)]
            loc_2 = [i + (j+1)/frame1_link2_n*5, (j+2) % 2 * (-thick_1)]
            link_from_loc(loc_1, loc_2, 10, 'Link2-2')

# 小横杆
for i in frame1_x_add:
    if i in frame1_x:
        pass
    else:
        loc_1 = [i, 0]
        loc_2 = [i, -thick_1]
        link_from_loc(loc_1, loc_2, 12, 'Link2-3')

# 横联
loc_1 = [0, 0]
loc_2 = [thick_2, -thick_1]
link_from_loc(loc_1, loc_2, 3, 'Link3')

for i in frame1_x:
    if frame_super[0] - 8 < i < frame_super[1] + 8:
        link3_sec = 13
    else:
        link3_sec = 3
    loc_1 = [i, 0]
    loc_2 = [i, -thick_1]
    link_from_loc(loc_1, loc_2, link3_sec, 'Link3')

for i in frame2_y:
    loc_1 = [0, i]
    loc_2 = [thick_2, i]
    link_from_loc(loc_1, loc_2, 3, 'Link3')

# 斜联
n_frame_z = len(frame_z)
n1 = node[(node['x'] == 0) & (node['y'] == 0)]
n2 = node[(node['x'] == thick_2) & (node['y'] == -thick_1)]
n12 = [n1.iloc[np.r_[0:n_frame_z:2]], n2.iloc[np.r_[1:n_frame_z:2]]]
n = pd.concat(n12).sort_values(by='z').index
elem_from_node(n, 4, 'Link4')

for i in frame1_x:
    if frame_super[0] - 8 < i < frame_super[1] + 8:
        link4_sec = 14
    else:
        link4_sec = 4
    n1 = node[(node['x'] == i) & (node['y'] == 0)]
    n2 = node[(node['x'] == i) & (node['y'] == -thick_1)]
    n12 = [n1.iloc[np.r_[0:n_frame_z:2]], n2.iloc[np.r_[1:n_frame_z:2]]]
    n = pd.concat(n12).sort_values(by='z').index
    elem_from_node(n, link4_sec, 'Link4')

for i in frame2_y:
    n1 = node[(node['x'] == 0) & (node['y'] == i)]
    n2 = node[(node['x'] == thick_2) & (node['y'] == i)]
    n12 = [n1.iloc[np.r_[0:n_frame_z:2]], n2.iloc[np.r_[1:n_frame_z:2]]]
    n = pd.concat(n12).sort_values(by='z').index
    elem_from_node(n, 4, 'Link4')

# 斜撑
for i in frame1_x:
    if frame_super[0] - 8 < i < frame_super[1] + 8:
        support_sec = 11
    else:
        support_sec = 5
    n = []
    for j in support_division:
        sy = np.interp(j, [0, support_h], [support_d, 0])
        ni = node[(node['x'] == i) & (node['y'] == sy) & (node['z'] == j)].index[0]
        n.append(ni)
    elem_from_node(n, support_sec, 'Support1')

for i in frame2_y:
    support_sec = 5
    n = []
    for j in support_division:
        sx = np.interp(j, [0, support_h], [-support_d_2, 0])
        ni = node[(node['x'] == sx) & (node['y'] == i) & (node['z'] == j)].index[0]
        n.append(ni)
    elem_from_node(n, support_sec, 'Support1')


# 斜撑横杆
for i in support_division[1:-1]:
    sy = np.interp(i, [0, support_h], [support_d, 0])
    n = node[(node['y'] == sy) & (node['z'] == i)].index
    elem_from_node(n, 6, 'Support2')

    sx = np.interp(i, [0, support_h], [-support_d_2, 0])
    n = node[(node['x'] == sx) & (node['z'] == i)].index
    elem_from_node(n, 6, 'Support2')

# 斜撑横联
for i in frame1_x:
    for j in support_division[1:-1]:
        sy = np.interp(j, [0, support_h], [support_d, 0])
        n1 = node[(node['x'] == i) & (node['y'] == sy) & (node['z'] == j)].index[0]
        n2 = node[(node['x'] == i) & (node['y'] == 0) & (node['z'] == j)].index[0]
        elem_from_node([n1, n2], 7, 'Support3')

for i in frame2_y:
    for j in support_division[1:-1]:
        sx = np.interp(j, [0, support_h], [-support_d_2, 0])
        n1 = node[(node['x'] == sx) & (node['y'] == i) & (node['z'] == j)].index[0]
        n2 = node[(node['x'] == 0) & (node['y'] == i) & (node['z'] == j)].index[0]
        elem_from_node([n1, n2], 7, 'Support3')


# ---------------------------------------- 写入mct文件 ----------------------------------------

t1 = time.gmtime()
t2 = f'{t1.tm_year}{t1.tm_mon}{t1.tm_mday}'
mct_file = open(f'IO\\{filename}_{t2[2:]}.mct', 'w+')

# 常规信息
with open(f'IO\\{usual_file}') as f:
    usual_content = f.read()
mct_file.write(usual_content + '\n')

# 节点信息
mct_file.write('*NODE\n')
for i, j in node.iterrows():
    mct_file.write(f"{i}, {j['x']}, {j['y']}, {j['z']}\n")

# 单元信息
mct_file.write('*ELEMENT\n')
for i, j in elem.iterrows():
    if j['WHAT'] in ['Link2-2', 'Link2-3', 'Support2', 'Link3', 'Link4', 'Support3']:
        link_type = 'TRUSS'
    else:
        link_type = 'BEAM'
    mct_file.write(f"{i}, {link_type}, {j['m']}, {j['s']}, {j['n1']}, {j['n2']}, {j['b']}\n")

# 约束信息
mct_file.write('*BNDR-GROUP\nsupport\n')    # 定义约束组
mct_file.write('*CONSTRAINT\n')
for i, j in node[node['z'] == 0].iterrows():
    if frame_super[0] + 1 < j['x'] < frame_super[1] - 1:
        support_type = 101000
    else:
        support_type = 111000
    mct_file.write(f'{i}, {support_type}, support\n')

# 荷载信息
# 自重
mct_file.write('*USE-STLD, DEAD\n')
mct_file.write('*SELFWEIGHT, 0, 0, -1, self-weight\n')

# 风荷载
mct_file.write('*USE-STLD, WIND1\n')
mct_file.write('*BEAMLOAD\n')
elem_wind = elem[elem['WHAT'] == 'Link1']

for i, j in elem_wind.iterrows():
    x1 = node.loc[j['n1']]['x']
    y1 = node.loc[j['n1']]['y']
    z1 = node.loc[j['n1']]['z']
    z2 = node.loc[j['n2']]['z']
    wind1 = np.interp(z1, wind_h[0], wind_h[1]) * wind_10
    wind2 = np.interp(z2, wind_h[0], wind_h[1]) * wind_10
    fg1 = 0.613 * wind1 ** 2 * (-2 + 0.3) * 5 / 1000
    fg2 = 0.613 * wind2 ** 2 * (-2 + 0.3) * 5 / 1000
    if y1 == 0:
        if x1 in [0, frame1_x[-1]]:
            fg1 *= 0.5
            fg2 *= 0.5
        elif frame_super[0] < x1 < frame_super[1] and z2 <= 10:
            continue
        mct_file.write(f'{i}, BEAM, UNILOAD, GY, NO , NO, aDir[1], , '
                       f', , 0, {fg1}, 1, {fg2}, 0, 0, 0, 0, wind, NO, 0, 0, NO\n')

mct_file.write('*USE-STLD, WIND2\n')
mct_file.write('*BEAMLOAD\n')
for i, j in elem_wind.iterrows():
    x1 = node.loc[j['n1']]['x']
    y1 = node.loc[j['n1']]['y']
    z1 = node.loc[j['n1']]['z']
    z2 = node.loc[j['n2']]['z']
    wind1 = np.interp(z1, wind_h[0], wind_h[1]) * wind_10
    wind2 = np.interp(z2, wind_h[0], wind_h[1]) * wind_10
    fg1 = 0.613 * wind1 ** 2 * (-2 + 0.3) * 5 / 1000
    fg2 = 0.613 * wind2 ** 2 * (-2 + 0.3) * 5 / 1000
    if x1 == 0:
        if y1 in [0, frame2_y[0]]:
            fg1 *= 0.5
            fg2 *= 0.5
        mct_file.write(f'{i}, BEAM, UNILOAD, GX, NO , NO, aDir[1], ,\
                    , , 0, {-fg1}, 1, {-fg2}, 0, 0, 0, 0, wind, NO, 0, 0, NO\n')

# 荷载组合
mct_file.write('*LOADCOMB\n')
mct_file.write('NAME=com1, GEN, ACTIVE, 0, 0, , 0, 0\n')
mct_file.write('ST, DEAD, 1.2, ST, WIND1, 1.4\n')
mct_file.write('NAME=com2, GEN, ACTIVE, 0, 0, , 0, 0\n')
mct_file.write('ST, DEAD, 1.2, ST, WIND2, 1.4\n')

# 写入 mct 文件完毕
mct_file.write('*ENDDATA')
mct_file.close()

