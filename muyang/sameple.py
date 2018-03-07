指数行情 - QT_IndexQuote
1.收录了指数每日的行情数据，包括了国内外指数发布机构发布的常用指数的高、开、低、收等信息； 2.使用说明：库内交易所指数代码对应的成交量额统计口径为其样本券的成交量额的总和（
不包含成份股的大宗交易）、深交所同时提供市场成交量、额统计口径，代码以“395***”开头； 3.补充说明：常见发布方指数的全量行情，如申万系列指数全量行情详见“申万指数行情表QT_SYWGIndexQuote”、
中证系列指数全量行情详见“中证指数行情QT_CSIIndexQuote”、中债系列指数全量行情详见“中债指数行情Bond_ChinaBondIndexQuote”。 4.历史数据：1928年10月至今 5.数据源：中证指数有限公司、
上海证券交易所、深圳证券交易所、中央国债登记结算有限责任公司、申银万国研究所、标普道琼斯指数公司等
收起详情
字段名	中文名	类型	单位	示例	说明
ID	ID	bigint		1	None
InnerCode	证券内部编码	int		1	证券内部编码（InnerCode）：与“证券主表（SecuMain）”中的“证券内部编码（InnerCode）”关联，得到指数的代码、简称等。
TradingDay	交易日	文本		1990-12-19 00:00:00	None
PrevClosePrice	昨收盘(元/点)	数字		100.0000	None
OpenPrice	今开盘(元/点)	数字		96.0500	None
HighPrice	最高价(元/点)	数字		99.9800	None
LowPrice	最低价(元/点)	数字		95.7900	None
ClosePrice	收盘价(元/点)	数字		99.9800	None
TurnoverVolume	成交量	数字		126000.00	None
TurnoverValue	成交金额(元)	数字		494000.0000	None
TurnoverDeals	成交笔数	int		6	None
ChangePCT	涨跌幅	数字		-0.02000000	None
NegotiableMV	流通市值	数字			None
XGRQ	更新时间	文本		2015-08-30 00:04:20	None
JSID	JSID	bigint		494208260879	None

输入：申万行业代码，开始日期，结束日期
输出：指数高开低收等行情数据，具体可参考聚源数据的申万指数行情 - QT_SYWGIndexQuote表内容
注意：导入相应的库
用法示例：
from jqdata import jy
get_SW_index(850111,start_date='2017-1-31',end_date='2017-9-1')

def get_SW_index(SW_index = 801010,start_date = '2017-01-31',end_date = '2018-01-31'):
    index_list = ['PrevClosePrice','OpenPrice','HighPrice','LowPrice','ClosePrice','TurnoverVolume','TurnoverValue','TurnoverDeals','ChangePCT','UpdateTime']
    jydf = jy.run_query(query(jy.SecuMain).filter(jy.SecuMain.SecuCode==str(SW_index)))
    link=jydf[jydf.SecuCode==str(SW_index)]
    rows=jydf[jydf.SecuCode==str(SW_index)].index.tolist()
    result=link['InnerCode'][rows]

    df = jy.run_query(query(jy.QT_SYWGIndexQuote).filter(jy.QT_SYWGIndexQuote.InnerCode==str(result[0]),\
                                                   jy.QT_SYWGIndexQuote.TradingDay>=start_date,\
                                                         jy.QT_SYWGIndexQuote.TradingDay<=end_date
                                                        ))
    df.index = df['TradingDay']
    df = df[index_list]
    return df

#将申万一级行业代码80XXXX转换为证券内部代码，并返回字典。键为申万行业代码，值为对应的行业行情（注意只适用于申万一级行业）

from jqdata import jy
import pandas as pd

SW_ZY_num= [801010, 801020, 801030, 801040, 801050, 801080, 801110, 801120,
       801130, 801140, 801150, 801160, 801170, 801180, 801200, 801210,
       801230, 801710, 801720, 801730, 801740, 801750, 801760, 801770,
       801780, 801790, 801880, 801890]
SW_CN=['农林牧渔I', '采掘I', '化工I', '钢铁I', '有色金属I', '电子I', '家用电器I', '食品饮料I',
       '纺织服装I', '轻工制造I', '医药生物I', '公用事业I', '交通运输I', '房地产I', '商业贸易I',
       '休闲服务I', '综合I', '建筑材料I', '建筑装饰I', '电气设备I', '国防军工I', '计算机I', '传媒I',
       '通信I', '银行I', '非银金融I', '汽车I', '机械设备I']
SW_ZY=[str(i) for i in SW_ZY_num]
jydf = jy.run_query(query(jy.SecuMain).filter(jy.SecuMain.SecuCode.in_(SW_ZY)))

'''def get_industry_situ_sw(SWnumber):
    SW_LINK={'SW_ZY':SW_ZY,'SW_CN':SW_CN}
    SW_LINK=pd.DataFrame(SW_LINK)
    SW_LINK[SW_LINK.SW_ZY==str(SWnumber)]
    returnvalue=SW_LINK['SW_CN'][0]
    return returnvalue'''#把申万行业代码转换为对应的行业中文名称，适用于申万一级行业

def get_inner_code(SWnumber):
    link=jydf[jydf.SecuCode==str(SWnumber)]
    rows=jydf[jydf.SecuCode==str(SWnumber)].index.tolist()
    result=link['InnerCode'][rows]
    return result

def generate_SW_CD(SW_ZY):
    SW_CD=[]
    for i in range(len(SW_ZY)):
        number=int(SW_ZY[i])
        innercode=get_inner_code(number)
        innercode=int(innercode)
        SW_CD.append(innercode)
    return SW_CD

def get_IndexQuote_SW_ZY_dict(SWnumbers):
    SW_CD=generate_SW_CD(SWnumbers)
    result={}
    for i in range(len(SWnumbers)):
        SW_CDi=SW_CD[i]
        IQi = jy.run_query(query(jy.QT_IndexQuote).filter(jy.QT_IndexQuote.InnerCode.in_([SW_CDi])))#报空集
        result[SWnumbers[i]]=IQi
    return result#最后返回的是字典，键为申万行业代码
        
#如：
trial=get_IndexQuote_SW_ZY_dict(['801010','801020','801030'])
print(trial)
{'801030':                 ID  InnerCode TradingDay  PrevClosePrice  OpenPrice  \
0     234267121737       5377 2000-01-04        1000.000   1003.040   
1     234267121691       5377 2000-01-05        1025.030   1023.580   

2999  392140084831       5377 2012-06-04        1882.204   1850.358   

      HighPrice  LowPrice  ClosePrice  TurnoverVolume  TurnoverValue  \
0      1031.380   990.180    1025.030        77518413   7.294163e+08   
1      1063.540  1011.430    1034.060       143710708   1.282740e+09   
2      1086.810  1020.610    1081.010       200333939   1.716101e+09   
3      1131.690  1075.270    1114.650       331143780   3.137770e+09   
 
2999   1854.310  1812.834    1812.834      1172580596   1.073421e+10   

     TurnoverDeals  ChangePCT                XGRQ          JSID NegotiableMV  
0              NaN   2.500000 2016-08-12 02:00:16  524282416865          NaN  
1              NaN   0.880000 2016-08-12 02:00:16  524282416928          NaN  

2999           NaN  -3.685573 2015-08-30 23:04:43  494291086593          NaN  

[3000 rows x 15 columns], '801020':                 ID  InnerCode TradingDay  PrevClosePrice  OpenPrice  \
0     234267121735       5376 2000-01-04        1000.000   1008.490   


      HighPrice  LowPrice  ClosePrice  TurnoverVolume  TurnoverValue  \
0      1042.200   992.900    1032.970        18601310   2.041041e+08   
 

     TurnoverDeals  ChangePCT                XGRQ          JSID NegotiableMV  
0              NaN   3.300000 2016-08-12 02:00:16  524282416862          NaN  


[3000 rows x 15 columns], '801010':                 ID  InnerCode TradingDay  PrevClosePrice  OpenPrice  \
0     234267121733       5375 2000-01-04        1000.000   1001.980   


      HighPrice  LowPrice  ClosePrice  TurnoverVolume  TurnoverValue  \
0      1035.360   985.470    1027.660        14011599   1.831998e+08   

     TurnoverDeals  ChangePCT                XGRQ          JSID NegotiableMV  
0              NaN   2.770000 2016-08-12 02:00:16  524282416860          NaN  
 

[3000 rows x 15 columns]}