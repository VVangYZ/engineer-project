#%%
import numpy as np
import pandas as pd

#====================================================================================
# 一些参数
#=====================================================================================
## 脚本参数

usual_file = 'usual_data.txt'
ter_file = 'terrain.csv'

filename = 'input_2_1'
node_file = 'node_A.csv'
elem_file = 'elem_A.csv'

wind_beam = [0.41, 0.154]
wind_pier = pd.read_csv('wind_pier.csv')

## 材料及截面
mat = {'C50':1, 'Q345':2, 'Q420':3}
sec = {'uc':1, 'lc':2, 'wmv':3, 'wmd':4, 'ulbt':5, 'ulbd':6, 'llbt':7, 'llbd':8}

sec_id = ['HW 200x200x8/12', 'HW 200x200x8/12', 'HN 150x75x5/7', 
    'HN 150x75x5/7'] + ['HN 100x50x5/7']*4

sec_pier = {'pier1':[0.5, 0.01], 'pier2': [0.3, 0.006], 'pier3': [0.4, 0.008], 'pier4': [0.4, 0.006]}

sec['pier1'] = 9                 # 桥墩主截面
sec['pier2'] = 10                 # 桥墩纵向横联
sec['pier3'] = 12                 # 桥墩横向联系
sec['pier4'] = 11                 # 斜撑

# sec_id = ['HW 300x300x10/15', 'HW 300x300x10/15', 'HW 250x255x14/14', 'HW 250x255x14/14',
#     'HW 175x175x7.5/11', 'HW 175x175x7.5/11', 'HW 175x175x7.5/11', 'HW 175x175x7.5/11']

## 主梁参数
beam_l = 2.5+360+30
beam_angle = 1.406647 * np.pi / 180                   # 主梁倾角
beam_h = 2.5
beam_b = 2.5
beam_il = 2.5                 # 主桁节间长度
beam_high = {}                  # 变高度节（第 n 个竖杆，从 1 开始）
beam_n = int(beam_l/beam_il)                    # 节数

spans = [27.5, 75, 80, 80, 75, 55, 0]                  # 各跨度长度（默认两侧为悬臂，无悬臂则输入 0）
fixed = 6                  # 第几个支座为梁上支座
beam_start = -2.5

## 墩柱参数
pier_s1 = (5 - beam_il) / 2 / 100                   # 纵桥向桥墩斜度
pier_s2 = (15 - beam_b) / 2 / 100                   # 横桥向桥墩斜度
pier_inc1 = 2                   # 桥墩纵向小系梁间距（同时也是桥墩单元长度）
pier_inc2 = 10                  # 桥墩横向刚架间撑梁间距
pier_support1 = 2                   # 斜撑在主梁上的节数
pier_support2 = 4                   # 斜撑在墩上的节数

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
terrain = pd.read_csv('IO\%s'%ter_file)
ter_x = terrain['x'].to_numpy()
ter_z = terrain['z'].to_numpy()

pier = pd.DataFrame(columns = ['loc1', 'loc2', 'bot'])
for i in range(len(spans)-2):
    pier_loc1 = sum(spans[0: i+1]) + beam_start - beam_il
    pier_loc2 = sum(spans[0: i+1]) + beam_start
    pier_bot1 = np.interp(pier_loc1, ter_x, ter_z)
    pier_bot2 = np.interp(pier_loc2, ter_x, ter_z)
    pier_bot = min(pier_bot1, pier_bot2)
    pier.loc[i+1]  = [pier_loc1,pier_loc2, pier_bot]

node_pier = pd.DataFrame(columns = ['x', 'y', 'z', 'N'])
pnum = node_beam.shape[0]
for i, j in pier.iterrows():
    for m, n in node_beam[(node_beam['x'] == j['loc1']) &
         (node_beam['z'] <  j['loc1'] * np.tan(beam_angle))].iterrows():
        pier_z = n['z']
        node_pier.loc[m] = [n['x'], n['y'], n['z'], i]
        ppn1 = 0
        while True:
            ppn1 += 1
            pier_z -= pier_inc1
            if pier_z - 0.5 < j['bot']: 
                pier_x = n['x'] - (n['z'] -  j['bot']) * pier_s1
                if n['y'] < 0:
                    pier_y = n['y'] - (n['z'] -  j['bot']) * pier_s2
                else:
                    pier_y = n['y'] + (n['z'] -  j['bot']) * pier_s2
                pnum += 1
                node_pier.loc[pnum] = [pier_x, pier_y,  j['bot'], i]
                break
            pier_x = n['x'] - (n['z'] - pier_z) * pier_s1
            if n['y'] < 0:
                pier_y = n['y'] - (n['z'] - pier_z) * pier_s2
            else:
                pier_y = n['y'] + (n['z'] - pier_z) * pier_s2
            pnum += 1
            node_pier.loc[pnum] = [pier_x, pier_y, pier_z, i]
    
    for m, n in node_beam[(node_beam['x'] == j['loc2']) &
         (node_beam['z'] <  j['loc2'] * np.tan(beam_angle))].iterrows():
        pier_z = n['z']
        node_pier.loc[m] = [n['x'], n['y'], n['z'], i]
        ppn2 = 0
        while True:
            pier_z -= pier_inc1
            ppn2 += 1
            if ppn2 == ppn1: 
                pier_x = n['x'] + (n['z'] -  j['bot']) * pier_s1
                if n['y'] < 0:
                    pier_y = n['y'] - (n['z'] -  j['bot']) * pier_s2
                else:
                    pier_y = n['y'] + (n['z'] -  j['bot']) * pier_s2
                pnum += 1
                node_pier.loc[pnum] = [pier_x, pier_y,  j['bot'], i]
                break
            
            pier_x = n['x'] + (n['z'] - pier_z) * pier_s1
            if n['y'] < 0:
                pier_y = n['y'] - (n['z'] - pier_z) * pier_s2
            else:
                pier_y = n['y'] + (n['z'] - pier_z) * pier_s2
            pnum += 1
            node_pier.loc[pnum] = [pier_x, pier_y, pier_z, i]


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
        elem_beam.loc[enum] = [mat['Q345'], sec['uc'], 0, i + j*4 + 1, i + j*4 + 5, 'upper chord']
### 下弦杆
for i in range(2):
    for j in range(beam_n):
        enum += 1
        elem_beam.loc[enum] = [mat['Q345'], sec['lc'], 0, i + j*4 + 3, i + j*4 + 7, 'lower chord']
### 腹板
#### 直腹杆
for i in range(2):
    for j in range(beam_n+1):
        enum += 1
        elem_beam.loc[enum] = [mat['Q345'], sec['wmv'], 90, i + j*4 + 1, i + j*4 + 3, 'web member V']
#### 斜腹杆
for i in range(2):
    for j in range(beam_n):
        if j%2:
            enum += 1
            elem_beam.loc[enum] = [mat['Q345'], sec['wmd'], 90, i + j*4 + 1, i + j*4 + 7, 'web member D']
        else:
            enum += 1
            elem_beam.loc[enum] = [mat['Q345'], sec['wmd'], 90, i + j*4 + 3, i + j*4 + 5, 'web member D']
### 上部纵向连接系
for i in range(beam_n):
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec['ulbt'], 0, i*4 + 1, i*4 + 2, 'upper lateral bracing T']
for i in range(beam_n):
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec['ulbd'], 0, i*4 + 1, i*4 + 6, 'upper lateral bracing D']
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec['ulbd'], 0, i*4 + 2, i*4 + 5, 'upper lateral bracing D']
### 下部纵向连接系
for i in range(beam_n):
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec['llbt'], 0, i*4 + 3, i*4 + 4, 'lower lateral bracing T']
for i in range(beam_n):
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec['llbd'], 0, i*4 + 3, i*4 + 8, 'lower lateral bracing D']
    enum += 1
    elem_beam.loc[enum] = [mat['Q345'], sec['llbd'], 0, i*4 + 4, i*4 + 7, 'lower lateral bracing D']

#%%
## 桥墩单元
elem_pier = pd.DataFrame(columns=['m', 's', 'b', 'n1', 'n2', 'N', 'WHAT'])

### 竖杆
for i in range(len(spans) - 2):
    nn = node_pier[node_pier['N'] == i+1].shape[0] // 4
    for j in range(4):
        ni = 0
        node_pier_1 = node_pier[node_pier['N'] == i+1][j*nn: j*nn + nn]
        for m, n in node_pier_1[:-1].iterrows():
            ni += 1
            enum += 1
            elem_pier.loc[enum] = [mat['Q345'], sec['pier1'], 0, m, node_pier_1.iloc[ni].name, i+1, 'pier-1']

### 小横联
for i in range(len(spans) - 2):
    nn = node_pier[node_pier['N'] == i+1].shape[0] // 4
    for j in [0, 1]:
        node_pier_2 = node_pier[node_pier['N'] == i+1][j*nn + 1: j*nn + nn -1]
        for m, n in node_pier_2.iterrows():
            enum += 1
            elem_pier.loc[enum] = [mat['Q345'], sec['pier2'], 0, m, m + (nn - 1)*2, i+1,'pier-2']

### 大横联
for i in range(len(spans) - 2):
    nn = node_pier[node_pier['N'] == i+1].shape[0] // 4
    for j in [0, 2]:
        nnn = -1
        for m, n in node_pier[node_pier['N'] == i+1][j*nn: j*nn + nn -1].iterrows():
            nnn += 1
            if (nnn + 1 ) * pier_inc1 == pier_inc2:
                enum += 1
                elem_pier.loc[enum] = [mat['Q345'], sec['pier3'], 0, m, m + nn - 1, i+1,'pier-3']
            if nnn * pier_inc1 == pier_inc2:
                nnn = 0
                enum += 1
                elem_pier.loc[enum] = [mat['Q345'], sec['pier3'], 0, m, m + nn - 1, i+1,'pier-3']
                
### 斜撑
for i, j in pier.iterrows():
    nn = node_pier[node_pier['N'] == i].shape[0] // 4
    for k in [0, 1]:
        b1= node_beam[node_beam['x'] == j['loc1'] - pier_support1 * beam_il].index[2 + k]
        b2= node_beam[node_beam['x'] == j['loc1'] + (pier_support1 + 1) * beam_il].index[2 + k]
        p1 = node_pier[node_pier['N'] == i].index[k*nn + pier_support2]
        p2 = node_pier[node_pier['N'] == i].index[k*nn + 2*nn + pier_support2]
        enum += 1
        elem_pier.loc[enum] = [mat['Q345'], sec['pier4'], 0, b1, p1, i,'pier-4']
        enum += 1
        elem_pier.loc[enum] = [mat['Q345'], sec['pier4'], 0, b2, p2, i,'pier-4']


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
for i, j in sec.items():
    if 'pier' in i:
        mct_file.write('%d, DBUSER, %s, CC, 0, 0, 0, 0, 0, 0, YES, P , \
            2, %f, %f, 0, 0, 0, 0, 0, 0, 0, 0\n'%(j, i, sec_pier[i][0], sec_pier[i][1]))
    else:
        mct_file.write('%d , DBUSER,%s, CC, 0, 0, 0, 0, 0, 0, YES, H,\
             1, GB-YB05, %s\n'%(j, i, sec_id[j-1]))

## 节点信息
frames = [node_beam.iloc[:, :3], node_pier[node_pier.index > node_beam.shape[0]].iloc[:, :3]]
node = pd.concat(frames)
node.to_csv('IO\\%s'%node_file)

mct_file.write('*NODE\n')
for i, j in node.iterrows():
    mct_file.write('%d, %f, %f, %f\n' %(i, j['x'], j['y'], j['z']))

## 单元信息
frames = [elem_beam.iloc[:, :5], elem_pier.iloc[:, :5]]
elem = pd.concat(frames)
elem.to_csv('IO\\%s'%elem_file)

mct_file.write('*ELEMENT\n')
for i, j in elem_beam.iterrows():
    mct_file.write('%d, BEAM, %d, %d, %d, %d, %d\n' %(i, j['m'], j['s'], j['n1'], j['n2'], j['b']))
for i, j in elem_pier.iterrows():
    mct_file.write('%d, BEAM, %d, %d, %d, %d, %d\n' %(i, j['m'], j['s'], j['n1'], j['n2'], j['b']))

## 成组信息
mct_file.write('*GROUP\n')
for i in elem_beam['WHAT'].unique():
    elem_min = elem_beam[elem_beam['WHAT'] == i].index.min()
    elem_max = elem_beam[elem_beam['WHAT'] == i].index.max()
    mct_file.write('%s, , %dto%d\n'%(i, elem_min, elem_max))

mct_file.write('*BNDR-GROUP\nsupport\n')

## 约束信息
mct_file.write('*CONSTRAINT\n')
for i in range(len(spans)-1):
    loc = sum(spans[0: i+1]) + beam_start
    if i == fixed-1:
        res = '011000'
        for j in node_beam[node_beam['x'] == loc].index[2:]:
            mct_file.write('%d, %s, support\n'%(j, res))
    else:
        pass

for i, j in pier.iterrows():
    res = '111111'
    the_pier = node_pier[node_pier['N'] == i]
    set_node = the_pier[the_pier['z'] == j['bot']]
    for m, n in set_node.iterrows():
        mct_file.write('%d, %s, support\n'%(m, res))

## 荷载信息
### 自重
mct_file.write('*USE-STLD, DEAD\n')
mct_file.write('*SELFWEIGHT, 0, 0, -1, self-weight\n')
### 助航灯
mct_file.write('*USE-STLD, SUPER-DEAD\n')
mct_file.write('*CONLOAD\n')
for i in light_loc:
    for j in node_beam[node_beam['x'] == i].index[0:2]:
        mct_file.write('%d, 0, 0, %f, 0, 0, 0, %s\n'%(j, -light_weight/2, 'light'))
### 检修道
for i in node_beam['x'].unique():
    if i == node_beam['x'].max() or i == node_beam['x'].min():
        l = - foot_path_load * beam_il / 4
    else:
        l = - foot_path_load * beam_il /2
    for j in node_beam[node_beam['x'] == i].index[2:]:
        mct_file.write('%d, 0, 0, %f, 0, 0, 0, %s\n'%(j, l, 'footpath'))
### 横向风荷载
mct_file.write('*USE-STLD, WIND-T\n')
mct_file.write('*BEAMLOAD\n')
for i, j in elem_beam.iterrows():
    if node_beam.loc[j['n1']]['y'] < 100:
        wind_elem = i
        if j['WHAT'] in ['upper chord', ]:
            wind_f = wind_beam[0] * 2
        elif j['WHAT'] in ['lower chord', ]:
            wind_f = wind_beam[0]
        elif j['WHAT'] in ['web member V', 'web member D']:
            wind_f = wind_beam[1]
        else:
            continue
        mct_file.write('%d, BEAM, UNILOAD, GY, NO , NO, aDir[1], ,\
            , , 0, %f, 1, %f, 0, 0, 0, 0, wind-t, NO, 0, 0, NO\n'%(wind_elem, wind_f,  wind_f)) 

for i, j in elem_pier.iterrows():
    if node.loc[j['n1']]['y'] < 0:
        wind_elem = i
        if j['WHAT'] in ['pier-1', 'pier-2', 'pier-4']:
            wind_f = wind_pier.iloc[j['N']-1, j['s']-8]/1000
        else:
            continue
        mct_file.write('%d, BEAM, UNILOAD, GY, NO , NO, aDir[1], ,\
            , , 0, %f, 1, %f, 0, 0, 0, 0, wind-t, NO, 0, 0, NO\n'%(wind_elem, wind_f,  wind_f))

# ### 纵向风荷载
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
#     if node.loc[j['n1']]['x'] <=  pier.loc[j['N'], 'loc1']:
#         wind_elem = i
#         if j['WHAT'] == 'pier-1':
#             wind_f = 0.5
#         elif j['WHAT'] == 'pier-3':
#             wind_f = 0.4
#         else:
#             continue
#         mct_file.write('%d, BEAM, UNILOAD, GX, NO , NO, aDir[1], ,\
#             , , 0, %f, 1, %f, 0, 0, 0, 0, wind-l, NO, 0, 0, NO\n'%(wind_elem, wind_f,  wind_f))



## 定义屈曲分析
mct_file.write('*BUCK-CTRL\n')
mct_file.write('20, YES, NO, 0, 0, NO\n')
mct_file.write('DEAD, 1, 0\n')


mct_file.write('*ENDDATA')
mct_file.close()



#%%
