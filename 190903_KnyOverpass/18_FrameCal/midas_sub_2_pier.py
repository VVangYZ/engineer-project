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

sub_my_pd.loc[22297.108, 'pier'][0] += 3
sub_my_pd.loc[22327.108, 'pier'][0] += 5
sub_my_pd.loc[22297.189, 'type'] = ''


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

sub_inf_book = xw.Book('my_sub.xlsx')
all_station = sub_inf_book.sheets['my_model']['A2'].expand('down').value
all_support_or_not = sub_inf_book.sheets['my_model']['B2'].expand('down').value

sub_result_book = xw.Book('pier_results_toZLZ.xlsx')

all_model_inf = {}

secs_midas = [secs.secs_to_midas(pt='CT')[i]
              for i in range(len(secs.secs)) if 'B' in secs.sec_name[i]]

for i, j in enumerate(all_station):
    bridge = kny_sub.KnySub(sub_my_pd.loc[j])
    i_pier_link = list(pier_link_dic[bridge.bridge_inf['type']])

    if all_support_or_not[i] == 1:
        i_pier_link[-1] = 0

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
    bridge.beam_create()
    pier_sec, cap_loc, cap_sec = kny_tool.get_pier_cap_inf(
        bridge, pier_sec_dic, cap_sec_dic, sec_box, fc_cap_l1)

    cap_height = kny_tool.get_cap_height(
        cap_loc, cap_sec, bridge.bridge_inf['pier'], sec_box)

    bridge.pier_create(pier_sec, cap_height, sec_box, i_pier_link)
    bridge.cap_create(cap_loc, cap_sec)

    bridge.node_elem_mct()
    bridge.variable_sec_group()
    bridge.struct_group()

    bridge.boundary()
    bridge.rigid_link()
    bridge.elastic_link(i_pier_link)

    bridge.self_weight()
    bridge.pavement()
    bridge.tem()
    bridge.stage()
    bridge.earthquake()
    bridge.vehicle()
    bridge.brake_force()
    bridge.wind()
    bridge.load_com()

    all_model_inf[j] = bridge

all_results = {}

for i, j in enumerate(all_station):
    i_result = sub_result_book.sheets[i]['A1'].options(pd.DataFrame, expand='table').value
    all_results[j] = i_result

for i, j in enumerate(all_station):
    i_elems = all_model_inf[j].elem
    i_nodes = all_model_inf[j].node
    i_elems['x'] = i_elems['n1'].map(lambda x: i_nodes.loc[x]['x'])
    i_elems['y'] = i_elems['n1'].map(lambda x: i_nodes.loc[x]['y'])
    i_pier_elem = i_elems[(i_elems['what'] == 'pier') & (i_elems['x'] == 0)]
    i_pier_loc = sub_my_pd.loc[j]['pier']
    pier_bots = []
    for m in i_pier_loc:
        m_pier = i_pier_elem[i_pier_elem['y'] == m].index
        # m_pier_top = m_pier[-1]
        pier_bots.append(m_pier[0])
    pier_bot_results = all_results[j].loc[pier_bots]
    sub_result_book.sheets[i]['M1'].value = pier_bot_results






