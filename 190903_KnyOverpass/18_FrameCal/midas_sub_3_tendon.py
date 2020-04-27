import numpy as np
import pandas as pd
import kny_tool
import kny_sub
import xlwings as xw
import pprint
import time
import pier_post

# 参数 ==============================================================================================================

# 桥梁参数 --------------------------------------------------------------------------------


def change_side(x):
    return sorted([-i for i in x])


def get_l(x):
    return x[1] - x[0]


sub_pd = pd.read_json('../IO/sub_df_now_2.json', orient='split')
my_sub = 'F2', 'F3', 'FC1', 'FC2'
sub_my_pd = pd.DataFrame(columns=['cap', 'pier', 'bridge', 'ramp', 'type', 'pier_h'])

for i, j in sub_pd[sub_pd['Type'].isin(my_sub)].iterrows():
    if abs(j['pier'][0]) > abs(j['pier'][-1]):
        sub_my_pd.loc[j['span_name']] = [
            change_side(j['cap']), change_side(j['pier']),
            change_side(j['bridge']), change_side(j['ramp']), j['Type'], j['pier_h']]
    else:
        sub_my_pd.loc[j['span_name']] = [j['cap'], j['pier'], j['bridge'], j['ramp'], j['Type'], j['pier_h']]

sub_my_pd['cap_l'] = sub_my_pd['cap'].map(lambda x: x[1] - x[0])
# sub_f3 = sub_my_pd[sub_my_pd['type'] == 'F3']
# sub_f3['cap_span'] = sub_f3['pier'].map(lambda x: [x[1] - x[0], x[2] - x[1]])
# xw.Range('A1').value = sub_f3['cap_span'].tolist()
# sub_my_pd.loc[22297.108, 'pier'][0] += 3
# sub_my_pd.loc[22327.108, 'pier'][0] += 5
# sub_my_pd.loc[16925, 'type'] = 'FC1S'
# sub_my_pd.loc[16430, 'type'] = 'FC2S'


# 截面参数 --------------------------------------------------------------------------------

psc_dic = {                             # 盖梁、桥墩截面
    'C1': [2.2, 1.1, 2, 0.01],          # 盖梁截面，阶梯形 b1/h1/b2/h2
    'C2': [2.2, 1.1, 2, 0.4],
    'C3': [2.2, 1.1, 2, 1.1],
    'C4': [2.2, 1.1, 2, 1.4],
    'C5': [2.2, 1.1, 2, 1.9],
    'C6': [2.2, 1.1, 2, 0.6],
    'C7': [2.2, 1.1, 2, 0.5],
    'P1': [1.8, 1.8],                    # 桥墩截面，矩形 b/h
    'P2': [2, 1.8],
    'P3': [2.2, 1.8],
    'P4': [1.6, 1.6],
    'P5': [4, 1.8]
}

cap_sec_dic = {                         # 不同下部结构盖梁截面
    'F2': ('C3', ),                     # 通长
    'F3': ('C3', 'C5', 'C3'),           # 边、中、边
    'FC1': ('C1', 'C4', 'C6', 'C3'),    # 悬臂边、主中、跨中、支撑边
    'FC2': ('C1', 'C3', 'C2', 'C3'),    # 悬臂边、主中、跨中、支撑边
    'FC1S': ('C1', 'C5', 'C3', 'C3'),   # 超级悬臂 1
    'FC2S': ('C1', 'C3', 'C3', 'C3'),    # 超级悬臂 1
    'F2S': ('C4', ),
    'F2X': ('C7', )
}

tendon_sec_dic = {                      # 不同下部结构对应的预应力关注截面
    'F2': ('C3', ),
    'F3': ('C5', 'C3', 'C3'),
    'FC1': ('C4', 'C6'),
    'FC2': ('C3', 'C2'),
    'FC1S': ('C5', 'C3'),
    'FC2S': ('C4', 'C3'),
    'F2S': ('C4', ),
    'F2X': ('C7', )
}

pier_sec_dic = {                        # 不同下部类型桥墩截面（左-右）
    'F2': ('P1', 'P1'),
    'F3': ('P1', 'P2', 'P1'),
    'FC1': ('P5', 'P1'),
    'FC2': ('P1', 'P1', 'P1'),
    'FC1S': ('P5', 'P1'),
    'FC2S': ('P1', 'P1', 'P1'),
    'F2S': ('P1', 'P1'),
    'F2X': ('P4', 'P4')
}

pier_link_dic = {               # 不同下部类型连接方式
    'F2': (1, 1),
    'F3': (1, 1, 1),
    'FC1': (1, 1),
    'FC2': (1, 1, 1),
    'FC1S': (1, 1),
    'FC2S': (1, 1, 1),
    'F2S': (1, 1),
    'F2X': (1, 1)
}

fc_cap_l1 = 5.9                         # 框架墩右侧预制块宽度，m

# 连接 cad
secs = kny_tool.get_my_sec('sec_0410.dwg')
sec_box = kny_tool.get_sec_box(secs)        # 获取截面边框

secs_midas = [secs.secs_to_midas(pt='CT')[i]
              for i in range(len(secs.secs)) if 'B' in secs.sec_name[i]]

# # 预应力参数
# f_lim = [22.4, 22.4, -2, -2]        # 混凝土容许应力（施工、使用、施工、使用）
# tendon_curve_r = 10                 # 预应力半径，m
# tendon_per_n = 15                   # 单束预应力股数
# tendon_edge = 0.3                   # 预应力到边缘距离，m
# tendon_between = 0.35               # 预应力之间横向距离，m


# 建立模型 ============================================================================================================

# 读取桩号及信息
sub_inf_book = xw.Book('mysub_0414.xlsx')
all_station = sub_inf_book.sheets['creat_sub']['A2'].expand('down').value            # 桩号
all_support_or_not = sub_inf_book.sheets['creat_sub']['C2'].expand('down').value     # 墩-盖梁是否设置支座

# 建立所有模型
all_model_inf = {}
for i, j in enumerate(all_station):
    print(j)
    if sub_my_pd.loc[j]['type'] in ['F2']:
        if sub_my_pd.loc[j]['cap_l'] < 17:
            sub_my_pd.loc[j, 'type'] = 'F2X'
        elif sub_my_pd.loc[j]['cap_l'] > 25:
            sub_my_pd.loc[j, 'type'] = 'F2S'
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
                                    (bridge.sec_dic['C5'], bridge.sec_dic['C3']),
                                    (bridge.sec_dic['C4'], bridge.sec_dic['C6']),
                                    (bridge.sec_dic['C6'], bridge.sec_dic['C4']),
                                    (bridge.sec_dic['C6'], bridge.sec_dic['C3']),
                                    (bridge.sec_dic['C3'], bridge.sec_dic['C6']),))
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

# 手动配置预应力
for i, j in enumerate(all_station):
    # if sub_my_pd.loc[j]['type'] not in ['F2', 'F2S', 'F2X']:
    #     continue
    i_inf = sub_my_pd.loc[j]
    if i_inf['type'] == 'FC1':
        ni, to_top = kny_tool.tendon_fc1(i_inf['cap_l'])
    elif i_inf['type'] == 'FC2':
        ni, to_top = kny_tool.tendon_fc2(i_inf['cap_l'])
    elif i_inf['type'] == 'F3':
        ni, to_top = kny_tool.tendon_f3(i_inf['cap_l'])
    elif i_inf['type'] in ['F2', 'F2S', 'F2X']:
        ni, to_top = kny_tool.tendon_f2(i_inf['cap_l'])
    else:
        print('种类错误！')
        raise Exception
    i_model = all_model_inf[j]
    i_elems = i_model.elem
    i_nodes = i_model.node
    i_elems['x'] = i_elems['n1'].map(lambda x: i_nodes.loc[x]['x'])
    i_model.tendon_inf['tendon_ni'] = ni
    i_model.tendon_inf['tendon_to_top'] = to_top
    i_model.add_tendon(cap_sec_dic[i_model.bridge_inf['type']], secs)


# 保存 mct 文件
for i in all_model_inf.keys():
    note = '_基础配置'
    str_now = time.strftime('%y%m%d%H%M', time.localtime())
    mct_file = f'..\\IO\\wow_{str_now}_{i}{note}.mct'

    with open(mct_file, 'w', encoding='utf-8') as change_side:
        change_side.write('\n'.join(all_model_inf[i].mct_l))


# 计算桥墩承载力及钢筋
# for i, j in enumerate(all_station):
#     if int(j) == j:
#         all_station[i] = int(j)

for i, j in enumerate(all_station):
    # if sub_my_pd.loc[j]['type'] not in ['F3']:
    #     continue
    i_sht = xw.books['all_result_0416.xlsx'].sheets[j]
    i_results = i_sht['A1'].options(pd.DataFrame, expand='table').value
    i_elems = all_model_inf[j].elem
    i_nodes = all_model_inf[j].node
    i_elems['x'] = i_elems['n1'].map(lambda x: i_nodes.loc[x]['x'])
    i_pier_elem = i_elems[(i_elems['what'] == 'pier') & (i_elems['x'] == 0)]
    i_pier_results = pier_post.result_myz(i_pier_elem, i_results)
    pier_rectangles = pier_post.creat_rectangle(i_pier_elem, all_model_inf[j].sec_dic, sec_box, rebar=32)
    pier_res = pier_post.pier_capacity(i_pier_elem, pier_rectangles, i_pier_results)
    pier_crack = pier_post.pier_crack(i_pier_elem, pier_rectangles, i_pier_results)
    cap_check, crack_check = pier_post.pier_checkout(i_pier_elem, pier_res, pier_crack, i_pier_results)
    i_sht['M1'].value = cap_check
    i_sht['M10'].value = crack_check
    i_sht['V1'].value = pier_res
    i_sht['AQ1'].value = pier_crack

# 提取墩底力
for i, j in enumerate(all_station):
    # if sub_my_pd.loc[j]['type'] not in ['F3']:
    #     continue
    print(j)
    i_sht = xw.books['all_result_0416.xlsx'].sheets[j]
    i_results = i_sht['A1'].options(pd.DataFrame, expand='table').value

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
    pier_bot_results = i_results.loc[pier_bots]
    i_sht['AV1'].value = pier_bot_results

#
#
#
# # 获取所有计算结果
# sub_result_book = xw.Book('tendon_result.xlsx')
# all_results = {}
# for i, j in enumerate(all_station):
#     i_result = sub_result_book.sheets[i]['A1'].options(pd.DataFrame, expand='table').value
#     all_results[j] = i_result
#
# # 获取预应力计算所需结果
# cap_cases = ['DEAD', 'ms(全部)', 'me(全部)', 'mu(全部)']
# tendon_secs_f = {}
# for i, j in enumerate(all_station):
#     i_elems = all_model_inf[j].elem
#     i_nodes = all_model_inf[j].node
#     i_elems['x'] = i_elems['n1'].map(lambda x: i_nodes.loc[x]['x'])
#     i_elems['y1'] = i_elems['n1'].map(lambda x: i_nodes.loc[x]['y'])
#     i_elems['y2'] = i_elems['n2'].map(lambda x: i_nodes.loc[x]['y'])
#     i_cap_elem = i_elems[(i_elems['what'] == 'cap') & (i_elems['x'] == 0)]
#     i_result = all_results[j]
#
#     if sub_my_pd.loc[j]['type'] == 'F3':
#         i_cap_elem_1 = i_cap_elem[i_cap_elem['y2'] <= sub_my_pd.loc[j]['pier'][1]]
#         i_cap_elem_2 = i_cap_elem[i_cap_elem['y1'] >= sub_my_pd.loc[j]['pier'][1]]
#         M1 = []
#         M2 = []
#         M3 = []
#         for m in cap_cases:
#             m_result = i_result[i_result['荷载'] == m]
#             m_M1 = m_result.loc[i_cap_elem.index]['弯矩-y (kN*m)'].min()
#             m_M2 = m_result.loc[i_cap_elem_1.index]['弯矩-y (kN*m)'].max()
#             m_M3 = m_result.loc[i_cap_elem_2.index]['弯矩-y (kN*m)'].max()
#             M1.append(m_M1)
#             M2.append(m_M2)
#             M3.append(m_M3)
#         tendon_secs_f[j] = [M1, M2, M3]
#     else:
#         M_max_cases = []
#         M_min_cases = []
#         for m in cap_cases:
#             m_result = i_result[i_result['荷载'] == m]
#             # i_str = f'{j}\t{m}\t{m_result.index[0]}'
#             M_max = m_result.loc[i_cap_elem.index]['弯矩-y (kN*m)'].max()
#             M_min = m_result.loc[i_cap_elem.index]['弯矩-y (kN*m)'].min()
#             M_max_cases.append(M_max)
#             M_min_cases.append(M_min)
#         if sub_my_pd.loc[j]['type'] == 'F2':
#             tendon_secs_f[j] = [M_max_cases]
#         elif sub_my_pd.loc[j]['type'] in ['FC1', 'FC1S']:
#             tendon_secs_f[j] = [M_min_cases, M_max_cases]
#         elif sub_my_pd.loc[j]['type'] in ['FC2', 'FC2S']:
#             tendon_secs_f[j] = [M_min_cases, M_max_cases]
#
# # 获取预应力配置信息
# tendon_infs = {}
# for i, j in enumerate(all_station):
#     print(j)
#     i_tendon_sec = tendon_sec_dic[sub_my_pd.loc[j]['type']]
#     i_model = all_model_inf[j]
#     i_model.tendon_cal(i_tendon_sec, secs, sec_box, tendon_secs_f[j])
#     i_model.add_tendon(cap_sec_dic[i_model.bridge_inf['type']], secs)
#
# # 保存 mct 文件
# for i in all_model_inf.keys():
#     note = '_手动配置预应力'
#     str_now = time.strftime('%y%m%d%H%M', time.localtime())
#     mct_file = f'..\\IO\\wow_{str_now}_{i}{note}.mct'
#
#     with open(mct_file, 'w', encoding='utf-8') as change_side:
#         change_side.write('\n'.join(all_model_inf[i].mct_l))
#
#
# # 计算桥墩承载力及钢筋
# for i, j in enumerate(all_station):
#     if int(j) == j:
#         all_station[i] = int(j)
#
# for i, j in enumerate(all_station):
#     sht_name = sub_my_pd.loc[j]['type']
#     if sht_name == 'FC1S':
#         sht_name = 'FC1'
#     elif sht_name == 'FC2S':
#         sht_name = 'FC2'
#     i_sht = xw.books[f'{sht_name}.xlsx'].sheets[str(j)]
#     i_results = i_sht['A1'].options(pd.DataFrame, expand='table').value
#     i_elems = all_model_inf[j].elem
#     i_nodes = all_model_inf[j].node
#     i_elems['x'] = i_elems['n1'].map(lambda x: i_nodes.loc[x]['x'])
#     i_pier_elem = i_elems[(i_elems['what'] == 'pier') & (i_elems['x'] == 0)]
#     i_pier_results = pier_post.result_myz(i_pier_elem, i_results)
#     pier_rectangles = pier_post.creat_rectangle(i_pier_elem, all_model_inf[j].sec_dic, sec_box)
#     pier_res = pier_post.pier_capacity(i_pier_elem, pier_rectangles, i_pier_results)
#     pier_crack = pier_post.pier_crack(i_pier_elem, pier_rectangles, i_pier_results)
#     cap_check, crack_check = pier_post.pier_checkout(i_pier_elem, pier_res, pier_crack, i_pier_results)
#     i_sht['M1'].value = cap_check
#     i_sht['M10'].value = crack_check
#     i_sht['V1'].value = pier_res
#     i_sht['AQ1'].value = pier_crack
#
#
#




