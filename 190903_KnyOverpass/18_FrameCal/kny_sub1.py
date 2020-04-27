import midas1
import kny_tool
import pandas as pd
import numpy as np


class KnySub:

    def __init__(self, bridge_inf):
        self.span_length = 30  # 跨长
        self.beam_height = 1.6  # 主梁高度
        self.support_height = 0.15  # 支座高度
        self.stone_height = 0.15   # 垫石高度
        self.beam_offset = 0.04  # 梁端距墩中心线
        self.beam_support_offset = 0.5  # 梁端到支座中心
        self.link_pier_loc = set()         # 桥墩连接位置
        self.link_prop = [(1e7, 5e6, 5e6), (5e6, 5e6, 5e6)]     # 弹性连接刚度
        self.support_prop = (1e3, 1e2, 1e2)     # 支座刚度
        self.barrier = (0.5, 0.6, 0.5), (0.41, 0.53, 0.41)      # 护栏宽度，截面积
        self.pave_thickness = (0.1, 0.07)       # 铺装层厚度（混凝土、沥青）

        self.mct_l = []  # mct 文件列表
        self.num_l = [0] * 4  # 截面号、节点号、单元号、弹性连接号
        self.bandgroup = ('constraint', 'support', 'pier_link', 'pier_cap', 'beam_link', 'cap_link', 'cap_stone')
        self.stldcase = ('DEAD', 'TENDON', 'PAVEMENT', 'TEM_U', 'TEM_D', 'WIND_1', 'WIND_2', 'E1', 'E2')
        self.loadgroup = ('dead', 'tendon', 'pavement', 'tem_u', 'tem_d', 'wind_1', 'wind_2', 'e1', 'e2')
        self.node_space = 1
        self.temp = (-15, 15)

        self.sec_dic = {}
        self.node = pd.DataFrame(columns=['x', 'y', 'z', 'what'])
        self.elem = pd.DataFrame(columns=['m', 's', 'b', 'n1', 'n2', 'what'])

        midas1.usual_data(mct_list=self.mct_l,
                          loadgroup=self.loadgroup,
                          stldcase=self.stldcase,
                          bandgroup=self.bandgroup)

        self.bridge_inf = bridge_inf
        bridge_range = bridge_inf['bridge']
        bridge_w = bridge_range[1] - bridge_range[0]
        self.beam_num = kny_tool.num_from_width(bridge_w)
        self.support_loc = kny_tool.support_from_width(bridge_w)
        self.support_loc = [i + bridge_range[0] for i in self.support_loc]

    def add_my_sec(self, my_sec_midas):
        midas1.psv_sec_start(self.mct_l)
        sec_dic_add = midas1.add_my_sec(my_sec_midas, mct_list=self.mct_l, num=self.num_l)
        self.sec_dic.update(sec_dic_add)

    def add_psc_sec(self, psc_sec_dic):
        midas1.sec_start(self.mct_l)
        for i, j in psc_sec_dic.items():
            if len(j) == 2:
                num_add, name_add = midas1.add_rectangle_sec(
                    i, 'CC', j[0], j[1], mct_list=self.mct_l, num=self.num_l)
            else:
                num_add, name_add = midas1.add_edge_sec(
                    i, 'CT', j[0], j[1], j[2], j[3], mct_list=self.mct_l, num=self.num_l)

            self.sec_dic[name_add] = num_add

    def add_simple_variable_sec(self, variable_sec_l):
        for i in variable_sec_l:
            num_add, name_add = midas1.add_simple_change_sec(i[0], i[1], mct_list=self.mct_l, num=self.num_l)
            self.sec_dic[name_add] = num_add

    def add_node(self, x, y, z, what):
        self.num_l[1] += 1
        self.node.loc[self.num_l[1]] = [x, y, z, what]

    def beam_create(self):

        beam_sec_id = self.sec_dic['B' + str(self.beam_num)]

        support_dis = self.beam_offset + self.beam_support_offset
        node_x = [self.beam_offset, support_dis]
        node_x += list(range(1, int(self.span_length)))
        node_x += [self.span_length - support_dis, self.span_length - self.beam_offset]
        node_x += [round(i - self.span_length, 5) for i in node_x]
        node_x.sort()

        node_y = sum(self.bridge_inf['bridge']) / 2
        node_z = 0

        for i in node_x:
            self.add_node(i, node_y, node_z, 'beam')

        for i in [-self.span_length + support_dis, -support_dis, support_dis, self.span_length - support_dis]:
            for j in self.support_loc:
                self.add_node(i, j, -self.beam_height, 'support_beam')
                self.add_node(i, j, -self.beam_height - self.support_height, 'support_stone')

        nodes = self.node[(self.node['what'] == 'beam') & (self.node['x'] < 0)].index
        elem1 = midas1.elem_from_nodes(nodes, s=beam_sec_id, m=1, num=self.num_l, what='beam')
        nodes = self.node[(self.node['what'] == 'beam') & (self.node['x'] > 0)].index
        elem2 = midas1.elem_from_nodes(nodes, s=beam_sec_id, m=1, num=self.num_l, what='beam')
        self.elem = pd.concat([self.elem, elem1, elem2])

    def pier_create(self, pier_sec, cap_height, sec_box):
        for i, j in enumerate(self.bridge_inf['pier']):
            pier_width = sec_box[pier_sec[i]][1]
            i_top = -self.beam_height - self.support_height - self.stone_height - cap_height[i]
            i_bot = i_top + cap_height[i] - max(cap_height) - self.bridge_inf['pier_h']
            i_x = -self.span_length, 0, self.span_length
            i_z = np.linspace(i_bot, i_top, 11)
            for m in i_x:
                for n in i_z:
                    self.add_node(m, j, n, 'pier')

                i_nodes = self.node[
                    (self.node['what'] == 'pier') & (self.node['x'] == m) & (self.node['y'] == j)].index
                i_pier_elem = midas1.elem_from_nodes(
                    i_nodes, s=self.sec_dic[pier_sec[i]], m=3, num=self.num_l, what='pier')
                self.elem = pd.concat([self.elem, i_pier_elem])

                for n in [-pier_width/2 + 0.5, pier_width/2 - 0.5]:
                    self.add_node(m, j + n, i_top, 'link_pier')
                    self.link_pier_loc.add(j + n)

    def cap_create(self, cap_loc, cap_sec):
        cap_must = sorted(cap_loc + list(self.link_pier_loc) + self.bridge_inf['pier'] + self.support_loc)
        cap_add = []

        for i, j in enumerate(cap_must):
            if i != 0:
                space = j - cap_must[i - 1]
                if space > self.node_space:
                    segment = int(space // self.node_space + 1)
                    node_add_i = np.linspace(cap_must[i - 1], j, segment + 1).tolist()
                    cap_add += node_add_i[1:-1]

        cap_y = sorted(cap_must + cap_add)
        i_x = -self.span_length, 0, self.span_length
        i_z = -self.beam_height - self.support_height - self.stone_height
        for i in cap_y:
            for j in i_x:
                self.add_node(j, i, i_z, 'cap')

        for i in self.support_loc:
            for j in i_x:
                self.add_node(j, i, i_z + self.stone_height, 'cap_link')

        for m in i_x:
            for i, j in enumerate(cap_sec[:-1]):
                if cap_sec[i + 1] == j:
                    i_sec = self.sec_dic[j]
                else:
                    i_sec = self.sec_dic[j + '_' + cap_sec[i + 1]]
                cap_interval = cap_loc[i: i + 2]
                i_nodes = self.node[(self.node['y'] >= cap_interval[0]) & (self.node['y'] <= cap_interval[1])
                                    & (self.node['x'] == m) & (self.node['what'] == 'cap')].index
                i_cap_elem = midas1.elem_from_nodes(
                    i_nodes, s=i_sec, m=1, num=self.num_l, what='cap')
                self.elem = pd.concat([self.elem, i_cap_elem])

    def node_elem_mct(self):
        midas1.node_to_mct(self.node, self.mct_l)
        midas1.elem_to_mct(self.elem, mct_list=self.mct_l)

    def variable_sec_group(self):
        midas1.start_change_group(self.mct_l)
        for i in self.sec_dic:
            if '_' in i:
                i_group = ' '.join(map(str, self.elem[self.elem['s'] == self.sec_dic[i]].index))
                midas1.add_change_group(self.sec_dic[i], i_group, mct_list=self.mct_l)

    def struct_group(self):
        group_l = self.elem['what'].unique().tolist()
        group_elem = []
        group_node = []

        for i in group_l:
            i_elem = ' '.join([str(a) for a in self.elem[self.elem['what'] == i].index])
            i_node = ' '.join([str(a) for a in self.node[self.node['what'] == i].index])
            group_elem.append(i_elem)
            group_node.append(i_node)

        i_node = ' '.join([str(a) for a in self.node[~self.node['what'].isin(group_l)].index])
        group_l.append('other')
        group_node.append(i_node)
        group_elem.append(' ')
        midas1.add_group(group_l, group_node, group_elem, mct_list=self.mct_l)

    def boundary(self):
        midas1.start_boundary(self.mct_l)
        pier_bot = self.node[self.node['what'] == 'pier']['z'].min()
        bot_node = self.node[self.node['z'] == pier_bot].index
        for i in bot_node:
            midas1.add_boundary(i, 'constraint', '111111', mct_list=self.mct_l)

    def rigid_link(self):
        midas1.start_link(self.mct_l)
        for i in self.node[self.node['what'] == 'link_pier'].index:
            i_node = self.node.loc[i]
            i_pier_node = self.node[(self.node['x'] == i_node['x']) &
                                    (self.node['z'] == i_node['z']) &
                                    (self.node['what'] == 'pier') &
                                    (self.node['y'] < i_node['y'] + 2.5) &
                                    (self.node['y'] > i_node['y'] - 2.5)].index[0]
            midas1.add_rigid_link(i_pier_node, i, 'pier_link', num=self.num_l, mct_list=self.mct_l)

        for i in self.node[self.node['what'] == 'support_beam'].index:
            i_node = self.node.loc[i]
            i_beam_node = self.node[(self.node['what'] == 'beam') & (self.node['x'] == i_node['x'])].index[0]
            midas1.add_rigid_link(i_beam_node, i, 'beam_link', num=self.num_l, mct_list=self.mct_l)

        for i in self.node[self.node['what'] == 'support_stone'].index:
            i_node = self.node.loc[i]
            i_cap_link_node = self.node[
                (self.node['what'] == 'cap_link') & (self.node['y'] == i_node['y']) &
                (self.node['x'] < i_node['x'] + 1) & (self.node['x'] > i_node['x'] - 1)].index[0]
            midas1.add_rigid_link(i_cap_link_node, i, 'cap_stone', num=self.num_l, mct_list=self.mct_l)

        for i in self.node[self.node['what'] == 'cap_link'].index:
            i_node = self.node.loc[i]
            i_cap_node = self.node[(self.node['what'] == 'cap') & (self.node['y'] == i_node['y']) &
                                   (self.node['x'] == i_node['x'])].index[0]
            midas1.add_rigid_link(i_cap_node, i, 'cap_link', num=self.num_l, mct_list=self.mct_l)

    def elastic_link(self):
        midas1.start_link(self.mct_l)
        pier_y = self.node[self.node['what'] == 'pier']['y'].unique()
        pier_top = [self.node[(self.node['what'] == 'pier') & (self.node['y'] == i)]['z'].max() for i in pier_y]
        for i in self.node[(self.node['what'] == 'pier') & (self.node['z'].isin(pier_top))].index:
            i_node = self.node.loc[i]
            i_cap_node = self.node[(self.node['what'] == 'cap') &
                                   (self.node['x'] == i_node['x']) & (self.node['y'] == i_node['y'])].index[0]
            midas1.add_elastic_link(i, i_cap_node, 'pier_cap', num=self.num_l, mct_list=self.mct_l,
                                    sdx=self.link_prop[0][0], sdy=self.link_prop[0][1], sdz=self.link_prop[0][2])

        for i in self.node[self.node['what'] == 'link_pier'].index:
            i_node = self.node.loc[i]
            i_cap_node = self.node[(self.node['what'] == 'cap') &
                                   (self.node['x'] == i_node['x']) & (self.node['y'] == i_node['y'])].index[0]
            midas1.add_elastic_link(i, i_cap_node, 'pier_cap', num=self.num_l, mct_list=self.mct_l,
                                    sdx=self.link_prop[1][0], sdy=self.link_prop[1][1], sdz=self.link_prop[1][2])

        for i in self.node[self.node['what'] == 'support_stone'].index:
            i_node = self.node.loc[i]
            i_beam_support_node = self.node[(self.node['what'] == 'support_beam') &
                                            (self.node['x'] == i_node['x']) & (self.node['y'] == i_node['y'])].index[0]
            midas1.add_elastic_link(i, i_beam_support_node, 'support', num=self.num_l, mct_list=self.mct_l,
                                    sdx=self.support_prop[0], sdy=self.support_prop[1], sdz=self.support_prop[2])

    def self_weight(self):
        midas1.start_stld('DEAD', mct_list=self.mct_l)
        midas1.add_self_weight(1, mct_list=self.mct_l, group='dead')

    def pavement(self):
        bridge_w = self.bridge_inf['bridge'][1] - self.bridge_inf['bridge'][0]
        pave_w = bridge_w - sum(self.barrier[0])
        barrier_f = sum(self.barrier[1]) * 26
        pave_f = bridge_w * self.pave_thickness[0] * 26 + pave_w * self.pave_thickness[1] * 24
        fz = -barrier_f - pave_f
        midas1.start_stld('PAVEMENT', self.mct_l)
        midas1.start_beam_load(self.mct_l)
        i_elems = self.elem[self.elem['what'] == 'beam'].index
        midas1.beam_load(i_elems, fz, mct_list=self.mct_l, group='pavement')

    def tem(self):
        i_elems = self.elem.index
        midas1.start_stld('TEM_U', self.mct_l)
        midas1.start_tem_load(self.mct_l)
        for i in i_elems:
            midas1.tem_load(i, self.temp[0], mct_list=self.mct_l, group='tem_u')
        midas1.start_stld('TEM_D', self.mct_l)
        midas1.start_tem_load(self.mct_l)
        for i in i_elems:
            midas1.tem_load(i, self.temp[1], mct_list=self.mct_l, group='tem_d')

    def stage(self):
        midas1.start_stage(self.mct_l)
        name = ['pier', 'cap', 'beam', 'pavement']
        group_s = [['pier', 'other'], ['cap'], ['beam'], []]
        start_t = [[30, 30], [60], [90], []]
        group_b = [['pier_link', 'constraint'], ['cap_link', 'pier_cap', 'cap_stone'], ['beam_link', 'support'], []]
        group_l = [['dead'], ['tendon'], [], ['pavement']]

        for i, j in enumerate(name):
            midas1.add_stage(j, 28, elem=group_s[i], elem_time=start_t[i],
                             banr=group_b[i], load=group_l[i], mct_list=self.mct_l)
        midas1.add_stage('wait', 3600, mct_list=self.mct_l)

    def earthquake(self):
        with open('spectrum.txt') as f:
            spectrum = f.read()
        self.mct_l.append(spectrum)






