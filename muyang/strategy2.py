#coding: utf-8
from jqdata import jy
from jqdata import *
import pandas as pd
import numpy as np
import Utils
import talib as tb
from NewIndustryClass import *

# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    # 000001(股票:平安银行)
    g.security = '000001.XSHE'
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)

    #做排序
def get_sw_industry_stocks(name,datetime,count,history_data,current_data):
    codes = get_industries(name).index;
    panel_industry = Utils.get_sw_quote(codes,end_date=datetime,count=count)
    industry_closes = panel_industry.ClosePrice
    industry_names = panel_industry.ChiName
    series_market_closes = get_mightlymarket_closes(datetime,count)
    df_close = history_data["close"]
    df_volume = history_data["volume"]
    print(df_close)
    series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
    for i in range(len(codes)):
        industry_code = codes[i]
        if(not industry_code in industry_closes.columns):
            continue
        # industry_close = industry_closes[industry_code]
        industry_name = industry_names[industry_code][-1]
        securities = get_industry_stocks(industry_code)
     
        stock_infos = list()
        for security in securities:
            if(not security in series_increase or current_data[security].paused):
                continue
            increase = round(series_increase[security],4)
            stock_close = df_close[security]
            series_rs = stock_close/series_market_closes
            # print(series_rs)
            ema_rs = round(tb.EMA(np.array(series_rs),39)[-1],4)
            volume = df_volume[security][-1]
            cur_rs = round(series_rs[-1],4)
            close_price = stock_close[-1]
            stock_info = StockInfo(security,industry_code,industry_name,name)
            stock_info.set_data(increase,close_price,stock_close,cur_rs,ema_rs,volume)
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
                print(stock_info)
                new_industry.add_stockinfo(stock_info)
        if(pick_count>0):
            check_rs = new_industry.check_ema_rs(series_market_closes)
            if(check_rs):
                g.new_industries.append(new_industry)



def get_mightlymarket_closes(datetime,count):
    codes = ["000001.XSHG","399006.XSHE","399005.XSHE"]
    panel = get_price(codes,end_date = datetime,count = count,fields = ["close"])
    df_close = panel["close"]
    series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
    max_value = -1
    max_code = None
    for code in codes:
        if(series_increase[code]>max_value):
            max_value = series_increase[code]
            max_code = code
    return df_close[max_code]

def handle_data(context,data):
    count = 240
    end_date = context.current_dt - timedelta(days = 1)
    securities = list()
    for industry in g.new_industries:
        for stock_info in industry.stock_infos:
            securities.append(stock_info.security)
    history_data = get_price(security = securities,end_date = end_date,count = count,fields = ['close','volume'])
    series_market_closes = get_mightlymarket_closes(end_date,count)
    df_close = history_data["close"]
    df_volume = history_data["volume"]
    series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
    for industry in g.new_industries:
        for stock_info in industry.stock_infos:
            security = stock_info.security
            if(data[security].paused):
                continue
            increase = round(series_increase[security],4)
            stock_close = df_close[security]
            series_rs = stock_close/series_market_closes
            ema_rs = round(tb.EMA(np.array(series_rs),39)[-1],4)
            volume = df_volume[security][-1]
            cur_rs = round(series_rs[-1],4)
            close_price = stock_close[-1]
            stock_info.set_data(increase,close_price,stock_close,cur_rs,ema_rs,volume)
            # print(stock_info)
        industry.check_ema_rs(series_market_closes)
def initialize(context):
    g.new_industries = list()
    run_monthly(monthly_function,monthday = 1,time = "before_open")

def monthly_function(context):
    del g.new_industries[:]
    current_dt = context.current_dt
    end_date = current_dt - timedelta(days = 1)
    start_date = current_dt - timedelta(days = 400)
    start_date = start_date.date()
    current_data = get_current_data()
    securities_df = get_all_securities()
    securities_df = securities_df[securities_df["start_date"] <= start_date]
    securities = securities_df.index.tolist()
    history_data = get_price(security = securities,end_date = end_date,count = 240,fields = ['close','volume'])
    get_sw_industry_stocks("sw_l1",end_date,240,history_data,current_data)
    # get_sw_industry_stocks("sw_l2",end_date,240,history_data,current_data)
    
