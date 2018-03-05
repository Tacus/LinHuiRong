from jqdata import jy
import numpy as np
import math

from sqlalchemy import or_
from jy_sw_industry_code import *
industry_level = 1 # 行业级别（1，2，3）
industry_st = 9 #行业标准


jydf = jy.run_query(query(jy.SecuMain))


index_list = ['OpenPrice','ClosePrice']

# 获取行业指数
def get_SW_index(SW_index,start_date = '2017-01-31',end_date = '2018-01-31'):
    jydf = jy.run_query(query(jy.SecuMain).filter(jy.SecuMain.SecuCode == (SW_index)))
    result=jydf['InnerCode'][0]
    
    df = jy.run_query(query(jy.QT_SYWGIndexQuote).filter(jy.QT_SYWGIndexQuote.InnerCode == result,\
                                                   jy.QT_SYWGIndexQuote.TradingDay>=start_date,\
                                                         jy.QT_SYWGIndexQuote.TradingDay<=end_date
                                                       ))
    df.index = df['TradingDay']
    return df[index_list]



ratioList = list()

def secuindex_sort(el1,el2):
    if(el1["ratio"] >  el2["ratio"]):
        return 1
    elif el1["ratio"] ==  el2["ratio"]:
        return 0
    else:
        return -1

    
def handle_data(context, data):
    cur_date = context.current_dt
    star_date = cur_date + datetime.timedelta(days=-120)
    sortedList_level1 = get_ratioandsort(SW1,star_date,cur_date)
    sortedList_level2 = get_ratioandsort(SW2,star_date,cur_date)
    print(sortedList_level1)

def get_ratioandsort(secus,start_date,end_date):
    securitys = list()
    # print(dir(npar))
    for x in secus:
        df = get_SW_index(x,start_date,end_date)
        ratio = get_ratio(x,df)
        securitys.append({"secu":x,"ratio":ratio})
    result = sorted(securitys,cmp = secuindex_sort)
    minRatio = result[0]["ratio"]
    maxRatio = result[-1]["ratio"]
    max_delta = maxRatio - minRatio
    for x in result:
        ratio = x["ratio"]
        detal = ratio - minRatio
        weight = detal/max_delta*100
        x["ratevalue"] = math.floor(weight)
        name = jydf[jydf["SecuCode"]==x["secu"]]["ChiName"][0]
        x["name"] = name
        print(name)
    return result

def get_ratio(secuCode,df):
    openPrice = df["ClosePrice"][0]
    closePrice = df["ClosePrice"][-1]
    return (closePrice - openPrice)/openPrice
   

# df = get_SW_index(SW1)
# print(df)
# df = get_SW_index(SW2)
# print(df)