#coding: utf-8
from jqdata import jy
from jqdata import *
import pandas as pd
import numpy as np
import Utils
import talib as tb
from StockRSData import *

def initialize(context):
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

def after_market_close(context):
    pick_stocks(context);
    
def pick_stocks(context):
	current_dt = context.current_dt
	end_date = current_dt
	start_date = current_dt - timedelta(days = 400)
	start_date = start_date.date()
	current_data = get_current_data()
	securities_df = get_all_securities()
	securities_df = securities_df[securities_df["start_date"] <= start_date]
	securities = securities_df.index.tolist()
	count = 240
	history_data = get_price(security = securities,end_date = end_date,count = count,fields = ['close','volume'])
	pick_strong_stocks("sw_l1",end_date,count,history_data,current_data)
	
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
	
def pick_strong_stocks(name,datetime,count,history_data,current_data):
	codes = get_industries(name).index;
	panel_industry = Utils.get_sw_quote(codes,end_date=datetime,count=count)
	industry_closes = panel_industry.ClosePrice
	industry_names = panel_industry.ChiName
	# series_market_closes = get_mightlymarket_closes(datetime,count)
	df_close = history_data["close"]
	df_volume = history_data["volume"]
	series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
	current_data = get_current_data()
	stock_infos = list()
	for i in range(len(codes)):
		industry_code = codes[i]
		if(not industry_code in industry_closes.columns):
			continue
		# industry_close = industry_closes[industry_code]
		industry_name = industry_names[industry_code][-1]
		securities = get_industry_stocks(industry_code)
	 
		for security in securities:
			if(not security in series_increase or current_data[security].paused):
				continue

			stock_close = df_close[security]
			# series_rs = stock_close/series_market_closes
			# series_rs = stock_close/series_market_closes
			# cur_ema_rs = round(tb.EMA(np.array(stock_close),39)[-1],4)
			cur_ema_rs = stock_close[-1]
			# increase = round(series_increase[security],4)

			ref_ema_rs30 = stock_close[-60]
			c30 = (cur_ema_rs - ref_ema_rs30)/ref_ema_rs30

			ref_ema_rs60 = stock_close[-120]
			c60 = (ref_ema_rs30 - ref_ema_rs60)/ref_ema_rs60
			
			ref_ema_rs90 = stock_close[-180]
			c90 = (ref_ema_rs60 - ref_ema_rs90)/ref_ema_rs90

			ref_ema_rs120 = stock_close[-240]
			c120 = (ref_ema_rs90 - ref_ema_rs120)/ref_ema_rs120

			stock_strength = ((1+c120*0.8)*(1+c90*0.8)*(1+c60*0.8)*(1+c30*1.6)-1)*100#计算个股强度

			volume = df_volume[security][-1]
			cur_rs = round(stock_close[-1],4)
			close_price = stock_close[-1]
			security_name = current_data[security].name
			stock_info = StockInfo(security,security_name,industry_code,industry_name)
			stock_info.set_data(stock_strength,close_price,stock_close,cur_rs,cur_ema_rs,volume)
			stock_info.init_rs_data(stock_close)
			stock_infos.append(stock_info)
	stock_infos = sorted(stock_infos,key = lambda data: data.increase,reverse = True)
	pick_count = 0
	new_industry = CustomIndustry(industry_code)
	for stock_info in stock_infos:
		cur_rs = stock_info.cur_rs
		ema_rs = stock_info.ema_rs
		# if(pick_count >= 5):
		# 	break
		# if(cur_rs>ema_rs):
		pick_count+=1
		print(stock_info)
		new_industry.add_stockinfo(stock_info)

		# if(pick_count>0):
		# 	new_industry.check_ema_rs(series_market_closes)
# 			self.new_industries.append(new_industry)



class BaseClass(object):
	def __init__(self):
		self.tag = self.__class__.__name__

class StockInfo(BaseClass):
	def __init__(self,code,name,industry_code,industry_name):
		super(StockInfo,self).__init__()
		self.code = code
		self.name = name
		self.industry_code = industry_code
		self.industry_name = industry_name

		self.dollars_per_share = 1
		self.portfolio_strategy_short = 0
		self.position_day = 0

		# 系统1所配金额占总金额比例
		self.ratio = 0.8
		#加仓系数 例如：1N/0.5N
		self.add_ratio = 1
		# 最大允许单元
		self.unit_limit = 4
		#M日涨幅要求--20日涨幅20%
		self.increase_period = 20

		self.rs_period = 250
		self.tight_out = True
		self.N = list()

		#更新rs数据
	def init_rs_data(self,rs):
	    self.rs_data = StockRSData(self.code,self.rs_period)
	    self.rs_data.set_rs(rs.tolist())

	def set_data(self,increase,close_price,close_prices,cur_rs,ema_rs,volume):
		self.increase = increase
		self.close_price = close_price
		self.close_prices = close_prices
		self.cur_rs = cur_rs
		self.ema_rs = ema_rs
		self.volume = volume


	def daily_function(self,tq_longhighprice,tq_longlowprice,tq_shorthighprice,tq_shortlowprice,se_close,sh_close):
		#唐安奇通道
		self.tq_longhighprice = tq_longhighprice
		self.tq_longlowprice = tq_longlowprice
		self.tq_shorthighprice = tq_shorthighprice
		self.tq_shortlowprice = tq_shortlowprice
		self.rs_data.update_daily(se_close,sh_close)

		if(self.portfolio_strategy_short!=0):
			self.position_day += 1

	def handle_data(self,context,current_data,sh_close):
		current_price = current_data[self.code].last_price
		self.calculate_unit(context.portfolio.total_value)
		current_dt = context.current_dt;
		#短时系统操作（买入，加仓，止损，清仓）
		#更新rs数据
		self.rs_data.update(current_price,sh_close,current_dt)
		cash = context.portfolio.cash
		order_info = None
		if(self.portfolio_strategy_short == 0):
			order_info = self.try_market_in(current_price,cash)
			return order_info
		else:
			self.set_appropriate_out_price(current_price)
			order_info = self.try_stop_loss(current_price)
			if(order_info != None):
				return order_info
			order_info = self.try_market_add(current_price, self.ratio*cash)
			if(order_info != None):
				return order_info
			order_info = self.try_market_out(current_price)
			if(order_info != None):
				return order_info
			# order_info = self.try_market_stop_profit(current_price)
			# if(order_info != None):
			#     return order_info

	#计算交易单位
	def calculate_unit(self,total_value):
		value = total_value
		# 计算波动的价格
		current_N = (self.N)[-1]
		dollar_volatility = self.dollars_per_share*current_N
		# 依本策略，计算买卖的单位
		print("calculate_unit",value,current_N,dollar_volatility,len(self.N))
		self.unit = value*0.01/dollar_volatility
		print("unit value",self.unit)


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
		has_break_max = self.has_break_max(current_price,self.tq_shorthighprice)
		# rs_satisfied = self.rs_data.can_be_trade() TODO
		rs_satisfied = True

		if(not has_break_max or not rs_satisfied):
			return
		num_of_shares = cash/current_price
		num_of_shares = min(self.unit,num_of_shares)

		if num_of_shares < 100:
		    return

		if self.portfolio_strategy_short < int(self.unit_limit*self.unit):
			order_info = order(self.code, int(num_of_shares))
			if(order_info == None):
				print "想买买不起，因为没钱了----开仓！%s(%s)当前价：%s,最高价：%s,N:%s"%(self.name,self.code,current_price,self.tq_shorthighprice,self.N[-1])
				return
			# self.portfolio_strategy_short += int(self.unit)
			self.break_price_short = current_price
			self.next_add_price = current_price + self.add_ratio * self.N[-1]
			self.n_out_price = current_price - 2*self.N[-1]
			self.p_out_price = current_price - current_price*0.07
			self.next_out_price = max(self.n_out_price,self.p_out_price)
			self.mark_in_price = current_price
			print "开仓！当前价：%s,最高价：%s,N:%s"%(current_price,self.tq_shorthighprice,self.N[-1])
			return order_info 
	#7
	# 加仓函数
	# 输入：当前价格-float, 现金-float, 天数-int
	# 输出：none
	def try_market_add(self,current_price, cash):
		# if(self.unit == 0):
		#     return
		break_price = self.break_price_short
		# rs_satisfied = self.rs_data.can_be_trade()

		# 每上涨0.5N，加仓一个单元
		if current_price < self.next_add_price: 
			return
		num_of_shares = cash/current_price
		num_of_shares = min(self.unit,num_of_shares)
		if num_of_shares < 100: 
			print "想买买不起，因为没钱了！------加仓！%s(%s)当前价：%s,上次突破买入价：%s，N:%s,unit:%s,position:%s"%(self.name,self.code,current_price,break_price,self.N[-1],self.unit,self.portfolio_strategy_short)
			return
		order_info = order(self.code, int(num_of_shares))
		if(order_info == None):
			return
		# self.portfolio_strategy_short += int(self.unit)
		self.break_price_short = current_price
		self.next_add_price = current_price + self.add_ratio * self.N[-1]
		self.n_out_price = current_price - 2*self.N[-1]
		self.p_out_price = current_price - current_price*0.07
		self.next_out_price = max(self.n_out_price,self.p_out_price)

		print "加仓！当前价：%s,上次突破买入价：%s，N:%s,unit:%s,position:%s"%(current_price,break_price,self.N[-1],self.unit,self.portfolio_strategy_short)
		return order_info
	#8
	# 离场函数
	# 输入：当前价格-float, 天数-int
	# 输出：none
	def try_market_out(self,current_price):
		# Function for leaving the market
		has_break_min = self.has_break_min(current_price ,self.tq_shortlowprice)
		# 若当前价格低于前out_date天的收盘价的最小值, 则卖掉所有持仓
		if not has_break_min:
			return
		# print min(price['close'])
		if self.portfolio_strategy_short > 0:
			# self.portfolio_strategy_short = 0
			order_info = order(self.code, - self.portfolio_strategy_short)
			print "离场！当前价：%s,最低价：%s，position:%s"%(current_price,self.tq_shortlowprice,self.portfolio_strategy_short)
			return order_info

	#15交易日涨幅小于20%退出
	def try_market_stop_profit(self,current_price):
		# Function for leaving the market
		increase_ratio = (current_price - self.mark_in_price)/self.mark_in_price
		if(self.position_day >= self.increase_period and increase_ratio < self.increase_ratio):
			print "%s清仓，交易日未满足涨幅20,入场价：%s,涨幅：%s,当前价:%s"%(self.position_day,self.mark_in_price,increase_ratio,current_price)
			return order(self.code, - self.portfolio_strategy_short)
		elif(self.position_day >= self.increase_period):
			print "%s宽止损，交易日满足涨幅20,入场价：%s,涨幅：%s,当前价:%s"%(self.position_day,self.mark_in_price,increase_ratio,current_price)
			self.tight_out = False
	#9
	# 止损函数
	# 输入：当前价格-float
	# 输出：none
	def try_stop_loss(self,current_price):
		# 损失大于2N，卖出股票
		break_price = self.break_price_short
		# If the price has decreased by 2N, then clear all position
		if current_price < self.next_out_price:
			order_info = order(self.code, - self.portfolio_strategy_short)
			print "止损！当前价：%s,上次突破买入价：%s，N:%s,position:%s"%(current_price,break_price,self.N[-1],self.portfolio_strategy_short)
			return order_info

	 #更新止损价格
	def set_appropriate_out_price(self,current_price):
		# Function for leaving the market
		min_price = max(self.n_out_price,self.p_out_price)
		n_out_price = current_price - 2*self.N[-1]
		min_cur_price = min(self.tq_shortlowprice,n_out_price)
		if (not self.tight_out and  min_cur_price > min_price):
			print "宽止损！当前价：%s,min_cur_price：%s，min_price:%s"%(current_price,min_cur_price,min_price)
			self.next_out_price = min_price
		else:
			# print "紧止损！当前价：%s,min_cur_price：%s，min_price:%s"%(current_price,min_cur_price,min_price)
			self.next_out_price = max(self.next_out_price,n_out_price)

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
		value = "行业：%s,代码:%s,名称:%s,increase:%s,cur_rs:%s,ema_rs:%s"%(self.industry_name,self.code,self.name,self.increase,self.cur_rs,self.ema_rs)
		return value

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
class CustomIndustry:
    def __init__(self,industry):
        self.industry = industry
        self.stock_infos = list()
    def init_data(self):
        pass

    def check_ema_rs(self,series_market_closes):
        values = self.cal_value()
        series_rs = values/series_market_closes
        ema_rs = tb.EMA(np.array(series_rs),39)
        # print(values,ema_rs,series_rs)
        self.cur_rs = series_rs[-1]
        self.cur_emars = ema_rs[-1]
        return self.cur_rs > self.cur_emars

    def add_stockinfo(self,stock_info):
        self.stock_infos.append(stock_info)
    def cal_value(self):
        # value = 0
        values = 0
        for index in range(len(self.stock_infos)):
            stock_info = self.stock_infos[index]
            # value += stock_info.close_price
            if(index == 0):
                values = stock_info.close_prices
            else:
                values += stock_info.close_prices
        # value = round(value/len(self.stock_infos),4)
        values = values/len(self.stock_infos)
        return values
    def __str__(self):
        text = ""
        for stock_info in self.stock_infos:
            text = text + str(stock_info)+";"
        return "CustomIndustry:"+text
