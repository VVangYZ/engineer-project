import numpy as np
import pandas as pd
import xlwings as xw
import matplotlib.pyplot as plt


def fc1_tendon_id(cap_l):
    if cap_l <= 30:
        tendon_space = 0.4
        tendon_num = [4, 5]
        tendon_z = [
            [-0.3, -0.25, -0.25, -1.5, -1.5, -0.85],
            [-0.3 - 0.5, -0.45, -0.45, -1.5, -1.5, -0.85 - 0.5]
        ]
        l_change = cap_l - 8.45 - 4 - 4.4 - 0.8 * 2 - 6.7
        tendon_y = [
            [0, 8.45, 4, 4.4 + 0.8, l_change, 0.8 + 6.7],
            [0, 8.45, 4, 4.4, l_change + 0.8 * 2, 6.7]
        ]
    elif cap_l <= 35:
        tendon_space = 0.4
        tendon_num = [3, 4, 5]
        tendon_z = [
            [-0.2, -0.25, -0.25, -1.3, -1.3, -0.7],
            [-0.2 - 0.35, -0.45, -0.45, -1.5, -1.5, -0.7 - 0.4],
            [-0.2 - 0.35 - 0.35, -0.65, -0.65, -1.5, -1.5, -0.7 - 0.4 - 0.4]
        ]
        l_change = cap_l - 8.45 - 4 - 5.2 - 1 * 2 - 7.5
        tendon_y = [
            [0, 8.45, 4, 5.2 + 1, l_change, 1 + 7.5],
            [0, 8.45, 4, 5.2 + 1, l_change, 1 + 7.5],
            [0, 8.45, 4, 5.2, l_change + 1 * 2, 7.5]
        ]
    else:
        tendon_space = 0.4
        tendon_num = [5, 4, 5]
        tendon_z = [
            [-0.2, -0.25, -0.25, -1.3, -1.3, -0.7],
            [-0.2 - 0.35, -0.45, -0.45, -1.5, -1.5, -0.7 - 0.4],
            [-0.2 - 0.35 - 0.35, -0.65, -0.65, -1.5, -1.5, -0.7 - 0.4 - 0.4]
        ]
        l_change = cap_l - 8.45 - 4 - 5.7 - 1 * 2 - 8
        tendon_y = [
            [0, 8.45, 4, 5.7 + 1, l_change, 1 + 8],
            [0, 8.45, 4, 5.7 + 1, l_change, 1 + 8],
            [0, 8.45, 4, 5.7, l_change + 1 * 2, 8]
        ]

    tendon_x = []
    for i, j in enumerate(tendon_y):
        j[0] = np.interp(tendon_z[i][0], [-1.1, 0], [0, 0.19])
        j[1] -= j[0]
        tendon_ni = tendon_num[i]
        tendon_xi = np.linspace(- (tendon_ni - 1) / 2 * tendon_space,
                                (tendon_ni - 1) / 2 * tendon_space, tendon_ni)
        tendon_x.append(tendon_xi)

    tendon_y = [np.cumsum(i) for i in tendon_y]

    tendon_id = []
    for i, j in enumerate(tendon_x):
        for k in j:
            tendon_xk = np.ones(len(tendon_y[i])) * k
            id_i = np.array([tendon_xk, tendon_y[i], tendon_z[i]]).T
            tendon_id.append(id_i)
    return np.array(tendon_id)


def fc2_tendon_id(cap_l):
    if cap_l <= 33:
        tendon_space = 0.4
        tendon_num = [5, 4]
        tendon_z = [
            [-0.3, -0.2, -0.2, -1, -1, -0.85],
            [-0.3 - 0.5, -0.2, -0.2, -1.2, -1.2, -0.85 - 0.5]
        ]
        l_change = cap_l - 6.35 - 1.1 - 6 - 1.1 - 5.5 - 8
        tendon_y = [
            [0, 6.35, 1.1 + 6 + 1.1, 5.5, l_change, 8],
            [0, 6.35 + 1.1, 6, 1.1 + 5.5, l_change, 8]
        ]
    elif cap_l <= 36:
        tendon_space = 0.4
        tendon_num = [5, 4, 3]
        tendon_z = [
            [-0.2, -0.2, -0.2, -0.2, -0.9, -0.9, -0.7],
            [-0.2 - 0.35, -0.2 - 0.35, -0.2, -0.2, -1.1, -1.1, -0.7 - 0.4],
            [-0.2 - 0.35 - 0.35, -0.2 - 0.35 - 0.35, -0.4, -0.4, -1.3, -1.3, -0.7 - 0.4 - 0.4]
        ]
        l_change = cap_l - 3.5 - 5.85 - 1.1 - 4.1 - 1.1 - 5.4 - 9
        tendon_y = [
            [0, 3.5, 5.85, 1.1 + 4.1 + 1.1, 5.4, l_change, 9],
            [0, 3.5, 5.85 + 1.1, 4.1, 1.1 + 5.4, l_change, 9],
            [0, 3.5, 5.85 + 1.1, 4.1, 1.1 + 5.4, l_change, 9]
        ]
    else:
        tendon_space = 0.4
        tendon_num = [5, 4, 5]
        tendon_z = [
            [-0.2, -0.2, -0.2, -0.2, -1.1, -1.1, -0.7],
            [-0.2 - 0.35, -0.2 - 0.35, -0.2, -0.2, -1.3, -1.3, -0.7 - 0.4],
            [-0.2 - 0.35 - 0.35, -0.2 - 0.35 - 0.35, -0.4, -0.4, -1.3, -1.3, -0.7 - 0.4 - 0.4]
        ]
        l_change = cap_l - 3.5 - 5.85 - 1.1 - 4.1 - 1.1 - 4.8 - 1.1 - 1.1 - 8.4
        tendon_y = [
            [0, 3.5, 5.85, 1.1 + 4.1 + 1.1, 4.8 + 1.1, l_change, 1.1 + 8.4],
            [0, 3.5, 5.85 + 1.1, 4.1, 1.1 + 4.8 + 1.1, l_change, 1.1 + 8.4],
            [0, 3.5, 5.85 + 1.1, 4.1, 1.1 + 4.8, 1.1 + l_change + 1.1, 8.4]
        ]
    tendon_x = []
    for i, j in enumerate(tendon_y):
        j[0] = np.interp(tendon_z[i][0], [-1.1, 0], [0, 0.19])
        j[1] -= j[0]
        tendon_ni = tendon_num[i]
        tendon_xi = np.linspace(- (tendon_ni - 1) / 2 * tendon_space,
                                (tendon_ni - 1) / 2 * tendon_space, tendon_ni)
        tendon_x.append(tendon_xi)

    tendon_y = [np.cumsum(i) for i in tendon_y]

    tendon_id = []
    for i, j in enumerate(tendon_x):
        for k in j:
            tendon_xk = np.ones(len(tendon_y[i])) * k
            id_i = np.array([tendon_xk, tendon_y[i], tendon_z[i]]).T
            tendon_id.append(id_i)
    return np.array(tendon_id)


def f2_tendon_id(cap_l, edge=0.5):
    if edge < 3:
        if cap_l <= 17:
            tendon_space = 0.4
            tendon_num = [4, 5]
            tendon_z = [
                [-0.6, -1.4, -1.4, -0.6],
                [-0.6 - 0.4, -1.4, -1.4, -0.6 - 0.4]
            ]
            l_change = cap_l - 3.9 * 2 - 1.5 * 2
            tendon_y = [
                [0, 3.9 + 1.5, l_change, 1.5 + 3.9],
                [0, 3.9, 1.5 + l_change + 1.5, 3.9]
            ]
        elif cap_l <= 22:
            tendon_space = 0.4
            tendon_num = [5, 4, 5]
            tendon_z = [
                [-0.7, -1.8, -1.8, -0.7],
                [-0.7 - 0.4, -2, -2, -0.7 - 0.4],
                [-0.7 - 0.4 - 0.4, -2, -2, -0.7 - 0.4 - 0.4]
            ]

            l_change = cap_l - edge - 4.8 - 1.5 - 1.5 - 5.3
            tendon_y = [
                [0, edge + 4.8 + 1.5, l_change, 1.5 + 5.3],
                [0, edge + 4.8 + 1.5, l_change, 1.5 + 5.3],
                [0, edge + 4.8, 1.5 + l_change + 1.5, 5.3]
            ]
        elif cap_l <= 25:
            tendon_space = 0.4
            tendon_num = [5, 4, 5]
            tendon_z = [
                [-0.7, -1.8, -1.8, -0.7],
                [-0.7 - 0.4, -2, -2, -0.7 - 0.4],
                [-0.7 - 0.4 - 0.4, -2, -2, -0.7 - 0.4 - 0.4]
            ]

            l_change = cap_l - 6.8 * 2 - 1.5 * 2
            tendon_y = [
                [0, 6.8 + 1.5, l_change, 1.5 + 6.8],
                [0, 6.8 + 1.5, l_change, 1.5 + 6.8],
                [0, 6.8, 1.5 + l_change + 1.5, 6.8]
            ]
        else:
            tendon_space = 0.4
            tendon_num = [5, 4, 5]
            tendon_z = [
                [-0.85, -2.1, -2.1, -0.85],
                [-0.85 - 0.4, -2.3, -2.3, -0.85 - 0.4],
                [-0.85 - 0.4 - 0.4, -2.3, -2.3, -0.85 - 0.4 - 0.4]
            ]

            l_change = cap_l - 8.3 * 2 - 1.5 * 2
            tendon_y = [
                [0, 8.3 + 1.5, l_change, 1.5 + 8.3],
                [0, 8.3 + 1.5, l_change, 1.5 + 8.3],
                [0, 8.3, 1.5 + l_change + 1.5, 8.3]
            ]
    else:
        if cap_l <= 24:
            tendon_space = 0.4
            tendon_num = [4, 5]
            tendon_z = [
                [-0.85, -0.5, -0.5, -1.6, -1.6, -0.85],
                [-0.85 - 0.5, -0.7, -0.7, -1.8, -1.8, -0.85 - 0.5]
            ]

            l_change = cap_l - edge - 2 - 4.9 - 4.3
            tendon_y = [
                [0, edge, 2, 4.9, l_change, 4.3],
                [0, edge, 2, 4.9, l_change, 4.3]
            ]
        elif cap_l <= 30:
            tendon_space = 0.4
            tendon_num = [4, 5]
            tendon_z = [
                [-0.85, -0.5, -0.5, -2, -2, -0.85],
                [-0.85 - 0.5, -0.7, -0.7, -2, -2, -0.85 - 0.5]
            ]

            l_change = cap_l - edge - 2 - 4.9 - 0.8 - 1.5 - 4.3
            tendon_y = [
                [0, edge, 2, 4.9 + 0.8, l_change, 1.5 + 4.3],
                [0, edge, 2, 4.9, 0.8 + l_change + 1.5, 4.3]
            ]
        else:
            tendon_space = 0.4
            tendon_num = [5, 4, 5]
            tendon_z = [
                [-0.7, -0.5, -0.5, -1.8, -1.8, -0.7],
                [-0.7 - 0.4, -0.7, -0.7, -2, -2, -0.7 - 0.4],
                [-0.7 - 0.4 - 0.4, -0.9, -0.9, -2, -2, -0.7 - 0.4 - 0.4]
            ]

            l_change = cap_l - edge - 2 - 5.9 - 1 - 1.5 - 7.3
            tendon_y = [
                [0, edge, 2, 5.9 + 1, l_change, 1.5 + 7.3],
                [0, edge, 2, 5.9 + 1, l_change, 1.5 + 7.3],
                [0, edge, 2, 5.9, 1 + l_change + 1.5, 7.3]
            ]

    tendon_x = []
    for i, j in enumerate(tendon_y):
        # j[0] = np.interp(tendon_z[i][0], [-1.1, 0], [0, 0.19])
        # j[1] -= j[0]
        tendon_ni = tendon_num[i]
        tendon_xi = np.linspace(- (tendon_ni - 1) / 2 * tendon_space,
                                (tendon_ni - 1) / 2 * tendon_space, tendon_ni)
        tendon_x.append(tendon_xi)

    tendon_y = [np.cumsum(i) for i in tendon_y]

    tendon_id = []
    for i, j in enumerate(tendon_x):
        for k in j:
            tendon_xk = np.ones(len(tendon_y[i])) * k
            id_i = np.array([tendon_xk, tendon_y[i], tendon_z[i]]).T
            tendon_id.append(id_i)
    return np.array(tendon_id)


def f3_tendon_id(s1=16, s2=16):
    cap_l = s1 + s2 + 2.8
    d1 = 0.5 if s1 < 17 else 0.2
    d2 = 0.5 if s2 < 17 else 0.2
    if cap_l <= 37:
        tendon_space = 0.4
        tendon_num = [3, 5]
        tendon_z = [
            [-0.85, -2.2 + d1 + 0.2, -2.2 + d1 + 0.2, -0.3, -0.3, -2.2 + d2 + 0.2, -2.2 + d2 + 0.2, -0.85],
            [-0.85 - 0.5, -2.2 + d1, -2.2 + d1, -0.3 - 0.2, -0.3 - 0.2, -2.2 + d2, -2.2 + d2, -0.85 - 0.5]
        ]

        l1_change = s1 - 4.4 - 4 - 2
        l2_change = s2 - 4.4 - 4 - 2
        tendon_y = [
            [0, 5.8, l1_change, 4, 4, 4, l2_change, 5.8],
            [0, 5.8, l1_change, 4, 4, 4, l2_change, 5.8]
        ]
    elif cap_l <= 50:
        tendon_space = 0.4
        tendon_num = [5, 5]
        tendon_z = [
            [-0.85, -2.2 + d1 + 0.2, -2.2 + d1 + 0.2, -0.3, -0.3, -2.2 + d2 + 0.2, -2.2 + d2 + 0.2, -0.85],
            [-0.85 - 0.5, -2.2 + d1, -2.2 + d1, -0.3 - 0.2, -0.3 - 0.2, -2.2 + d2, -2.2 + d2, -0.85 - 0.5]
        ]

        l1_change = s1 - 4.9 - 5 - 2
        l2_change = s2 - 4.9 - 5 - 2
        tendon_y = [
            [0, 6.3, l1_change, 5, 4, 5, l2_change, 6.3],
            [0, 6.3, l1_change, 5, 4, 5, l2_change, 6.3]
        ]
    else:
        tendon_space = 0.4
        tendon_num = [5, 4, 5]
        tendon_z = [
            [-0.7, -1.6, -1.6, -1, -1, -1.8, -1.8, -0.7],
            [-0.7 - 0.4, -1.8, -1.8, -1 - 0.2, -1 - 0.2, -2, -2, -0.7 - 0.4],
            [-0.7 - 0.4 - 0.4, -2, -2, -1 - 0.2 - 0.2, -1 - 0.2 - 0.2, -2, -2, -0.7 - 0.4 - 0.4]
        ]

        l1_change = s1 - 5.6 - 5.5 - 2
        l2_change = s2 - 5.6 - 0.8 - 0.8 - 5.5 - 2
        tendon_y = [
            [0, 7, l1_change, 5.5, 4, 5.5 + 0.8, l2_change, 0.8 + 7],
            [0, 7, l1_change, 5.5, 4, 5.5 + 0.8, l2_change, 0.8 + 7],
            [0, 7, l1_change, 5.5, 4, 5.5, 0.8 + l2_change + 0.8, 7]
        ]
    tendon_x = []
    for i, j in enumerate(tendon_y):
        # j[0] = np.interp(tendon_z[i][0], [-1.1, 0], [0, 0.19])
        # j[1] -= j[0]
        tendon_ni = tendon_num[i]
        tendon_xi = np.linspace(- (tendon_ni - 1) / 2 * tendon_space,
                                (tendon_ni - 1) / 2 * tendon_space, tendon_ni)
        tendon_x.append(tendon_xi)

    tendon_y = [np.cumsum(i) for i in tendon_y]

    tendon_id = []
    for i, j in enumerate(tendon_x):
        for k in j:
            tendon_xk = np.ones(len(tendon_y[i])) * k
            id_i = np.array([tendon_xk, tendon_y[i], tendon_z[i]]).T
            tendon_id.append(id_i)
    return np.array(tendon_id)


def tendon_to_excel(tendon_array):
    # plt.ion()
    plt.figure(figsize=(8, 3))
    tendon_line = []
    for i in tendon_array:
        l1 = np.linalg.norm(i[0] - i[1])
        y1 = np.interp(0.2, [0, l1], [i[0, 1], i[1, 1]])
        i[0, 1] = y1
        l2 = np.linalg.norm(i[-1] - i[-2])
        y2 = np.interp(0.2, [0, l2], [i[-1, 1], i[-2, 1]])
        i[-1, 1] = y2
        plt.plot(i[:, 1], i[:, 2])
        tendon_line.append(i.flatten())
    plt.show()
    return np.array(tendon_line)


if __name__ == '__main__':
    span_dic = {
        'fc1': [27.2, 31, 36],
        'fc2': [30.8, 33.85, 38],
        'f2': [
            (12.8, 0.5),
            (22, 0.5),
            (25, 0.5),
            (27, 0.5),
            (21, 5.75),
            (27, 5.75),
            (32.65, 5.75)
        ],
        'f3': [
            (12.9, 19.3),
            (17.1, 20.1),
            (23.1, 25.82)
        ]
    }
    for i in span_dic:
        for k, j in enumerate(span_dic[i]):
            if i == 'fc1':
                a = fc1_tendon_id(j)
            elif i == 'fc2':
                a = fc2_tendon_id(j)
            elif i == 'f2':
                a = f2_tendon_id(*j)
            elif i == 'f3':
                a = f3_tendon_id(*j)
            else:
                raise Exception
            b = tendon_to_excel(a)
            tendon_n = b.shape[0]
            tendon_name_list = [[f'Tube{a+1}'] for a in range(tendon_n)]
            point_n = b.shape[1] // 3
            id_list = [[f'x{a+1}', f'y{a+1}', f'z{a+1}'] for a in range(point_n)]
            name_dic = {'fc1': 'MC', 'fc2': 'MD', 'f2': 'ME', 'f3': 'MF'}

            xw.sheets.add(f'{name_dic[i]}_{j}')
            xw.Range('A1').value = 'name'
            xw.Range('A2').value = tendon_name_list
            xw.Range('B1').value = np.array(id_list).flatten()
            xw.Range('B2').value = b








