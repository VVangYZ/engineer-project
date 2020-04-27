import openseespy.opensees as ops
from openseespy.postprocessing.Get_Rendering import plot_model
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd


# 一些参数
elem_num = 100


# 计算单桩最不利弯矩
def get_pile_m(pile_z0=0, pile_z1=-30, pile_d=2, m0=7.5, pile_f=0, pile_m=0):
    pile_h = pile_z0 - pile_z1
    pile_a = np.pi * (pile_d / 2) ** 2
    pile_i = np.pi * pile_d ** 4 / 64
    pile_b1 = 0.9 * (1.5 + 0.5 / pile_d) * 1 * pile_d

    # 建立模型
    ops.wipe()
    ops.model('basic', '-ndm', 2, '-ndf', 3)

    # 建立节点
    node_z = np.linspace(pile_z0, pile_z1, elem_num + 1)
    for i, j in enumerate(node_z):
        ops.node(i + 1, 0, j)
        ops.node(i + 201, 0, j)

    # 约束
    for i in range(len(node_z)):
        ops.fix(i + 1, 0, 1, 0)
        ops.fix(i + 201, 1, 1, 1)

    # 建立材料
    ops.uniaxialMaterial('Elastic', 1, 3e4)
    for i in range(len(node_z)):
        pile_depth = i * (pile_h / elem_num)
        pile_depth_nominal = 10 if pile_depth <= 10 else pile_depth
        soil_k = m0 * pile_depth_nominal * pile_b1 * (pile_h / elem_num)
        if i == 0:
            ops.uniaxialMaterial('Elastic', 100 + i, soil_k / 2)
            continue
        ops.uniaxialMaterial('Elastic', 100 + i, soil_k)

    # 装配
    ops.geomTransf('Linear', 1)

    # 建立单元
    for i in range(elem_num):
        ops.element('elasticBeamColumn', i + 1, i + 1, i + 2, pile_a, 3e10, pile_i, 1)

    # 建立弹簧
    for i in range(len(node_z)):
        ops.element('zeroLength', i + 201, i + 1, i + 201, '-mat', 100 + i, '-dir', 1)

    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)
    ops.load(1, pile_f, 0, pile_m)

    ops.system('BandGeneral')
    ops.numberer('Plain')
    ops.constraints('Plain')

    ops.integrator('LoadControl', 0.01)
    ops.test('EnergyIncr', 1e-6, 200)
    ops.algorithm('Newton')
    ops.analysis('Static')

    ops.analyze(100)

    # 绘制位移图
    node_disp = []
    for i in range(101):
        node_disp.append(ops.nodeDisp(i + 1))

    node_disp = np.array(node_disp) * 1000

    plt.figure()
    plt.subplot(121)
    for i, j in enumerate(node_z):
        if abs(node_disp[:, 0][i]) > max(abs(node_disp[:, 0])) / 50:
            if i == 0:
                plt.plot([0, node_disp[:, 0][i]], [j, j], linewidth=1.5, color='grey')
            else:
                plt.plot([0, node_disp[:, 0][i]], [j, j], linewidth=0.7, color='grey')
        if abs(node_disp[:, 0][i]) == max(abs(node_disp[:, 0])):
            plt.annotate(f'{node_disp[:, 0][i]:.1f} mm', xy=(node_disp[:, 0][i], j),
                         xytext=(0.3, 0.5), textcoords='axes fraction',
                         bbox=dict(boxstyle="round", fc="0.8"),
                         arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=-0.3"))
    plt.plot([0, 0], [node_z[0], node_z[-1]], linewidth=1.5, color='dimgray')
    plt.plot(node_disp[:, 0], node_z, linewidth=1.5, color='midnightblue')

    plt.xlabel('Displacement(mm)')
    plt.ylabel('Pile Depth(m)')

    # 绘制弯矩图
    elem_m = []
    for i in range(100):
        elem_m.append(ops.eleForce(i + 1))
    elem_m = np.array(elem_m) / 1000

    plt.subplot(122)
    for i, j in enumerate(node_z[:-1]):
        if abs(elem_m[:, 2][i]) > max(abs(elem_m[:, 2])) / 50:
            if i == 0:
                plt.plot([0, elem_m[:, 2][i]], [j, j], linewidth=1.5, color='grey')
            else:
                plt.plot([0, elem_m[:, 2][i]], [j, j], linewidth=0.7, color='grey')
        if abs(elem_m[:, 2][i]) == max(abs(elem_m[:, 2])):
            plt.annotate(f'{elem_m[:, 2][i]:.1f} kN.m', xy=(elem_m[:, 2][i], j),
                         xytext=(0.5, 0.5), textcoords='axes fraction',
                         bbox=dict(boxstyle="round", fc="0.8"),
                         arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=0.3"))

    plt.plot([0, 0], [node_z[0], node_z[-1]], linewidth=1.5, color='dimgray')
    plt.plot(elem_m[:, 2], node_z[:-1], linewidth=1.5, color='brown')
    plt.xlabel('Moment(kN.m)')
    # plt.ylabel('Pile Depth(m)')
    plt.show()

    return abs(max(elem_m[:, 2]))


def get_multi_pile_m(
        pile_layout,
        cap_edge=0,
        cap_thickness=2,
        pile_z0=-2.5,
        pile_z1=-30,
        pile_d=2,
        m0=7500000,
        top_f=0.0,
        top_h=0.0,
        top_m=0.0
):
    if cap_edge == 0:
        if pile_d <= 1:
            cap_edge = max(0.25, 0.5 * pile_d)
        else:
            cap_edge = max(0.5, 0.3 * pile_d)
    cap_w = max(pile_layout[0]) - min(pile_layout[0]) + pile_d + cap_edge * 2
    cap_l = max(pile_layout[1]) - min(pile_layout[1]) + pile_d + cap_edge * 2
    top_f += cap_w * cap_l * cap_thickness * 26e3       # 承台自重
    top_f += (cap_w * cap_l) * (-pile_z0 - cap_thickness) * 15e3    # 盖梁重量
    pile_rows = len(pile_layout[1])     # 桩排数
    top_f /= pile_rows      # 桩顶力分配
    top_h /= pile_rows      # 桩顶水平力分配
    top_m /= pile_rows      # 桩顶弯矩分配
    cap_i = cap_l * cap_thickness ** 3 / 12 / pile_rows     # 承台横向刚度

    pile_h = pile_z0 - pile_z1
    pile_a = np.pi * (pile_d / 2) ** 2
    pile_i = np.pi * pile_d ** 4 / 64
    pile_b1 = 0.9 * (1.5 + 0.5 / pile_d) * 1 * pile_d

    # 建立模型
    ops.wipe()
    ops.model('basic', '-ndm', 2, '-ndf', 3)

    # 建立节点
    cap_bot = pile_z0
    # ops.node(1, 0, cap_top)     # 承台竖向节点
    if 0 not in pile_layout[0]:
        ops.node(2, 0, cap_bot)

    # 建立桩基节点
    node_z = np.linspace(pile_z0, pile_z1, elem_num + 1)
    for i, j in enumerate(pile_layout[0]):
        node_start = 100 + i * 300
        for m, n in enumerate(node_z):
            ops.node(node_start + m + 1, j, n)
            ops.node(node_start + m + 151, j, n)

    nodes = {}
    for i in ops.getNodeTags():
        nodes[i] = ops.nodeCoord(i)

    # 建立约束
    for i, j in enumerate(pile_layout[0]):
        node_start = 100 + i * 300
        for m, n in enumerate(node_z):
            ops.fix(node_start + m + 151, 1, 1, 1)
            if n == node_z[-1]:
                ops.fix(node_start + m + 1, 1, 1, 1)

    # 建立材料
    for i in range(len(node_z)):
        pile_depth = i * (pile_h / elem_num)
        pile_depth_nominal = 10 if pile_depth <= 10 else pile_depth
        soil_k = m0 * pile_depth_nominal * pile_b1 * (pile_h / elem_num)
        if i == 0:
            ops.uniaxialMaterial('Elastic', 1 + i, soil_k / 2)
            continue
        ops.uniaxialMaterial('Elastic', 1 + i, soil_k)

    # 装配
    ops.geomTransf('Linear', 1)

    # 建立单元
    if len(pile_layout[0]) > 1:     # 承台横向单元
        cap_nodes = []
        for i in nodes:
            if nodes[i][1] == cap_bot:
                if len(cap_nodes) == 0:
                    cap_nodes.append(i)
                elif nodes[i][0] != nodes[cap_nodes[-1]][0]:
                    cap_nodes.append(i)
        cap_nodes = sorted(cap_nodes, key=lambda x: nodes[x][0])
        for i, j in enumerate(cap_nodes[:-1]):
            ops.element('elasticBeamColumn', 10 + i, j, cap_nodes[i+1], cap_l * cap_thickness, 3e10, cap_i, 1)

    pile_elem = []
    for i, j in enumerate(pile_layout[0]):      # 桩基单元
        node_start = 100 + i * 300
        pile_elem_i = []
        for m, n in enumerate(node_z):
            if n != pile_z1:
                ops.element('elasticBeamColumn', node_start + m + 1, node_start + m + 1,
                            node_start + m + 2, pile_a, 3e10, pile_i, 1)
                pile_elem_i.append(node_start + m + 1)
            ops.element('zeroLength', node_start + m + 151, node_start + m + 151,
                        node_start + m + 1, '-mat', 1 + m, '-dir', 1)
        pile_elem.append(pile_elem_i)

    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)
    for i in nodes:
        if nodes[i] == [0, pile_z0]:
            ops.load(i, -top_h, -top_f, top_m)    # 加载

    ops.system('BandGeneral')
    ops.numberer('Plain')
    ops.constraints('Plain')

    ops.integrator('LoadControl', 0.01)
    ops.test('EnergyIncr', 1e-6, 200)
    ops.algorithm('Newton')
    ops.analysis('Static')

    ops.analyze(100)

    node_disp = {}
    for i in ops.getNodeTags():
        node_disp[i] = [j * 1000 for j in ops.nodeDisp(i)]

    elem_m = {}
    for i in pile_elem:
        for j in i:
            elem_m[j] = [k / 1000 for k in ops.eleForce(j)]

    plt.figure()
    for i, j in enumerate(pile_elem):
        plt.subplot(f'1{len(pile_elem)}{i+1}')
        if i == 0:
            plt.ylabel('Pile Depth(m)')
        node_disp_x = []
        for m, n in enumerate(j):
            node_1 = ops.eleNodes(n)[0]
            if m == 0:
                plt.plot([0, node_disp[node_1][0]], [nodes[node_1][1], nodes[node_1][1]],
                         linewidth=1.5, color='grey')
            else:
                plt.plot([0, node_disp[node_1][0]], [nodes[node_1][1], nodes[node_1][1]],
                         linewidth=0.7, color='grey')
            node_disp_x.append(node_disp[node_1][0])
        for m, n in enumerate(j):
            node_1 = ops.eleNodes(n)[0]
            if abs(node_disp[node_1][0]) == max([abs(i) for i in node_disp_x]):
                side = 1 if node_disp[node_1][0] > 0 else -1
                plt.annotate(f'{node_disp[node_1][0]:.1f} mm', xy=(node_disp[node_1][0], nodes[node_1][1]),
                             xytext=(0.4 + 0.1 * side, 0.5), textcoords='axes fraction',
                             bbox=dict(boxstyle="round", fc="0.8"),
                             arrowprops=dict(arrowstyle='->', connectionstyle=f"arc3,rad={side * 0.3}"))
                break
        plt.plot([0, 0], [node_z[0], node_z[-1]], linewidth=1.5, color='dimgray')
        plt.plot(node_disp_x, node_z[:-1], linewidth=1.5, color='midnightblue')
        plt.xlabel(f'Displacement_{i+1} (mm)')
    plt.show()

    plt.figure()
    for i, j in enumerate(pile_elem):
        plt.subplot(f'1{len(pile_elem)}{i + 1}')
        if i == 0:
            plt.ylabel('Pile Depth(m)')
        elem_mi = []
        for m, n in enumerate(j):
            node_1 = ops.eleNodes(n)[0]
            if m == 0:
                plt.plot([0, elem_m[n][2]], [nodes[node_1][1], nodes[node_1][1]],
                         linewidth=1.5, color='grey')
            else:
                plt.plot([0, elem_m[n][2]], [nodes[node_1][1], nodes[node_1][1]],
                         linewidth=0.7, color='grey')
            elem_mi.append(elem_m[n][2])
        for m, n in enumerate(j):
            node_1 = ops.eleNodes(n)[0]
            if abs(elem_m[n][2]) == max([abs(i) for i in elem_mi]):
                side = 1 if elem_m[n][2] > 0 else -1
                plt.annotate(f'{elem_m[n][2]:.1f} kN.m', xy=(elem_m[n][2], nodes[node_1][1]),
                             xytext=(0.4 + 0.1 * side, 0.5), textcoords='axes fraction',
                             bbox=dict(boxstyle="round", fc="0.8"),
                             arrowprops=dict(arrowstyle='->', connectionstyle=f"arc3,rad={side * 0.3}"))
                break
        plt.plot([0, 0], [node_z[0], node_z[-1]], linewidth=1.5, color='dimgray')
        plt.plot(elem_mi, node_z[:-1], linewidth=1.5, color='brown')
        plt.xlabel(f'Moment_{i + 1} (kN.m)')
    plt.show()

    return pile_elem, elem_m


def soil_m_from_zk(zk_pd):
    """
    通过钻孔信息获取桩基计算 m
    :param zk_pd: 钻孔 pd
    :return: m（N/m4)
    """
    soil_top_1 = zk_pd[zk_pd['层底深度'] <= 6]
    soil_top_2 = zk_pd[zk_pd['层底深度'] > 6].iloc[0:1]
    soil_top_2['地层厚度'] = 6 - soil_top_1.iloc[-1]['层底深度']
    soil_top = pd.concat([soil_top_1, soil_top_2])
    soil_top['m'] = soil_top['岩土描述'].map(lambda x: 7.5e6 if '土' in x else 5.5e7)
    h1 = soil_top.iloc[0]['地层厚度']
    m1 = soil_top.iloc[0]['m']
    if soil_top.shape[0] > 1:
        m2 = soil_top.iloc[1]['m']
        if h1 <= 0.2 * 6:
            gamma = 5 * (h1 / 6) ** 2
        else:
            gamma = 1 - 1.25 * (1 - h1 / 6) ** 2
        m = gamma * m1 + (1 - gamma) * m2
    else:
        m = m1
    return m


def pile_fe_from_pd(f_dic):
    case_all = ['me']
    f_all = ['fx', 'mz']
    f_m_result = []
    for i in f_dic:
        i_result = []
        for j in f_all:
            j_result = [0, 0, 0]
            for k in case_all:
                h = abs(i[k][j]['fy'])
                f = abs(i[k][j]['fx'])
                m = abs(i[k][j]['mz'])
                if m > j_result[2]:
                    j_result = [h, f, m]
            i_result.append(j_result)
        f_m_result.append(i_result)

    return f_m_result


def pile_fu_from_pd(f_dic):
    """
    获取桩基自身承载力计算所需荷载工况
    :param f_dic: 承台顶面反力各工况列表
    :return: 加载
    """
    # 获取各位置最大力
    case_all = ['mu', 'me2']
    f_all = ['mz', 'my']
    f_m_result = []
    for i in f_dic:
        i_result = []
        for j in f_all:
            j_result = [0, 0, 0]
            for k in case_all:
                fi = 'fz' if j == 'my' else 'fy'
                h = abs(i[k][j][fi])
                f = abs(i[k][j]['fx'])
                m = abs(i[k][j][j])
                if m > j_result[2]:
                    j_result = [h, f, m]
            i_result.append(j_result)
        f_m_result.append(i_result)

    return f_m_result


if __name__ == '__main__':
    pile_elem = get_multi_pile_m([[-3, 0, 3], [0]], top_f=1e7, top_h=1e6, top_m=1e7)
    # pile_elem = get_multi_pile_m([[-2, 2], [0]], top_f=0, top_h=0, top_m=1e6)

    # m_max = get_pile_m(pile_z0=0, pile_z1=-30, pile_f=-1184000, pile_m=8608000, m0=7500000)
    # print(f'{m_max:.0f} kN.m')





