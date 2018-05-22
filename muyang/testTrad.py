#1、价格强势股的当前价格是否需要实时计算？√
#2、海龟交易的计算起始日期是否是根据当前交易开始日期累计，还是往前推
#3、需要考虑停牌，上市交易天数过小,这时候是否需要参与交易

enable_profile()
from jqdata import jy
import jqdata
import numpy as np
import pandas as pd
import math

from sqlalchemy import or_
from jy_sw_industry_code import *

jydf = jy.run_query(query(jy.SecuMain))

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

    g.unit = 1000
    # A list storing info of N
    g.N = []
    # Record the number of days for this trading system
    g.days = 0
    # 系统1的突破价格
    g.break_price1 = 0
    # 系统2的突破价格
    g.break_price2 = 0
    # 系统1建的仓数
    g.sys1 = 0
    # 系统2建的仓数
    g.sys2 = 0
    # 系统1执行且系统2不执行
    g.system1 = True

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

    # g.debug_stocks = ["000729.XSHE"]
    g.debug_stocks = None

    init_turtle_data()

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

def before_trading_start(context):
    cur_date = context.current_dt
    g.all_trade_days = jqdata.get_trade_days(count = 300)
    start_date = g.all_trade_days[-g.industry_rangeDays]
    sortedList_level1 = get_ratioandsort(SW1,start_date,cur_date)
    sortedList_level2 = get_ratioandsort(SW2,start_date,cur_date)
    mighty_price_list = get_mighty_price_stocks(context,data,sortedList_level1,sortedList_level2)
    mighty_eps_list = get_mighty_eps_stocks(context,g.debug_stocks)
    result = []
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
                stInfo = StockInfo(price_stock,eps_stock)
                result.append(stInfo)
                # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s,最近两个季度eps增长率：%s%%,%s%%"%(stock,
                # price_stock["security_name"],price_stock["index"],price_stock["value"], price_stock["weight"] ,eps_stock["eps_ratio2"], 
                # eps_stock["eps_ratio"]))
    gr_index2 = get_growth_rate("000016.XSHG")
    gr_index8 = get_growth_rate("399333.XSHE")
    if(gr_index8<gr_index2):
        log.info("当前大盘强于小盘",gr_index2,gr_index8)
    else:
        log.info("当前小盘强于大盘",gr_index2,gr_index8)
    g.valid_stocks = sorted(result,key = lambda d: d.market_cap,reverse = gr_index2>gr_index8)
    for single in g.valid_stocks:
        print(single)
        single.calculate_n()
    # return g.valid_stocks

def handle_data(context, data):
    

def common_get_weight(list):
    size = len(list)
    for index in range(len(list)):
        x = list[index]    
        # value =  (index+1)*(99/(1-size))+100-(99/(1-size))
        value = index*(99.0/(1-size))+100
        x["weight"] = round(value,1)
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

# 获取价格强势股
def get_mighty_price_stocks(context,data,sw1dict,sw2dict):
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
        
        stock_score = x["weight"]
        if(security_name is not None and close>security_avg1 
            and security_avg1>security_avg2 
            and security_avg2>security_avg3
            and close>min_close*1.1
            and close>max_close*0.7
            and stock_score >87):
            if(security_name["display_name"].size == 0):
                #  log.info("name 为空",security,security_name,sw1mapdf)
                 continue
            security_name = security_name["display_name"][0]
            # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s"%(x["secu"],security_name,index,x["value"],x["weight"] ) )
            x["index"] = index
            x["security_name"] = security_name
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
        print(str.format("eps:%s,rps:%s,eps:%s"%(cldata.eps,cldata.adjusted_profit_to_profit,eps)))
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
        print(str.format("eps:%s,eps2:%s,eps3:%s"%(last_eps,last_eps2,last_eps3)))
        ratio = (eps - last_eps)/last_eps
        ratio2 = (last_eps2 - last_eps3)/last_eps3
        # x["eps_ratio"] = math.floor(ratio*100)
        # x["eps_ratio2"] = math.floor(ratio2*100)
        if(ratio<0.2 or ratio2 <0.2):
            continue
        result.append({"code":code,
        "eps_ratio":round(ratio*100,1),
        "eps_ratio2":round(ratio2*100,1),
        "eps_date":dt_str,
        "eps_date2":dt_str2,
        "market_cap":market_cap
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
class StockInfo:
    # def __init__(self, eps_ratio,eps_ratio2,year_eps_ratio, year_eps_ratio2):
    #     self.eps_ratio = eps_ratio
    #     self.eps_ratio2 = eps_ratio2
    #     self.year_eps_ratio = year_eps_ratio
    #     self.year_eps_ratio2 = year_eps_ratio2
    # def __init__(self, data):
    #     self.eps_ratio = data["eps_ratio"]
    #     self.eps_ratio2 = data["eps_ratio2"]
    #     self.year_eps_ratio = data["year_eps_ratio"]
    #     self.year_eps_ratio2 = data["year_eps_ratio2"]
    def __init__(self, price_stock,eps_stock):
        self.year_eps_ratio2 = None
        if eps_stock.has_key("year_eps_ratio2"):
           self.year_eps_ratio2 = eps_stock["year_eps_ratio2"]
        self.year_eps_ratio3 = None
        if eps_stock.has_key("year_eps_ratio3"):
           self.year_eps_ratio3 = eps_stock["year_eps_ratio3"]
        self.year_eps_ratio = None
        if eps_stock.has_key("year_eps_ratio"):
           self.year_eps_ratio = eps_stock["year_eps_ratio"]
        self.code = eps_stock["code"]
        self.eps_ratio2 = eps_stock["eps_ratio2"]
        self.eps_ratio = eps_stock["eps_ratio"]
        self.value = price_stock["value"]
        self.security_name = price_stock["security_name"]
        self.index = price_stock["index"]
        self.weight = price_stock["weight"]
        self.market_cap = eps_stock["market_cap"]
        self._init_data()

    def _init_data(self):
        self.N = []
        self.portfolio_strategy_1 = 0
        self.portfolio_strategy_2 = 0
        df = attribute_history(self.code,g.short_in_date,"1d",("high","low"))
        self.system_high_short = max(df.high)
        self.system_low_short = min(df.low)

        df = attribute_history(self.code,g.long_in_date,"1d",("high","low"))
        self.system_high_long = max(df.high)
        self.system_low_long = min(df.low)

    #计算海龟系统N
    def calculate_n(self):
        # 需要考虑停牌，上市交易天数过小,这时候是否需要参与交易
        if(len(self.N) == 0):
            price = attribute_history(self.code, g.number_days*2, '1d',('high','low','close'))
            lst = []
            for i in range(0, g.number_days*2):
                if(np.isnan(price['high'])):
                    continue
                h_l = price['high'][i]-price['low'][i]
                h_c = price['high'][i]-price['close'][i]
                c_l = price['close'][i]-price['low'][i]
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
            price = attribute_history(self.code, 1, '1d',('high','low','close'))
            h_l = price['high'][0]-price['low'][0]
            h_c = price['high'][0]-price['close'][0]
            c_l = price['close'][0]-price['low'][0]
            # Calculate the True Range
            True_Range = max(h_l, h_c, c_l)
            # 计算前g.number_days（大于20）天的True_Range平均值，即当前N的值：
            current_N = (True_Range + (g.number_days-1)*(g.N)[-1])/g.number_days
            (self.N).append(current_N)
    #是否突破新高
    def has_break_max(self,max_price):
        current_data = get_current_data()
        close = current_data[self.code].last_price
        if(close > max_price):
            return True
        else:
            return False
    #是否创新低
    def has_break_min(self,low_price):
        current_data = get_current_data()
        close = current_data[self.code].last_price
        if(close < low_price):
            return True
        else:
            return False

    #尝试买入
    def try_buy(self,context):
        #短时系统操作（买入，加仓，止损，清仓）
        if(self.portfolio_strategy_short == 0):
            unit,cash = self.calculate_unit(context)
            # Build position if current price is higher than highest in past
            current_data = get_current_data()
            current_price = current_data[self.code].last_price
            has_break_max = self.has_break_max(self.system_high_short)
            if(has_break_max):
            num_of_shares = cash/current_price
            if num_of_shares >= unit:
                    if g.sys1 < int(g.unit_limit*g.unit):
                        order(g.security, int(g.unit))
                        g.sys1 += int(g.unit)
                        g.break_price1 = current_price
                else:
                    if g.sys2 < int(g.unit_limit*g.unit):
                        order(g.security, int(g.unit))
                        g.sys2 += int(g.unit)
                        g.break_price2 = current_price
        else:

        else:

    #计算交易单位
    def calculate_unit(self,context):
        value = context.portfolio.portfolio_value
        # 可花费的现金
        cash = context.portfolio.cash 
        if self.portfolio_strategy_1 == 0 and self.portfolio_strategy_1 == 0:
            # 若损失率大于g.loss，则调整（减小）可持有现金和总价值
            if value < (1-g.loss)*context.portfolio.starting_cash:
                cash *= g.adjust
                value *= g.adjust
         # 计算波动的价格
        dollar_volatility = g.dollars_per_share*(self.N)[-1]
        # 依本策略，计算买卖的单位
        unit = value*0.01/dollar_volatility
        return unit,cash

   def __str__(self):
        log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s,最近两个季度eps增长率：%s%%,%s%%,市值：%s"%(self.code,
        self.security_name,self.index,self.value, self.weight ,self.eps_ratio2,self.eps_ratio,self.market_cap))
        return ""
