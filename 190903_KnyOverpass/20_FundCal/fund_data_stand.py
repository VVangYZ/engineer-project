import pandas as pd

my_sub_fund = pd.read_excel(r'..\IO\wow_0426_v3.xlsx', sheet_name='wow_0426_v3', usecols='A,B,F,H,I,V:X,Z,AA,AG,AI')
my_sub_fund['fund_size'] = my_sub_fund['fund_size'].map(eval)
my_sub_fund['pile_layout'] = my_sub_fund['pile_layout'].map(eval)
my_sub_fund['pile_ra'] = my_sub_fund['pile_ra'].map(eval)
my_sub_fund['pile_ra'] = my_sub_fund['pile_ra'].map(lambda x: x['mc'])


for i, j in my_sub_fund.iterrows():
    if isinstance(j['fund_depth'], str):
        my_sub_fund.at[i, 'fund_depth'] = [float(k) for k in j['fund_depth'].split(',')]
    else:
        my_sub_fund.at[i, 'fund_depth'] = [j['fund_depth']] * len(j['fund_size'])


for i, j in my_sub_fund.iterrows():
    if j['fund_type'] == '扩基':
        if j['Type'] in ['FC1', 'FC2']:
            side = 1 if j['LeftWidth'] < j['RightWidth'] else -1
            my_sub_fund.at[i, 'fund_size'] = j['fund_size'][::side]
            my_sub_fund.at[i, 'fund_depth'] = j['fund_depth'][::side]
        else:
            i_size = j['fund_size']
            if i_size[0] != i_size[-1]:
                i_size = [i_size[0]] * 2 if i_size[0][0] > i_size[1][0] else [i_size[1]] * 2
                my_sub_fund.at[i, 'fund_size'] = i_size
    else:
        if j['Type'] in ['FC1', 'FC2']:
            side = 1 if j['LeftWidth'] < j['RightWidth'] else -1
            my_sub_fund.at[i, 'fund_size'] = j['fund_size'][::side]
            my_sub_fund.at[i, 'fund_depth'] = j['fund_depth'][::side]
            my_sub_fund.at[i, 'pile_layout'] = j['pile_layout'][::side]
            my_sub_fund.at[i, 'pile_ra'] = j['pile_ra'][::side]

        if j['fund_type'] != '摩擦桩':
            my_sub_fund.at[i, 'pile_ra'] = []


my_sub_fund.to_csv(r'..\IO\wyz_fund_0426.csv', encoding='gbk')



