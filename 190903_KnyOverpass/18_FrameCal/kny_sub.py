import midas1
import kny_tool
import pandas as pd
import numpy as np
import wind
import tendon_new1


class KnySub:

    def __init__(self, bridge_inf):
        self.gamma = 1.1  # 结构重要性系数
        self.span_length = 30  # 跨长
        self.beam_height = 1.6  # 主梁高度
        self.support_height = 0.15  # 支座高度
        self.beam_offset = 0.04  # 梁端距墩中心线
        self.beam_support_offset = 0.5  # 梁端到支座中心
        self.link_pier_loc = set()  # 桥墩连接位置
        self.link_prop = [(1e8, 1e7, 1e7, 1e6, 1e6, 1e8), (5e7, 3e3, 3e3, 10, 10, 10)]  # 弹性连接刚度
        self.support_prop = (1.3e6, 2.71e3, 2.71e3, 10, 10, 10)  # 支座刚度
        self.pier_support_prop = (1e8, 3e3, 3e3, 100, 100, 100)  # 桥墩支座刚度
        self.barrier = (0.5, 0.6, 0.5), (0.41, 0.53, 0.41)  # 护栏宽度，截面积
        self.pave_thickness = (0.1, 0.07)  # 铺装层厚度（混凝土、沥青）

        self.f_lim = [22.4, 22.4, -2, -2]  # 混凝土容许应力（施工、使用、施工、使用）
        self.tendon_curve_r = 10  # 预应力半径，m
        self.tendon_per_n = 15  # 单束预应力股数
        self.tendon_edge = 0.3  # 预应力到边缘距离，m
        self.tendon_between = 0.35  # 预应力之间横向距离，m
        self.tendon_inf = {}  # 预应力配置信息

        self.mct_l = []  # mct 文件列表
        self.num_l = [0] * 4  # 截面号、节点号、单元号、弹性连接号
        self.bandgroup = ('constraint', 'support', 'pier_link', 'pier_cap', 'beam_link', 'cap_link')
        self.stldcase = ('DEAD', 'TENDON', 'PAVEMENT', 'TEM_U', 'TEM_D', 'WIND_1', 'WIND_2', 'BRAKE_FORCE')
        self.loadgroup = ('dead', 'tendon', 'pavement', 'tem_u', 'tem_d', 'wind_1', 'wind_2', 'brake_force')
        self.node_space = 1.5
        self.beam_space = 3
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

        beam_sec_id = self.sec_dic['B1']
        beam_h_sec_id = self.sec_dic['BH']

        support_dis = self.beam_offset + self.beam_support_offset
        node_x = [self.beam_offset, support_dis]
        node_x += np.linspace(self.beam_space / 2, self.span_length - self.beam_space / 2,
                              self.span_length // self.beam_space).tolist()
        node_x += [self.span_length - support_dis, self.span_length - self.beam_offset]
        node_x += [round(i - self.span_length, 5) for i in node_x]
        node_x.sort()

        node_y = self.support_loc
        node_z = 0

        for j in node_y:
            for i in node_x:
                self.add_node(i, j, node_z, 'beam')

        for i in [-self.span_length + support_dis, -support_dis, support_dis, self.span_length - support_dis]:
            for j in self.support_loc:
                self.add_node(i, j, node_z - self.beam_height, 'support_beam')
                self.add_node(i, j, node_z - self.beam_height - self.support_height, 'support_cap')

        for i in node_y:
            nodes = self.node[(self.node['what'] == 'beam') & (self.node['x'] < 0) & (self.node['y'] == i)].index
            elem1 = midas1.elem_from_nodes(nodes, s=beam_sec_id, m=1, num=self.num_l, what='beam')
            nodes = self.node[(self.node['what'] == 'beam') & (self.node['x'] > 0) & (self.node['y'] == i)].index
            elem2 = midas1.elem_from_nodes(nodes, s=beam_sec_id, m=1, num=self.num_l, what='beam')
            self.elem = pd.concat([self.elem, elem1, elem2])

        h_x = np.linspace(self.beam_space / 2, self.span_length - self.beam_space / 2,
                          self.span_length // self.beam_space).tolist()
        h_x += np.linspace(self.beam_space / 2 - self.span_length, -self.beam_space / 2,
                           self.span_length // self.beam_space).tolist()

        for i in h_x:
            nodes = self.node[(self.node['what'] == 'beam') & (self.node['x'] == i)].index
            elem1 = midas1.elem_from_nodes(nodes, s=beam_h_sec_id, m=4, num=self.num_l, what='beam_h')
            self.elem = pd.concat([self.elem, elem1])

    def pier_create(self, pier_sec, cap_height, sec_box, pier_link_list):
        for i, j in enumerate(self.bridge_inf['pier']):
            link_type = pier_link_list[i]
            pier_width = sec_box[pier_sec[i]][0]
            i_top = -self.beam_height - self.support_height - cap_height[i]
            i_bot = i_top + cap_height[i] - max(cap_height) - self.bridge_inf['pier_h']
            i_x = -self.span_length, 0, self.span_length
            i_z = np.linspace(i_bot, i_top, 9)
            for m in i_x:
                for n in i_z:
                    self.add_node(m, j, n, 'pier')

                i_nodes = self.node[
                    (self.node['what'] == 'pier') & (self.node['x'] == m) & (self.node['y'] == j)].index
                i_pier_elem = midas1.elem_from_nodes(
                    i_nodes, s=self.sec_dic[pier_sec[i]], m=3, num=self.num_l, what='pier')
                self.elem = pd.concat([self.elem, i_pier_elem])

                if link_type == 1:
                    for n in [-pier_width / 2 + 0.5, pier_width / 2 - 0.5]:
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
        i_z = -self.beam_height - self.support_height
        for i in cap_y:
            for j in i_x:
                self.add_node(j, i, i_z, 'cap')

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
                i_elem = self.elem[self.elem['s'] == self.sec_dic[i]].index
                if len(i_elem) != 0:
                    i_group = ' '.join(map(str, i_elem))
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
            i_beam_node = self.node[(self.node['what'] == 'beam') &
                                    (self.node['x'] == i_node['x']) & (self.node['y'] == i_node['y'])].index[0]
            midas1.add_rigid_link(i_beam_node, i, 'beam_link', num=self.num_l, mct_list=self.mct_l)

        for i in self.node[self.node['what'] == 'support_cap'].index:
            i_node = self.node.loc[i]
            i_cap_link_node = self.node[
                (self.node['what'] == 'cap') & (self.node['y'] == i_node['y']) &
                (self.node['x'] < i_node['x'] + 1) & (self.node['x'] > i_node['x'] - 1)].index[0]
            midas1.add_rigid_link(i_cap_link_node, i, 'cap_link', num=self.num_l, mct_list=self.mct_l)

    def elastic_link(self, pier_link_list):
        midas1.start_link(self.mct_l)
        pier_y = self.node[self.node['what'] == 'pier']['y'].unique()
        pier_top = [self.node[(self.node['what'] == 'pier') & (self.node['y'] == i)]['z'].max() for i in pier_y]

        for i in self.node[(self.node['what'] == 'pier') & (self.node['z'].isin(pier_top))].index:
            link_type = pier_link_list[self.bridge_inf['pier'].index(self.node.loc[i]['y'])]
            i_link_prop = self.link_prop[0] if link_type == 1 else self.pier_support_prop

            i_node = self.node.loc[i]
            i_cap_node = self.node[(self.node['what'] == 'cap') &
                                   (self.node['x'] == i_node['x']) & (self.node['y'] == i_node['y'])].index[0]
            midas1.add_elastic_link(i, i_cap_node, 'pier_cap', num=self.num_l, mct_list=self.mct_l,
                                    sdx=i_link_prop[0], sdy=i_link_prop[1], sdz=i_link_prop[2],
                                    srx=i_link_prop[3], sry=i_link_prop[4], srz=i_link_prop[5])

        for i in self.node[self.node['what'] == 'link_pier'].index:
            i_link_prop = self.link_prop[1]
            i_node = self.node.loc[i]
            i_cap_node = self.node[(self.node['what'] == 'cap') &
                                   (self.node['x'] == i_node['x']) & (self.node['y'] == i_node['y'])].index[0]
            midas1.add_elastic_link(i, i_cap_node, 'pier_cap', num=self.num_l, mct_list=self.mct_l,
                                    sdx=i_link_prop[0], sdy=i_link_prop[1], sdz=i_link_prop[2],
                                    srx=i_link_prop[3], sry=i_link_prop[4], srz=i_link_prop[5])

        for i in self.node[self.node['what'] == 'support_cap'].index:
            i_node = self.node.loc[i]
            i_beam_support_node = self.node[(self.node['what'] == 'support_beam') &
                                            (self.node['x'] == i_node['x']) & (self.node['y'] == i_node['y'])].index[0]
            midas1.add_elastic_link(i, i_beam_support_node, 'support', num=self.num_l, mct_list=self.mct_l,
                                    sdx=self.support_prop[0], sdy=self.support_prop[1], sdz=self.support_prop[2],
                                    srx=self.support_prop[3], sry=self.support_prop[4], srz=self.support_prop[5])

    def self_weight(self):
        midas1.start_stld('DEAD', mct_list=self.mct_l)
        midas1.add_self_weight(1, mct_list=self.mct_l, group='dead')

    def pavement(self):
        bridge_w = self.bridge_inf['bridge'][1] - self.bridge_inf['bridge'][0]
        joint_w = bridge_w - self.beam_num * 2.4
        joint_f = joint_w * 0.18 * 26

        pave_w = bridge_w - sum(self.barrier[0])
        barrier_f = sum(self.barrier[1]) * 26
        pave_f = bridge_w * self.pave_thickness[0] * 26 + pave_w * self.pave_thickness[1] * 24
        fz = (-barrier_f - pave_f - joint_f) / self.beam_num

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
        group_s = [['pier', 'other'], ['cap'], ['beam', 'beam_h'], []]
        start_t = [[30, 30], [60], [90, 90], []]
        group_b = [['pier_link', 'constraint'], ['cap_link', 'pier_cap', 'support'], ['beam_link'], []]
        group_l = [['dead'], ['tendon'], [], ['pavement']]

        for i, j in enumerate(name):
            midas1.add_stage(j, 28, elem=group_s[i], elem_time=start_t[i],
                             banr=group_b[i], load=group_l[i], mct_list=self.mct_l)
        midas1.add_stage('wait', 3600, mct_list=self.mct_l)

    def earthquake(self):
        with open('spectrum.txt') as f:
            spectrum = f.read()
        self.mct_l.append(spectrum)

    def vehicle(self, side=2):
        midas1.add_move_code(self.mct_l)

        bridge_w = self.bridge_inf['bridge'][1] - self.bridge_inf['bridge'][0]
        if side == 1:
            lane_num = kny_tool.get_lanes_from_w(bridge_w - 2, side=side)
        else:
            lane_num = kny_tool.get_lanes_from_w(bridge_w - 4, side=side)
        lane_w = (bridge_w - 2) / lane_num
        names = [f'lane_{i + 1}' for i in range(lane_num)]
        offsets = np.linspace(-(lane_num - 1) / 2 * lane_w, (lane_num - 1) / 2 * lane_w, lane_num)
        elems = []
        offsets_elem = []
        elem_y = self.elem[self.elem['what'] == 'beam']['n1'].map(lambda x: self.node.loc[x]['y'])
        for i in offsets:
            lane_y = i + sum(self.bridge_inf['bridge']) / 2
            offset_1 = elem_y - lane_y
            offset_2 = abs(offset_1)
            i_elem_y = elem_y[offset_2 == offset_2.min()].iloc[0]
            i_elems = self.elem[(self.elem['what'] == 'beam') & (elem_y == i_elem_y)].index.tolist()
            elems.append(i_elems)
            offsets_elem.append(i_elem_y - lane_y)
        spans = [self.span_length] * lane_num
        midas1.add_lanes(names, elems, offsets_elem, spans, mct_list=self.mct_l)
        midas1.add_vehicles(self.mct_l)
        midas1.add_move_case('mv', names, mct_list=self.mct_l)

    def brake_force(self, side=2):
        midas1.start_stld('BRAKE_FORCE', self.mct_l)
        midas1.start_beam_load(self.mct_l)

        bridge_w = self.bridge_inf['bridge'][1] - self.bridge_inf['bridge'][0]
        if side == 2:
            lane_num = kny_tool.get_lanes_from_w(bridge_w - 4, side=side)
            brake_f = lane_num / 2 * 165
        else:
            lane_num = kny_tool.get_lanes_from_w(bridge_w - 2, side=side)
            brake_f = lane_num * 165
        brake_f *= 1 / (self.span_length * self.beam_num)
        brake_elem = self.elem[self.elem['what'] == 'beam'].index
        midas1.beam_load(brake_elem, brake_f, side='X', offset_side='Z', offset_dis=1.2,
                         mct_list=self.mct_l, group='brake_force')

    def wind(self, h=5):
        bridge_w = self.bridge_inf['bridge'][1] - self.bridge_inf['bridge'][0]
        wind_beam = wind.BeamWind(0, [bridge_w, 1.6, 14], h, 30)
        beam_f = wind_beam.Fg / 1000 / self.beam_num
        elem_wind = self.elem[self.elem['what'] == 'beam'].index

        midas1.start_stld('WIND_1', self.mct_l)
        midas1.start_beam_load(self.mct_l)
        midas1.beam_load(elem_wind, beam_f, mct_list=self.mct_l, group='wind_1', side='Y')
        midas1.start_stld('WIND_2', self.mct_l)
        midas1.start_beam_load(self.mct_l)
        midas1.beam_load(elem_wind, -beam_f, mct_list=self.mct_l, group='wind_2', side='Y')

    def load_com(self):
        midas1.start_com(self.mct_l)
        com1 = ['TEM_U', 'TEM_D']
        com2 = ['WIND_1', 'WIND_2']
        for i, j in zip(['tem', 'wind'], [com1, com2]):
            midas1.com_f(i, j, [1, 1], ['ST', 'ST'], 1, mct_list=self.mct_l)

        com3 = ['合计', 'mv', 'BRAKE_FORCE', 'wind', 'tem']
        f3 = np.array([1.2, 1.4, 1.4, 1.1 * 0.75, 1.4 * 0.75]) * self.gamma
        t3 = ['CS', 'MV', 'ST', 'CB', 'CB']
        midas1.com_f('mu', com3, f3, t3, 0, mct_list=self.mct_l)

        f4 = np.array([1, 0.7, 0.7, 0.4, 0.4])
        midas1.com_f('ms', com3, f4, t3, 0, mct_list=self.mct_l)
        f5 = np.array([1, 0.4, 0.4, 0.4, 0.4])
        midas1.com_f('ml', com3, f5, t3, 0, mct_list=self.mct_l)
        f6 = np.ones(5)
        midas1.com_f('me', com3, f6, t3, 0, mct_list=self.mct_l)

        com_e1 = ['e1-x', 'e1-y']
        com_e2 = ['e2-x', 'e2-y']
        for i, j in zip(['e1', 'e2'], [com_e1, com_e2]):
            midas1.com_f(i, j, [1, 1], ['RS', 'RS'], 1, mct_list=self.mct_l)
        com_e1 = ['合计', 'e1', 'mv', 'BRAKE_FORCE', 'wind', 'tem']
        f_e1 = [1, 1, 0.4, 0.4, 0.4, 0.4]
        t_e1 = ['CS', 'CB', 'MV', 'ST', 'CB', 'CB']
        midas1.com_f('me1', com_e1, f_e1, t_e1, 0, mct_list=self.mct_l)
        com_e2 = ['合计', 'e2', 'tem']
        f_e2 = [1, 1, 0.4]
        t_e2 = ['CS', 'CB', 'CB']
        midas1.com_f('me2', com_e2, f_e2, t_e2, 0, mct_list=self.mct_l)

    def load_com_some(self):
        midas1.start_com(self.mct_l)
        com1 = ['TEM_U', 'TEM_D']
        com2 = ['WIND_1', 'WIND_2']
        for i, j in zip(['tem', 'wind'], [com1, com2]):
            midas1.com_f(i, j, [1, 1], ['ST', 'ST'], 1, mct_list=self.mct_l)

        com3 = ['合计', 'mv', 'BRAKE_FORCE', 'wind', 'tem']
        f3 = np.array([1.2, 1.4, 1.4, 1.1 * 0.75, 1.4 * 0.75]) * self.gamma
        t3 = ['CS', 'MV', 'ST', 'CB', 'CB']
        midas1.com_f('mu', com3, f3, t3, 0, mct_list=self.mct_l)

        f4 = np.array([1, 0.7, 0.7, 0.4, 0.4])
        midas1.com_f('ms', com3, f4, t3, 0, mct_list=self.mct_l)
        f5 = np.array([1, 0.4, 0.4, 0.4, 0.4])
        midas1.com_f('ml', com3, f5, t3, 0, mct_list=self.mct_l)
        f6 = np.ones(5)
        midas1.com_f('me', com3, f6, t3, 0, mct_list=self.mct_l)

    def tendon_cal(self, tendon_sec, secs, sec_box, tendon_secs_f):
        t_secs = []
        for i in tendon_sec:
            i_sec_id = self.sec_dic[i]
            t_secs.append(secs.secs[i_sec_id - 1])
        ts = [tendon_new1.Tendon(i) for i in t_secs]
        pro_infs = []
        pro_ep = []
        pro_to_top = []
        pro_ult = []
        pro_np = 1
        pro_ni = 1
        for m, n in enumerate(tendon_secs_f):
            ts[m].tendon_cal(n[0], n[2], n[1], self.f_lim[2], self.f_lim[0], self.f_lim[3], self.f_lim[1])
            i_sec_width = sec_box[tendon_sec[0]][0]
            if m == 0:
                pro_infs.append(ts[m].get_np_from_pw(i_sec_width, pro_one=self.tendon_per_n, s_p_h=self.tendon_edge,
                                                     p_p_h=self.tendon_between))
                pro_np = pro_infs[0][0]
                pro_ep.append(pro_infs[0][1])
                pro_ni = pro_infs[0][2]
                pro_to_top.append(pro_infs[0][3])
                pro_ult.append(ts[m].get_np_from_mu(n[3], self.f_lim[0], i_sec_width, pro_ep[0]))
            else:
                pro_infs.append(ts[m].get_ep_from_np(pro_np, pro_ni))
                pro_ep.append(pro_infs[-1][0])
                pro_to_top.append(pro_infs[-1][1])
                ts[m].plot_pro(ts[m].ep, ts[m].np, pro_ep[-1], 1 / pro_np)
                pro_ult.append(ts[m].get_np_from_mu(n[3], self.f_lim[0], i_sec_width, pro_ep[-1]))

        self.tendon_inf['tendon_ni'] = pro_ni
        self.tendon_inf['tendon_to_top'] = pro_to_top
        self.tendon_inf['tendon_np'] = pro_np
        self.tendon_inf['tendon_ep'] = pro_ep
        self.tendon_inf['tendon_ult'] = pro_ult

    def add_tendon(self, cap_sec, secs):

        # 钢束线型
        midas1.tendon_prop(['T1'], [140 * self.tendon_per_n / 1e6], 2, self.mct_l)
        # 钢束线型
        tendon_loc, tendon_type = kny_tool.tendon_loc_type(self.bridge_inf)
        midas1.start_tendon_type(self.mct_l)
        tendon_z = []
        tendon_r = []
        for i, j in enumerate(tendon_type):
            if j == 0:
                i_sec = cap_sec[0] if i == 0 else cap_sec[-1]
                i_cz = -secs.secs[self.sec_dic[i_sec] - 1].prop['c'][2]
                i_z = i_cz + self.tendon_inf['tendon_to_top'][0] - \
                      np.average(self.tendon_inf['tendon_to_top'][0], weights=self.tendon_inf['tendon_ni'])
                tendon_z.append(i_z)
                tendon_r.append(0)
            else:
                tendon_z.append(self.tendon_inf['tendon_to_top'][j-1])
                tendon_r.append(self.tendon_curve_r)
        origin_pt = (0, 0, - self.beam_height - self.support_height)
        tendon_elem = self.elem[(self.elem['what'] == 'cap') & (self.elem['x'] == 0)].index
        y_pt = [(min(tendon_loc), 0, 0), (max(tendon_loc), 0, 0)]
        for i, j in enumerate(self.tendon_inf['tendon_ni']):
            i_pt_z = [m[i] for m in tendon_z]
            z_pt = np.array([tendon_loc, i_pt_z, tendon_r]).T
            midas1.tendon_type(f't-{i+1}', 'T1', tendon_elem,
                               self.tendon_inf['tendon_ni'][i], origin_pt, 'Y', y_pt, z_pt, self.mct_l)
        # 张拉预应力
        midas1.start_stld('TENDON', self.mct_l)
        midas1.start_tendon_f(self.mct_l)
        for i, j in enumerate(self.tendon_inf['tendon_ni']):
            midas1.tendon_f(f't-{i + 1}', mct_list=self.mct_l)


