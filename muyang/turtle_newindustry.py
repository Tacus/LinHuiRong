#coding = utf-8
######### rs选股-海龟交易 #########

#coding: utf-8
from jqdata import jy
from jqdata import *
import pandas as pd
import numpy as np
import Utils
import talib as tb
from NewIndustryClass import *



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
    for _,stock_info in g.position_pool.items():
        order = stock_info.update(context)

        if order != None and order.filled  > 0 and order.is_buy :
            stock_info.add_buy_count( order.filled)
        elif(order != None and order.filled > 0 and not order.is_buy):
            stock_info.reduce_buy_count( order.filled)
            count = stock_info.get_buy_count()
            if(count <= 0):
                del g.position_pool[stock_info.code]

    for single in g.stock_pool:
        order = single.update(context)
        if order != None and order.filled  > 0 and order.is_buy :
            single.set_buy_count( order.filled)
            g.stock_pool.remove(single)
            g.position_pool[single.code] = single


def initialize(context):
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    g.period = 240
    g.first_run = True
    g.new_industries = list()
    g.strategy = TurtleStrategy(g.period)
    run_monthly(monthly_function,monthday = 1,time = "before_open")
    run_daily(daily_function,monthday = 1,time = "before_open")

def daily_function(context):
	g.strategy.daily_function(context)
    

def monthly_function(context):
	g.strategy.monthly_function(context)
    del g.new_industries[:]
    current_dt = context.current_dt
    end_date = current_dt - timedelta(days = 1)
    start_date = current_dt - timedelta(days = 400)
    start_date = start_date.date()
    current_data = get_current_data()
    securities_df = get_all_securities()
    securities_df = securities_df[securities_df["start_date"] <= start_date]
    securities = securities_df.index.tolist()
    count = g.period
    history_data = get_price(security = securities,end_date = end_date,count = count,fields = ['close','volume'])
    get_sw_industry_stocks("sw_l1",end_date,count,history_data,current_data)
        
class BaseStrategy(object):
	"""docstring for BaseStrategy"""
	def __init__(self, arg):
		super(BaseStrategy, self).__init__()
		self.arg = arg

	def pick_stocks(self):
		return None

	def start_trade(self):
		pass

	def check_sell(self):
		pass

	def check_buy(self):
		pass

	def daily_function(self):
		pass

	def monthly_function(self):
		pass

	def handle_data(self,context,data):
		pass


class TurtleStrategy(BaseStrategy):
	"""docstring for TurtleStrategy"""
	def __init__(self, trading_period):
		super(TurtleStrategy, self).__init__()
		self.trading_period = trading_period
		self.first_run = True  #是否选股后第一次运行
	
	def pick_stocks(self,context):
		del self.new_industries[:]
		current_dt = context.current_dt
		end_date = current_dt - timedelta(days = 1)
		start_date = current_dt - timedelta(days = 400)
		start_date = start_date.date()
		current_data = get_current_data()
		securities_df = get_all_securities()
		securities_df = securities_df[securities_df["start_date"] <= start_date]
		securities = securities_df.index.tolist()
		count = self.trading_period
		history_data = get_price(security = securities,end_date = end_date,count = count,fields = ['close','volume'])
		pick_strong_stocks("sw_l1",end_date,count,history_data,current_data)

	def monthly_function(self,context):
		self.pick_stocks(context)



	def daily_function(self,context):
		if(g.fir or 0 == len(g.new_industries)):
		    return
		g.first_run = False
		count = g.period
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
		        stock_close = df_close[security]
		        series_rs = stock_close/series_market_closes
		        cur_ema_rs = round(tb.EMA(np.array(series_rs),39)[-1],4)

		        # increase = round(series_increase[security],4) #deprecate
		        ref_ema_rs30 = series_rs[-30]
		        c30 = (cur_ema_rs - ref_ema_rs30)/ref_ema_rs30

		        ref_ema_rs60 = series_rs[-60]
		        c60 = (ref_ema_rs30 - ref_ema_rs60)/ref_ema_rs60
		        
		        ref_ema_rs90 = series_rs[-90]
		        c90 = (ref_ema_rs60 - ref_ema_rs90)/ref_ema_rs90

		        ref_ema_rs120 = series_rs[-120]
		        c120 = (ref_ema_rs90 - ref_ema_rs120)/ref_ema_rs120

		        stock_strength = ((1+c120*0.8)*(1+c90*0.8)*(1+c60*0.8)*(1+c30*1.6)-1)*100

		        volume = df_volume[security][-1]
		        cur_rs = round(series_rs[-1],4)
		        close_price = stock_close[-1]
		        # stock_info.set_data(increase,close_price,stock_close,cur_rs,cur_ema_rs,volume)
		        stock_info.set_data(stock_strength,close_price,stock_close,cur_rs,cur_ema_rs,volume)


		#唐安琪通道最高最低价的周期不同
		df = attribute_history(self.code,g.short_in_date,"1d",("high","low"))
		self.system_high_short = max(df.high)
		self.system_low_short = min(df.low[g.short_out_date:])

		df = attribute_history(self.code,g.long_in_date,"1d",("high","low"))
		self.system_high_long = max(df.high)
		self.system_low_long = min(df.low)

		#获取今日该股最高价与上证最高价求得rs（未来函数）
		df = get_price(["000001.XSHG",self.code],end_date = context.current_dt,count = 1,frequency = "1d",fields = ("high"))
		sh_close = df.high["000001.XSHG"][0]
		se_close = df.high[self.code][0]
		self.rs_data.update_daily(se_close,sh_close)

		self.calculate_n()
		if(self.portfolio_strategy_short!=0):
		    self.position_day += 1

	def start_trade(self,context,data):
		pass

	def handle_data(self,context,data):
		self.start_trade(context,data)

	def get_strong_stocks(name,datetime,count,history_data,current_data):
	    codes = get_industries(name).index;
	    panel_industry = Utils.get_sw_quote(codes,end_date=datetime,count=count)
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
	        # industry_close = industry_closes[industry_code]
	        industry_name = industry_names[industry_code][-1]
	        securities = get_industry_stocks(industry_code)
	     
	        stock_infos = list()
	        for security in securities:
	            if(not security in series_increase or current_data[security].paused):
	                continue

	            stock_close = df_close[security]
	            series_rs = stock_close/series_market_closes
	            cur_ema_rs = round(tb.EMA(np.array(series_rs),39)[-1],4)
	            # increase = round(series_increase[security],4)

	            ref_ema_rs30 = series_rs[-30]
	            c30 = (cur_ema_rs - ref_ema_rs30)/ref_ema_rs30

	            ref_ema_rs60 = series_rs[-60]
	            c60 = (ref_ema_rs30 - ref_ema_rs60)/ref_ema_rs60
	            
	            ref_ema_rs90 = series_rs[-90]
	            c90 = (ref_ema_rs60 - ref_ema_rs90)/ref_ema_rs90

	            ref_ema_rs120 = series_rs[-120]
	            c120 = (ref_ema_rs90 - ref_ema_rs120)/ref_ema_rs120

	            stock_strength = ((1+c120*0.8)*(1+c90*0.8)*(1+c60*0.8)*(1+c30*1.6)-1)*100#计算个股强度

	            volume = df_volume[security][-1]
	            cur_rs = round(series_rs[-1],4)
	            close_price = stock_close[-1]
	            stock_info = StockInfo(security,industry_code,industry_name,name)
	            stock_info.set_data(stock_strength,close_price,stock_close,cur_rs,cur_ema_rs,volume)
	            stock_infos.append(stock_info)
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
	            new_industry.check_ema_rs(series_market_closes)
	            self.new_industries.append(new_industry)
