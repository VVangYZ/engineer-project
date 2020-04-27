import steel
import pandas as pd

inf = pd.read_csv('IO/sta.csv')

a = []
for i, j in inf.iterrows():
    a1 = steel.Steel_c(j['l'], [j['ix'], j['iy']], [j['ux'], j['uy']])
    a2 = a1.get_phi(j['t'], j['shape'], 100, 100)
    a3 = a1.get_ncrd(j['A'])
    a.append([a1, a2, a3])


# 立柱
a1 = steel.Steel_c(2, [4.18, 2.48], [2, 1])
a2 = a1.get_phi(8, 2, 100, 100)
a3 = a1.get_ncrd(21.58)

# 横杆
b1 = steel.Steel_c(5, [2.714, 2.714], [1, 1])
b2 = b1.get_phi(3, 10)
b3 = b1.get_ncrd(7.808)

# 横联
c1 = steel.Steel_c(2, [2.714, 2.714], [1, 1])
c2 = c1.get_phi(3, 10)
c3 = c1.get_ncrd(7.808)

# 斜联
d1 = steel.Steel_c(5**0.5, [2.714, 2.714], [1, 1])
d2 = d1.get_phi(3, 10)
d3 = d1.get_ncrd(7.808)

# 斜撑
e1 = steel.Steel_c((4.5**2+12**2)**0.5/6,  [4.18, 2.48], [2, 1])
e2 = e1.get_phi(3, 2, 100, 100)
e3 = e1.get_ncrd(21.58)

# 斜撑横杆
f1 = steel.Steel_c(4.5/2, [2.714, 2.714], [1, 1])
f2 = f1.get_phi(3, 10)
f3 = f1.get_ncrd(7.808)

lam_x = '\lambda_x &= \\dfrac{l_{ox}}{i_x} ='
lam_y = '\lambda_y &= \\dfrac{l_{oy}}{i_y} ='
lam_b_x = '\overline{\lambda_x}&=\\dfrac{\lambda_x}{\pi}\sqrt{\\dfrac{f_y}{E}}='
lam_b_y = '\overline{\lambda_y}&=\\dfrac{\lambda_y}{\pi}\sqrt{\\dfrac{f_y}{E}}='
ncrd = 'N_{crd} = \\varphi A f_d ='

a_all = f'''
$\\begin{{aligned}}
    \qquad i_x &=  {a1.i[0]:.2f}\,cm & i_y &= {a1.i[1]:.2f}\,cm \\\\
    \qquad {lam_x}{a1.lam[0]:.2f}\,cm & {lam_y}{a1.lam[1]:.2f}\,cm \\\\
    \qquad {lam_b_x}{a1.lam_b[0]:.4f} & \quad {lam_b_y}{a1.lam_b[1]:.4f}
\\end{{aligned}}$

$\qquad \\varphi=min(\\varphi_x, \\varphi_y)={min(a2):.4f}$

$\qquad {ncrd}{a3:.1f}\,kN$
'''

def get_f(f, N):
    ff = f'$\qquad N_{{crd}}={f:.1f}\,kN > N={N}\,kN$'
    return ff

