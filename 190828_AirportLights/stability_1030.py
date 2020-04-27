import steel
import pandas as pd

inf = pd.read_csv('IO/stability.csv')
out = pd.DataFrame(columns=['phi', 'Ncrd'])
num = 0

for i, j in inf.iterrows():
    a1 = steel.Steel_c(j['l'], [j['ix'], j['iy']], [j['u'], j['u']])
    a2 = a1.get_phi(j['t'], int(j['shape']))
    a3 = a1.get_ncrd(j['A'])/100
    num += 1
    out.loc[num] = [min(a2), a3]

    print(f'{a3:.2f} is bigger than {j["N"]}\t{a3 > j["N"]}')

out.to_csv('IO/sta_out.csv')


