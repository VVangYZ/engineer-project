import win32com.client as win32
import pythoncom
import numpy as np
import pandas as pd

acad = win32.Dispatch("AutoCAD.Application")
doc = acad.ActiveDocument
ms = doc.ModelSpace
doc.name

# 获取数据
inf = pd.read_excel('ALL_190920.xlsx', sheet_name='out')
inf = inf.reindex(columns = ['num', 'which', 'chainage', '编号', '深度', '保留'])

# 获取线路长度
pl = []
pll = pd.DataFrame(columns=['which', 'length'])
for i in range(ms.count):
    if ms.item(i).objectname == 'AcDbPolyline':
        pl.append(ms.item(i))
        pll.loc[i] = [ms.item(i).layer, ms.item(i).length]
pll.sort_values(by='which')

# 获取块
bk = doc.blocks.item(3)
bk.name

# 定义函数
## 获取多段线坐标
def get_c(pli):
    pl_c = pli.coordinates
    pl_c = np.array(pl_c).reshape(len(pl_c)//2, 2)
    return pl_c

## 获取长度数组
def get_l(ci):
    p1 = ci[:-1, :]
    p2 = ci[1:, :]
    pl_l = (((p2 - p1)**2)[:, 0] + ((p2 - p1)**2)[:, 1])**0.5
    pl_l = np.insert(pl_l, 0, 0)
    pl_l = np.cumsum(pl_l)
    return pl_l


## 获取插入点坐标
def get_pt(infi, pl_l, pl_c):
    li = infi['chainage']
    if li > pl_l[-1]:
        print(infi['编号'])
        ni = len(pl_l) - 1
        x = np.interp(li-pl_l[ni-1], [0, pl_l[ni] - pl_l[ni-1]], [pl_c[ni-1, 0], pl_c[ni, 0]])
        y = np.interp(li-pl_l[ni-1], [0, pl_l[ni] - pl_l[ni-1]], [pl_c[ni-1, 1], pl_c[ni, 1]])
    else:
        ni = np.where(pl_l > li)[0].min()
        x = np.interp(li-pl_l[ni-1], [0, pl_l[ni] - pl_l[ni-1]], [pl_c[ni-1, 0], pl_c[ni, 0]])
        y = np.interp(li-pl_l[ni-1], [0, pl_l[ni] - pl_l[ni-1]], [pl_c[ni-1, 1], pl_c[ni, 1]])
    return x, y, 0


## 通过坐标获得插入点数据
def POINT(x,y,z):
   return win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8,(x,y,z))

## 插入块函数
def ins_bk(infi, plli, plci):
    pt = POINT(*get_pt(infi, plli, plci))
    bki = ms.insertblock(pt, bk.name, 2, 2, 2, 0)
    bki_a = bki.getattributes()
    bki_a[0].textstring = infi['编号']
    bki_a[1].textstring = '%.2f' % infi['深度']
    bki.update()


# 获取路线信息
plc = []
pll = []
for i in pl:
    j = get_c(i)
    plc.append(j)
    k = get_l(j)
    pll.append(k)

# 插入钻孔信息
for i, j in inf.iterrows():
    if j['保留'] == True:
        for m, n in enumerate(pl):
            if str(j['num']) in n.layer and str(j['which']) in n.layer:
                pln = m
        ins_bk(j, pll[pln], plc[pln])


# 查询数据
z_depth = []
w_depth = []

for i in range(ms.count):
    if ms.item(i).objectname == 'AcDbBlockReference':
        if ms.item(i).layer == '钻孔-D' or ms.item(i).layer == '钻孔':
            a = ms.item(i).getattributes()
            if a[0].textstring[1] == 'Z':
                z_depth.append(float(a[1].textstring))
            elif a[0].textstring[1] == 'W':
                w_depth.append(float(a[1].textstring))

print('szt:%f'%sum(z_depth))
print('swt:%f'%sum(w_depth))
