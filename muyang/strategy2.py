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
    if isinstance(codes,str):
        codes=[codes]
    days = get_trade_days(start_date,end_date,count)
    code_df = jy.run_query(query(
         jy.SecuMain.InnerCode,jy.SecuMain.SecuCode).filter(
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
def get_sw_industry_stocks(name,datetime,count):
    codes = get_industries(name).index;
    panel_industry = get_sw_quote(codes,end_date=datetime,count=count)
    industry_closes = panel_industry.ClosePrice
    series_market_closes = get_mightlymarket_closes(datetime,count)
    for i in range(len(codes)):
        industry_code = codes[i]
        if(not industry_code in industry_closes.columns):
            continue
        industry_close = industry_closes[industry_code]
        securities = get_industry_stocks(industry_code)
        panel = get_price(security = securities,end_date = datetime,count = count,fields = ['pre_close','close','volume'])
        df_preclose = panel["pre_close"]
        df_close = panel["close"]
        df_volume = panel["volume"]
        df = (df_close - df_preclose)/df_preclose
        stock_infos = list()
        for security in securities:
            increase = df[security][-1]
            stock_close = df_close[security]
            series_rs = stock_close/industry_close
            ema_rs = tb.EMA(np.array(series_rs),39)
            volume = df_volume[security][-1]
            cur_rs = series_rs[-1]
            close_price = stock_close[-1]
            stock_info = StockInfo(security,close_price,industry_code,name)
            stock_info.init_data(increase,cur_rs,ema_rs,volume)
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
                new_industry.set_market_closes(series_market_closes)

def initialize(context):
    run_daily(get_lastday_increase)

def get_mightlymarket_closes(datetime,count):
    codes = ["000001.XSHG","399006.XSHE","399005.XSHE"]
    panel = get_price(codes,end_date = datetime,count = count,filter = ["close,pre_close"])
    df = panel["close"]
    pre_df = panel["pre_close"]
    series_increase = (df.iloc[-1] - pre_df.iloc[-1])/pre_df.iloc[-1]
    max_value = -1
    max_code = None
    for code in codes:
        if(series_increase[code]>max_value):
            max_value = series_increase[code]
            max_code = code
    return df[max_code]

def get_lastday_increase(context):
    print("get_lastday_increase",context.current_dt)
    pass

def handle_data(context,data):
    current_dt = context.current_dt
    end_date = current_dt - timedelta(days = 1)
    get_sw_industry_stocks("sw_l1",end_date,60)
    get_sw_industry_stocks("sw_l2",end_date,60)

class StockInfo:
    def __init__(self,security,industry,swl):
        self.security = security
        self.industry = industry
        self.swl = swl
        pass
    def init_data(self,increase,close_price,cur_rs,ema_rs,volume):
        self.increase = increase
        self.close_price = close_price
        self.cur_rs = cur_rs
        self.ema_rs = ema_rs[-1]
        self.volume = volume
    def __str__(self):
        value = "name:%s,increase:%s,cur_rs:%s,ema_rs:%s"%(self.security,self.increase,self.cur_rs,self.ema_rs)
        return value
class CustomIndustry:
    def __init__(self,industry):
        self.industry = industry
        self.stock_infos = list()
        self.value = 0
    def init_data(self):
        pass
    def set_market_closes(series_market_closes):
        
        
    def add_stockinfo(self,stock_info):
        self.stock_infos.append(stock_info)
    def get_value(self):
        if(self.value != 0):
            return self.value
        for stock_info in self.stock_infos:
            self.value += stock_info.close_price
        self.value = round(self.value/len(self.stock_infos),2)
    def __str__(self):
        return "CustomIndustry"