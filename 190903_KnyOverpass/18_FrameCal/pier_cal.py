import numpy as np
import midas
import win32com.client as win32
import cad
import pandas as pd
import tendon_new
import time
import math

# 参数 ==============================================================================================================

# 文件参数
str_now = time.strftime('%y%m%d%H%M', time.localtime())
mct_file = f'IO\\wow_{str_now}.mct'

# 截面参数 ==========================================================================================================
acad = win32.Dispatch("AutoCAD.Application")
doc = acad.ActiveDocument
ms = doc.ModelSpace
doc.name

secs = cad.CadSecs(ms)

# 截面参数
sec_box = {}
for i, j in enumerate(secs.secs):   # 获取截面边框
    lx = round(j.prop['c'][0] + j.prop['c'][1], 4)
    ly = round(j.prop['c'][2] + j.prop['c'][3], 4)
    if 'C' in secs.sec_name[i]:
        sec_box.setdefault('cap', []).append((lx, ly))
    else:
        sec_box.setdefault('pier', []).append((lx, ly))

# 几何参数
pier_loc = (0, )      # 桥墩位置
pier_sec = (2, )      # 桥墩截面类型（墩柱类型，1开始）
pier_height = 7         # 桥墩高度

cap_loc = (-10.8, -4.1, 4.1, 10.8)   # 盖梁变截面位置
cap_sec = (1, 3, 3, 1)      # 盖梁各截面类型（盖梁类型，1开始）
cap_height = tuple(sec_box['cap'][i-1][1] for i in cap_sec)     # 盖梁高度

link_to_side = 0.5      # 刚臂到边缘距离
pier_link = {}      # 刚臂连接位置
pier_link_loc = []
for i, j in enumerate(pier_loc):
    link_distance = sec_box['pier'][pier_sec[i] - 1][0] / 2 - link_to_side
    pier_link.setdefault(j, []).extend([j - link_distance, j + link_distance])
    pier_link_loc.extend([j - link_distance, j + link_distance])
pier_link_loc = tuple(pier_link_loc)

# 荷载参数
support_space = (3.05, 2.9)     # 支座间距
f_loc = tuple(i * support_space[0] for i in range(-3, 4))    # 作用力的位置
f_value = ((680, 635), (790, 635))   # 力的大小（恒载、活载）
f_type = (1, ) * len(f_loc)     # 力的种类（ 1 开始）

tendon_sec = (3, )     # 关注截面（第一个截面为控制截面）
tendon_sec_f = (        # 关注截面受力（DSEU)
    (-4015.7, -19533.8, -22162.7, -31182.62),
)
tendon_loc = (      # 预应力实际截面位置
    cap_loc[0],
    -3,
    3,
    cap_loc[-1])
tendon_type = (0, 1, 1, 0)       # 预应力实际截面种类
tendon_curve_r = 10       # 预应力半径

# 模型参数
have_tendon = True
mct_l = []      # mct 文件列表
num_l = [0] * 4     # 截面号、节点号、单元号、弹性连接号
node_space = 1      # 节点最大间距（单位：m）
temp = (-15, 15)    # 温度
cap_m = []      # 弯矩值
f_lim = [22.4, 22.4, -2, -2]    # 混凝土容许应力（施工、使用、施工、使用）
tendon_per_n = 15       # 单束预应力股数
tendon_edge = 0.3  # 预应力到边缘距离
tendon_between = 0.35   # 预应力之间横向距离

# 各种组
stldcase = ('DEAD', 'TENDON', 'BEAM1', 'BEAM2', 'TEM_U', 'TEM_D')
loadgroup = ('dead', 'tendon', 'beam_1', 'beam_2', 'tem_u', 'tem_d')

# 预应力计算 =========================================================================================================

t_secs = []
for i in tendon_sec:
    t_secs.append(secs.secs[i - 1])
    # t_secs[-1].sec.plot_mesh()

if have_tendon:
    # 建立预应力截面
    ts = [tendon_new.Tendon(i) for i in t_secs]

    # 对截面进行计算
    pro_infs = []
    pro_ep = []
    pro_to_top = []
    pro_ult = []
    pro_np = 1
    pro_ni = 1
    for i, j in enumerate(tendon_sec_f):
        ts[i].tendon_cal(j[0], j[2], j[1], f_lim[2], f_lim[0], f_lim[3], f_lim[1])
        i_sec_width = sec_box['cap'][tendon_sec[i] - 1][0]
        if i == 0:
            pro_infs.append(ts[i].get_np_from_pw(i_sec_width, pro_one=tendon_per_n,
                                                 s_p_h=tendon_edge, p_p_h=tendon_between))
            pro_np = pro_infs[0][0]
            pro_ep.append(pro_infs[0][1])
            pro_ni = pro_infs[0][2]
            pro_to_top.append(pro_infs[0][3])
            pro_ult.append(ts[i].get_np_from_mu(j[3], f_lim[0], i_sec_width, pro_ep[0]))
        else:
            pro_infs.append(ts[i].get_ep_from_np(pro_np, pro_ni))
            pro_ep.append(pro_infs[-1][0])
            pro_to_top.append(pro_infs[-1][1])
            ts[i].plot_pro(ts[i].ep, ts[i].np, pro_ep[-1], 1 / pro_np)
            pro_ult.append(ts[i].get_np_from_mu(j[3], f_lim[0], i_sec_width, pro_ep[-1]))


# 初始化 ==============================================================================================================

midas.usual_data(mct_list=mct_l, loadgroup=loadgroup, stldcase=stldcase)

# 添加截面 ===========================================================================================================

secs_midas = secs.secs_to_midas()

# 墩柱截面参考点改为中心
for i, j in enumerate(secs_midas):
    if 'P' in secs.sec_name[i]:
        secs_midas[i][0] = j[0].replace('CT', 'CC')

midas.psv_sec_start(mct_l)
midas.add_my_sec(secs_midas, mct_list=mct_l, num=num_l)

# 变截面
sec_change = {}
for i, j in enumerate(cap_sec[:-1]):
    if cap_sec[i + 1] != j:
        i_sec_change = (j, cap_sec[i + 1])
        if i_sec_change not in sec_change:
            i_sec_name = 'sec_' + '_'.join(map(str, i_sec_change))
            sec_change[i_sec_change] = midas.add_change_sec(j, cap_sec[i + 1], secs_midas, i_sec_name, 'CT', mct_l, num_l)

# midas.add_change_sec(1, 2, secs_midas, 'C1-C2', 'CT', mct_l, num_l)
# midas.add_change_sec(2, 1, secs_midas, 'C2-C1', 'CT', mct_l, num_l)

# 节点和单元 =========================================================================================================

# 盖梁节点坐标
cap_node_must = list(set(pier_loc + cap_loc + f_loc + pier_link_loc))
cap_node_must.sort()

cap_node_add = []
for i, j in enumerate(cap_node_must):
    if i != 0:
        space = j - cap_node_must[i - 1]
        if space > node_space:
            segment = int(space // node_space + 1)
            node_add_i = np.linspace(cap_node_must[i-1], j, segment + 1).tolist()
            cap_node_add += node_add_i[1:-1]

cap_node = sorted(cap_node_must + cap_node_add)

# 定义节点和单元
node = pd.DataFrame(columns=['x', 'y', 'z', 'what'])
elem = pd.DataFrame(columns=['m', 's', 'b', 'n1', 'n2', 'what'])

# 盖梁
for i in cap_node:
    num_l[1] += 1
    node.loc[num_l[1]] = [0, i, 0, 'cap']

for i, j in enumerate(cap_sec[:-1]):
    if cap_sec[i + 1] == j:
        i_sec = j
    else:
        i_sec = sec_change[(j, cap_sec[i + 1])]
    cap_interval = cap_loc[i: i + 2]
    i_cap_node = node[(node['y'] >= cap_interval[0]) & (node['y'] <= cap_interval[1])].index
    for m, n in enumerate(i_cap_node[:-1]):
        num_l[2] += 1
        elem.loc[num_l[2]] = [1, i_sec, 0, n, n + 1, 'cap']

# 桥墩
for i, j in enumerate(pier_loc):
    i_sec = pier_sec[i] + len(sec_box['cap'])
    i_z_top = -np.interp(j, cap_loc, cap_height)
    i_z_bot = i_z_top - pier_height
    i_z = np.linspace(i_z_bot, i_z_top, math.ceil(pier_height + 1))
    for m in i_z:
        num_l[1] += 1
        node.loc[num_l[1]] = [0, j, m, 'pier']
    for m in pier_link[j]:
        num_l[1] += 1
        node.loc[num_l[1]] = [0, m, i_z_top, 'link']
    i_pier_node = node[(node['what'] == 'pier') & (node['y'] == j)].index
    for m, n in enumerate(i_pier_node[:-1]):
        num_l[2] += 1
        elem.loc[num_l[2]] = [3, i_sec, 0, n, n+1, 'pier']

# 添加至 mct
midas.node_to_mct(node, mct_l)
midas.elem_to_mct(elem, mct_list=mct_l)

# 变截面组
midas.start_change_group(mct_l)
for i in sec_change.values():
    i_group = ' '.join(map(str, elem[(elem['s'] == i)].index))
    midas.add_change_group(i, i_group, mct_list=mct_l)

# 结构组
group_l = ['cap_and_pier', ]
group_elem = [f'{elem.index.min()}to{elem.index.max()}', ]
group_node = [f'{node.index.min()}to{node.index.max()}', ]
midas.add_group(group_l, group_node, group_elem, mct_l)

# 添加约束 ====================================================================================================

# 墩底约束
midas.start_boundary(mct_l)
for i in pier_loc:
    i_node = node[(node['y'] == i) & (node['what'] == 'pier')].index[0]
    i_type = '111111'
    midas.add_boundary(i_node, 'constraint', i_type, mct_l)

# 连接
midas.start_link(mct_l)

for i, j in enumerate(pier_loc):
    i_z_top = -np.interp(j, cap_loc, cap_height)
    i_p = node[(node['y'] == j) & (node['z'] == i_z_top) & (node['what'] == 'pier')].index[0]
    i_cap = node[(node['y'] == j) & (node['what'] == 'cap')].index[0]
    midas.add_elastic_link(i_p, i_cap, 'elastic_connection', num_l, mct_l, sdx=1e10, sdy=1e6, sdz=1e6)
    for m in pier_link[j]:
        i_link = node[(node['y'] == m) & (node['what'] == 'link')].index[0]
        midas.add_rigid_link(i_p, i_link, 'rigid_connection', num_l, mct_list=mct_l)
        i_cap = node[(node['y'] == m) & (node['what'] == 'cap')].index[0]
        midas.add_elastic_link(i_link, i_cap, 'elastic_connection', num_l, mct_l, sdx=5e9, sdy=1e6, sdz=1e6)

# 荷载信息 ====================================================================================================

# 自重
midas.start_stld('DEAD', mct_l)
midas.add_self_weight(1, mct_l, 'dead')

# 预应力
if have_tendon:
    # 钢束特性
    midas.tendon_prop(['T1'], [140 * tendon_per_n / 1000000], 2, mct_l)

    # 钢束线型
    midas.start_tendon_type(mct_l)
    tendon_z = []
    tendon_r = []
    for i, j in enumerate(tendon_type):
        if j == 0:
            i_sec = cap_sec[cap_loc.index(tendon_loc[i])]
            i_cz = -secs.secs[i_sec - 1].prop['c'][2]
            i_z = i_cz + pro_to_top[0] - np.average(pro_to_top[0], weights=pro_ni)
            tendon_z.append(i_z)
            tendon_r.append(0)
        else:
            tendon_z.append(pro_to_top[j - 1])
            tendon_r.append(tendon_curve_r)

    origin_pt = (0, 0, 0)
    tendon_elem = elem[elem['what'] == 'cap'].index
    y_pt = ((min(tendon_loc), 0, 0), (max(tendon_loc), 0, 0))
    for i, j in enumerate(pro_ni):
        i_pt_z = [m[i] for m in tendon_z]
        z_pt = np.array([tendon_loc, i_pt_z, tendon_r]).T
        midas.tendon_type(f't-{i+1}', 'T1', tendon_elem, pro_ni[i], origin_pt, 'Y', y_pt, z_pt, mct_l)

    # 张拉预应力
    midas.start_stld('TENDON', mct_l)
    midas.start_tendon_f(mct_l)
    for i, j in enumerate(pro_ni):
        midas.tendon_f(f't-{i + 1}', mct_list=mct_l)

# 主梁作用
midas.start_stld('BEAM1', mct_l)
midas.start_node_load(mct_l)

for i, j in enumerate(f_loc):
    f = f_value[f_type[i] - 1][0]
    i_node = node[(node['y'] == j) & (node['what'] == 'cap')].index[0]
    midas.node_load(i_node, mct_l, 'beam_1', fz=-f)

midas.start_stld('BEAM2', mct_l)
midas.start_node_load(mct_l)

for i, j in enumerate(f_loc):
    f = f_value[f_type[i] - 1][1]
    i_node = node[(node['y'] == j) & (node['what'] == 'cap')].index[0]
    midas.node_load(i_node, mct_l, 'beam_2', fz=-f)

# 温度
midas.start_stld('TEM_U', mct_l)
midas.start_tem_load(mct_l)
for i, j in elem.iterrows():
    midas.tem_load(i, temp[0], mct_l, 'tem_d')

midas.start_stld('TEM_D', mct_l)
midas.start_tem_load(mct_l)
for i, j in elem.iterrows():
    midas.tem_load(i, temp[1], mct_l, 'tem_u')

# 施工阶段
midas.start_stage(mct_l)
g1 = ['cap_and_pier', ]
t1 = [7, ]
b1 = ['support', 'rigid_connection', 'constraint', 'elastic_connection']
l1 = ['dead', 'tendon']
midas.add_stage('erection', 28, g1, t1, b1, l1, mct_l)
l2 = ['beam_1']
midas.add_stage('add_beam', 28, load=l2, mct_list=mct_l)
midas.add_stage('wait', 3600, mct_list=mct_l)

# 荷载组合
# 荷载组合
midas.start_com(mct_l)

com1 = ['TEM_U', 'TEM_D']
f1 = [1, 1]
t1 = ['ST', 'ST']
midas.com_f('tem', com1, f1, t1, 1, mct_l)

com2 = ['合计', 'TENDON', 'BEAM2', 'tem']
f2 = [1, -0.15, 0.7, 1]
t2 = ['CS', 'ST', 'ST', 'CB']
midas.com_f('ms', com2, f2, t2, 0, mct_l)

com3 = ['合计', 'BEAM2', 'tem']
f3 = [1] * 4
t3 = ['CS', 'ST', 'CB']
midas.com_f('me', com3, f3, t3, 0, mct_l)

com4 = ['DEAD', 'BEAM1', 'BEAM2', 'tem']
f4 = [1.32, 1.32, 1.54, 1.54]
t4 = ['ST', 'ST', 'ST', 'CB']
midas.com_f('mu', com4, f4, t4, 0, mct_l)

# 导出 mct 文件 ====================================================================================================

midas_str = '\n'.join(mct_l)
with open(mct_file, 'w') as f:
    f.write(midas_str)




