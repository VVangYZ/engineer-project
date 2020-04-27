import xlwings as xw
import pandas as pd
import numpy as np
import difflib

pile_depth_max = 33

soil_all = xw.sheets['soil'].range('A1').options(pd.DataFrame, expand='table').value
zk_all = xw.sheets['zk_all'].range('A1').options(pd.DataFrame, expand='table').value
sub_all = xw.sheets['sub_all_0425'].range('A1').options(pd.DataFrame, expand='table').value

# 规范钻孔信息
# # 添加土体重度
soil_gamma = {}
no_gamma = []
soil_gamma['素填土'] = 15
for i in zk_all['岩土描述'].unique():
    if i in soil_all.index:
        soil_gamma[i] = soil_all.loc[i, '重度'].mean() * 10
    else:
        no_gamma.append(i)

for i in no_gamma:
    same = 0
    match_soil = ''
    for j in soil_gamma:
        same_i = difflib.SequenceMatcher(None, i, j).quick_ratio()
        if same_i > same:
            same = same_i
            match_soil = j
    soil_gamma[i] = soil_gamma[match_soil]

zk_all['gamma'] = zk_all['岩土描述'].map(lambda x: soil_gamma[x])

xw.sheets['zk_all'].range('A1').value = zk_all

# 获取最近距离钻孔
for i, j in sub_all.iterrows():
    sub_loc = [j['x'], j['y']]
    sub_to_zk = (zk_all['x'] - j['x']) ** 2 + (zk_all['y'] - j['y']) ** 2
    zk_close = sub_to_zk[sub_to_zk == sub_to_zk.min()].index[0]
    sub_all.loc[i, 'ZK'] = zk_close
    sub_all.loc[i, 'distance'] = sub_to_zk.min() ** 0.5

# 获取扩基埋深
bad_zk = []
for i, j in sub_all.iterrows():
    zk_inf = zk_all.loc[j['ZK']]
    lyr_nb = zk_inf[zk_inf['fa0'] >= 500]
    lyr_sb = zk_inf[zk_inf['fa0'] < 500]

    if len(lyr_sb) == 0:
        good_lyr = 0
    else:
        if lyr_nb['层底深度'].min() < lyr_sb['层底深度'].max():
            print(f'桩号{j["span_name"]}  钻孔{j["ZK"]} 有软弱下卧层')
            bad_zk.append(j['ZK'])
        good_lyr = lyr_sb['层底深度'].max()
    sub_all.loc[i, 'good_depth'] = good_lyr

    if good_lyr < 4 and j['Type'] not in ['FC1', 'FC2', 'F2', 'F3']:
        sub_all.loc[i, 'fund_type'] = '扩基'
        expand_depth = good_lyr + 0.5
        if expand_depth <= 2.5:
            sub_all.loc[i, 'fund_depth'] = 2.5
        else:
            sub_all.loc[i, 'fund_depth'] = expand_depth
    else:
        lyr_type = zk_inf['岩土描述']
        if '中风化' not in ''.join(lyr_type):
            rock_length = 100
            print('该钻孔无中风化层')
            # sub_all.loc[i, 'fund_depth'] = rock_length
            # continue
        else:
            rock_length = 0
            for m in lyr_type:
                if '中风化' not in m:
                    rock_length = zk_inf[zk_inf['岩土描述'] == m]['层底深度'].max() + 4
            if rock_length == 0:
                print(f'钻孔 {j["ZK"]} 没有中风化以下地质层')
                raise Exception
        sub_all.loc[i, 'good_depth'] = rock_length - 4
        sub_all.loc[i, 'fund_type'] = '端承桩' if rock_length < pile_depth_max else '摩擦桩'

        if j['Type'] in ['F2', 'FC1', 'FC2']:
            pile_num = 2
        elif j['Type'] in ['F3']:
            pile_num = 3
        else:
            pile_num = 1
        sub_all.loc[i, 'fund_depth'] = ','.join([str(min(pile_depth_max, rock_length))] * pile_num)

bad_zk = set(bad_zk)
xw.sheets['wow_0425_2'].range('A1').value = sub_all



