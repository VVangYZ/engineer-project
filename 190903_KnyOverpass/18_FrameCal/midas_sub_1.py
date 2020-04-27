import numpy as np
import midas1
import win32com.client as win32
import cad
import pandas as pd
import tendon_new
import time
import math
import kny_tool
import kny_sub
import pickle
import pier_post
import xlwings as xw

# 参数 ==============================================================================================================

# 文件参数 --------------------------------------------------------------------------------

bridge_station = 22297.108
note = '_魔改版本'
str_now = time.strftime('%y%m%d%H%M', time.localtime())
mct_file = f'..\\IO\\wow_{str_now}_{bridge_station}{note}.mct'

# 桥梁参数 --------------------------------------------------------------------------------


def change_side(x):
    return sorted([-i for i in x])


def get_l(x):
    return x[1] - x[0]


sub_pd = pd.read_json('../IO/sub_df.json', orient='split')
my_sub = 'F2', 'F3', 'FC1', 'FC2'
sub_my_pd = pd.DataFrame(columns=sub_pd.columns)

for i, j in sub_pd[sub_pd['type'].isin(my_sub)].iterrows():
    if abs(j['pier'][0]) > abs(j['pier'][-1]):
        sub_my_pd.loc[i] = [
            change_side(j['cap']), change_side(j['pier']),
            change_side(j['bridge']), change_side(j['ramp']), j['type'], j['pier_h']]
    else:
        sub_my_pd.loc[i] = j

# sub_my_pd['cap_l'] = sub_my_pd['cap'].map(get_l)
# sub_my_pd['bridge_l'] = sub_my_pd['bridge'].map(get_l)
# sub_my_pd['beam_num'] = sub_my_pd['bridge_l'].map(kny_tool.num_from_width)
# sub_my_pd.to_csv('../IO/my_sub.csv')
# sub_fc2 = sub_my_pd[sub_my_pd['type'] == 'FC2']


# 截面参数 --------------------------------------------------------------------------------

psc_dic = {                             # 盖梁、桥墩截面
    'C1': [2.2, 1.1, 2, 0.01],          # 盖梁截面，阶梯形 b1/h1/b2/h2
    'C2': [2.2, 1.1, 2, 0.4],
    'C3': [2.2, 1.1, 2, 1.1],
    'C4': [2.2, 1.1, 2, 1.4],
    'C5': [2.2, 1.1, 2, 1.9],
    'P1': [1.8, 1.8],                    # 桥墩截面，矩形 b/h
    'P2': [2, 1.8],
    'P3': [2.2, 1.8],
    'P4': [2.4, 1.8],
    'P5': [4, 1.8]
}

cap_sec_dic = {                         # 不同下部结构盖梁截面
    'F2': ('C3', ),                     # 通长
    'F3': ('C3', 'C5', 'C3'),           # 边、中
    'FC1': ('C1', 'C4', 'C2', 'C3'),    # 悬臂边、主中、跨中、支撑边
    'FC2': ('C1', 'C3', 'C2', 'C3')     # 悬臂边、主中、跨中、支撑边
}

pier_sec_dic = {                        # 不同下部类型桥墩截面（左-右）
    'F2': ('P1', 'P1'),
    'F3': ('P1', 'P2', 'P1'),
    'FC1': ('P5', 'P1'),
    'FC2': ('P1', 'P1', 'P1')
}

pier_link_dic = {               # 不同下部类型连接方式
    'F2': (1, 1),
    'F3': (1, 1, 1),
    'FC1': (1, 1),
    'FC2': (1, 1, 1)
}

fc_cap_l1 = 5.9                         # 框架墩右侧预制块宽度，m

# 连接 cad
secs = kny_tool.get_my_sec()
sec_box = kny_tool.get_sec_box(secs)        # 获取截面边框

# 建立模型 ============================================================================================================

# 初始化
bridge = kny_sub.KnySub(sub_my_pd.loc[bridge_station])

a = sub_my_pd.loc[bridge_station, 'pier']
sub_my_pd.loc[bridge_station, 'pier'][0] = a[0] + 3


# 截面 --------------------------------------------------------------------------------

secs_midas = [secs.secs_to_midas(pt='CT')[i]
              for i in range(len(secs.secs)) if 'B' in secs.sec_name[i]]

bridge.add_my_sec(secs_midas)

bridge.add_psc_sec(psc_dic)
bridge.add_simple_variable_sec(((bridge.sec_dic['C1'], bridge.sec_dic['C3']),
                                (bridge.sec_dic['C3'], bridge.sec_dic['C1']),
                                (bridge.sec_dic['C1'], bridge.sec_dic['C4']),
                                (bridge.sec_dic['C4'], bridge.sec_dic['C1']),
                                (bridge.sec_dic['C3'], bridge.sec_dic['C2']),
                                (bridge.sec_dic['C2'], bridge.sec_dic['C3']),
                                (bridge.sec_dic['C4'], bridge.sec_dic['C2']),
                                (bridge.sec_dic['C2'], bridge.sec_dic['C4']),
                                (bridge.sec_dic['C3'], bridge.sec_dic['C5']),
                                (bridge.sec_dic['C5'], bridge.sec_dic['C3'])))

# 几何模型 --------------------------------------------------------------------------------

# 主梁
bridge.beam_create()

# 桥墩和盖梁
pier_sec, cap_loc, cap_sec = kny_tool.get_pier_cap_inf(
    bridge, pier_sec_dic, cap_sec_dic, sec_box, fc_cap_l1)

cap_height = kny_tool.get_cap_height(
    cap_loc, cap_sec, bridge.bridge_inf['pier'], sec_box)

bridge.pier_create(pier_sec, cap_height, sec_box, pier_link_dic[bridge.bridge_inf['type']])
bridge.cap_create(cap_loc, cap_sec)

bridge.node_elem_mct()
bridge.variable_sec_group()
bridge.struct_group()

# 边界条件 --------------------------------------------------------------------------------

bridge.boundary()
bridge.rigid_link()
bridge.elastic_link(pier_link_dic[bridge.bridge_inf['type']])

# 荷载 --------------------------------------------------------------------------------

# 自重
bridge.self_weight()

# 二期铺装
bridge.pavement()

# 温度
bridge.tem()

# 施工阶段
bridge.stage()

# 地震
bridge.earthquake()

# 车辆
bridge.vehicle()
bridge.brake_force()

# 风
bridge.wind()

# 荷载组合
bridge.load_com()

# 保存数据 =========================================================================================================

with open(mct_file, 'w', encoding='utf-8') as change_side:
    change_side.write('\n'.join(bridge.mct_l))

# bridge.elem.to_json(r'../IO/elem_test.json', orient='split')
# bridge.node.to_json(r'../IO/node_test.json', orient='split')


# 后处理 =========================================================================================================

# 获取桥墩单元
bridge.elem['x'] = bridge.elem['n1'].map(lambda x: bridge.node.loc[x]['x'])
pier_elem = bridge.elem[(bridge.elem['what'] == 'pier') & (bridge.elem['x'] == 0)]

# pier_elem.loc[[318, 342], 's'] = bridge.sec_dic['P4']
# pier_elem.loc[[317, 341], 's'] = bridge.sec_dic['P3']

# 桥墩结果
all_results = pier_post.get_all_results()
pier_results = pier_post.result_myz(pier_elem, all_results)

# 桥墩截面及钢筋
pier_rectangles = pier_post.creat_rectangle(pier_elem, bridge.sec_dic, sec_box, space=120)

# 承载力及裂缝计算
pier_res = pier_post.pier_capacity(pier_elem, pier_rectangles, pier_results)
pier_crack = pier_post.pier_crack(pier_elem, pier_rectangles, pier_results)

# 承载力及裂缝验算结果
cap_check, crack_check = pier_post.pier_checkout(pier_elem, pier_res, pier_crack, pier_results)
pier_post.print_check(cap_check, crack_check)

# 计算结果写入 excel
xw.Range('M1').value = cap_check
xw.Range('M10').value = crack_check
xw.Range('V1').value = pier_res
xw.Range('AQ1').value = pier_crack




