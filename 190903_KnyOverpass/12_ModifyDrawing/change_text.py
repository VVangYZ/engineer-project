import win32com.client as win32
import pythoncom
import numpy as np
import re

acad = win32.Dispatch("AutoCAD.Application")
doc = acad.ActiveDocument
ms = doc.ModelSpace
doc.name

replace_dic = {
    '立 面': 'ELEVATION',
    '平 面': 'PLAN',
    '预制小箱梁': 'Precast PSC Box Girder',
    '桥梁起点桩号': 'START CHAINAGE',
    '桥梁终点桩号': 'END CHAINAGE',
    '中间地面线': 'Ground Level',
    '80型伸缩缝': '80 Movement Joint',
    '里程桩号': 'CHAINAGE',
    '设计高程': 'PROPOSED LEVEL',
    '地面高程': 'GROUND LEVEL',
    '超  高': 'SUPERELEVATION',
    '平 曲 线': 'HORIZONTAL ALIGNMENT',
    '注：': 'NOTE:',
    '坡度(%)': 'ELEVATION ALIGNMENT',
    '桥型布置图': 'GENERAL ARRANGEMENT'
}

re_1 = re.compile(r'1\.\D')
re_2 = re.compile(r'(\d{1,2}\.\D|路基设计高程|坡长|.*搭板)')

t1 = '1. All dimensions are in centimeters, elevation and chainage are in meters.'

for i in range(ms.count):
    the_item = ms.item(i)
    if the_item.objectname == 'AcDbText':
        origin_text = the_item.TextString
        if re_1.match(origin_text):
            the_item.TextString = t1
        elif re_2.match(origin_text):
            the_item.TextString = ''
        else:
            for m in replace_dic:
                if m in origin_text:
                    done_text = origin_text.replace(m, replace_dic[m])
                    origin_text = done_text
                    the_item.TextString = done_text


ts = doc.TextStyles
for i in range(ts.count):
    the_item = ts.item(i)
    the_item.SetFont('Arial', False, False, 0, 0)
    the_item.Width = 1
