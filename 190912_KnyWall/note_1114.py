import steel
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']    # 绘图支持中文

# 上部构件几何信息及内力信息表格
inf = pd.read_csv('IO/sta_1114.csv')
# 基础顶面内力信息
base_depth = np.arange(1, 10.5, 0.5)   # 深度范围
base_f = [509, 535, 48]   # 前端压力、后端拉力、剪力
# base_d = [1.5, 5]    # 基础尺寸，纵、横、竖
base_d = [2.7, 5]    # 基础尺寸，纵、横、竖


def get_f(f, N):
    ff = f'$\qquad N_{{crd}}={f:.1f}\,kN > N={N}\,kN$'
    return ff

# 各杆件稳定性计算
a = []
b = []

for i, j in inf.iterrows():
    a1 = steel.Steel_c(j['l'], [j['ix'], j['iy']], [j['ux'], j['uy']])
    a2 = a1.get_phi(j['t'], int(j['shape']), 100, 100)
    a3 = a1.get_ncrd(j['A'])
    f = j['N']

    a.append([a1, a2, a3, f])
    b.append(get_f(a3, f))

lam_x = '\lambda_x &= \\dfrac{l_{ox}}{i_x} ='
lam_y = '\lambda_y &= \\dfrac{l_{oy}}{i_y} ='
lam_b_x = '\overline{\lambda_x}&=\\dfrac{\lambda_x}{\pi}\sqrt{\\dfrac{f_y}{E}}='
lam_b_y = '\overline{\lambda_y}&=\\dfrac{\lambda_y}{\pi}\sqrt{\\dfrac{f_y}{E}}='
ncrd = 'N_{crd} = \\varphi A f_d ='

a_all = f'''
$\\begin{{aligned}}
    \qquad i_x &=  {a[0][0].i[0]:.2f}\,cm & i_y &= {a[0][0].i[1]:.2f}\,cm \\\\
    \qquad {lam_x}{a[0][0].lam[0]:.2f} & {lam_y}{a[0][0].lam[1]:.2f} \\\\
    \qquad {lam_b_x}{a[0][0].lam_b[0]:.4f} & \quad {lam_b_y}{a[0][0].lam_b[1]:.4f}
\\end{{aligned}}$

$\qquad \\varphi=min(\\varphi_x, \\varphi_y)={min(a[0][1]):.4f}$

$\qquad {ncrd}{a[0][2]:.1f}\,kN$
'''

# 基础计算
def base_cal(base_d, depth):
    base_g = base_d[0] * base_d[1] * depth * 25
    m1 = 0.6 * base_f[0] + 0.6 * base_f[1] + base_f[2] * depth * 2 / 3
    f1 = base_f[1] - base_f[0] + base_g
    e0 = m1 / f1
    p1 = f1 / (base_d[0] * base_d[1])
    p2 = m1 / (1 / 6 * base_d[1] * base_d[0] ** 2)
    pmax = p1 + p2
    rho = e0 / (1 - (p1 - p2) * (base_d[0] * base_d[1]) / f1)
    return p1, p2, pmax, e0, rho

p = []
e = []
for i in base_depth:
    p1, p2, pmax, e0, rho = base_cal(base_d, i)
    p.append([p1, p2, pmax])
    e.append([e0, rho])
p = np.array(p)
e = np.array(e)


plt.figure(figsize=(8, 3))

ax = plt.subplot(1, 2, 1)
ax.set_yticks([200.1, ], minor = True)
ax.yaxis.grid(True, which ='minor', ls='--', c='r')
plt.plot(base_depth, p[:, 0], label='轴力应力')
plt.plot(base_depth, p[:, 1], label='弯矩应力')
plt.plot(base_depth, p[:, 2], label='边缘应力')
plt.legend()
plt.xlabel('基础深度 (m)')
plt.ylabel('基础底面应力 (kPa)')
ax2 = plt.subplot(1, 2, 2)

plt.plot(base_depth, e[:, 0], label='偏心距 $e_0$')
plt.plot(base_depth, e[:, 1], label='核心半径 $\\rho$')
plt.xlabel('基础深度 (m)')
plt.ylabel('偏心距离 (m)')
plt.legend()
plt.savefig('IO/pyout.png', dpi = 500, bbox_inches = 'tight')



