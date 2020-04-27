### 桁架墙计算
---

#### 结构概述
结构采用桁架+斜撑形式，结构高度为 22m，于 2m 至 22m 范围内设置围网，计算其在自重及风荷载作用下力学性能。
风荷载按《CP3: Chapter V: Part 2》标准进行计算，内罗毕当地基本风速取 28m/s。荷载组合按照《建筑结构荷载规范》3.2.3基本组合确定，取 $S_d=1.2 \times S_G + 1.4 \times S_{wind}$ 。
建立四节模型，单节宽 5m，合计 20m，模型渲染图如下所示。

@import "IO\model2.jpg" {width='256px' height='220px'}

#### 耐久性设计
根据相关资料可知，在相应环境条件下钢结构年腐蚀深度约为 2.5-5μm，考虑设计基准周期为 50 年，则基准周期内约腐蚀 1.25-2.5mm，故构造杆件板厚度最薄选用 5mm。

#### 杆件内力
基本组合下，各杆件轴力计算结果如下表所示。通过计算结果可知，立柱、斜联、斜撑轴力较大，横杆、横联、斜杆横联轴力较小。其中立柱轴力最大，最大值为 {++212kN++}。
且由计算结果可知，各杆件弯矩相对轴力均较小，可认为各杆件为轴向受力构件。

构件|轴力 (kN)
:--:|:--:
立柱|212
横杆|2.9
横联|9.7
斜联|83
斜撑|188
斜撑横联|1.4


#### 杆件稳定性计算
基于以上内力计算结果，以立柱为例，可进行如下杆件整体稳定计算：
@import "note_1.py" {cmd="python" hide id='iziziz'}

```python {cmd continue='iziziz' hide output="markdown"}
print(a_all)
```
以相同上述方法对所有类型构件进行整体稳定计算，可得如下所示计算结果：
* 立柱 (HW100x100x6/8)
```python {cmd continue='iziziz' hide output="markdown"}
print(b[0])
```
* 横杆（P70x5）
```python {cmd continue='iziziz' hide output="markdown"}
print(b[1])
```
* 横联（P70x5）
```python {cmd continue='iziziz' hide output="markdown"}
print(b[2])
```
* 斜联（P70x5）
```python {cmd continue='iziziz' hide output="markdown"}
print(b[3])
```
* 斜撑（HW100x100x6/8）
```python {cmd continue='iziziz' hide output="markdown"}
print(b[4])
```
* 斜撑横联（P70x5）
```python {cmd continue='iziziz' hide output="markdown"}
print(b[5])
```

由以上分析可知，各构件整体稳定性能均{++满足规范要求++}。


#### 杆件应力及位移结果
基本组合作用下，结构最不利应力结果如下图所示，最大应力值为 {++171MPa++}。

@import "IO\stress3.jpg" {width="300px" height="175px"}

风荷载作用下，结构最大位移结果如下图所示，最大位移值为 {++6.1cm++}。

@import "IO\displacement2.jpg" {width="300px" height="175px"}

#### 用钢量统计
本模型取 20m 宽钢架进行计算分析，用钢量为 10.9t，实际结构长度为 (102+36.5)m，合计用钢量约为 {++75t++}。



