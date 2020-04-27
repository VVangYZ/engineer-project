import numpy as np
import cad
import win32com.client as win32
import pickle


# 通过桥宽获取主梁片数、湿接缝宽度及支座位置信息 =======================================================================

beam_width = [2.85, 2.4]        # 梁宽（边、中）
beam_joint = [0.3, 1]           # 接缝宽度范围
bridge_width_with_num = {}
for num in range(3, 15):
    beam_range = [beam_width[0] * 2 + (num - 2) * beam_width[1] + (num - 1) * j for j in beam_joint]
    bridge_width_with_num[num] = beam_range
    # i_note = '主梁片数：{:<5}最窄：{:<7.1f}最宽：{:<7.1f}'
    # print(i_note.format(num, beam_range[0], beam_range[1]))


def num_from_width(w):
    """
    通过桥梁宽度确定所需梁片数及湿接缝宽度
    :param w: 桥梁宽度，单位 m
    :return: 桥梁片数，湿接缝宽度
    """
    beam_num = 100

    for i, j in bridge_width_with_num.items():
        if j[0] <= w <= j[1]:
            beam_num = i if i < beam_num else beam_num

    if beam_num == 100:
        print('无法正常配置湿接缝')

    return beam_num


def joint_from_width(w):
    """通过桥梁宽度获得湿接缝宽度"""
    beam_num = num_from_width(w)
    return (w - (beam_num - 2) * beam_width[1] - 2 * beam_width[0]) / (beam_num - 1)


def support_from_width(w):
    """
    通过桥梁宽度获取支座位置（相对于桥梁最左侧）
    :param w: 桥梁宽度，单位 m
    :return: 支座位置列表
    """
    beam_num = num_from_width(w)
    joint_width = joint_from_width(w)
    if beam_num == 100:
        beam_num = int(w // beam_width[1])
        joint_width = (w - beam_num * beam_width[1]) / (beam_num - 1)
        if beam_joint[0] < joint_width < beam_joint[1]:
            print(f'再次配置湿接缝宽度为{joint_width}m，满足要求')
            support_space = beam_width[1] + joint_width
            support_loc_list = [beam_width[1] / 2 + i * support_space for i in range(beam_num)]
        else:
            print(f'再次配置湿接缝宽度为{joint_width}m，不满足要求')
            raise Exception
    else:
        support_space = beam_width[1] + joint_width
        support_loc_list = [beam_width[0] - beam_width[1] / 2 + i * support_space for i in range(beam_num)]
    return support_loc_list


# 截面函数 ====================================================================================================

def get_my_sec(name):
    acad = win32.Dispatch("AutoCAD.Application")
    doc = acad.ActiveDocument
    ms = doc.ModelSpace
    if doc.name == name:
        secs = cad.CadSecs(ms)
    else:
        raise Exception
    return secs


def get_sec_box(secs):
    """
    获取截面边框
    :param secs: cad.cadsecs 类
    :return: 边框字典
    """
    sec_box = {}
    for i, j in enumerate(secs.secs):
        lx = round(j.prop['c'][0] + j.prop['c'][1], 4)
        ly = round(j.prop['c'][2] + j.prop['c'][3], 4)
        sec_box[secs.sec_name[i]] = (lx, ly)
    return sec_box


def get_pier_cap_inf(bridge, pier_sec_dic, cap_sec_dic, sec_box, fc_cap_l1):
    """
    通过桥梁类型获取墩、盖梁信息
    :param bridge: kny_sub 类
    :param pier_sec_dic: 桥墩截面字典
    :param cap_sec_dic: 盖梁截面字典
    :param sec_box: 截面名称-边框字典
    :param fc_cap_l1: fc 类型下部预制块长度，m
    :return: 桥墩截面、盖梁坐标、盖梁截面
    """
    if bridge.bridge_inf['type'] in ['F2', 'F2S', 'F2X']:
        pier_sec = pier_sec_dic[bridge.bridge_inf['type']]
        cap_loc = bridge.bridge_inf['cap']
        cap_sec = [cap_sec_dic[bridge.bridge_inf['type']][0]] * 2
    elif bridge.bridge_inf['type'] == 'F3':
        pier_sec = pier_sec_dic['F3']
        cap_loc = bridge.bridge_inf['cap'].copy()
        cap_loc += [bridge.bridge_inf['pier'][1] + i
                    for i in (-5, -sec_box[pier_sec[1]][0] / 2 - 0.2, sec_box[pier_sec[1]][0] / 2 + 0.2, 5)]
        cap_loc.sort()
        cap_sec = cap_sec_dic['F3']
        cap_sec = [cap_sec[0]] * 2 + [cap_sec[1]] * 2 + [cap_sec[2]] * 2
    elif bridge.bridge_inf['type'] in ['FC1', 'FC1S']:
        pier_sec = pier_sec_dic['FC1']
        cap_loc = bridge.bridge_inf['cap'].copy()
        cap_loc += [bridge.bridge_inf['pier'][0] - sec_box[pier_sec[0]][0] / 2 - 0.2,
                    bridge.bridge_inf['pier'][0] + sec_box[pier_sec[0]][0] / 2 + 0.2,
                    bridge.bridge_inf['pier'][1] - sec_box[pier_sec[1]][0] / 2 - 0.2]
        cap_loc += [cap_loc[-1] - fc_cap_l1, cap_loc[-2] + fc_cap_l1]
        cap_loc.sort()
        cap_sec = [cap_sec_dic['FC1'][0]] + [cap_sec_dic['FC1'][1]] * 2 + \
                  [cap_sec_dic['FC1'][2]] * 2 + [cap_sec_dic['FC1'][3]] * 2
    elif bridge.bridge_inf['type'] in ['FC2', 'FC2S']:
        pier_sec = pier_sec_dic['FC2']
        cap_loc = bridge.bridge_inf['cap'].copy()
        cap_loc += [bridge.bridge_inf['pier'][0] - sec_box[pier_sec[0]][0] / 2 - 0.2,
                    bridge.bridge_inf['pier'][1] + sec_box[pier_sec[1]][0] / 2 + 0.2,
                    bridge.bridge_inf['pier'][2] - sec_box[pier_sec[2]][0] / 2 - 0.2]
        cap_loc += [cap_loc[-1] - fc_cap_l1, cap_loc[-2] + fc_cap_l1]
        cap_loc.sort()
        cap_sec = [cap_sec_dic['FC2'][0]] + [cap_sec_dic['FC2'][1]] * 2 + \
                  [cap_sec_dic['FC2'][2]] * 2 + [cap_sec_dic['FC2'][3]] * 2
    else:
        print('WRONG!')
        raise Exception

    return pier_sec, cap_loc, cap_sec


def get_cap_height(cap_loc, cap_sec, pier_loc, sec_box):
    """
    获取桥墩位置盖梁高度
    :param cap_loc:
    :param cap_sec:
    :param pier_loc:
    :param sec_box:
    :return: 盖梁高度列表
    """
    cap_h = []
    for i in pier_loc:
        i_cap = cap_sec[np.where(np.array(cap_loc) > i)[0][0]]
        cap_h.append(sec_box[i_cap][1])
    return cap_h


def get_lanes_from_w(w, side=1):
    w1 = [7, 10.5, 14, 17.5, 21, 24.5, 28, 31.5]
    w2 = [14, 21, 28, 35]
    l1 = list(range(1, 9))
    l2 = [2, 4, 6, 8]
    if side == 1:
        for i, j in enumerate(w1):
            if j > w:
                return l1[i]
    else:
        for i, j in enumerate(w2):
            if j > w:
                return l2[i]
    print('宽度不合适')
    raise Exception


def tendon_loc_type(bridge):
    if bridge['type'] in ['F2', 'F2S', 'F2X']:
        mid = sum(bridge['cap']) / 2
        dis_dic = {'F2X': 5.4, 'F2': 6.8, 'F2S': 9.8}
        loc = [bridge['cap'][0], bridge['cap'][0] + dis_dic[bridge['type']],
               bridge['cap'][1] - dis_dic[bridge['type']], bridge['cap'][1]]
        t_type = (0, 1, 1, 0)
    elif bridge['type'] == 'F3':
        mid1 = sum(bridge['pier'][:2]) / 2
        mid2 = sum(bridge['pier'][1:]) / 2
        loc = [
            bridge['cap'][0],
            mid1 - 4,
            mid1,
            bridge['pier'][1] - 2,
            bridge['pier'][1] + 2,
            mid2,
            mid2 + 4,
            bridge['cap'][1]
        ]
        t_type = (0, 2, 2, 1, 1, 3, 3, 0)
    elif bridge['type'] in ['FC1', 'FC1S']:
        mid = sum(bridge['pier']) / 2
        loc = [
            bridge['cap'][0],
            bridge['pier'][0] - 2,
            bridge['pier'][0] + 2,
            mid - 2,
            mid + 2,
            bridge['cap'][1]
        ]
        t_type = (0, 1, 1, 2, 2, 0)
    elif bridge['type'] in ['FC2', 'FC2S']:
        mid = sum(bridge['pier'][1:]) / 2
        loc = [
            bridge['cap'][0],
            bridge['pier'][0] - 0.8,
            bridge['pier'][1] + 0.8,
            mid - 2,
            mid + 2,
            bridge['cap'][1]
        ]
        t_type = (0, 1, 1, 2, 2, 0)
    else:
        raise Exception
    return loc, t_type


def tendon_fc1(cap_l):
    if cap_l < 30:
        ni = [4, 5]
        to_top = [np.array([-0.25, -0.45]), np.array([-1.3, -1.5])]
    elif cap_l < 35:
        ni = [3, 4, 5]
        to_top = [np.array([-0.25, -0.45, -0.65]), np.array([-1.1, -1.3, -1.5])]
    else:
        ni = [5, 4, 5]
        to_top = [np.array([-0.25, -0.45, -0.65]), np.array([-1.1, -1.3, -1.5])]
    return ni, to_top


def tendon_fc2(cap_l):
    if cap_l < 33:
        ni = [5, 4]
        to_top = [np.array([-0.2, -0.4]), np.array([-1, -1.2])]
    elif cap_l < 36:
        ni = [5, 4, 3]
        to_top = [np.array([-0.2, -0.4, -0.6]), np.array([-0.8, -1, -1.2])]
    else:
        ni = [5, 4, 5]
        to_top = [np.array([-0.2, -0.4, -0.6]), np.array([-0.8, -1, -1.2])]
    return ni, to_top


def tendon_f2(cap_l):
    if cap_l < 17:
        ni = [4, 5]
        to_top = [np.array([-1.2, -1.4])]
    elif cap_l < 25:
        ni = [5, 4, 5]
        to_top = [np.array([-1.6, -1.8, -2])]
    elif cap_l < 35:
        ni = [5, 4, 5]
        to_top = [np.array([-2.1, -2.3, -2.3])]
    else:
        ni = [3, 5, 5, 5]
        to_top = [np.array([-1.7, -1.9, -2.1, -2.3])]
    return ni, to_top


def tendon_f3(cap_l):
    if cap_l < 37:
        ni = [3, 5]
        to_top = [np.array([-0.5, -0.7]), np.array([-1.5, -1.7]), np.array([-1.5, -1.7])]
    else:
        ni = [5, 5]
        to_top = [np.array([-0.5, -0.7]), np.array([-1.5, -1.7]), np.array([-1.5, -1.7])]
    return ni, to_top


class KnyBlock:
    def __init__(self, block_type, block_length, edge=0):
        self.type = block_type
        self.length = block_length
        self.density = 2.5
        self.vari = -1
        self.volume = 0
        self.edge = edge
        little_thing = lambda x, y=1.8: x*y*0.5 + (x-0.5)*(y-0.5)*0.24
        cap_v = lambda x, y: x*2.2 + y*2
        if block_type == 'CB06':
            self.volume = cap_v(13.08, 9.38) + little_thing(1.8)
        elif block_type == 'CB01':
            self.volume = cap_v(7.36, 3.58)
        elif block_type == 'CB02':
            self.volume = cap_v(8.03, 9.9) + little_thing(4)
        elif block_type == 'CB07':
            self.vari = block_length
            self.volume = cap_v(self.vari * 1.1, self.vari * 1.1)
        elif block_type == 'CB14':
            self.vari = block_length - 8.45
            self.volume = cap_v(9.295 + self.vari * 1.1, 7.23 + self.vari * 0.4)
        elif block_type == 'CB15':
            self.volume = cap_v(9.24, 7.175) + little_thing(1.8)
        elif block_type == 'CB16':
            self.vari = block_length
            self.volume = cap_v(1.1 * self.vari, 0.4 * self.vari)
        elif block_type == 'CB11':
            self.vari = block_length - 4.15
            self.volume = cap_v(4.565 + 1.1 * self.vari, 3.658 + 0.6 * self.vari)
        elif block_type == 'CB12':
            self.volume = cap_v(9.24, 7.765) + little_thing(1.8)
        elif block_type == 'CB13':
            self.vari = block_length
            self.volume = cap_v(self.vari * 1.1, self.vari * 0.6)
        elif block_type == 'CB18':
            self.vari = block_length
            self.edge = edge
            self.volume = cap_v(self.vari * 1.1, self.vari * 1.1) + little_thing(1.8)
        elif block_type == 'CB17':
            self.vari = block_length
            self.volume = cap_v(self.vari * 1.1, self.vari * 0.5)
        elif block_type == 'CB19':
            self.vari = block_length
            self.edge = edge
            self.volume = cap_v(self.vari * 1.1, self.vari * 1.4) + little_thing(1.8)
        elif block_type == 'CB20':
            self.vari = block_length
            self.volume = cap_v(self.vari * 1.1, self.vari * 1.4)
        elif block_type == 'CB21':
            self.volume = cap_v(11, 15.96) + little_thing(2)
        self.weight = self.volume * self.density


