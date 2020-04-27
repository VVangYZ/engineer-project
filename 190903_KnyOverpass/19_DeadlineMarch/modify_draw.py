import win32com.client as win32
import numpy as np
import xlwings as xw

# 连接 cad 文件
acad = win32.Dispatch("AutoCad.Application")
doc = acad.ActiveDocument
ms = doc.ModelSpace
print(doc.name)


# 字体修改
ts = doc.TextStyles
for i in range(ts.count):
    the_item = ts.item(i)
    the_item.SetFont('Arial', False, False, 0, 0)

# 内容替换
all_text = []

for i in range(ms.count):
    item = ms.item(i)
    if item.objectname == 'AcDbText':
        all_text.append(item)

replace_dict = xw.Range('A1').options(dict, expand='table').value
replace_word = xw.Range('D1').options(dict, expand='table').value

for i in all_text:
    i_content = i.textstring.strip()
    i_content.replace(' ', '')
    if i_content in replace_dict:
        i.textstring = replace_dict[i_content]
    else:
        for j in replace_word:
            if i_content.find(j):
                i.textstring = i_content.replace(j, replace_word[j])
                i_content = i.textstring





