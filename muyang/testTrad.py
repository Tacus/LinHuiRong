#1、价格强势股的当前价格是否需要实时计算？√
#2、海龟交易的计算起始日期是否是根据当前交易开始日期累计，还是往前推
#3、需要考虑停牌，上市交易天数过小,这时候是否需要参与交易
#4、止损部分：加仓三次，止损计算针对的是每次加仓时的数据，还是最后一次

enable_profile()
from jqdata import jy
import jqdata
import numpy as np
import pandas as pd
import math

from sqlalchemy import or_
from jy_sw_industry_code import *

jydf = jy.run_query(query(jy.SecuMain))

index_list = ['OpenPrice','ClosePrice','InnerCode']


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

    g.debug_stocks = ["601155.XSHG"]
    # g.debug_stocks = None
    g.stock_pool = []
    g.position_pool = {}
    init_turtle_data()
    # run_weekly(weekly_fun,"open")
    #计算N天内最从高价回落最多%M

#设定每周第一个交易日为该周内账户总市值
def weekly_fun(context):
    date = context.current_dt
    g.total_value = context.portfolio.total_value
    print("current date:%s,total_value:%d"%(str(date),g.total_value))

#获取有效股票并更新有效股票历史数据 price_info,eps_info
def before_trading_start(context):
    g.stock_pool = get_valid_stocks(context,g.debug_stocks)
    for single in g.stock_pool:
        single.run_daily(context)

    for _,stock_info in g.position_pool.items():
        stock_info.run_daily(context)
    # return g.valid_stocks

def handle_data(context, data):

    for _,stock_info in g.position_pool.items():
        order = stock_info.start_process(context)

        if order != None and order.filled  > 0 and order.is_buy :
            stock_info.add_buy_count( order.filled)
        elif(order != None and order.filled > 0 and not order.is_buy):
            stock_info.reduce_buy_count( order.filled)
            count = stock_info.get_buy_count()
            if(count <= 0):
                del g.position_pool[stock_info.code]

    for single in g.stock_pool:
        order = single.start_process(context)
        if order != None and order.filled  > 0 and order.is_buy :
            single.set_buy_count( order.filled)
            g.stock_pool.remove(single)
            g.position_pool[single.code] = single
    #订单追踪


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

def init_turtle_data():
    # 系统1入市的trailing date
    g.short_in_date = 20
    # 系统2入市的trailing date
    g.long_in_date = 55
    # 系统1 exiting market trailing date
    g.short_out_date = 10
    # 系统2 exiting market trailing date
    g.long_out_date = 20
    # g.dollars_per_share是标的股票每波动一个最小单位，1手股票的总价格变化量。
    # 在国内最小变化量是0.01元，所以就是0.01×100=1
    g.dollars_per_share = 1
    # 可承受的最大损失率
    g.loss = 0.1
    # 若超过最大损失率，则调整率为：
    g.adjust = 0.8
    # 计算N值的天数
    g.number_days = 20
    # 最大允许单元
    g.unit_limit = 4
    # 系统1所配金额占总金额比例
    g.ratio = 0.8

    g.N = []

    #计算N天内最从高价回落最多%M
    g.rblh_d = 250
    g.rblh_r = 0.35

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
#获取有效的eps price条件股票
def get_valid_stocks(context,securitys = None):
    result = []
    if(securitys != None):
        for i in range(len(securitys)):
            security = securitys[i]
            fake_eps_info = {"code":security}
            stInfo = get_stock_info(None,fake_eps_info)
            if(stInfo != None):
                result.append(stInfo)
        return result
    cur_date = context.current_dt
    g.all_trade_days = jqdata.get_trade_days(end_date = cur_date,count = 300)
    start_date = g.all_trade_days[-g.industry_rangeDays]
    sortedList_level1 = get_ratioandsort(SW1,start_date,cur_date)
    sortedList_level2 = get_ratioandsort(SW2,start_date,cur_date)
    mighty_price_list = get_mighty_price_stocks(context,sortedList_level1,sortedList_level2)
    mighty_eps_list = get_mighty_eps_stocks(context,g.debug_stocks)
    for stock,price_stock in mighty_price_list.items():
        for eps_stock in mighty_eps_list :
            if eps_stock["code"] == stock:
                year_eps_ratio2 = "None"
                if eps_stock.has_key("year_eps_ratio2"):
                   year_eps_ratio2 = eps_stock["year_eps_ratio2"]
                year_eps_ratio3 = "None"
                if eps_stock.has_key("year_eps_ratio3"):
                   year_eps_ratio3 = eps_stock["year_eps_ratio3"]
            #     log.info("%s的最近两个季度eps增长率：%s:%s%%,%s:%s%%，最近年度eps增长率：%s%%,%s%%,%s%%"%(x["code"],
            #   x["eps_date2"],x["eps_ratio2"],x["eps_date"], x["eps_ratio"],year_eps_ratio3,year_eps_ratio2,x["year_eps_ratio"]))
                # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s,最近两个季度eps增长率：%s%%,%s%%,\最近年度eps增长率：%s%%,%s%%,%s%%"%(stock,
                # price_stock["security_name"],price_stock["index"],price_stock["value"], price_stock["weight"] ,eps_stock["eps_ratio2"], 
                # eps_stock["eps_ratio"],year_eps_ratio3,year_eps_ratio2,eps_stock["year_eps_ratio"]))
                stInfo = get_stock_info(price_stock,eps_stock)
                if(stInfo != None):
                    result.append(stInfo)
                # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s,最近两个季度eps增长率：%s%%,%s%%"%(stock,
                # price_stock["security_name"],price_stock["index"],price_stock["value"], price_stock["weight"] ,eps_stock["eps_ratio2"], 
                # eps_stock["eps_ratio"]))
    gr_index2 = get_growth_rate("000016.XSHG")
    gr_index8 = get_growth_rate("399333.XSHE")
    # if(gr_index8<gr_index2):
    #     log.info("当前大盘强于小盘",gr_index2,gr_index8)
    # else:
    #     log.info("当前小盘强于大盘",gr_index2,gr_index8)
    result = sorted(result,key = lambda d: d.market_cap,reverse = gr_index2>gr_index8)
    return result

def get_stock_info(price_info,eps_info):
    code = eps_info["code"]
    exsit = False
    for code_,stock_info in g.position_pool.items():
        if(code == code_):
            stock_info.update_info(price_info,eps_info)
            exsit = True
            break
    if not exsit:
        return StockInfo(price_info,eps_info)

def common_get_weight(list):
    size = len(list)
    for index in range(len(list)):
        x = list[index]    
        # value =  (index+1)*(99/(1-size))+100-(99/(1-size))
        value = index*(99.0/(1-size))+100
        x["weight"] = round(value,1)
        # print("common_get_weight:",x["secu"],index,size,value)

def get_ratioandsort(secus,start_date,end_date):
    # 获取行业指数
    jydf = jy.run_query(query(jy.SecuMain).filter(jy.SecuMain.SecuCode.in_(secus)))
    result=jydf['InnerCode']
    # print(jydf)
    df = jy.run_query(query(jy.QT_SYWGIndexQuote).filter(jy.QT_SYWGIndexQuote.InnerCode.in_( result),\
                                                  jy.QT_SYWGIndexQuote.TradingDay>=start_date,\
                                                         jy.QT_SYWGIndexQuote.TradingDay<=end_date
                                                      ))
    series = pd.Series(jydf["SecuCode"].tolist(),index = result)
    # print(dir(result))
    df = df[index_list]
    offset = 0

    securitys = list()
    currentSecuCode = None
    closePrice_open = None
    closePrice_close = None
    while len(df) > 0 :
        dflist = list(df.itertuples(index=False))
        for array in dflist :
            if(array[2] != currentSecuCode):

                if(currentSecuCode != None):
                    ratio = (closePrice_close - closePrice_open)/closePrice_open 
                    securitys.append({"secu":series.loc(currentSecuCode),"value":ratio})
                closePrice_open = array[0]
                
                currentSecuCode = array[2]

            closePrice_close = array[1]

        offset += len(df)
        df = jy.run_query(query(jy.QT_SYWGIndexQuote).filter(jy.QT_SYWGIndexQuote.InnerCode.in_( result),\
                                                  jy.QT_SYWGIndexQuote.TradingDay>=start_date,\
                                                         jy.QT_SYWGIndexQuote.TradingDay<=end_date
                                                      ).offset(offset))
        df = df[index_list]
        
    result = sorted(securitys,key  = lambda d: d["value"],reverse = True)
    common_get_weight(result)
    return result
    # return df[index_list],series

def get_ratio(df):
    openPrice = df["ClosePrice"][0]
    closePrice = df["ClosePrice"][-1]
    if(openPrice == None) or closePrice == None :
        return float("nan")
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

# 获取价格强势股
def get_mighty_price_stocks(context,sw1dict,sw2dict):
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
        x["value"] = round(weight,1)
    result = sorted(securitys,key  = lambda d: d["value"],reverse = True)
    num =int( math.floor(len(result)*0.2))
    # (result)
    # result = result[:num]
    # print("num:",num)
    index = 1
    fileter_securitys = {}
    stocks = []
    data = get_current_data()
    for x in result:
        # security_name = sw1mapdf.loc[x["secu"]]
        security = x["secu"]
        close = data[security].last_price
        security_avg1 = avg_1[security]
        security_avg2 = avg_2[security]
        security_avg3 = avg_3[security]
        min_close = min_closes[security]
        max_close = max_closes[security]
        # log.info("%s当前价：%s,avg1为：%s,avg2为：%s,avg3为：%s,\
        #     min_close为：%s,max_close为：%s,"%(
        #     security,close,security_avg1,security_avg2 ,
        #     security_avg3,min_close,max_close) )
        
        stock_score = x["weight"]
        if(close>security_avg1 
            and security_avg1>security_avg2 
            and security_avg2>security_avg3
            and close>min_close*1.1
            and close>max_close*0.7
            and stock_score >87):
 
            # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s"%(x["secu"],security_name,index,x["value"],x["weight"] ) )
            x["index"] = index
            index += 1
            fileter_securitys[x["secu"]] = x
            stocks.append(x["secu"])
            if(index > num):
                break
        
        # else:
        #     security_name = "已退市"
        # log.info("%s（%s）的排名为：%s,分数为：%s"%(x["secu"],security_name,index,x["value"] ) )
        # index +=1
    # for i in arrange
    # (result)
    return fileter_securitys

#获取行业权重
def get_plante_weight(security,sw1list,sw2list):
    weightValue = 0
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
              
#获取上一个季度的时间
def get_last_reason_date(dt,month_count = 0,year_count = 0):
    date = dt.date()
    month = date.month
    year = date.year
    month = month -3*month_count
    if(month <=0):
        month = 12
        year = year -1
    year = year -year_count
    return str(year)+"q"+str(month/3)
#获取上一年的时间
def get_last_year_date(dt,year_count = 0):
    date = dt.date()
    year = date.year
    year = year - year_count
    return str(year)

    # 获取扣非eps
def get_adjust_eps(df):
    eps = df["eps"][0]
    eps = eps*df["adjusted_profit_to_profit"][0]/100
    return eps


#获取eps强势股    
def get_mighty_eps_stocks(context,securitys=None):
    if(securitys):
        qobj = query(valuation.code,valuation.circulating_market_cap,income.basic_eps,indicator.eps,indicator.statDate,indicator.adjusted_profit_to_profit).filter(valuation.code.in_(securitys))
    else:
        qobj = query(valuation.code,valuation.circulating_market_cap,income.basic_eps,indicator.eps,indicator.statDate,indicator.adjusted_profit_to_profit)
    current_dt = context.current_dt
    df = get_fundamentals(qobj,date=current_dt)
    # print(df)
    result = []
    for index in df.index:
        cldata = df.loc[index]
        dt_str = cldata.statDate
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d')
        code = cldata.code
        eps = cldata.eps*cldata.adjusted_profit_to_profit/100
        # print(str.format("eps:%s,rps:%s,eps:%s"%(cldata.eps,cldata.adjusted_profit_to_profit,eps)))
        market_cap = cldata.circulating_market_cap
        
        last_dt = get_last_reason_date(dt,0,1)
        last_dt2 = get_last_reason_date(dt,1)
        last_dt3 = get_last_reason_date(dt,1,1)
        
        single_query = query(valuation.code,income.basic_eps,indicator.eps,indicator.statDate,indicator.adjusted_profit_to_profit).filter(valuation.code == code)
        single_df = get_fundamentals(single_query,statDate=last_dt)
        single_df2 = get_fundamentals(single_query,statDate=last_dt2)
        single_df3 = get_fundamentals(single_query,statDate=last_dt3)
        # print(dt,last_dt,last_dt2,last_dt3)
        if(single_df.empty or single_df2.empty or single_df3.empty):
            # print("未找到财报数据",code,dt,last_dt,last_dt2,last_dt3)
            continue
        dt_str2 = single_df2["statDate"][0]
        last_eps = get_adjust_eps(single_df)
        last_eps2 = get_adjust_eps(single_df2)
        last_eps3 = get_adjust_eps(single_df3)
        # print(str.format("eps:%s,eps2:%s,eps3:%s"%(last_eps,last_eps2,last_eps3)))
        ratio = (eps - last_eps)/last_eps
        ratio2 = (last_eps2 - last_eps3)/last_eps3
        # x["eps_ratio"] = math.floor(ratio*100)
        # x["eps_ratio2"] = math.floor(ratio2*100)
        if(ratio<0.2 or ratio2 <0.2):
            continue
        security_name = sw1mapdf[sw1mapdf["code"] == code]
        security_name = security_name["security_name"][0]
        result.append({"code":code,
        "eps_ratio":round(ratio*100,1),
        "eps_ratio2":round(ratio2*100,1),
        "eps_date":dt_str,
        "eps_date2":dt_str2,
        "market_cap":market_cap,
        "security_name":security_name
        })
        # result.append({"code":code,"eps_ratio":round(ratio*100,1),"eps_ratio2":round(ratio2*100,1)})
        # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s,eps增长率：%s%%"%(x["secu"],x["security_name"],x["index"],x["value"],math.floor(x["weight"]) ,math.floor(ratio*100)) )
        # last_year_dt = get_last_year_date(current_dt,year_count=1)
        # single_df = get_fundamentals(single_query,statDate=last_year_dt)
        # if(single_df.empty):
        #     last_year_eps = get_total_eps_stocks(last_year_dt,code)
        #     if(not last_year_eps):
        #         continue
        # else:
        #     last_year_eps = single_df["eps"][0]
        # last_year_dt2 = get_last_year_date(current_dt,year_count=2)
        # single_df2 = get_fundamentals(single_query,statDate=last_year_dt2)
        # if(single_df2.empty):
        #     continue
        
        # last_year_eps2 = single_df2["eps"][0]
        # year_ratio = (last_year_eps - last_year_eps2)/last_year_eps2
        # if(year_ratio<0.2):
        #     continue
        # last_year_dt3 = get_last_year_date(current_dt,year_count=3)
        # single_df3 = get_fundamentals(single_query,statDate=last_year_dt3)
        # year_ratio2 = None
        
        # if(not single_df3.empty):
        #     last_year_eps3 = single_df3["eps"][0]
        #     year_ratio2 = (last_year_eps2 - last_year_eps3)/last_year_eps3
        # else:
        #     result.append({"code":code,
        #     "eps_ratio":round(ratio*100,1),
        #     "eps_date":dt_str,
        #     "eps_date2":dt_str2,
        #     "eps_ratio2":round(ratio2*100,1),
        #     "year_eps_date":last_year_dt,
        #     "year_eps_ratio":round(year_ratio*100,1)})
        #     continue
        # if(year_ratio2<0.2):
        #     continue
        # last_year_dt4 = get_last_year_date(dt,year_count=4)
        # single_df4 = get_fundamentals(single_query,statDate=last_year_dt4)
        # year_ratio3 = None
        # if(not single_df4.empty):
        #     last_year_eps4 = single_df4["eps"][0]
        #     year_ratio3 = (last_year_eps3 - last_year_eps4)/last_year_eps4
        # else:
        #     result.append({"code":code,
        #     "eps_ratio":round(ratio*100,1),
        #     "eps_date":dt_str,
        #     "eps_date2":dt_str2,
        #     "eps_ratio2":round(ratio2*100,1),
        #     "year_eps_date":last_year_dt,
        #     "year_eps_date2":last_year_dt2,
        #     "year_eps_ratio":round(year_ratio*100,1),
        #     "year_eps_ratio2":round(year_ratio2*100,1)
        #     }) 
        #     continue
        # if(year_ratio3 <0.2):
        #     continue
        # else:
        #     result.append({"code":code,
        #     "eps_ratio":round(ratio*100,1),
        #     "eps_ratio2":round(ratio2*100,1),
        #     "eps_date":dt_str,
        #     "eps_date2":dt_str2,
        #     "year_eps_date":last_year_dt,
        #     "year_eps_date2":last_year_dt2,
        #     "year_eps_date3":last_year_dt3,
        #     "year_eps_ratio":round(year_ratio*100,1),
        #     "year_eps_ratio2":round(year_ratio2*100,1),
        #     "year_eps_ratio3":round(year_ratio3*100,1)
        #     })
        # print(single_df)
    # # result = sorted(result,key  = lambda d: d["index"])
    # for x in result:
    #     # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s,eps1增长率：%s%%,eps2增长率：%s%%"%(x["secu"], x["security_name"],x["index"],x["value"],math.floor(x["weight"]) ,x["eps_ratio"],x["eps_ratio2"]) )
    #     year_eps_ratio2 = "None"
    #     if x.has_key("year_eps_ratio2"):
    #       year_eps_ratio2 = x["year_eps_ratio2"]
    #       year_eps_ratio2 = x["year_eps_ratio2"]
    #     year_eps_ratio3 = "None"
    #     if x.has_key("year_eps_ratio3"):
    #       year_eps_ratio3 = x["year_eps_ratio3"]
    # #     log.info("%s的最近两个季度eps增长率：%s:%s%%,%s:%s%%，最近年度eps增长率：%s%%,%s%%,%s%%"%(x["code"],
    # #   x["eps_date2"],x["eps_ratio2"],x["eps_date"], x["eps_ratio"],year_eps_ratio3,year_eps_ratio2,x["year_eps_ratio"]))
    #     log.info("%s的最近两个季度eps增长率：%s%%,%s%%，最近年度eps增长率：%s%%,%s%%"%(x["code"],
    #   x["eps_ratio2"], x["eps_ratio"],year_eps_ratio3,year_eps_ratio2))
    return result
    # fileter_securitys = np.zeros(shape = (10))
    # np.append(fileter_securitys,10)

# #获取年度季度eps累计
def get_total_eps_stocks(dt_str,code):
    single_query = query(valuation.code,income.basic_eps,indicator.eps,indicator.statDate,indicator.adjusted_profit_to_profit).filter(valuation.code == code)
    reason = dt_str+"q1"
    eps = 0
    simple_df = get_fundamentals(single_query,statDate=reason)
    if(simple_df.empty):
        return None
    eps = eps+get_adjust_eps(simple_df)
    reason = dt_str+"q2"
    simple_df = get_fundamentals(single_query,statDate=reason)
    if(simple_df.empty):
        return None
    eps = eps+get_adjust_eps(simple_df)
    reason = dt_str+"q3"
    simple_df = get_fundamentals(single_query,statDate=reason)
    if(simple_df.empty):
        return None
    eps = eps+get_adjust_eps(simple_df)
    return eps
# 获取股票n日以来涨幅，根据当前价计算
# n 默认20日

def get_growth_rate(security, n=20):
    lc = get_close_price(security, n)
    #c = data[security].close
    c = get_close_price(security, 1, '1m')
    
    if not isnan(lc) and not isnan(c) and lc != 0:
        return (c - lc) / lc
    else:
        log.error("数据非法, security: %s, %d日收盘价: %f, 当前价: %f" %(security, n, lc, c))
        return 0


# 获取前n个单位时间当时的收盘价
def get_close_price(security, n, unit='1d'):
    return attribute_history(security, n, unit, ('close'), True)['close'][0]

#抽象策略交易类
#1、选股
#2、开仓、加仓
#3、止损离场

class Strategy:
    def __init__(self):
        pass
    def filter_stocks(self):
        pass
    def market_in(self):
        pass
    def market_out(self):
        pass

class StockInfo:
    #初始化，价格信息，eps信息
    def __init__(self, price_info,eps_info):
        self._init_data()
        self.update_info(price_info,eps_info)
    #更新价格
    def update_price_info(self,price_info):
        if(price_info == None):
            return
        self.value = price_info["value"]
        self.index = price_info["index"]
        self.weight = price_info["weight"]

    #更新eps信息
    def update_eps_info(self,eps_info):
        self.code = eps_info["code"]
        if(self.code == None):
            return
        if eps_info.has_key("eps_ratio2"):
           self.eps_ratio2 = eps_info["eps_ratio2"]
        if eps_info.has_key("security_name"):
           self.security_name = eps_info["security_name"]
        if eps_info.has_key("eps_ratio"):
           self.eps_ratio = eps_info["eps_ratio"]
        if eps_info.has_key("market_cap"):
           self.market_cap = eps_info["market_cap"]
        if eps_info.has_key("year_eps_ratio2"):
           self.year_eps_ratio2 = eps_info["year_eps_ratio2"]
        if eps_info.has_key("year_eps_ratio3"):
           self.year_eps_ratio3 = eps_info["year_eps_ratio3"]
        if eps_info.has_key("year_eps_ratio"):
           self.year_eps_ratio = eps_info["year_eps_ratio"]
    #更新
    def update_info(self,price_info,eps_info):
        self.update_price_info(price_info)
        self.update_eps_info(eps_info)

    #初始化
    def _init_data(self):
        self.N = []
        self.year_eps_ratio2 = None
        self.year_eps_ratio3 = None
        self.year_eps_ratio = None
        self.market_cap = 0
        self.portfolio_strategy_short = 0
        self.position_day = 0

    #每日更新当前数据信息
    def run_daily(self,context):
        #唐安琪通道最高最低价的周期不同
        df = attribute_history(self.code,g.short_in_date,"1d",("high","low"))
        self.system_high_short = max(df.high)
        self.system_low_short = min(df.low[g.short_out_date:])

        df = attribute_history(self.code,g.long_in_date,"1d",("high","low"))
        self.system_high_long = max(df.high)
        self.system_low_long = min(df.low)
        self.calculate_n()
        if(self.portfolio_strategy_short!=0):
            self.position_day += 1

    #计算海龟系统N
    def calculate_n(self):
        # 需要考虑停牌，上市交易天数过小,这时候是否需要参与交易
        if(len(self.N) == 0):
            price = attribute_history(self.code, g.number_days*2, '1d',('high','low','close'))
            lst = []
            for i in range(0, g.number_days*2):
                if(np.isnan(price['high'][i])):
                    continue
                high_price = price['high'][i]
                low_price = price['low'][i]
                index = i
                if(i == 0):
                    index = 0
                else:
                    index = i-1
                last_close = price['close'][index]
                h_l = high_price-low_price
                h_c = high_price-last_close
                c_l = last_close-low_price
                # 计算 True Range 取计算第一天的前20天波动范围平均值
                True_Range = max(h_l, h_c, c_l)
                if(len(lst) < g.number_days):
                    lst.append(True_Range)
                else:
                    if(len(self.N) == 0):
                        current_N = np.mean(lst)
                        (self.N).append(current_N)
                    current_N = (True_Range + (g.number_days-1)*(self.N)[-1])/g.number_days
                    (self.N).append(current_N)
        else:
            price = attribute_history(self.code, 2, '1d',('high','low','close'))
            h_l = price['high'][0]-price['low'][0]
            h_c = price['high'][0]-price['close'][1]
            c_l = price['close'][1]-price['low'][0]
            # Calculate the True Range
            True_Range = max(h_l, h_c, c_l)
            # 计算前g.number_days（大于20）天的True_Range平均值，即当前N的值：
            current_N = (True_Range + (g.number_days-1)*(self.N)[-1])/g.number_days
            (self.N).append(current_N)
            del self.N[0]
    #是否突破新高
    def has_break_max(self,close,max_price):
        if(close > max_price):
            return True
        else:
            return False
    #是否创新低
    def has_break_min(self,close,low_price):
        if(close < low_price):
            return True
        else:
            return False

    def start_process(self,context):
        if(len(self.N) == 0):
            return
        self.calculate_unit(context)
        #短时系统操作（买入，加仓，止损，清仓）
        current_data = get_current_data()
        current_price = current_data[self.code].last_price
        cash = context.portfolio.cash
        order_info = None
        if(self.portfolio_strategy_short == 0):
            order_info = self.try_market_in(current_price,cash)
        else:
            order_info = self.try_stop_loss(current_price)
            if(order_info != None):
                return order_info
            order_info = self.try_market_add(current_price, g.ratio*cash)
            if(order_info != None):
                return order_info
            order_info = self.try_market_out(current_price)
            if(order_info != None):
                return order_info
            # order_info = self.try_market_stop_profit(current_price)
            # if(order_info != None):
            #     return order_info
            self.set_appropriate_out_price(current_price)

        return order_info
    #6
    # 入市：决定系统1、系统2是否应该入市，更新系统1和系统2的突破价格
    # 海龟将所有资金分为2部分：一部分资金按系统1执行，一部分资金按系统2执行
    # 输入：当前价格-float, 现金-float, 天数-int
    # 输出：none
    #暂时只考虑一个系统运行情况
    def try_market_in(self,current_price, cash):
       #短时系统操作是否可以入市
        if(self.unit == 0):
            return
        has_break_max = self.has_break_max(current_price,self.system_high_short)
        if(not has_break_max):
            return
        num_of_shares = cash/current_price
        # if num_of_shares < self.unit:
        #     return
        if self.portfolio_strategy_short < int(g.unit_limit*self.unit):
            order_info = order(self.code, int(self.unit))
            # self.portfolio_strategy_short += int(self.unit)
            self.break_price_short = current_price
            self.next_add_price = current_price + 0.5*self.N[-1]
            self.next_out_price = current_price - 2*self.N[-1]
            self.mark_in_price = current_price

            print "开仓！当前价：%s,最高价：%s,N:%s"%(current_price,self.system_high_short,self.N[-1])
            return order_info 
    #7
    # 加仓函数
    # 输入：当前价格-float, 现金-float, 天数-int
    # 输出：none
    def try_market_add(self,current_price, cash):
        # if(self.unit == 0):
        #     return
        break_price = self.break_price_short
        # 每上涨0.5N，加仓一个单元
        if current_price < self.next_add_price: 
            return
        num_of_shares = cash/current_price
        # if num_of_shares < self.unit: 
        #     return
        order_info = order(self.code, int(self.unit))
        # self.portfolio_strategy_short += int(self.unit)
        self.break_price_short = current_price
        self.next_add_price = current_price + 0.5*self.N[-1]
        self.next_out_price = current_price - 2*self.N[-1]
        print "加仓！当前价：%s,上次突破买入价：%s，N:%s,unit:%s,position:%s"%(current_price,break_price,self.N[-1],self.unit,self.portfolio_strategy_short)
        return order_info
    #8
    # 离场函数
    # 输入：当前价格-float, 天数-int
    # 输出：none
    def try_market_out(self,current_price):
        # Function for leaving the market
        has_break_min = self.has_break_min(current_price ,self.system_low_short)
        # 若当前价格低于前out_date天的收盘价的最小值, 则卖掉所有持仓
        if not has_break_min:
            return
        # print min(price['close'])
        if self.portfolio_strategy_short > 0:
            # self.portfolio_strategy_short = 0
            order_info = order(self.code, -self.portfolio_strategy_short)
            print "离场！当前价：%s,最低价：%s，position:%s"%(current_price,self.system_low_short,self.portfolio_strategy_short)
            return order_info

    #15交易日涨幅小于20%退出
    def try_market_stop_profit(self,current_price):
        # Function for leaving the market
        if(self.position_day >=15 and (self.break_price_short - self.mark_in_price)/self.mark_in_price <0.2):
            print "%s交易日未满足涨幅20,入场价：%s,当前价:%s"%(self.position_day,self.mark_in_price,self.break_price_short)
            return order(self.code, -self.portfolio_strategy_short)

    #9
    # 止损函数
    # 输入：当前价格-float
    # 输出：none
    def try_stop_loss(self,current_price):
        # 损失大于2N，卖出股票
        break_price = self.break_price_short
        # If the price has decreased by 2N, then clear all position
        if current_price < self.next_out_price:
            # print break_price - 2*(g.N)[-1]
            # self.portfolio_strategy_short = 0  
            order_info = order(self.code, - self.portfolio_strategy_short)
            print "止损！当前价：%s,上次突破买入价：%s，N:%s,position:%s"%(current_price,break_price,self.N[-1],self.portfolio_strategy_short)
            return order_info

     #更新止损价格
    def set_appropriate_out_price(self,current_price):
        # Function for leaving the market
        self.next_out_price = max(self.next_out_price,current_price - 2*self.N[-1])

    #计算交易单位
    def calculate_unit(self,context):
        value = context.portfolio.total_value
        # 计算波动的价格
        current_N = (self.N)[-1]
        dollar_volatility = g.dollars_per_share*current_N
        # 依本策略，计算买卖的单位
        self.unit = value*0.01/dollar_volatility
        # unit = new_unit - self.portfolio_strategy_short
        # if(unit >=100):
        #     self.unit = unit
        # else:
        #     self.unit = 0

    #加仓数量
    def add_buy_count(self,count):
        self.portfolio_strategy_short += count

     #减仓数量
    def reduce_buy_count(self,count):
        self.portfolio_strategy_short -= count

     #获得仓位数量
    def get_buy_count(self):
        return self.portfolio_strategy_short

     #设置仓位数量
    def set_buy_count(self,count):
        self.portfolio_strategy_short = count

    def __str__(self):
        # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s,最近两个季度eps增长率：%s%%,%s%%,市值：%s"%(self.code,
        # self.security_name,self.index,self.value, self.weight ,self.eps_ratio2,self.eps_ratio,self.market_cap))
        return ""
#股票管理类
class StockManager():
    def __init__(self):
        pass
    def init_data(self):
        self.daliy_pool = []
        pass
    def daily_process(self):
        pass
    def daily_end(self):
        pass