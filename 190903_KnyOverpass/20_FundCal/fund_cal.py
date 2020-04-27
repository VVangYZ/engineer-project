import xlwings as xw
import pandas as pd
import fund_tool
import numpy as np
import copy
import pile
import pile_tool
import concrete
import warnings
warnings.filterwarnings("ignore")


default_rebar = 16      # 默认主筋直径
default_fy = 500        # 默认主筋型号（屈服强度）
default_space = 150     # 默认主筋间距


sub_file = xw.books['mysub_0414.xlsx']
result_file = xw.books['all_result_0416.xlsx']
fund_file = xw.books['fund_0425.xlsx']
default_pile_size = {
    'M1K+17285.000': [2, 2.2],
    'M1K+16985.000': [2, 2.2],
    'M1K+16955.000': [2, 2.2],
    'M1K+16865.000': [2, 2.2],
    'M1K+17375.000': [2, 2.2],
    'M1K+17315.000': [2, 2.2],
    'M2K+21885.000': [2.2, 2.2],
    'M1K+07597.000': [2.2, 2.2],
    'M2K+22327.000': [2.2, 2.2],
    'L1K+19766.000': [2.2, 2.2, 2.2],
    'L1K+19085.000': [2.2, 2.2, 2.2]
}

sub_typical = sub_file.sheets['creat_sub'].range('A1').options(pd.DataFrame, expand='table').value
all_sub = fund_file.sheets['wow_0425_2'].range('A1').options(pd.DataFrame, expand='table').value
zk_all = fund_file.sheets['zk_all'].range('A1').options(pd.DataFrame, expand='table').value

# 获取参考受力下部结构
for i, j in all_sub.iterrows():
    for m, n in sub_typical.iterrows():
        if j['Type'] == n['类型']:
            if n['参考长度1'] < j['LeftWidth'] + j['RightWidth'] <= n['参考长度2']:
                all_sub.loc[i, 'sub_ref'] = m

my_sub = all_sub[all_sub['Type'].isin(['FC1', 'FC2', 'F2', 'F3'])]

# 获取指定桩号规范基础顶面力
# res_pd = result_file.sheets['M1K+17285.000'].range('AV1').options(pd.DataFrame, expand='table').value
# res_pd2 = result_file.sheets['M2K+22507.000'].range('AV1').options(pd.DataFrame, expand='table').value
# a = fund_tool.get_f_from_pd(res_pd, 'FC1')
# b = fund_tool.get_f_from_pd(res_pd2, 'FC2')

my_sub['fund_size'] = my_sub['Type'].map(lambda x: [])
my_sub['fa0'] = my_sub['Type'].map(lambda x: 0)
my_sub['fa'] = my_sub['Type'].map(lambda x: [])
my_sub['fund_sig'] = my_sub['Type'].map(lambda x: [])
my_sub['fund_as'] = my_sub['Type'].map(lambda x: [])
my_sub['fund_as_default'] = my_sub['Type'].map(lambda x: [])
my_sub['fund_cut'] = my_sub['Type'].map(lambda x: [])
my_sub['pile_layout'] = my_sub['Type'].map(lambda x: [])
my_sub['pile_fe'] = my_sub['Type'].map(lambda x: {})
my_sub['pile_ra'] = my_sub['Type'].map(lambda x: {})
my_sub['pile_mu'] = my_sub['Type'].map(lambda x: [])
my_sub['pile_safe_factor'] = my_sub['Type'].map(lambda x: [])
my_sub['pile_crack_width'] = my_sub['Type'].map(lambda x: [])


def zk_stand(zk_pd):
    del zk_pd['路线']
    del zk_pd['桩号']
    replace_column = {'岩土描述': 'name', '层底深度': 'height', '地层厚度': 'depth'}
    zk_pd.rename(columns=replace_column, inplace=True)
    zk_pd['height'] = - zk_pd['height']
    zk_pd.reset_index(inplace=True, drop=True)
    zk_pd['frk'].fillna(0, inplace=True)
    for i in range(zk_pd.shape[0]):
        if i == 0 and zk_pd.iloc[-1, 5] == 0:
            break
        elif zk_pd.iloc[-(i + 1), 5] > 0:
            pass
        elif ('中风化' in zk_pd.iloc[-(i+1), 0]) and (zk_pd.iloc[-i, 5] > 0):
            zk_pd.iloc[-(i+1), 5] = zk_pd.iloc[-i, 5]
    zk_pd['per'] = zk_pd['name'].map(lambda x: False if '黏土' in x else True)


for i, j in my_sub.iterrows():
    if j['fund_type'] == '扩基':
        ref_sub = j['sub_ref']
        ref_sub_pd = result_file.sheets[ref_sub].range('AV1').options(pd.DataFrame, expand='table').value

        min_size = fund_tool.expand_min_size(j['Type'])
        fund_top_f = fund_tool.get_f_from_pd(ref_sub_pd, j['Type'])
        fa = [fund_tool.get_fa(a, j['fund_depth'], zk_all.loc[j['ZK']]) for a in min_size]
        my_sub.loc[i, 'fa0'] = fa[0][-1]
        size = copy.deepcopy(min_size)
        fund_sig = [0 for i in min_size]
        fa_i = [0 for i in min_size]
        for m, n in enumerate(size):
            fund_i = fund_tool.ExpandFund(n, fund_top_f[m], j['fund_depth'], fa[m][0], fa[m][1])
            pass_or_not = fund_i.cal_ground()
            fund_sig[m] = fund_i.p_max
            fa_i[m] = fund_i.fa
            if not pass_or_not[-1]:
                size_1 = n
                while True:
                    print(pass_or_not[0], end=' ')
                    size_1[0] += 0.5
                    size_1[1] += 0.5
                    fa1 = fund_tool.get_fa(size_1, j['fund_depth'], zk_all.loc[j['ZK']])
                    fund_i1 = fund_tool.ExpandFund(size_1, fund_top_f[m], j['fund_depth'], fa[m][0], fa1[1])
                    pass_or_not = fund_i1.cal_ground()
                    if pass_or_not[-1]:
                        print('\n')
                        break
                        # if pass_or_not[1] == 'my':
                        #     size_1[1] += 0.1
                        # else:
                        #     size_1[0] += 0.1

                fa[m] = fa1
                size[m] = size_1
                fund_sig[m] = fund_i1.p_max
                fa_i[m] = fund_i1.fa

                fund_edge = (np.array(size_1) - min_size[m]) / 2 + 2
                m_all = fund_i1.cal_fund(fund_edge)
                m_max = np.max(m_all, axis=0)
                as_need = m_max / (0.9 * default_fy * 1000 * 1.92) * 1e6
                my_sub.at[i, 'fund_as'].append([round(a, 0) for a in as_need])

                as_default = ((np.array(size_1) - 0.04 - 0.05 * 2) // (default_space / 1000) + 1) * \
                             (default_rebar / 2) ** 2 * np.pi
                my_sub.at[i, 'fund_as_default'].append([round(a, 0) for a in as_default])

                cut_safe = fund_i1.cal_other(np.array(min_size[m]) - 4)
                my_sub.at[i, 'fund_cut'].append([round(a, 2) for a in cut_safe])
            else:
                my_sub.at[i, 'fund_as'].append([])
                as_default = ((np.array(n) - 0.04 - 0.05 * 2) // (default_space / 1000) + 1) * \
                             (default_rebar / 2) ** 2 * np.pi
                my_sub.at[i, 'fund_as_default'].append([round(a, 0) for a in as_default])
                my_sub.at[i, 'fund_cut'].append([])

            size[m] = [round(a, 3) for a in size[m]]

        my_sub.at[i, 'fund_size'] = size
        my_sub.at[i, 'fund_sig'] = fund_sig
        my_sub.at[i, 'fa'] = [round(i, 0) for i in fa_i]
    else:
        # 桩基布置和桩基尺寸
        pile_layout = fund_tool.default_pile_layout(j['Type'], j['fund_type'])
        my_sub.at[i, 'pile_layout'] = pile_layout
        if j['sub_ref'] in default_pile_size:
            pile_size = default_pile_size[j['sub_ref']]
        else:
            pile_size = len(pile_layout) * [2]
        my_sub.at[i, 'fund_size'] = pile_size

        # 提取承台顶面力
        ref_sub = j['sub_ref']
        ref_sub_pd = result_file.sheets[ref_sub].range('AV1').options(pd.DataFrame, expand='table').value
        fund_top_f = fund_tool.get_f_from_pd(ref_sub_pd, j['Type'])
        soil_m = pile_tool.soil_m_from_zk(zk_all.loc[j['ZK']])
        pile_fe = pile_tool.pile_fe_from_pd(fund_top_f)
        pile_fu = pile_tool.pile_fu_from_pd(fund_top_f)

        # 获取标准组合下桩基内力
        pile_z0 = -2.5
        # pile_z1 = -j['fund_depth']
        pile_z1 = j['fund_depth'].split(',')
        pile_z = [[pile_z0, -float(i)] for i in pile_z1]

        pile_cal_case_e = []
        for m, n in enumerate(pile_fe):
            pile_cal_case_e.append([[pile_layout[m], n[0]], [pile_layout[m][::-1], n[1]]])

        pile_f_max = []
        for k, m in enumerate(pile_cal_case_e):
            pile_f_maxi = []
            for n in m:
                pile_elem, pile_m = pile_tool.get_multi_pile_m(
                    n[0], pile_z0=pile_z[k][0], pile_z1=pile_z[k][1], m0=soil_m, top_h=n[1][0] * 1000,
                    top_f=n[1][1] * 1000, top_m=n[1][2] * 1000, pile_d=pile_size[k]
                )
                for x in pile_elem:
                    pile_f_x = pile_m[x[0]][1]
                    pile_f_maxi.append(pile_f_x)
            pile_f_max.append(min(pile_f_maxi))
        my_sub.at[i, 'pile_fe'] = [round(x, 0) for x in pile_f_max]

        # 桩长计算
        zk_i = zk_all.loc[j['ZK']].copy()
        zk_stand(zk_i)
        soil_i = pile.Soil(zk_i)
        pile_mc = []
        pile_dc = []
        for m, n in enumerate(pile_size):
            pile_i_mc = pile.Pile_mc_zk(soil_i, n, pile_z[m][0] - pile_z[m][1], h1=pile_z[m][0])
            pile_i_dc = pile.Pile_dc(soil_i, n, pile_z[m][0] - pile_z[m][1], h1=pile_z[m][0])
            pile_mc.append(int(pile_i_mc.ra * 1.25))
            pile_dc.append(int(pile_i_dc.ra * 1.25))
        my_sub.loc[i, 'pile_ra']['mc'] = pile_mc
        my_sub.loc[i, 'pile_ra']['dc'] = pile_dc
        my_sub.loc[i, 'pile_ra']['mc_safe'] = [round(- m / n, 2) for m, n in zip(pile_mc, pile_f_max)]

        # 计算桩基内力
        pile_cal_case_u = []
        for m, n in enumerate(pile_fu):
            pile_cal_case_u.append([[pile_layout[m], n[0]], [pile_layout[m][::-1], n[1]]])

        pile_m_max = []
        for k, m in enumerate(pile_cal_case_u):
            pile_m_maxi = []
            for n in m:
                pile_elem, pile_m = pile_tool.get_multi_pile_m(
                    n[0], pile_z0=pile_z[k][0], pile_z1=pile_z[k][1], m0=soil_m, top_h=n[1][0] * 1000,
                    top_f=n[1][1] * 1000, top_m=n[1][2] * 1000, pile_d=pile_size[k]
                )
                for x in pile_elem:
                    pile_m_x = sorted([pile_m[y] for y in x], key=lambda wow: abs(wow[2]), reverse=True)[0]
                    pile_m_maxi.append([int(pile_m_x[1]), int(pile_m_x[2])])
            pile_m_max.append(pile_m_maxi)

        my_sub.at[i, 'pile_mu'] = pile_m_max

        # 桩基截面验算
        pile_safe_factor = []
        pile_crack_width = []
        for k, m in enumerate(pile_m_max):
            pile_d = pile_size[k]
            rebar_num = 38 if pile_d == 2 else 44
            factor_m = []
            crack_width_m = []
            for n in m:
                pile_i = concrete.CircularCompress(pile_d, rebar_num, 32, 13.8, 415, 400)
                pile_i.capacity(abs(n[0]), abs(n[1]))
                pile_i.crack_width(abs(n[0]) * 0.8, abs(n[1]) * 0.8)

                factor_m.append(round(pile_i.nud / (abs(n[0]) * 1.1), 2))
                crack_width_m.append(round(pile_i.wcr, 3))
            pile_safe_factor.append(factor_m)
            pile_crack_width.append(crack_width_m)

        my_sub.at[i, 'pile_safe_factor'] = pile_safe_factor
        my_sub.at[i, 'pile_crack_width'] = pile_crack_width

        # pile_m_max = []
        # for m, n in enumerate(pile_f):
        #     m_max = pile_tool.get_pile_m(pile_z0=pile_z0, pile_z1=pile_z1, m0=soil_m,
        #                                  pile_f=n[0], pile_m=n[1])
        #     pile_m_max.append(round(m_max / 1000, 1))
        # my_sub.at[i, 'pile_m'] = pile_m_max

# fund_file.sheets['sub_frame'].range('A1').value = my_sub

my_sub.to_csv(r'..\IO\wow_0426_v3.csv', encoding='gbk')


