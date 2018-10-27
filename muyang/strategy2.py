from jqdata import jy
from jqdata import *
import pandas as pd
import numpy as np
import talib as tb

# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    # 000001(股票:平安银行)
    g.security = '000001.XSHE'
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)


def get_sw_quote(codes,end_date=None,count=None,start_date=None):
    '''获取申万指数行情,返回panel结构'''
    if isinstance(codes,unicode):
        codes=[codes]
    days = get_trade_days(start_date,end_date,count)
    code_df = jy.run_query(query(
         jy.SecuMain.InnerCode,jy.SecuMain.SecuCode,jy.SecuMain.ChiName).filter(
        jy.SecuMain.SecuCode.in_(codes)))
    
    df = jy.run_query(query(
         jy.QT_SYWGIndexQuote.InnerCode,jy.QT_SYWGIndexQuote.ClosePrice,jy.QT_SYWGIndexQuote.TradingDay).filter(
        jy.QT_SYWGIndexQuote.InnerCode.in_(code_df.InnerCode),
        jy.QT_SYWGIndexQuote.TradingDay.in_(days),
        ))
    df2  = pd.merge(code_df, df, on='InnerCode').set_index(['TradingDay','SecuCode'])
    df2.drop(['InnerCode'],axis=1,inplace=True)
    return df2.to_panel()
    
    #做排序
def get_sw_industry_stocks(name,datetime,count,history_data,current_data):
    codes = get_industries(name).index;
    series_market_closes = get_mightlymarket_closes(datetime,count)
    df_close = history_data["close"]
    df_volume = history_data["volume"]
    series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
    for i in range(len(codes)):
        industry_code = codes[i]
        panel_industry = get_sw_quote(industry_code,end_date=datetime,count=count)
        industry_closes = panel_industry.ClosePrice
        industry_names = panel_industry.ChiName
        if(not industry_code in industry_closes.columns):
            continue
        industry_close = industry_closes[industry_code]
        industry_name = industry_names[industry_code][-1]
        securities = get_industry_stocks(industry_code)
     
        stock_infos = list()
        for security in securities:
            if(current_data[security].paused):
                continue
            increase = round(series_increase[security],2)
            stock_close = df_close[security]
            series_rs = stock_close/industry_close
            # print(security,industry_code,series_rs)
            ema_rs = round(tb.EMA(np.array(series_rs),39)[-1],2)
            volume = df_volume[security][-1]
            cur_rs = round(series_rs[-1],2)
            close_price = stock_close[-1]
            stock_info = StockInfo(security,industry_code,industry_name,name)
            stock_info.init_data(increase,close_price,stock_close,cur_rs,ema_rs,volume)
            stock_infos.append(stock_info)
            # stock_info
        stock_infos = sorted(stock_infos,key = lambda data: data.increase,reverse = True)
        pick_count = 0
        new_industry = CustomIndustry(industry_code)
        for stock_info in stock_infos:
            cur_rs = stock_info.cur_rs
            ema_rs = stock_info.ema_rs
            if(pick_count >= 5):
                break
            if(cur_rs>ema_rs):
                pick_count+=1
                new_industry.add_stockinfo(stock_info)
        if(pick_count>0):
            check_rs = new_industry.check_ema_rs(series_market_closes)
            if(check_rs):
                g.new_industries.append(new_industry)


def common_get_weight(list):
    size = len(list)
    for index in range(size):
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
    closePrice_pre = None
    closePrice_close = None
    while len(df) > 0 :
        dflist = list(df.itertuples(index=False))
        for array in dflist :
            if(array[2] != currentSecuCode):
                if(currentSecuCode != None):
                    ratio = (closePrice_close - closePrice_pre)/closePrice_pre 
                    securitys.append({"secu":series.loc(currentSecuCode),"value":ratio})
                closePrice_pre = array[0]
                
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


def get_mightlymarket_closes(datetime,count):
    codes = ["000001.XSHG","399006.XSHE","399005.XSHE"]
    panel = get_price(codes,end_date = datetime,count = count,fields = ["close"])
    df = panel["close"]
    series_increase = (df.iloc[-1] - df.iloc[0])/df.iloc[0]
    max_value = -1
    max_code = None
    for code in codes:
        if(series_increase[code]>max_value):
            max_value = series_increase[code]
            max_code = code
    return df[max_code]

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
    
    result = get_price(secuData, None, context.current_dt, str(g.stock_rangeDays)+"d", ["pre_close","close"], False, "pre", 1)
    # result.fillnan(0)
    securitys = list()
    resultRatio = (result["close"] - result["pre_close"])/result["pre_close"]
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
        # display_name = sw1mapdf.loc[x["secu"]]
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
 
            # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s"%(x["secu"],display_name,index,x["value"],x["weight"] ) )
            x["index"] = index
            index += 1
            fileter_securitys[x["secu"]] = x
            stocks.append(x["secu"])
            if(index > num):
                break
        
        # else:
        #     display_name = "已退市"
        # log.info("%s（%s）的排名为：%s,分数为：%s"%(x["secu"],display_name,index,x["value"] ) )
        # index +=1
    # for i in arrange
    # (result)
    return fileter_securitys

def handle_data(context,data):
    pass
def initialize(context):
    g.new_industries = list()
    run_daily(daily_function)

def daily_function(context):
    print("get_lastday_increase",context.current_dt)
    del g.new_industries[:]
    current_dt = context.current_dt
    end_date = current_dt - timedelta(days = 1)
    current_data = get_current_data()
    securities = get_all_securities().index.tolist()
    history_data = get_price(security = securities,end_date = end_date,count = 240,fields = ['close','volume'])

    get_sw_industry_stocks("sw_l1",end_date,240,history_data,current_data)
    get_sw_industry_stocks("sw_l2",end_date,240,history_data,current_data)

    for industry in g.new_industries:
        for stock_info in industry.stock_infos:
            print(stock_info)
