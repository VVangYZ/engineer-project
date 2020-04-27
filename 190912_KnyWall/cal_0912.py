import numpy as np
import pandas as pd

height = np.linspace(0, 22, 12)
width = np.array([0, 5, 10, 15, 20])
depth = np.array([0, 1.5])

node = []
for x in width:
    for y in depth:
        for z in height:
            node.append([x, y, z])

node = pd.DataFrame(node, columns = ['x', 'y', 'z'])


elem = pd.DataFrame(columns=['m', 's', 'b', 'n1', 'n2', 'WHAT'])
enum = 0

for z in height[:-1]:
    for i, j in node.iterrows():
        if j['z'] == z:
            n1 = i+1
            n2 = i+2
            enum += 1
            elem.loc[enum] = [1, 1, 1, n1, n2, 'LINK1']

for x in width[:-1]:
    for i, j in node.iterrows():
        if j['z'] == height.min():
            continue
        elif j['x'] == x:
            n1 = i+1
            n2 = i+1+len(height)*len(depth)
            enum += 1
            elem.loc[enum] = [1, 2, 1, n1, n2, 'LINK2']

for x in width:
    for i, j in node.iterrows():
        if j['x'] == x and j['y'] == depth[0]:
            n1 = i+1
            n2 = i+1+len(height)
            enum += 1
            elem.loc[enum] = [1, 3, 1, n1, n2, 'LINK3']

for x in width:
    for z in height[:-1:2]:
        for i, j in node.iterrows():
            if j['y'] == depth[0] and j['x'] == x and j['z'] == z:
                n1 = i+1
                n2 = i+1+len(height)+1
                enum += 1
                elem.loc[enum] = [1, 3, 1, n1, n2, 'LINK4']
    for z in height[1:-1:2]:
        for i, j in node.iterrows():
            if j['y'] == depth[1] and j['x'] == x and j['z'] == z:
                n1 = i+1
                n2 = i+1-len(height)+1
                enum += 1
                elem.loc[enum] = [1, 3, 1, n1, n2, 'LINK4']


node.to_csv('node.csv')
elem.to_csv('elem.csv')




            




        








