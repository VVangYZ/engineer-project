from input_data1 import get_distance, get_ei
from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
import xlwings as xw

Base = declarative_base()


class Ei(Base):
    """
    定义 ei 数据类别
    """
    __tablename__ = "ei_tbl"
    Name = Column(String, primary_key=True)
    ICD = Column(String)
    SQX = Column(String)
    DMX = Column(String)
    CG = Column(String)


engine = create_engine('mysql+pymysql://wyz:wang1234@cdb-2ashfo5g.bj.tencentcdb.com:10033/nep2020')
DBSession = sessionmaker(bind=engine)
session = DBSession()

align_dic = {}
for ins in session.query(Ei):
    get_ei(ins, align_dic)

print('导入路线完成')

# all_zk = xw.Range('A1').options(pd.DataFrame, expand='table').value
#
# for i, j in all_zk.iterrows():
#     line = j['路线']
#     station = j['桩号']
#     cord = align_dic[line].curPQX.GetCoord(station)
#     cord_x = cord[0]
#     cord_y = cord[1]
#     all_zk.loc[i, 'x'] = cord_x
#     all_zk.loc[i, 'y'] = cord_y
#
# print('读取坐标完成')

all_sub = pd.read_sql_query('select * from sub_tbl;', engine)
# all_sub = xw.Range('A1').options(pd.DataFrame, expand='table').value

for i, j in all_sub.iterrows():
    line = j['align_name']
    station = j['Station']
    cord = align_dic[line].curPQX.GetCoord(station)
    cord_x = cord[0]
    cord_y = cord[1]
    all_sub.loc[i, 'x'] = cord_x
    all_sub.loc[i, 'y'] = cord_y

xw.sheets['sub_all_0425'].range('A1').value = all_sub

print('读取坐标完成')

