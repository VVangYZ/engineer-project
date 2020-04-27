from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xlwings as xw
import cad_sub
import kny_tool
# from input_data1 import get_distance, get_ei

# 定义类 ===========================================================================================================
# Base = declarative_base()
#
#
# class Sub(Base):
#     """
#     定义下部构件类别
#     """
#     __tablename__ = "sub_tbl"
#     Line = Column(String)
#     Bridge = Column(String)
#     Station = Column(Float, primary_key=True)
#     Type = Column(String)
#     LeftWidth = Column(Float)
#     RightWidth = Column(Float)
#     SpaceList = Column(String)
#     H0 = Column(Float)
#     H1 = Column(Float)
#     SlopLeft = Column(Float)
#     SlopRight = Column(Float)
#
#
# class Ei(Base):
#     """
#     定义 ei 数据类别
#     """
#     __tablename__ = "ei_tbl"
#     Name = Column(String, primary_key=True)
#     ICD = Column(String)
#     SQX = Column(String)
#     DMX = Column(String)
#     CG = Column(String)


# 定义主线类别
# class Sec(Base):
#     __tablename__ = "sec202"
#     Line = Column(Integer)
#     Bridge = Column(Integer)
#     Station = Column(Float, primary_key=True)
#     Span = Column(Float)
#     WidthRight = Column(Float)
#     WidthLeft = Column(Float)
#     FundType = Column(Float)
#     sub_sta = Column(String, ForeignKey('sub_tbl.Station'))


def sheet_to_df(sheets, engine):
    """
    从数据库获取数据转化为 DataFrame
    :param sheets: 表名
    :return: 合并的 DataFrame 变量
    """
    i_dic = {}
    for i in sheets:
        sql_query = f'select * from {i};'
        i_dic[i] = pd.read_sql_query(sql_query, engine)
    i_df = pd.concat(i_dic.values())
    return i_df


# 连接数据库 ===========================================================================================================
engine = create_engine('mysql+pymysql://wyz:wang1234@cdb-2ashfo5g.bj.tencentcdb.com:10033/nep2020')
DBSession = sessionmaker(bind=engine)
session = DBSession()


# 读取上部数据 ========================================================================================================

sub_tbl = ['sub_tbl']
sub_df = sheet_to_df(sub_tbl, engine)
sub_df['bridge'] = sub_df['SpaceList'].map(lambda x: [0])
sub_df['cap'] = sub_df['SpaceList'].map(lambda x: [0])
sub_df['ramp'] = sub_df['SpaceList'].map(lambda x: [0])
bridges_df = sheet_to_df(['span_tbl'], engine)

# 添加桥面信息
for i, j in sub_df.iterrows():
    i_bridge = bridges_df[(bridges_df['Station'] == j['Station']) & (bridges_df['bridge_name'] == j['bridge_name'])]
    i_bridge_right = i_bridge.iloc[0]['deck_wr']
    i_bridge_left = i_bridge.iloc[0]['deck_wl']
    sub_df.loc[i, 'BridgeLeft'] = i_bridge_left
    sub_df.loc[i, 'BridgeRight'] = i_bridge_right
    sub_df.at[i, 'bridge'] = [-i_bridge_left, i_bridge_right]
    sub_df.at[i, 'cap'] = [-j['LeftWidth'], j['RightWidth']]


# 修正桥墩位置（以桥面左点为参照修正为以路线中心为参照）
def pier_loc_list(s):
    l1 = [float(i) for i in s.split(',')]
    l2 = []
    for i, j in enumerate(l1):
        if i != 0 and j == 0:
            pass
        else:
            l2.append(j)
    return np.array(l2)


sub_df['pier'] = sub_df['SpaceList'].map(pier_loc_list) - sub_df['BridgeLeft']
sub_df['pier'] = sub_df['pier'].map(lambda x: np.around(x, decimals=4))
sub_df['pier_h'] = sub_df['H0'] - sub_df['H1']
# cad_sub.plot_sub(sub_df)
sub_df.to_json(r'../IO/sub_df_now_0422.json', orient='split')


# 提取框架墩信息
my_type = ['FC1', 'FC2', 'F2', 'F3']
my_sub_df = sub_df[sub_df['Type'].isin(my_type)]
my_sub_df['block_type'] = my_sub_df['SpaceList'].map(lambda x: [0])
my_sub_df['block_length'] = my_sub_df['SpaceList'].map(lambda x: [0])
my_sub_df['block_weight'] = my_sub_df['SpaceList'].map(lambda x: [0])
my_sub_df['cap_length'] = my_sub_df['LeftWidth'] + my_sub_df['RightWidth']
my_sub_df['bridge_length'] = my_sub_df['BridgeLeft'] + my_sub_df['BridgeRight']

my_sub_df['P1'] = my_sub_df['pier'].map(lambda x: x[0])
my_sub_df['P2'] = my_sub_df['pier'].map(lambda x: x[1])
my_sub_df['P3'] = my_sub_df['pier'].map(lambda x: x[2] if len(x) == 3 else 0)
my_sub_df['span1'] = my_sub_df['pier'].map(lambda x: x[1] - x[0])
my_sub_df['span2'] = my_sub_df['pier'].map(lambda x: x[2] - x[1] if len(x) == 3 else 0)


# 写入分块信息
for i, j in my_sub_df.iterrows():
    blk_edge = []
    if j['Type'] == 'FC1':
        side = 1 if abs(j['P1']) < abs(j['P2']) else -1
        l_variable = j['cap_length'] - 6.5 - 7.3 - 4.15 - 8.4 - 0.3 * 4
        if l_variable > 3:
            blk_type = ['CB01', 'CB02', 'CB11', 'CB13', 'CB12'][::side]
            blk_length = [6.5, 7.3, 4.15, l_variable, 8.4][::side]
        else:
            l_variable = j['cap_length'] - 6.5 - 7.3 - 8.4 - 0.3 * 3
            blk_type = ['CB01', 'CB02', 'CB11', 'CB12'][::side]
            blk_length = [6.5, 7.3, l_variable, 8.4][::side]
    elif j['Type'] == 'FC2':
        side = 1 if abs(j['P1']) < abs(j['P3']) else -1
        l_variable = j['cap_length'] - 11.7 - 8.45 - 8.4 - 0.3 * 3
        if l_variable > 3:
            blk_type = ['CB06', 'CB14', 'CB16', 'CB15'][::side]
            blk_length = [11.7, 8.45, l_variable, 8.4][::side]
        else:
            l_variable = j['cap_length'] - 11.7 - 8.4 - 0.3 * 2
            blk_type = ['CB06', 'CB14', 'CB15'][::side]
            blk_length = [11.7, l_variable, 8.4][::side]
    elif j['Type'] == 'F3':
        blk_type = []
        blk_length = []
        l1_variable = j['span1'] - 5 - 0.3 + 1.4
        if l1_variable <= 11.5:
            blk_type += ['CB18', 'CB21']
            blk_length += [l1_variable, 10]
        else:
            l1_variable = j['span1'] - 5 * 2 - 0.3 * 2 + 1.4
            if l1_variable <= 11.5:
                blk_type += ['CB18', 'CB07', 'CB21']
                blk_length += [5, l1_variable, 10]
            else:
                blk_type += ['CB18', 'CB07', 'CB21']
                l1_variable = j['span1'] - 5 - 11.5 - 0.3 * 2 + 1.4
                blk_length += [l1_variable, 11.5, 10]

        l2_variable = j['span2'] - 5 - 0.3 + 1.4
        if l2_variable <= 11.5:
            blk_type += ['CB18']
            blk_length += [l2_variable]
        else:
            l2_variable = j['span2'] - 5 * 2 - 0.3 * 2 + 1.4
            if l2_variable <= 11.5:
                blk_type += ['CB07', 'CB18']
                blk_length += [l2_variable, 5]
            else:
                blk_type += ['CB07', 'CB18']
                l2_variable = j['span2'] - 5 - 11.5 - 0.3 * 2 + 1.4
                blk_length += [11.5, l2_variable]
    elif j['Type'] == 'F2':
        edge1 = j['P1'] + j['LeftWidth']
        edge2 = j['RightWidth'] - j['P2']
        if max(edge1, edge2) > 1.41:
            side = 1 if edge1 > edge2 + 0.1 else -1
            edge_blk_length = max(edge1, edge2) + 4
            l_variable = j['cap_length'] - edge_blk_length - 0.3
            if l_variable <= 11.5:
                blk_type = ['CB18', 'CB18']
                blk_length = [edge_blk_length, l_variable][::side]
            else:
                blk_type = ['CB18', 'CB07', 'CB18']
                l_variable = j['cap_length'] - edge_blk_length - 5 - 0.3 * 2
                if l_variable <= 11.5:
                    blk_length = [edge_blk_length, l_variable, 5][::side]
                else:
                    l_variable = j['cap_length'] - edge_blk_length - 11.5 - 0.3 * 2
                    blk_length = [edge_blk_length, 11.5, l_variable][::side]
            blk_edge = [edge_blk_length - 4] + (len(blk_type) - 1) * [0]
            blk_edge = blk_edge[::side]
        else:
            l_variable = (j['cap_length'] - 0.3) / 2
            if j['cap_length'] < 17:
                blk_type = ['CB17', 'CB17']
                blk_length = [l_variable, l_variable]
            elif j['cap_length'] < 22:
                blk_type = ['CB18', 'CB18']
                blk_length = [l_variable, l_variable]
            elif j['cap_length'] < 25:
                blk_type = ['CB18', 'CB07', 'CB18']
                l_variable = (j['cap_length'] - 10 - 0.3 * 2) / 2
                blk_length = [l_variable, 10, l_variable]
            else:
                blk_type = ['CB19', 'CB20', 'CB19']
                l_variable = (j['cap_length'] - 10 - 0.3 * 2) / 2
                blk_length = [l_variable, 10, l_variable]
    else:
        print('类型错误')
        raise Exception
    blk_edge = [0] * len(blk_type) if len(blk_edge) == 0 else blk_edge
    blk_instance = [kny_tool.KnyBlock(i, j, k) for i, j, k in zip(blk_type, blk_length, blk_edge)]
    blk_weight = [i.weight for i in blk_instance]
    my_sub_df.at[i, 'block_type'] = blk_type
    my_sub_df.at[i, 'block_length'] = [round(i, 4) for i in blk_length]
    my_sub_df.at[i, 'block_weight'] = [round(i, 3) for i in blk_weight]

# my_sub_df.to_csv('frame_sub_0410.csv')
cad_sub.plot_sub_with_joint(my_sub_df)

xw.Range('A1').value = my_sub_df

num = 1
for i, j in my_sub_df.iterrows():
    num += 1
    xw.Range(f'AC{num}').value = j['block_type']
    xw.Range(f'AH{num}').value = j['block_length']
    xw.Range(f'AM{num}').value = j['block_weight']


# 非框架墩信息
# hh_sub_df = sub_df[~sub_df['Type'].isin(my_type)]
# hh_sub_df['cap_length'] = hh_sub_df['LeftWidth'] + hh_sub_df['RightWidth']
# hh_sub_df['bridge_length'] = hh_sub_df['BridgeLeft'] + hh_sub_df['BridgeRight']
#
# hh_sub_df['P1'] = hh_sub_df['pier'].map(lambda x: x[0])
# hh_sub_df['P2'] = hh_sub_df['pier'].map(lambda x: x[1] if len(x) == 2 else 0)
# hh_sub_df['P3'] = hh_sub_df['pier'].map(lambda x: x[2] if len(x) == 3 else 0)
#
# xw.Range('A1').value = hh_sub_df
# cad_sub.plot_sub(hh_sub_df, hh_sub_df['Type'].unique())


#
#
# f2_df = sub_df[sub_df['Type'] == 'F2']
# f2_df['pier_distance'] = f2_df['pier'].map(lambda x: x[1] - x[0])
# f2_df['cap'] = f2_df['LeftWidth'] + f2_df['RightWidth']
# f2_df['P1'] = f2_df['pier'].map(lambda x: x[0])
# f2_df['P2'] = f2_df['pier'].map(lambda x: x[1])
# xw.Range('A1').value = f2_df
#
# f3_df = sub_df[sub_df['Type'] == 'F3']
# f3_df['cap'] = f3_df['LeftWidth'] + f3_df['RightWidth']
# f3_df['span1'] = f3_df['pier'].map(lambda x: x[1] - x[0])
# f3_df['span2'] = f3_df['pier'].map(lambda x: x[2] - x[1])
# f3_df['P1'] = f3_df['pier'].map(lambda x: x[0])
# f3_df['P2'] = f3_df['pier'].map(lambda x: x[1])
# f3_df['P3'] = f3_df['pier'].map(lambda x: x[2])
# xw.Range('A1').value = f3_df
#
#
# # 框架墩修正为左向右
# for i, j in my_sub_df.iterrows():
#     if j['Type'] in ['FC1', 'FC2']:
#         if abs(j['pier'][-1]) < abs(j['pier'][0]):
#             my_sub_df.at[i, 'pier'] = j['pier'][::-1] * -1
#             my_sub_df.loc[i, 'LeftWidth'] = j['RightWidth']
#             my_sub_df.loc[i, 'RightWidth'] = j['LeftWidth']
#             my_sub_df.loc[i, 'BridgeLeft'] = j['BridgeRight']
#             my_sub_df.loc[i, 'BridgeRight'] = j['BridgeLeft']
#
# fc1_df = my_sub_df[my_sub_df['Type'] == 'FC1']
# fc1_df['cap'] = fc1_df['LeftWidth'] + fc1_df['RightWidth']
# fc1_df['span'] = fc1_df['pier'].map(lambda x: x[-1] - x[-2])
# fc1_df['P1'] = fc1_df['pier'].map(lambda x: x[0])
# fc1_df['P2'] = fc1_df['pier'].map(lambda x: x[1])
# xw.Range('A1').value = fc1_df
#
#
# fc2_df = my_sub_df[my_sub_df['Type'] == 'FC2']
# fc2_df['cap'] = fc2_df['LeftWidth'] + fc2_df['RightWidth']
# fc2_df['span'] = fc2_df['SpaceList'].map(lambda x: x[-1] - x[-2])
# fc2_df['P1'] = fc2_df['SpaceList'].map(lambda x: x[0])
# fc2_df['P2'] = fc2_df['SpaceList'].map(lambda x: x[1])
# fc2_df['P3'] = fc2_df['SpaceList'].map(lambda x: x[2])
# xw.Range('A1').value = fc2_df
#
#
# # 统计结构信息
# f3_pier = my_sub_df[my_sub_df['Type'] == 'F3']['SpaceList']
# f3_span_1 = f3_pier.map(lambda x: x[1] - x[0]).values
# f3_span_2 = f3_pier.map(lambda x: x[2] - x[1]).values
#
# f2_pier = my_sub_df[my_sub_df['Type'] == 'F2']['SpaceList']
# fc1_pier = my_sub_df[my_sub_df['Type'] == 'FC1']['SpaceList']
# fc2_pier = my_sub_df[my_sub_df['Type'] == 'FC2']['SpaceList']
# f2_span = f2_pier.map(lambda x: x[1] - x[0]).values
# fc1_span = fc1_pier.map(lambda x: x[1] - x[0]).values
# fc2_span = fc2_pier.map(lambda x: x[2] - x[1]).values
#
# plt.figure(figsize=(9, 4))
# plt.subplot(121)
# plt.set_cmap('RdBu')
# plt.scatter(f3_span_1, f3_span_2, c=abs(f3_span_1 - f3_span_2), s=(f3_span_1+f3_span_2)*2, alpha=0.9)
# plt.axis([10, 24, 12, 27])
# plt.xticks(np.linspace(10, 24, 8))
# plt.xlabel('F3_Span1 (m)')
# plt.ylabel('F3_Span2 (m)')
# plt.grid(True)
# plt.colorbar()
#
# plt.subplot(122)
# plt.scatter(['F2']*len(f2_span), f2_span)
# plt.scatter(['FC1']*len(fc1_span), fc1_span)
# plt.scatter(['FC2']*len(fc2_span), fc2_span)
# plt.xlabel('SubType')
# plt.ylabel('Span (m)')
# plt.grid(axis='y')
#
# plt.savefig('my_sub_spans.svg')
# plt.show()


# # 读取并处理下部数据 ==================================================================================================
#
# # 获取 ei 数据
# align_dic = {}
# for ins in session.query(Ei):
#     get_ei(ins, align_dic)
#
# # 读取下部结构数据
# sub_dic = {}
#
# for instance in session.query(Sub).all():
#     i_type = instance.Type
#     i_station = instance.Station        # 桩号
#     i_sup = secs_df[secs_df['Station'] == i_station]        # 对应上部结构
#     i_bridge = [-i_sup['WidthLeft'].iloc[0], i_sup['WidthRight'].iloc[0]]        # 主线桥梁边线
#
#     i_pier_h = instance.H0 - instance.H1
#     i_cap = [-instance.LeftWidth, instance.RightWidth]      # 盖梁边线
#     i_pier = [float(i) for i in instance.SpaceList.split(',') if i != '0']      # 桥墩位置
#     i_pier = [i + i_bridge[0] for i in i_pier]
#     i_side = 1 if abs(max(i_pier)) >= abs(min(i_pier)) else -1
#
#     i_fundtype = i_sup['FundType'].iloc[0]    # 对应匝道
#
#     if i_fundtype == 'C2F':
#         sub_dic[i_station] = {'cap': i_cap, 'pier': i_pier, 'bridge': i_bridge,
#                               'ramp': [0], 'type': i_type, 'pier_h': i_pier_h}
#     else:
#         # print("|{0:^15}|{1:^15.1f}|{2:^15}|".format(instance.Type, instance.Station, i_fundtype))
#         sta1, dis1 = get_distance(i_fundtype, i_station, align_dic, instance.Line)
#         # print(i_fundtype, sta1, dis1)
#         i_ramp_df = ramps_df[(ramps_df['Bridge'] == i_fundtype) &
#                              (ramps_df['Station'] < sta1+0.01) &
#                              (ramps_df['Station'] > sta1-0.01)]
#         i_ramp = [-i_ramp_df['WidthLeft'].iloc[0], i_ramp_df['WidthRight'].iloc[0]]
#         i_ramp = [i + dis1 * i_side for i in i_ramp]
#         sub_dic[i_station] = {'cap': i_cap, 'pier': i_pier, 'bridge': i_bridge,
#                               'ramp': i_ramp, 'type': i_type, 'pier_h': i_pier_h}
#
#
# sub_df = pd.DataFrame(sub_dic).T
#
# # 重新计算盖梁数据并保留小数
# for i, j in sub_df.iterrows():
#     j['bridge'] = [round(a, 3) for a in j['bridge']]
#     j['pier'] = [round(a, 3) for a in j['pier']]
#     j['pier_h'] = round(j['pier_h'], 3)
#
#     bridge_range = [min(j['bridge']) + 0.75, max(j['bridge']) - 0.75]
#     pier_range = [min(j['pier']) - 1.5, max(j['pier']) + 1.5]
#     if j['ramp'] == 0:
#         j['cap'] = [min(bridge_range[0], pier_range[0]), max(bridge_range[1], pier_range[1])]
#     else:
#         j['ramp'] = [round(a, 3) for a in j['ramp']]
#         ramp_range = [min(j['ramp']) + 0.75, max(j['ramp']) - 0.75]
#         j['cap'] = [min(bridge_range[0], pier_range[0], ramp_range[0]),
#                     max(bridge_range[1], pier_range[1], ramp_range[1])]
#
#     j['cap'] = [round(a, 3) for a in j['cap']]

# # 保存数据
# sub_df.to_csv(r'../IO/sub_df.csv', encoding='gbk')
# sub_df.to_json(r'../IO/sub_df.json', orient='split')
#
# print('done!')




