from jqdata import jy
from sqlalchemy import or_
industry_level = 1 # 行业级别（1，2，3）
industry_st = 9 #行业标准

# 获取行业指数
def get_SW_index(SW_indexs,start_date = '2017-01-31',end_date = '2018-01-31'):
    index_list = ['PrevClosePrice','OpenPrice','HighPrice','LowPrice','ClosePrice','TurnoverVolume','TurnoverValue','TurnoverDeals','ChangePCT','UpdateTime']
    jydf = jy.run_query(query(jy.SecuMain).filter(jy.SecuMain.SecuCode==str(SW_index)))
    rows=jydf.index.tolist()
    result=link['InnerCode'][rows]
   
    df = jy.run_query(query(jy.QT_SYWGIndexQuote))
    print (df)
    df = jy.run_query(query(jy.QT_SYWGIndexQuote).filter(jy.QT_SYWGIndexQuote.InnerCode==str(result[0]),\
                                                   jy.QT_SYWGIndexQuote.TradingDay>=start_date,\
                                                         jy.QT_SYWGIndexQuote.TradingDay<=end_date
                                                        ))
    # print(df)
    df.index = df['TradingDay']
    df = df[index_list]
    return df
    
    
    
# df = get_SW_index()
# print(df)
df = jy.run_query(query(jy.QT_SYWGIndexQuote))
print (df)
# 获取所有一级行业 获取所有行业指数涨幅
# 获取所有二级行业 获取所有行业指数涨幅

df =jy.run_query(query(jy.CT_IndustryType).filter(jy.CT_IndustryType.Standard == industry_st,\
jy.CT_IndustryType.Classification == 3,or_(jy.CT_IndustryType.IndustryCode == 850111 ,\
jy.CT_IndustryType.IndustryNum == 850111)))
# print(df)