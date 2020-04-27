import pandas as pd
import numpy as np

soil_gamma = 18  # 上填土默认重度


def expand_min_size(sub_type):
    """
    获取对应下部结构类型的最小扩基尺寸列表
    :param sub_type: 下部结构类型
    :return: 最小扩基尺寸列表（m）
    """
    expand_size = {4: [4 + 4, 1.8 + 4], 1.8: [1.8 + 4, 1.8 + 4], 2: [2 + 4, 1.8 + 4]}
    if sub_type == 'FC1':
        min_size_1 = expand_size[4]
        min_size_2 = expand_size[1.8]
        min_size = [min_size_1, min_size_2]
    elif sub_type == 'FC2':
        min_size_1 = [6 + 1.8 + 4, 1.8 + 4]
        min_size_2 = expand_size[1.8]
        min_size = [min_size_1, min_size_2]
    elif sub_type == 'F2':
        min_size = [expand_size[1.8], expand_size[1.8]]
    elif sub_type == 'F3':
        min_size_1 = expand_size[1.8]
        min_size_2 = expand_size[2]
        min_size_3 = expand_size[1.8]
        min_size = [min_size_1, min_size_2, min_size_3]
    else:
        print('类型错误')
        raise Exception
    return min_size


def expand_fund_gravity(fund_size, rho=26):
    """
    通过扩基底面尺寸，获取扩基自重
    :param fund_size: 扩基底面尺寸 (m)
    :param rho: 扩基容重 (kN/m3)
    :return: 扩基自重 (kN)
    """
    fund_v = fund_size[0] * fund_size[1] * 1 + (fund_size[0] - 2) * (fund_size[1] - 2) * 1
    fund_g = fund_v * rho
    return fund_g


def get_fa(fund_size, fund_depth, zk_inf):
    b = min(fund_size)
    h = fund_depth
    if b < 2:
        b = 2
    elif b > 10:
        b = 10
    if h < 3:
        h = 3
    elif h / b > 4:
        h = 4 * b

    gamma1 = zk_inf[zk_inf['层底深度'] > fund_depth]['gamma'].iloc[0]
    up_gamma = zk_inf[zk_inf['层底深度'] <= fund_depth][['地层厚度', 'gamma']].to_numpy()
    i_depth = fund_depth - zk_inf[zk_inf['层底深度'] <= fund_depth]['地层厚度'].max()
    up_gamma = np.vstack((up_gamma, [i_depth, gamma1]))
    gamma2 = np.average(up_gamma[:, 1], weights=up_gamma[:, 0])
    i_type = zk_inf[zk_inf['层底深度'] > fund_depth]['岩土描述'].iloc[0]
    i_fa0 = zk_inf[zk_inf['层底深度'] > fund_depth]['fa0'].iloc[0]
    if '土' in i_type:
        k1, k2 = 0, 1.5
    elif '全风化' in i_type:
        k1, k2 = 4, 6
    elif '强风化' in i_type:
        k1, k2 = 3, 5
    else:
        k1, k2 = 0, 0
    fa = i_fa0 + k1 * gamma1 * (b - 2) + k2 * gamma2 * (h - 3)
    return i_type, round(fa, 1), i_fa0


def get_f_from_pd(pier_f_pd, sub_type):
    """
    通过结果 pd 获取格式化结果字典
    :param pier_f_pd: 结果 pd
    :param sub_type: 下部结构类型
    :return: 格式化结果字典
    """
    rename_dic = {
        '轴向 (kN)': 'fx',
        '剪力-y (kN)': 'fy',
        '剪力-z (kN)': 'fz',
        '扭矩 (kN*m)': 'ft',
        '弯矩-y (kN*m)': 'my',
        '弯矩-z (kN*m)': 'mz'
    }
    ref_dic = {
        '轴向': 'fx',
        '弯矩-y': 'my',
        '弯矩-z': 'mz'
    }
    pier_f_pd.rename(columns=rename_dic, inplace=True)
    pier_f_pd['荷载'] = pier_f_pd['荷载'].map(lambda x: x[:-4] if '全部' in x else x)
    pier_f_pd['位置'] = pier_f_pd['位置'].map(lambda x: x[0])
    pier_f_pd['成分'] = pier_f_pd['成分'].map(lambda x: ref_dic[x])
    pier_f_i = pier_f_pd[pier_f_pd['位置'] == 'I']

    elems = sorted(pier_f_i.index.unique())
    cases = pier_f_i['荷载'].unique()
    max_f = ['fx', 'my', 'mz']
    fund_top_f = []

    for i in elems:
        pier_f_i_i = pier_f_i.loc[i]
        fund_top_f_elem = {}
        for j in cases:
            f_case_case = {}
            for k in max_f:
                f_i = pier_f_i_i[(pier_f_i_i['荷载'] == j) &
                                 (pier_f_i_i['成分'] == k)].iloc[0, [3, 4, 5, 6, 7, 8]].to_dict()
                f_case_case[k] = f_i
            fund_top_f_elem[j] = f_case_case
        fund_top_f.append(fund_top_f_elem)

    if sub_type == 'FC2':
        fund_top_f_fc2 = [{}, fund_top_f[-1]]
        for i in cases:
            f_case = {}
            for j in max_f:
                f = {}
                f1 = fund_top_f[0][i][j]
                f2 = fund_top_f[1][i][j]
                for k in f1:
                    f[k] = f1[k] + f2[k]
                f_case[j] = f
            fund_top_f_fc2[0][i] = f_case
        return fund_top_f_fc2

    return fund_top_f


class ExpandFund:
    def __init__(self, fund_size, pier_f, fund_depth, rock_type, fa):
        """
        建立扩基计算对象
        :param fund_size: 扩基底面尺寸，横桥 x 顺桥 (m)
        :param pier_f: 基础顶面荷载字典 (kN/kN.m)
        :param fa: 根据基础尺寸修正后的地基承载力 (kPa)
        """
        self.fund_width = fund_size[0]
        self.fund_length = fund_size[1]
        self.fund_size = fund_size
        self.a = self.fund_width * self.fund_length
        self.wy = self.fund_width * self.fund_length ** 2 / 6
        self.wz = self.fund_length * self.fund_width ** 2 / 6
        self.w = [self.wz, self.wy]

        self.fund_gravity = expand_fund_gravity(fund_size)
        self.fund_depth = fund_depth
        self.pier_f = pier_f
        self.pier_f_me = pier_f['me']
        # self.fa = 1.25 * fa
        self.fa = fa
        self.p_max = {}
        self.rho = {}
        self.e0 = {}
        self.kc = {}
        self.rock_type = rock_type
        if '土' in rock_type:
            self.rho_k = 1
            self.mu = 0.25
        elif '全风化' in rock_type or '强风化' in rock_type:
            self.rho_k = 1.2
            self.mu = 0.45
        elif '中风化' in rock_type or '微风化' in rock_type or '未风化' in rock_type:
            self.rho_k = 1.5
            self.mu = 0.6
        else:
            print(rock_type)
            raise Exception
        # self.wy = self.fund_width * self.fund_length ** 2 / 12
        # self.wz = self.fund_length * self.fund_width ** 2 / 12

    def cal_ground(self):
        for i in self.pier_f_me:
            fi = -self.pier_f_me[i]['fx'] + self.fund_gravity + self.a * (self.fund_depth - 2) * soil_gamma
            myi = self.pier_f_me[i]['my']
            mzi = self.pier_f_me[i]['mz']

            # 抗滑移计算
            fh_min = min(abs(self.pier_f_me[i]['fy']), abs(self.pier_f_me[i]['fz']))
            fh_max = max(abs(self.pier_f_me[i]['fy']), abs(self.pier_f_me[i]['fz']))
            self.kc[i] = (self.mu * fi + fh_min) / fh_max

            # 基底应力计算
            p_maxi = fi / self.a + abs(myi) / self.wy + abs(mzi) / self.wz
            self.p_max[i] = round(p_maxi, 1)

            # 偏心距验算
            p_mini = fi / self.a - abs(myi) / self.wy - abs(mzi) / self.wz
            mi = (myi ** 2 + mzi ** 2) ** 0.5
            e0i = mi / fi
            rhoi = e0i / (1 - p_mini * self.a / fi)
            self.e0[i] = e0i
            self.rho[i] = rhoi * self.rho_k

        for i in self.p_max:
            if self.p_max[i] > self.fa:
                return ['f', i, False]
            elif self.rho[i] < self.e0[i]:
                return ['e', i, False]
            elif self.kc[i] < 1.2:
                return ['h', i, False]
        else:
            return [True]

    def print_result(self):
        for i in self.p_max:
            if self.p_max[i] > self.fa:
                print(f'工况{i}下，地基承载力不满足要求……')
                print(f'承载力: {self.fa:.1f} kPa\t基底应力: {self.p_max[i]:.1f} kPa')
            elif self.rho[i] < self.e0[i]:
                print(f'工况{i}下，偏心距不满足要求……')
                print(f'核心半径: {self.rho[i]:.2f}m\t偏心距: {self.e0[i]:.2f}m')
            elif self.kc[i] < 1.2:
                print(f'工况{i}下，抗滑移不满足要求……')
                print(f'抗滑动稳定系数: {self.kc[i]:.2f}\t限值: 1.2')
            else:
                print(f'工况{i}下，承载力验算通过！！！')
                print(f'承载力: {self.fa:.1f} kPa\t基底应力: {self.p_max[i]:.1f} kPa')
                print(f'工况{i}下，偏心距验算通过！！！')
                print(f'核心半径: {self.rho[i]:.2f}m\t偏心距: {self.e0[i]:.2f}m')
                print(f'工况{i}下，抗滑移验算通过！！！')
                print(f'抗滑动稳定系数: {self.kc[i]:.2f}\t限值: 1.2')

    def cal_fund(self, a1=(2, 2)):
        m_all = []
        for i in ['mu', 'me1', 'me2']:
            for j in self.pier_f[i]:
                fi = self.pier_f[i][j]['fx']
                m_case_i = []
                for a, b in enumerate(['mz', 'my']):
                    mi = self.pier_f[i][j][b]
                    pi_max = - fi / self.a + abs(mi) / self.w[a]
                    pi = - fi / self.a
                    bi = self.fund_size[a]
                    li = self.fund_size[-(a + 1)]
                    a1i = a1[a]
                    m1 = 1 / 12 * a1i ** 2 * ((2 * li + a1[a]) * (pi_max + pi) + (pi_max - pi) * li)
                    m_case_i.append(m1)
                m_all.append(m_case_i)
            return np.array(m_all)

    def cal_other(self, top=(1.8, 1.8)):
        beta = 0.9
        ft = 1.39 * 1000
        fi = - self.pier_f['mu']['fx']['fx']
        safe = []
        for i, j in enumerate(top):
            at = j
            ab = self.fund_size[i]
            am = 1 / 2 * (at + ab)
            al = (top[- i - 1] + 4 + self.fund_size[- i - 1]) / 2 * (self.fund_size[i] - top[i] - 4) / 2
            fl = al * fi / self.a
            fr = 0.7 * beta * ft * am * 1.92
            safe.append(fr/fl)
        return safe


def default_pile_layout(sub_type, fund_type='端承桩'):
    """
    获取对应下部结构类型的默认桩基配置
    :param sub_type:
    :return: 桩基配置列表 (m)
    """
    if sub_type == 'FC1':
        if fund_type == '摩擦桩':
            pile_layout = [
                [[-2.5, 2.5], [0]],
                [[0], [0]]
            ]
        else:
            pile_layout = [
                [[-2, 2], [0]],
                [[0], [0]]
            ]
    elif sub_type == 'FC2':
        pile_layout = [
            [[-3, 3], [0]],
            [[0], [0]]
        ]
    elif sub_type == 'F2':
        pile_layout = [
            [[0], [0]],
            [[0], [0]]
        ]
    elif sub_type == 'F3':
        pile_layout = [
            [[0], [0]],
            [[0], [0]],
            [[0], [0]]
        ]
    else:
        print('类型错误')
        raise Exception
    return pile_layout




