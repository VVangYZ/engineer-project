import xlwings as xw
import pandas as pd
import numpy as np
import concrete

# elem = pd.read_json('../IO/elem_test.json', orient='split')
# node = pd.read_json('../IO/node_test.json', orient='split')
#
#
# def get_x(i):
#     return node.loc[i]['x']
#
#
# elem['x'] = elem['n1'].map(get_x)


def get_all_results():
    return xw.Range('A1').options(pd.DataFrame, expand='table').value


def result_myz(elem, elem_all_results):
    all_case = elem_all_results['荷载'].unique()
    all_case_ok = [i[:-4] for i in all_case]
    pt = elem_all_results['位置'].unique()
    all_f = ['My', 'Fxy', 'Mz', 'Fxz']
    all_item = [[i + '-' + j for i in all_f] for j in all_case_ok]
    elem_results = pd.DataFrame(columns=np.array(all_item).flatten())

    for i, j in elem.iterrows():
        i_m_all = elem_all_results.loc[i]
        m_all = []
        for m in all_case:
            i_my = i_m_all[(i_m_all['荷载'] == m) & (i_m_all['成分'] == '弯矩-y')].to_numpy()[:, [-2, -6]]
            i_mz = i_m_all[(i_m_all['荷载'] == m) & (i_m_all['成分'] == '弯矩-z')].to_numpy()[:, [-1, -6]]
            i_myz = np.hstack((i_my, i_mz))
            i_myz = np.abs(i_myz)
            i_m = np.fmax(*i_myz).tolist()
            m_all += i_m
        elem_results.loc[i] = m_all

    return elem_results


def creat_rectangle(elem, sec_dic, sec_box, rebar=36, space=150, c=0.04, fcd=18.4):
    sec_dic = {v: k for k, v in sec_dic.items()}
    rectangles = {}
    for i, j in elem.iterrows():
        b, h = sec_box[sec_dic[j['s']]]
        a1 = c + rebar / 2000
        a2 = [a1 + space * i / 1000 for i in range(1, 4)]
        rebar_num_b = (b - 2 * a1) // (space / 1000) + 1
        rebar_num_h = (h - 2 * a1) // (space / 1000) + 1
        a_b = np.average([a1] + a2, weights=[rebar_num_b] + [2] * 3)
        a_h = np.average([a1] + a2, weights=[rebar_num_h] + [2] * 3)
        sec_y = concrete.RectangleCompress(
            b, h, rebar, rebar, rebar_num_b + 6, rebar_num_b + 6, fcd, 415, 400, a_b, a_b)
        sec_z = concrete.RectangleCompress(
            h, b, rebar, rebar, rebar_num_h + 6, rebar_num_h + 6, fcd, 415, 400, a_h, a_h)
        rectangles[i] = [sec_y, sec_z]
    return rectangles


def pier_capacity(elem, rectangles, elem_results, cases=('mu', 'me1', 'me2')):
    all_res = [[i + '-' + j for i in ['Msy', 'Mry', 'Msz', 'Mrz']] for j in cases]
    pier_res = pd.DataFrame(columns=np.array(all_res).flatten())
    for i, j in elem.iterrows():
        i_result = elem_results.loc[i]
        sec_y = rectangles[i][0]
        sec_z = rectangles[i][1]
        res = []
        for m in cases:
            i_fx1 = elem_results.loc[i][f'Fxy-{m}']
            i_my = elem_results.loc[i][f'My-{m}']
            i_fx2 = elem_results.loc[i][f'Fxz-{m}']
            i_mz = elem_results.loc[i][f'Mz-{m}']
            my = sec_y.capacity(i_fx1, i_my)
            mz = sec_z.capacity(i_fx2, i_mz)
            res += my + mz
        pier_res.loc[i] = res
    return pier_res


def pier_crack(elem, rectangles, elem_results, case='ms', rebar=36):
    pier_crack_width = pd.DataFrame(columns=['crack_width_y', 'crack_width_z'])
    for i, j in elem.iterrows():
        sec_y = rectangles[i][0]
        sec_z = rectangles[i][1]
        i_fx1 = elem_results.loc[i][f'Fxy-{case}']
        i_my = elem_results.loc[i][f'My-{case}']
        i_fx2 = elem_results.loc[i][f'Fxz-{case}']
        i_mz = elem_results.loc[i][f'Mz-{case}']
        wy = sec_y.crack_width(i_fx1, i_my, rebar=rebar)
        wz = sec_z.crack_width(i_fx2, i_mz, rebar=rebar)
        pier_crack_width.loc[i] = [wy, wz]
    return pier_crack_width


def pier_checkout(elem, pier_res, pier_crack_width, elem_results, cases=(('mu', 'me1', 'me2'), 'ms')):
    capacity_checkout = pd.DataFrame(columns=['elem', 'Fx', 'M', 'Ms', 'Mr', 'safety'])
    for i in cases[0]:
        for j in ['y', 'z']:
            pier_res['Safety-' + i + '-' + j] = pier_res['Mr' + j + '-' + i] / pier_res['Ms' + j + '-' + i]
            safety_min = pier_res['Safety-' + i + '-' + j].min()
            elem_id = pier_res[pier_res['Safety-' + i + '-' + j] == safety_min].index[0]
            i_fx = elem_results.loc[elem_id]['Fx' + j + '-' + i]
            i_m = elem_results.loc[elem_id]['M' + j + '-' + i]
            i_ms = pier_res.loc[elem_id]['Ms' + j + '-' + i]
            i_mr = pier_res.loc[elem_id]['Mr' + j + '-' + i]
            i_inf = [elem_id, i_fx, i_m, i_ms, i_mr, safety_min]
            capacity_checkout.loc[i + '-' + j] = i_inf

    crack_checkout = pd.DataFrame(columns=['elem', 'Fx', 'M', 'crack'])
    for j in ['y', 'z']:
        i = 'ms'
        crack_max = pier_crack_width['crack_width_' + j].max()
        elem_id = pier_crack_width[pier_crack_width['crack_width_' + j] == crack_max].index[0]
        i_fx = elem_results.loc[elem_id]['Fx' + j + '-' + i]
        i_m = elem_results.loc[elem_id]['M' + j + '-' + i]
        i_inf = [elem_id, i_fx, i_m, crack_max]
        crack_checkout.loc[j] = i_inf

    return capacity_checkout, crack_checkout


def print_check(cap_check, crack_check, safe=1, crack_width=0.2):
    most_unsafe = cap_check['safety'].min()
    bad_case = cap_check[cap_check['safety'] == most_unsafe].index[0]
    biggest_crack = crack_check['crack'].max()
    crack_case = crack_check[crack_check['crack'] == biggest_crack].index[0]
    print('=' * 28)
    if most_unsafe < safe:
        print('承载能力不满足要求')
    else:
        print('承载能力牛逼！！！！!')
    cap_check_str = '单元：{:>10.0f}\n轴力：{:>10.1f} kN\n弯矩：{:>10.1f} kN.m\n安全：{:>10.2f}'
    print(cap_check_str.format(*cap_check.loc[bad_case][['elem', 'Fx', 'M', 'safety']]))
    print(f'工况：{bad_case:>10}')

    print('-' * 28)

    if biggest_crack > crack_width:
        print('裂缝宽度满足要求')
    else:
        print('裂缝宽度垃圾！！！！！')
    crack_check_str = '单元：{:>10.0f}\n轴力：{:>10.1f} kN\n弯矩：{:>10.1f} kN.m\n宽度：{:>10.3f} mm'
    print(crack_check_str.format(*crack_check.loc[crack_case][['elem', 'Fx', 'M', 'crack']]))
    print(f'方向：{crack_case:>10}')
    print('=' * 28)


# elem_all_results = xw.Range('A1').options(pd.DataFrame, expand='table').value

# all_case = elem_all_results['荷载'].unique()
# all_case_ok = [i[:-4] for i in all_case]
# pt = elem_all_results['位置'].unique()
# all_f = ['My', 'Fx1', 'Mz', 'Fx2']

# all_item = [[i + '-' + j for i in all_f] for j in all_case_ok]

# elem_results = pd.DataFrame(columns=np.array(all_item).flatten())

# for i, j in elem.iterrows():
#     i_m_all = elem_all_results.loc[i]
#     m_all = []
#     for m in all_case:
#         i_my = i_m_all[(i_m_all['荷载'] == m) & (i_m_all['成分'] == '弯矩-y')].to_numpy()[:, [-2, -6]]
#         i_mz = i_m_all[(i_m_all['荷载'] == m) & (i_m_all['成分'] == '弯矩-z')].to_numpy()[:, [-1, -6]]
#         i_myz = np.hstack((i_my, i_mz))
#         i_myz = np.abs(i_myz)
#         i_m = np.fmax(*i_myz).tolist()
#         m_all += i_m
#     elem_results.loc[i] = m_all

# all_res = [[i + '-' + j for i in ['Msy', 'Mry', 'Msz', 'Mrz']] for j in all_case_ok]
# pier_res = pd.DataFrame(columns=np.array(all_res).flatten())

# for i, j in elem[(elem['what'] == 'pier') & (elem['x'] == 0)].iterrows():
#     res = []
#     for m in all_case_ok:
#         i_fx1 = elem_results.loc[i][f'Fx1-{m}']
#         i_my = elem_results.loc[i][f'My-{m}']
#         i_fx2 = elem_results.loc[i][f'Fx2-{m}']
#         i_mz = elem_results.loc[i][f'Mz-{m}']
#         my = concrete.RectangleCompress(
#             1.8, 1.8, concrete.get_as(36, 10), concrete.get_as(36, 10), 18.4, 415, 400, 0.08, 0.08, i_fx1, i_my)
#         mz = concrete.RectangleCompress(
#             1.8, 1.8, concrete.get_as(36, 10), concrete.get_as(36, 10), 18.4, 415, 400, 0.08, 0.08, i_fx2, i_mz)
#         res += [my.m_load, my.m_resistance, mz.m_load, mz.m_resistance]
#     pier_res.loc[i] = res

# pier_crack = pd.DataFrame(columns=['crack-y', 'crack-z'])
# for i, j in elem[(elem['what'] == 'pier') & (elem['x'] == 0)].iterrows():
#     i_fx1 = elem_results.loc[i]['Fx1-ms']
#     i_my = elem_results.loc[i]['My-ms']
#     i_fx2 = elem_results.loc[i]['Fx2-ms']
#     i_mz = elem_results.loc[i]['Mz-ms']
#     my = concrete.RectangleCompress(
#         1.8, 1.8, concrete.get_as(36, 10), concrete.get_as(36, 10), 18.4, 415, 400, 0.08, 0.08, i_fx1, i_my)
#     mz = concrete.RectangleCompress(
#         1.8, 1.8, concrete.get_as(36, 10), concrete.get_as(36, 10), 18.4, 415, 400, 0.08, 0.08, i_fx2, i_mz)
#     i_crack = [my.crack_width(i_fx1, i_my), mz.crack_width(i_fx2, i_mz)]
#     pier_crack.loc[i] = i_crack
#
# for i in all_case_ok:
#     msy_safe_y = pier_res[f'Mry-{i}'] / pier_res[f'Msy-{i}']
#     msy_safe_z = pier_res[f'Mrz-{i}'] / pier_res[f'Msz-{i}']
#     print([min(msy_safe_y), min(msy_safe_z)])



