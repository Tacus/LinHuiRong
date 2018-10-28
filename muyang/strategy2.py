from jqdata import jy
from jqdata import *
import pandas as pd
import numpy as np
import Utils
import talib as tb
import NewIndustryClass

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
    offset = 0
    achive_count = len(df)
    while achive_count>0:
        offset += achive_count
        temp_df = jy.run_query(query(
             jy.QT_SYWGIndexQuote.InnerCode,jy.QT_SYWGIndexQuote.ClosePrice,jy.QT_SYWGIndexQuote.TradingDay).filter(
            jy.QT_SYWGIndexQuote.InnerCode.in_(code_df.InnerCode),
            jy.QT_SYWGIndexQuote.TradingDay.in_(days),
            )).offset(offset)
        achive_count = len(temp_df)
        df.append(temp_df)
    df2  = pd.merge(code_df, df, on='InnerCode',copy = False).set_index(['TradingDay','SecuCode'])
    df2.drop(['InnerCode'],axis=1,inplace=True)
    return df2.to_panel()
    
    #做排序
def get_sw_industry_stocks(name,datetime,count,history_data,current_data):
    codes = get_industries(name).index;
    panel_industry = Utils.get_sw_quote(industry_code,end_date=datetime,count=count)
    industry_closes = panel_industry.ClosePrice
    industry_names = panel_industry.ChiName
    series_market_closes = get_mightlymarket_closes(datetime,count)
    df_close = history_data["close"]
    df_volume = history_data["volume"]
    series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
    for i in range(len(codes)):
        industry_code = codes[i]
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
            ema_rs = round(tb.EMA(np.array(series_rs),39)[-1],2)
            volume = df_volume[security][-1]
            cur_rs = round(series_rs[-1],2)
            close_price = stock_close[-1]
            stock_info = StockRSData(security,industry_code,industry_name,name)
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
    start_date = current_dt - timedelta(days = 400)
    current_data = get_current_data()
    securities_df = get_all_securities()
    securities_df = securities_df[securities_df.start_date <= start_date]
    securities = securities_df.index
    history_data = get_price(security = securities,end_date = end_date,count = 240,fields = ['close','volume'])

    get_sw_industry_stocks("sw_l1",end_date,240,history_data,current_data)
    get_sw_industry_stocks("sw_l2",end_date,240,history_data,current_data)

    for industry in g.new_industries:
        for stock_info in industry.stock_infos:
            print(stock_info)
