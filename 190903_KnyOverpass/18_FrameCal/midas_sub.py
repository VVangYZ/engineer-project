import numpy as np
import midas1
import win32com.client as win32
import cad
import pandas as pd
import tendon_new
import time
import math
import kny_tool

# 参数 ==============================================================================================================

# 文件参数 ------------------------------------------------------------------------------------------
str_now = time.strftime('%y%m%d%H%M', time.localtime())
mct_file = f'IO\\wow_{str_now}.mct'

# 几何参数 ------------------------------------------------------------------------------------------

sub_pd = pd.read_json('../IO/sub_df.json', orient='split')

sub_pd['bridge_w'] = sub_pd['bridge'].map(lambda x: x[1] - x[0])
sub_pd['beam_num'] = sub_pd['bridge_w'].map(kny_tool.num_from_width)
sub_pd['joint'] = sub_pd['bridge_w'].map(kny_tool.joint_from_width)


# 截面参数 ------------------------------------------------------------------------------------------

# 连接 cad
acad = win32.Dispatch("AutoCAD.Application")
doc = acad.ActiveDocument
ms = doc.ModelSpace
print(doc.name)

secs = cad.CadSecs(ms)

# 获取截面边框
sec_box = {}
for i, j in enumerate(secs.secs):
    lx = round(j.prop['c'][0] + j.prop['c'][1], 4)
    ly = round(j.prop['c'][2] + j.prop['c'][3], 4)
    if 'C' in secs.sec_name[i]:
        sec_box.setdefault('cap', []).append((lx, ly))
    else:
        sec_box.setdefault('pier', []).append((lx, ly))

# psc 截面参数
cap_dic = {'C1': [2.2, 1.1, 2, 0.01], 'C2': [2.2, 1.1, 2, 1.1]}
pier_dic = {'P1': [1.8, 1.8]}

# 模型参数 ------------------------------------------------------------------------------------------

mct_l = []      # mct 文件列表
num_l = [0] * 4     # 截面号、节点号、单元号、弹性连接号

# 预应力参数
have_tendon = True
cap_m = []      # 弯矩值
f_lim = [22.4, 22.4, -2, -2]    # 混凝土容许应力（施工、使用、施工、使用）
tendon_per_n = 15       # 单束预应力股数
tendon_edge = 0.3  # 预应力到边缘距离
tendon_between = 0.35   # 预应力之间横向距离

# midas 参数
node_space = 1      # 节点最大间距（单位：m）
temp = (-15, 15)    # 温度
stldcase = ('DEAD', 'TENDON', 'BEAM1', 'BEAM2', 'TEM_U', 'TEM_D')
loadgroup = ('dead', 'tendon', 'beam_1', 'beam_2', 'tem_u', 'tem_d')

# 几何模型 ============================================================================================================

# 初始化 ------------------------------------------------------------------------------------------

midas1.usual_data(mct_list=mct_l, loadgroup=loadgroup, stldcase=stldcase)

# 添加截面 ------------------------------------------------------------------------------------------

# 添加 cad 截面
secs_dic = dict(zip(secs.sec_name, secs.secs))
secs_midas = [secs.secs_to_midas()[i]
              for i in range(len(secs.secs)) if 'B' in secs.sec_name[i]]
midas1.psv_sec_start(mct_l)
midas1.add_my_sec(secs_midas, mct_list=mct_l, num=num_l)

# 添加 psc 截面
midas1.sec_start(mct_l)
for i, j in cap_dic.items():
    midas1.add_edge_sec(i, 'CT', j[0], j[1], j[2], j[3], mct_list=mct_l, num=num_l)

for i, j in pier_dic.items():
    midas1.add_rectangle_sec(i, 'CC', j[0], j[1], mct_list=mct_l, num=num_l)

# 变截面
midas1.add_simple_change_sec('C12', 'CT', 4, 5, mct_list=mct_l, num=num_l)
midas1.add_simple_change_sec('C12', 'CT', 5, 4, mct_list=mct_l, num=num_l)

# 节点和坐标 ------------------------------------------------------------------------------------------







