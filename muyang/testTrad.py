enable_profile()
from jqdata import jy
import numpy as np
import pandas as pd
import math

from sqlalchemy import or_
from jy_sw_industry_code import *
industry_level = 1 # 行业级别（1，2，3）
industry_st = 9 #行业标准


jydf = jy.run_query(query(jy.SecuMain))
# (jydf)

index_list = ['OpenPrice','ClosePrice']



#行业映射成分股    
def init_stock_security_map(sw):
    df = pd.DataFrame()
    for code in sw:
        _df = pd.DataFrame(get_industry_stocks(code),columns =['code'])
        _df['industrycode'] = code
        # _df['industryname'] = self.info[code]['name']
        # if date_col:
        #     _df['date'] = date               
        df = pd.concat([df,_df],axis =0)
    return df
    
sw1mapdf = init_stock_security_map(SW1)
sw2mapdf = init_stock_security_map(SW2)
# (sw2mapdf)
# (sw1mapdf)
def initialize(context):
    # g为全局变量
    g.sw1_weight = 1
    g.sw2_weight = 3
    g.stock_weight = 6
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
    if(el1["value"] >  el2["value"]):
        return 1
    elif el1["value"] ==  el2["value"]:
        return 0
    else:
        return -1

    
def handle_data(context, data):
    cur_date = context.current_dt
    start_date = cur_date + datetime.timedelta(days=-120)
    sortedList_level1 = get_ratioandsort(SW1,start_date,cur_date)
    sortedList_level2 = get_ratioandsort(SW2,start_date,cur_date)
    availiable = get_availible_stock(context,sortedList_level1,sortedList_level2)
    # (availiable)
    # (sortedList_level1)

def get_ratioandsort(secus,start_date,end_date):
    securitys = list()
    # print(dir(npar))
    for x in secus:
        df = get_SW_index(x,start_date,end_date)
        ratio = get_ratio(x,df)
        if math.isnan(ratio):
            ratio = 0
        securitys.append({"secu":x,"value":ratio})
    result = sorted(securitys,key  = lambda d: d["value"])
    minRatio = result[0]["value"]
    maxRatio = result[-1]["value"]
    max_delta = maxRatio - minRatio
    for x in result:
        ratio = x["value"]
        detal = ratio - minRatio
        weight = detal/max_delta*100
        x["weight"] = math.floor(weight)
        # print(x["secu"])
        # jydf = jy.run_query(query(jy.SecuMain).filter(jy.SecuMain.SecuCode == x["secu"]))
        # name = jydf["ChiName"][0]
        # # print(jydf)
        # x["name"] = str(name)
    return result

def get_ratio(secuCode,df):
    openPrice = df["ClosePrice"][0]
    closePrice = df["ClosePrice"][-1]
    return (closePrice - openPrice)/openPrice
   

# 获取上市大于300天的个股
def get_availible_stock(context,sw1dict,sw2dict):
    start_date = context.current_dt + datetime.timedelta(days = -300)
    start_date = start_date.date()
    secuData = get_all_securities(types=['stock'])
    secuData = secuData[secuData["start_date"]<=start_date]
    secuData = secuData.index.tolist()
    # retDictopen =  history(1,"250d",'open',secuData,True)
    # retDictclose =  history(1,"250d",'close',secuData,True)
    
    # resultDf = ((retDictclose - retDictopen)/retDictopen)
    # print( (retDictclose["close"]- retDictopen["open"])/retDictopen["open"])
    
    result = get_price(secuData, None, context.current_dt, "250d", ["open","close"], False, "pre", 1)
    # result.fillnan(0)
    securitys = list()
    resultRatio = (result["close"] - result["open"])/result["open"]
    # resultDelta = result["close"] - result["open"]
    for x in secuData:
        ratio = resultRatio[x][0]
        if math.isnan(ratio):
            ratio = 0
        securitys.append({"value":ratio,"secu":x})
    
    result = sorted(securitys,key  = lambda d: d["value"])
    # print(result)
    minRatio = result[0]["value"]
    maxRatio = result[-1]["value"]
    max_delta = maxRatio - minRatio
    for x in result:
        ratio = x["value"]
        detal = ratio - minRatio
        plateWeight = get_plante_weight(x["secu"],sw1dict,sw2dict)
        # plateWeight = 0
        deltaValue = detal/max_delta*100
        ret = math.isnan(deltaValue)
        weight = 0
        if(not ret):
             weight = deltaValue*g.stock_weight/10+plateWeight
        # print(x["secu"],ratio,maxRatio,minRatio,plateWeight,weight)
        x["value"] = math.floor(weight)
    result = sorted(securitys,key  = lambda d: d["value"],reverse = True)
    # print(result)
    num =int( math.floor(len(result)*0.2))
    # (result)
    result = result[:num]
    index = 1
    for x in result:
        log.info("%s的排名为：%s,分数为：%s"%(x["secu"],index,x["value"] ) )
        index +=1
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
        
    # return weightValue
    weightValue += get_weight(security,sw1mapdf,sw1list,g.sw1_weight,1)
    weightValue += get_weight(security,sw2mapdf,sw2list,g.sw2_weight,2)
    # log.info("%s的最终权重值为：%s"%(security,weightValue ) )
    return weightValue
    
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

    # pass
# df = get_SW_index(SW1)
# (df)
# df = get_SW_index(SW2)
# (df)