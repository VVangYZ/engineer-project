# from input_data import get_distance
#
# print(get_distance('cca', 16430))

import pandas as pd
import kny_tool
from pprint import pprint

sub_pd = pd.read_json('../IO/sub_df.json', orient='split')

get_w = lambda x: x[1] - x[0]

sub_pd['bridge_w'] = sub_pd['bridge'].map(get_w)
sub_pd['beam_num'] = sub_pd['bridge_w'].map(kny_tool.num_from_width)
sub_pd['joint'] = sub_pd['bridge_w'].map(kny_tool.joint_from_width)

my_type = ['F2', 'F3', 'FC2', 'FC1']
for i in my_type:
    i_sub = sub_pd[sub_pd['type'] == i]['beam_num']
    num_l = sorted(i_sub.unique())
    for j in num_l:
        i_count = i_sub[i_sub == j].count()
        i_bridge = sub_pd[(sub_pd['type'] == i) & (sub_pd['beam_num'] == j)]['bridge_w'].mean()
        i_note = '类型：{:<5}梁数：{:<5.0f}个数：{:<5.0f}平均梁宽：{:<7.2f}'
        print(i_note.format(i, j, i_count, i_bridge))

sub_max = sub_pd[sub_pd['beam_num'] == 11]
sub_my = sub_pd[sub_pd['type'].isin(my_type)]
sub_my[sub_my['joint'] > 0.95].count()


