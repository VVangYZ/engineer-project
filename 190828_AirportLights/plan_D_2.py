#%%
# 大斜拉方案
import numpy as np
import pandas as pd

#====================================================================================
# 一些参数
#=====================================================================================
## 脚本参数

usual_file = 'usual_data.txt'
ter_file = 'terrain.csv'

filename = 'input_D_2'
node_file = 'node_D_2.csv'
elem_file = 'elem_D_2.csv'

## 材料及截面
mat = {'C50':1, 'Q345':2, 'Q420':3}
sec_beam = {'uc':1, 'lc':2, 'wmv':3, 'wmd':4, 'ulbt':5, 'ulbd':6, 'llbt':7, 'llbd':8}

sec_id = ['HW 200x200x8/12', 'HW 200x200x8/12', 'HN 150x75x5/7', 
    'HN 150x75x5/7'] + ['HN 100x50x5/7']*4

## 主梁参数
spans = [62.5, 120, 90, 107.5, 0]                  # 各跨度长度（默认两侧为悬臂，无悬臂则输入 0）
beam_l = sum(spans)
beam_angle = 1.406647 * np.pi / 180                   # 主梁倾角
beam_h = 2.5
beam_b = 2.5
beam_il = 2.5                 # 主桁节间长度
beam_high = {}                  # 变高度节（第 n 个竖杆，从 1 开始）
beam_n = int(beam_l/beam_il)                    # 节数

fixed = 4                  # 第几个支座为梁上支座
beam_start = -2.5

## 墩柱参数
pier_d = [2, 3]
pier_t = [0.015, 0.015]
pier_il = 2

tower_d = [2, 1]
tower_t = [0.015, 0.015]
tower_il = 1

## 荷载信息
light_loc = np.linspace(0, 360, 13)                   # 助航灯位置
light_weight = 20                   # 单个助航灯重量，单位 kN
foot_path_load = 2                 # 检修道荷载，单位 kN/m

#%%
#====================================================================================
# 节点
#====================================================================================

## 主梁节点
nx = np.linspace(beam_start, beam_l + beam_start, beam_n + 1)
nz = np.array([0, -beam_h])
ny = np.array([-beam_b/2, beam_b/2])

node_beam = pd.DataFrame(columns=['x', 'y', 'z', 'H'])
num = 0

for i in nx:
    if (i - 1) * beam_il in beam_high:
        for j in [0, beam_high[(i - 1) * beam_il]]:
            for k in ny:
                num += 1
                node_beam.loc[num]  = [i, k, j + i * np.tan(beam_angle), 1]
    else:
        for j in nz:
            for k in ny:
                num += 1
                node_beam.loc[num]  = [i, k, j + + i * np.tan(beam_angle), 0]


#%%
## 桥墩节点
terrain = pd.read_csv('IO\%s'%(ter_file))
ter_x = terrain['x'].to_numpy()
ter_z = terrain['z'].to_numpy() + 3

pier = pd.DataFrame(columns = ['loc', 'bot'])
for i in range(len(spans)-2):
    pier_loc = sum(spans[0: i+1]) + beam_start
    pier_bot = np.interp(pier_loc, ter_x, ter_z)
    pier.loc[i+1]  = [pier_loc, pier_bot]

node_pier = pd.DataFrame(columns = ['x', 'y', 'z', 'N'])

for i, j in pier.iterrows():
    pier_z_start = node_beam[node_beam['x'] == j['loc']]['z'].min()
    pier_z_end = j['bot']
    pier_z = pier_z_start + pier_il
    while True:
        pier_z -= pier_il
        if pier_z - 0.5 < pier_z_end:
            num += 1
            pier_z = pier_z_end
            node_pier.loc[num] = [j['loc'], 0, pier_z, i]
            break
        else:
            num += 1
            node_pier.loc[num] = [j['loc'], 0, pier_z, i]

## 桥塔节点
node_tower = pd.DataFrame(columns = ['x', 'y', 'z', 'N'])
N = 0
for i, j in pier.iloc[[0, -1], :].iterrows():
    N += 1
    tower_bot = node_beam[node_beam['x'] == j['loc']]['z'].max()
    tower_top = tower_bot  + 15
    for k in np.linspace(tower_bot, tower_top - 5, 6)[:-1]:
        num += 1
        node_tower.loc[num] = [j['loc'], 0, k, N]
    for k in np.linspace(0, 5, 6):
        num += 1
        node_tower.loc[num] = [j['loc'], 0, tower_top - 5 + k, N]


#%%
#=====================================================================================
# 单元
#=====================================================================================

## 主梁单元
### 上弦杆
elem_beam = pd.DataFrame(columns=['m', 's', 'b', 'n1', 'n2', 'WHAT'])
enum = 0
for i in range(2):
    for j in range(beam_n):
        enum += 1
        elem_beam.loc[enum] = [mat['Q345'], sec_beam['uc'], 0, i + j*4 + 1, i + j*4 + 5, 'upper chord']
### 下弦杆
for i in range(2):
    for j in range(beam_n):
        enum += 1
        elem_beam.loc[enum] = [mat['Q345'], sec_beam['lc'], 0, i + j*4 + 3, i + j*4 + 7, 'lower chord']
### 腹板
#### 直腹杆
for i in range(2):
    for j in range(beam_n+1):
        enum += 1
        elem_beam.loc[enum] = [mat['Q345'], sec_beam['wmv'], 90, i + j*4 + 1, i + j*4 + 3, 'web member V']
#### 斜腹杆
for i in range(2):
    for j in range(beam_n):
        if j%2:
            enum += 1
            elem_beam.loc[enum] = [mat['Q345'], sec_beam['wmd'], 90, i + j*4 + 1, i + j*4 + 7, 'web member D']
        else:
            enum += 1
            elem_beam.loc[enum] = [mat['Q345'], sec_beam['wmd'], 90, i + j*4 + 3, i + j*4 + 5, 'web member D']
### 上部纵向连接系
for i in range(beam_n):
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec_beam['ulbt'], 0, i*4 + 1, i*4 + 2, 'upper lateral bracing T']
for i in range(beam_n):
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec_beam['ulbd'], 0, i*4 + 1, i*4 + 6, 'upper lateral bracing D']
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec_beam['ulbd'], 0, i*4 + 2, i*4 + 5, 'upper lateral bracing D']
### 下部纵向连接系
for i in range(beam_n):
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec_beam['llbt'], 0, i*4 + 3, i*4 + 4, 'lower lateral bracing T']
for i in range(beam_n):
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec_beam['llbd'], 0, i*4 + 3, i*4 + 8, 'lower lateral bracing D']
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec_beam['llbd'], 0, i*4 + 4, i*4 + 7, 'lower lateral bracing D']


#%%
## 桥墩单元
elem_pier = pd.DataFrame(columns=['m', 's', 'b', 'n1', 'n2', 'N'])

### 竖杆
for i, j in pier.iterrows():
    for m, n in node_pier[node_pier['N'] == i][: -1].iterrows():
        enum += 1
        elem_pier.loc[enum] = [mat['Q345'], i+len(sec_beam), 0, m, m+1, i]

## 桥塔单元
elem_tower = pd.DataFrame(columns=['m', 's', 'b', 'n1', 'n2', 'N'])

for i in range(2):
    for m, n in node_tower[node_tower['N'] == i + 1][: -1].iterrows():
        enum += 1
        elem_tower.loc[enum] = [mat['Q345'], len(pier)+len(sec_beam)+1, 0, m, m+1, i+1]


#%%
#=======================================================================================
# 写入 mct 文件
#=======================================================================================
mct_file = open('IO\%s.mct'%filename, 'w+')

## 常规信息
with open('IO\%s'%usual_file) as f:
    usual_content = f.read()
mct_file.write(usual_content + '\n')

## 截面信息
mct_file.write('*SECTION\n')
for i, j in sec_beam.items():
    mct_file.write('%d , DBUSER,%s, CC, 0, 0, 0, 0, 0, 0, YES, H,\
        1, GB-YB05, %s\n'%(j, i, sec_id[j-1]))

for i, j in pier.iterrows():
    pier_l = node_pier[node_pier['N'] == i]['z'].max() - node_pier[node_pier['N'] == i]['z'].min()
    pier_d_1 = pier_d[0]
    pier_d_2 = np.interp(pier_l, [0, 100], pier_d)
    pier_t_1 = pier_t[0]
    pier_t_2 = np.interp(pier_l,  [0, 100], pier_t)
    mct_file.write('%d, TAPERED, pier-%d, CC, 0, 0, 0, 0, 0, 0, 0, \
        0, YES, P  , 1, 1, USER\n'%(len(sec_beam)+i, i))
    mct_file.write('%f, %f, 0, 0, 0, 0, 0, 0,%f,%f, \
        0, 0, 0, 0, 0, 0\n'%(pier_d_1, pier_t_1, pier_d_2, pier_t_2))

mct_file.write('%d, TAPERED, tower, CC, 0, 0, 0, 0, 0, 0, 0, \
     0, YES, P  , 1, 1, USER\n'%(len(sec_beam)+pier.shape[0]+1))
mct_file.write('%f, %f, 0, 0, 0, 0, 0, 0,%f,%f, \
     0, 0, 0, 0, 0, 0\n'%(2, 0.015, 1, 0.015))

# mct_file.write('12,TAPERED,TOWER,CC,0,0,0,0,0,0,0,0,YES,B,1,1,USER\n')
# mct_file.write('0.75,1,0.1,0.1,0,0,0,0,3,5.5,0.25,0.25,0,0,0,0\n')
# mct_file.write('13,DBUSER,CABLE,CC,0,0,0,0,0,0,YES,SR,2,0.1,0,0,0,0,0,0,0,0,0\n')

## 节点信息
frames = [node_beam.iloc[:, :3], \
    node_pier[node_pier.index > node_beam.shape[0]].iloc[:, :3], node_tower.iloc[:, :3]]
node = pd.concat(frames)
node.to_csv('IO\\%s'%node_file)

mct_file.write('*NODE\n')
for i, j in node.iterrows():
    mct_file.write('%d, %f, %f, %f\n' %(i, j['x'], j['y'], j['z']))

## 单元信息
frames = [elem_beam.iloc[:, :5], elem_pier.iloc[:, :5], elem_tower.iloc[:, :5]]
elem = pd.concat(frames)
elem.to_csv('IO\\%s'%elem_file)

mct_file.write('*ELEMENT\n')
for i, j in elem.iterrows():
    mct_file.write('%d, BEAM, %d, %d, %d, %d, %d\n' %(i, j['m'], j['s'], j['n1'], j['n2'], j['b']))

## 成组信息
mct_file.write('*GROUP\n')
for i in elem_beam['WHAT'].unique():
    elem_min = elem_beam[elem_beam['WHAT'] == i].index.min()
    elem_max = elem_beam[elem_beam['WHAT'] == i].index.max()
    mct_file.write('%s, , %dto%d\n'%(i, elem_min, elem_max))

mct_file.write('*BNDR-GROUP\nsupport\n')
mct_file.write('rigid_connection\n')

## 变截面组
mct_file.write('*TS-GROUP\n')
for i, j in pier.iterrows():
    pier_elem_start = elem_pier[elem_pier['N'] == i].index.min()
    pier_elem_end = elem_pier[elem_pier['N'] == i].index.max()
    mct_file.write('pier-%d, %dto%d,  LINEAR, , , ,  \
        LINEAR, , , , 0\n'%(i, pier_elem_start, pier_elem_end))
for i in range(2):
    tower_elem_start = elem_tower[elem_tower['N'] == i+1].index.min()
    tower_elem_end = elem_tower[elem_tower['N'] == i+1].index.max()
    mct_file.write('tower-%d, %dto%d,  LINEAR, , , ,  \
        LINEAR, , , , 0\n'%(i + 1, tower_elem_start, tower_elem_end))

# ## 约束信息
# ### 支座
# mct_file.write('*CONSTRAINT\n')
# for i in range(len(spans)-1):
#     loc = sum(spans[0: i+1]) + beam_start
#     if i == fixed-1:
#         res = '011000'
#         for j in node_beam[node_beam['x'] == loc].index[2:]:
#             mct_file.write('%d, %s, support\n'%(j, res))
#     else:
#         pass

# for i, j in pier.iterrows():
#     res = '111111'
#     set_pier = node_pier[node_pier['N'] == i]
#     set_node = set_pier[set_pier['z'] == j['bot']]
#     for m, n in set_node.iterrows():
#         mct_file.write('%d, %s, support\n'%(m, res))

# ### 刚性连接
# mct_file.write('*ELASTICLINK\n')
# elnum = 0
# for i, j in  pier.iterrows():
#     el_node1 = node_pier[node_pier['N'] == i].index.min()
#     el_node2 = node_beam[node_beam['x'] == j['loc']].index[2:].to_list()
#     el_node2.extend(node_beam[node_beam['x'] == j['loc'] - beam_il].index[2:].to_list())
#     el_node2.extend(node_beam[node_beam['x'] == j['loc'] + beam_il].index[2:].to_list())
#     for k in el_node2:
#         elnum += 1
#         mct_file.write('%d,%d,%d, RIGID,\
#              0, NO, 0.5, 0.5, rigid_connection\n'%(elnum, el_node1, k))

# ## 荷载信息
# ### 自重
# mct_file.write('*USE-STLD, DEAD\n')
# mct_file.write('*SELFWEIGHT, 0, 0, -1, self-weight\n')
# ### 助航灯
# mct_file.write('*USE-STLD, SUPER-DEAD\n')
# mct_file.write('*CONLOAD\n')
# for i in light_loc:
#     for j in node_beam[node_beam['x'] == i].index[0:2]:
#         mct_file.write('%d, 0, 0, %f, 0, 0, 0, %s\n'%(j, -light_weight/2, 'light'))
# ### 检修道
# for i in node_beam['x'].unique():
#     if i == node_beam['x'].max() or i == node_beam['x'].min():
#         l = - foot_path_load * beam_il / 4
#     else:
#         l = - foot_path_load * beam_il /2
#     for j in node_beam[node_beam['x'] == i].index[2:]:
#         mct_file.write('%d, 0, 0, %f, 0, 0, 0, %s\n'%(j, l, 'footpath'))

# ### 横桥向风荷载
# mct_file.write('*USE-STLD, WIND-T\n')
# mct_file.write('*BEAMLOAD\n')
# for i, j in elem_beam.iterrows():
#     if node_beam.loc[j['n1']]['y'] < 0:
#         wind_elem = i
#         if j['WHAT'] in ['upper chord', 'lower chord']:
#             wind_f = 0.5
#         elif j['WHAT'] in ['web member V', 'web member D']:
#             wind_f = 0.4
#         else:
#             continue
#         mct_file.write('%d, BEAM, UNILOAD, GY, NO , NO, aDir[1], ,\
#             , , 0, %f, 1, %f, 0, 0, 0, 0, wind-t, NO, 0, 0, NO\n'%(wind_elem, wind_f,  wind_f)) 

# for i, j in elem_pier.iterrows():
#         wind_elem = i
#         wind_f = 2.5
#         mct_file.write('%d, BEAM, UNILOAD, GY, NO , NO, aDir[1], ,\
#             , , 0, %f, 1, %f, 0, 0, 0, 0, wind-t, NO, 0, 0, NO\n'%(wind_elem, wind_f,  wind_f))

# ### 顺桥向风荷载
# mct_file.write('*USE-STLD, WIND-L\n')
# mct_file.write('*BEAMLOAD\n')
# for i, j in elem_beam.iterrows():
#     wind_elem = i
#     if j['WHAT'] in ['upper chord', 'lower chord']:
#         wind_f = 0.5 * 0.25
#     elif j['WHAT'] in ['web member V', 'web member D']:
#         wind_f = 0.4 * 0.25
#     else:
#         continue
#     mct_file.write('%d, BEAM, UNILOAD, GX, NO , NO, aDir[1], ,\
#         , , 0, %f, 1, %f, 0, 0, 0, 0, wind-l, NO, 0, 0, NO\n'%(wind_elem, wind_f,  wind_f)) 

# for i, j in elem_pier.iterrows():
#         wind_elem = i
#         wind_f = 2.5
#         mct_file.write('%d, BEAM, UNILOAD, GX, NO , NO, aDir[1], ,\
#             , , 0, %f, 1, %f, 0, 0, 0, 0, wind-t, NO, 0, 0, NO\n'%(wind_elem, wind_f,  wind_f))

# ## 定义屈曲分析
# mct_file.write('*BUCK-CTRL\n')
# mct_file.write('20, YES, NO, 0, 0, NO\n')
# mct_file.write('DEAD, 1, 0\n')

mct_file.write('*ENDDATA')
mct_file.close()


#%%
