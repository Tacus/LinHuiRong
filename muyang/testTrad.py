enable_profile()
from jqdata import jy
import jqdata
import numpy as np
import pandas as pd
import math

from sqlalchemy import or_
from jy_sw_industry_code import *

jydf = jy.run_query(query(jy.SecuMain))
# (jydf)

index_list = ['OpenPrice','ClosePrice']

#行业映射成分股    
#sw 申万指数代码
def init_stock_security_map(sw):
    df = pd.DataFrame()
    allstocks_df = get_all_securities()
    allstocks_df["display_code"] = allstocks_df.index.tolist()
    for code in sw:
        stocks_list = get_industry_stocks(code)
        # stocks_list[]
        _df = pd.DataFrame(stocks_list,columns =['code'])
        _df['industrycode'] = code
        stock_info = allstocks_df[allstocks_df["display_code"].isin ( stocks_list)]
       
        _df["display_name"] = stock_info["display_name"].tolist()
        # print(_df)
        df = pd.concat([df,_df],axis =0)
        
    df.index = df["display_name"]
    # print(df
    return df
    
sw1mapdf = init_stock_security_map(SW1)
sw2mapdf = init_stock_security_map(SW2)

def initialize(context):
    # g为全局变量
    g.sw1_weight = 1
    g.sw2_weight = 3
    g.stock_weight = 6
    
    #个股均线周期
    g.avg_period_1 = 50 
    g.avg_period_2 = 150
    g.avg_period_3 = 200
    #个股涨幅周期
    g.min_increase_period = 250
    g.max_increase_period = 250
    #个股上市最小自然日
    g.stock_listDays = 300 #420
    #指数涨幅计算自然日区间
    g.industry_rangeDays = 120
    #个股涨幅计算自然日区间
    g.stock_rangeDays = 250 #250
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

def secuindex_sort(el1,el2):
    if(el1["value"] >  el2["value"]):
        return 1
    elif el1["value"] ==  el2["value"]:
        return 0
    else:
        return -1

def handle_data(context, data):
    cur_date = context.current_dt
    g.all_trade_days = jqdata.get_trade_days(count = 300)
    # start_date = cur_date + datetime.timedelta(days=-g.industry_rangeDays)
    start_date = g.all_trade_days[-g.industry_rangeDays]
    # print(g.all_trade_days)
    sortedList_level1 = get_ratioandsort(SW1,start_date,cur_date)
    sortedList_level2 = get_ratioandsort(SW2,start_date,cur_date)
    availiable = get_availible_stock(context,data,sortedList_level1,sortedList_level2)
    # (availiable)
    # (sortedList_level1)

def common_get_weight(list):
    size = len(list)
    for index in range(len(list)):
        x = list[index]    
        # value =  (index+1)*(99/(1-size))+100-(99/(1-size))
        value = index*(99.0/(1-size))+100
        x["weight"] = value
        # print("common_get_weight:",x["secu"],index,size,value)

def get_ratioandsort(secus,start_date,end_date):
    securitys = list()
    for x in secus:
        df = get_SW_index(x,start_date,end_date)
        ratio = get_ratio(df)
        if math.isnan(ratio):
            ratio = 0
        securitys.append({"secu":x,"value":ratio})
    result = sorted(securitys,key  = lambda d: d["value"],reverse = True)
    common_get_weight(result)
    return result

def get_ratio(df):
    openPrice = df["ClosePrice"][0]
    closePrice = df["ClosePrice"][-1]
    return (closePrice - openPrice)/openPrice
    
#计算N天均线值（skip_paused True：使用交易日，False:使用自然日 ）
def get_day_ratio(securitylist,days):
    df = history(days, "1d", "close", securitylist,skip_paused = True)
    series_sum = df.apply(sum)
    # print(df)
    avg = series_sum/days
    return avg
#计算N天极值
def get_day_extreme(securitylist,days,method):
    df = history(days, "1d", "close", securitylist)
    result = df.apply(method)
    # avg = series_sum/days
    return result

# 获取上市大于300天的个股
def get_availible_stock(context,data,sw1dict,sw2dict):
    # start_date = context.current_dt + datetime.timedelta(days = -g.stock_listDays)
    # start_date = start_date.date()
    start_date = g.all_trade_days[-g.stock_listDays]
    secuData = get_all_securities(types=['stock'])
    secuData = secuData[secuData["start_date"]<=start_date]
    secuData = secuData.index.tolist()
    
    avg_1 = get_day_ratio(secuData,g.avg_period_1)
    
    avg_2 = get_day_ratio(secuData,g.avg_period_2)
    
    avg_3 = get_day_ratio(secuData,g.avg_period_3)
    
    min_closes = get_day_extreme(secuData,g.min_increase_period,min)
    max_closes = get_day_extreme(secuData,g.max_increase_period,max)
    
    # resultDf = ((retDictclose - retDictopen)/retDictopen)
    # print( (retDictclose["close"]- retDictopen["open"])/retDictopen["open"])
    
    result = get_price(secuData, None, context.current_dt, str(g.stock_rangeDays)+"d", ["open","close"], False, "pre", 1)
    # result.fillnan(0)
    securitys = list()
    resultRatio = (result["close"] - result["open"])/result["open"]
    # resultDelta = result["close"] - result["open"]
    # print(resultRatio)
    for x in secuData:
        ratio = resultRatio[x][0]
        if math.isnan(ratio):
            # print(x,"null")
            ratio = 0
        securitys.append({"value":ratio,"secu":x})
    
    result = sorted(securitys,key  = lambda d: d["value"],reverse = True)
    common_get_weight(result)
    # print("result",result)
    for x in result:
        plateWeight = get_plante_weight(x["secu"],sw1dict,sw2dict)
        deltaValue = x["weight"]
        ret = math.isnan(deltaValue)
        weight = 0
        if(not ret):
             weight = deltaValue*g.stock_weight/10+plateWeight
        # print(x["secu"],ratio,maxRatio,minRatio,plateWeight,weight)
        x["value"] = math.floor(weight)
    result = sorted(securitys,key  = lambda d: d["value"],reverse = True)
    num =int( math.floor(len(result)*0.2))
    # (result)
    # result = result[:num]
    # print("num:",num)
    index = 1
    for x in result:
        # security_name = sw1mapdf.loc[x["secu"]]
        security = x["secu"]
        security_name = sw1mapdf[sw1mapdf["code"] == security]
        close = data[security].close
        security_avg1 = avg_1[security]
        security_avg2 = avg_2[security]
        security_avg3 = avg_3[security]
        min_close = min_closes[security]
        max_close = max_closes[security]
        # log.info("%s当前价：%s,avg1为：%s,avg2为：%s,avg3为：%s,\
        #     min_close为：%s,max_close为：%s,"%(
        #     security,close,security_avg1,security_avg2 ,
        #     security_avg3,min_close,max_close) )
        
        
        if(security_name is not None and close>security_avg1 
            and security_avg1>security_avg2 
            and security_avg2>security_avg3
            and close>min_close*1.1
            and close>max_close*0.7):
            if(security_name["display_name"].size == 0):
                #  log.info("name 为空",security,security_name,sw1mapdf)
                 continue
            security_name = security_name["display_name"][0]
            log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s"%(x["secu"],security_name,index,x["value"],x["weight"] ) )
            index += 1
            if(index > num):
                break
        # else:
        #     security_name = "已退市"
        # log.info("%s（%s）的排名为：%s,分数为：%s"%(x["secu"],security_name,index,x["value"] ) )
        # index +=1
    # for i in arrange
    # (result)


def get_plante_weight(security,sw1list,sw2list):
    weightValue = 0
    # code = get_sw_code(security,SW1)
    # for x in sw1list:
    #     if(x["secu"] ==code):
    #         weightValue += x["weight"]*g.sw1_weight/10
    #         break
    # code = get_sw_code(security,SW2)
    # for x in sw2list:
    #     if(x["secu"] ==code):
    #         weightValue += x["weight"]*g.sw2_weight/10
    #         break
        
    weightValue += get_weight(security,sw1mapdf,sw1list,g.sw1_weight,1)
    weightValue += get_weight(security,sw2mapdf,sw2list,g.sw2_weight,2)
    return weightValue
#
def get_weight(security,df,swlist,weightRatio,level):
    df = df[df['code'] == security]
    industrycode = list(df["industrycode"])
    if(len( industrycode)>0):
        industrycode = industrycode[0]
    else:
        return 0
    # (industrycode,type(industrycode))
    for x in swlist:
        if(industrycode == x["secu"]):
            return x["weight"]*weightRatio/10
    # log.info(security,u"不在%s级申万行业中"%(level))     
    return 0
def get_sw_code(security,sw):
    for x in sw:
        allstocks = get_industry_stocks(x)
        for y in allstocks:
            if(y == security):
                return x

