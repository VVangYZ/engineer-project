import steel
import pandas as pd

inf = pd.read_csv('IO/sta.csv')

def get_f(f, N):
    ff = f'$\qquad N_{{crd}}={f:.1f}\,kN > N={N}\,kN$'
    return ff


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



