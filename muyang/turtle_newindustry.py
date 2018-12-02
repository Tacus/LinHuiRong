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
from StockRSData import *



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
	g.strategy.handle_data(context,data)
#     for _,stock_info in g.position_pool.items():
#         order = stock_info.update(context)

#         if order != None and order.filled  > 0 and order.is_buy :
#             stock_info.add_buy_count( order.filled)
#         elif(order != None and order.filled > 0 and not order.is_buy):
#             stock_info.reduce_buy_count( order.filled)
#             count = stock_info.get_buy_count()
#             if(count <= 0):
#                 del g.position_pool[stock_info.code]

#     for single in g.stock_pool:
#         order = single.update(context)
#         if order != None and order.filled  > 0 and order.is_buy :
#             single.set_buy_count( order.filled)
#             g.stock_pool.remove(single)
#             g.position_pool[single.code] = single


def initialize(context):
	set_benchmark('000300.XSHG')
	# 开启动态复权模式(真实价格)
	set_option('use_real_price', True)
	g.period = 240
	# g.first_run = True
	# g.new_industries = list()
	g.strategy = TurtleStrategy(g.period)
	run_monthly(monthly_function,monthday = 1,time = "before_open")
	run_daily(daily_function,time = "before_open")

def daily_function(context):
	g.strategy.daily_function(context)
	

def monthly_function(context):
	g.strategy.monthly_function(context)
	# del g.new_industries[:]
	# current_dt = context.current_dt
	# end_date = current_dt - timedelta(days = 1)
	# start_date = current_dt - timedelta(days = 400)
	# start_date = start_date.date()
	# current_data = get_current_data()
	# securities_df = get_all_securities()
	# securities_df = securities_df[securities_df["start_date"] <= start_date]
	# securities = securities_df.index.tolist()
	# count = g.period
	# history_data = get_price(security = securities,end_date = end_date,count = count,fields = ['close','volume'])
	# get_sw_industry_stocks("sw_l1",end_date,count,history_data,current_data)
		
class BaseStrategy(BaseClass):
	"""docstring for BaseStrategy"""
	def __init__(self):
		super(BaseStrategy, self).__init__()

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
		self.tq_longperiod = 55
		self.tq_shortperiod = 20
		# 计算N值的天数
		self.number_days = 20
		self.new_industries = list()
	
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
		self.pick_strong_stocks("sw_l1",end_date,count,history_data,current_data)

	def monthly_function(self,context):
		self.pick_stocks(context)

	def daily_function(self,context):
		if(self.first_run or 0 == len(self.new_industries)):
			return
		self.first_run = False
		count = self.trading_period
		end_date = context.current_dt - timedelta(days = 1)
		securities = list()
		for industry in self.new_industries:
			for stock_info in industry.stock_infos:
				securities.append(stock_info.code)
		history_data = get_price(security = securities,end_date = end_date,count = count,fields = ['close','volume','high','low'])
		series_market_closes = get_mightlymarket_closes(end_date,count)
		df_close = history_data["close"]
		df_high = history_data["high"]
		df_low = history_data["low"]
		df_volume = history_data["volume"]
		series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
		for industry in self.new_industries:
			for stock_info in industry.stock_infos:
				code = stock_info.code
				if(data[code].paused):
					continue
				stock_closes = df_close[code]
				stock_highs = df_high[code]
				stock_lows = df_low[code]
				self.calculate_rs(stock_info,series_market_closes,stock_lows,stock_highs,stock_closes)
				self.calculate_n(stock_info,stock_lows,stock_highs,stock_closes)


	#计算rs数据
	def calculate_rs(self,stock_info,series_market_closes,stock_lows,stock_highs,stock_closes):
		series_rs = stock_closes/series_market_closes
		cur_ema_rs = round(tb.EMA(np.array(series_rs),39)[-1],4)

		# increase = round(series_increase[code],4) #deprecate
		ref_ema_rs30 = series_rs[-30]
		c30 = (cur_ema_rs - ref_ema_rs30)/ref_ema_rs30

		ref_ema_rs60 = series_rs[-60]
		c60 = (ref_ema_rs30 - ref_ema_rs60)/ref_ema_rs60
		
		ref_ema_rs90 = series_rs[-90]
		c90 = (ref_ema_rs60 - ref_ema_rs90)/ref_ema_rs90

		ref_ema_rs120 = series_rs[-120]
		c120 = (ref_ema_rs90 - ref_ema_rs120)/ref_ema_rs120

		stock_strength = ((1+c120*0.8)*(1+c90*0.8)*(1+c60*0.8)*(1+c30*1.6)-1)*100

		volume = df_volume[code][-1]
		cur_rs = round(series_rs[-1],4)
		close_price = stock_closes[-1]
		# stock_info.set_data(increase,close_price,stock_closes,cur_rs,cur_ema_rs,volume)
		stock_info.set_data(stock_strength,close_price,stock_closes,cur_rs,cur_ema_rs,volume)

		tq_longhighprice = max(stock_highs[-self.tq_longperiod:])
		tq_longlowprice = min(stock_lows[-self.tq_longperiod:])
		tq_shorthighprice = max(stock_highs[-self.tq_shortperiod:])
		tq_shortlowprice = max(stock_lows[-self.tq_shortperiod:])
		stock_info.daily_function(tq_longhighprice,tq_longlowprice,tq_shorthighprice,tq_shortlowprice)
	#计算海龟系统N
	def calculate_n(self,stock_info,stock_lows,stock_highs,stock_closes):
		# 需要考虑停牌，上市交易天数过小,这时候是否需要参与交易
		 #计算海龟交易系统N
		length = -self.number_days*2
		if(len(stock_info.N) == 0):
			series_lowN = stock_lows[-length:]
			series_highN = stock_highs[-length:]
			series_closeN = stock_closes[-length:]
			lst = []
			for i in range(0, length):
				if(np.isnan(series_closeN[i])):
					continue
				high_price = series_highN[i]
				low_price = series_lowN[i]
				index = i
				if(i == 0):
					index = 0
				else:
					index = i-1
				last_close = series_closeN[index]
				h_l = high_price-low_price
				h_c = high_price-last_close
				c_l = last_close-low_price
				# 计算 True Range 取计算第一天的前20天波动范围平均值
				True_Range = max(h_l, h_c, c_l)
				if(len(lst) < self.number_days):
					lst.append(True_Range)
				else:
					if(len(stock_info.N) == 0):
						current_N = np.mean(lst)
					else:
						current_N = (True_Range + (self.number_days-1)*(self.N)[-1])/self.number_days
					(stock_info.N).append(current_N)
		else:
			cur_low = stock_lows[-1]
			cur_high = stock_highs[-1]
			cur_close = stock_closes[-1]
			last_close = stock_closes[-2]
			h_l = cur_high-cur_low
			h_c = cur_high-last_close
			c_l = cur_close-cur_low
			# Calculate the True Range
			True_Range = max(h_l, h_c, c_l)
			# 计算前g.number_days（大于20）天的True_Range平均值，即当前N的值：
			current_N = (True_Range + (self.number_days-1)*(self.N)[-1])/self.number_days
			(stock_info.N).append(current_N)
			del stock_info.N[0]

	def start_trade(self,context,data):
		if(0 == len(self.new_industries)):
			return
		current_data = get_current_data()
		current_dt = context.current_dt
		sh_df = get_price("000001.XSHG",end_date = current_dt,frequency = "minute",fields="close",count=1)
		sh_close = sh_df.close[0],
		for industry in self.new_industries:
			for stock_info in industry.stock_infos:
				if(len(stock_info.N) == 0):
					continue
				order = stock_info.handle_data(context,current_data,sh_close)
				if order != None and order.filled  > 0 and order.is_buy :
					if(stock_info.portfolio_strategy_short != 0):
						stock_info.add_buy_count( order.filled)
					else:
						stock_info.set_buy_count(order.filled)
				elif(order != None and order.filled > 0 and not order.is_buy):
					stock_info.reduce_buy_count( order.filled)

	def handle_data(self,context,data):
		self.start_trade(context,data)

	def pick_strong_stocks(self,name,datetime,count,history_data,current_data):
		codes = get_industries(name).index;
		panel_industry = Utils.get_sw_quote(codes,end_date=datetime,count=count)
		industry_closes = panel_industry.ClosePrice
		industry_names = panel_industry.ChiName
		series_market_closes = get_mightlymarket_closes(datetime,count)
		df_close = history_data["close"]
		df_volume = history_data["volume"]
		series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
		current_data = get_current_data()
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
				security_name = current_data[security].name
				stock_info = StockInfo(security,security_name,industry_code,industry_name)
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

		self.N = list()
		pass

	def set_data(self,increase,close_price,close_prices,cur_rs,ema_rs,volume):
	    self.increase = increase
	    self.close_price = close_price
	    self.close_prices = close_prices
	    self.cur_rs = cur_rs
	    self.ema_rs = ema_rs
	    self.volume = volume


	def daily_function(self,tq_longhighprice,tq_longlowprice,tq_shorthighprice,tq_shortlowprice):
		#唐安奇通道
		self.tq_longhighprice = tq_longhighprice
		self.tq_longlowprice = tq_longlowprice
		self.tq_shorthighprice = tq_shorthighprice
		self.tq_shortlowprice = tq_shortlowprice

		#获取今日该股最高价与上证最高价求得rs（未来函数）
		df = get_price(["000001.XSHG",self.code],end_date = context.current_dt,count = 1,frequency = "1d",fields = ("high"))
		sh_close = df.high["000001.XSHG"][0]
		se_close = df.high[self.code][0]
		self.rs_data.update_daily(se_close,sh_close)

		self.calculate_n()
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
		else:
			stock_info.set_appropriate_out_price(current_price)
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
		self.unit = value*0.01/dollar_volatility

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
		rs_satisfied = self.rs_data.can_be_trade()

		# print("是否触发海龟交易信号：%s,rs是否满足条件：%s"%(has_break_max,rs_satisfied))

		if(not has_break_max or not rs_satisfied):
			return
		num_of_shares = cash/current_price
		# if num_of_shares < self.unit:
		#     return

		if self.portfolio_strategy_short < int(self.unit_limit*self.unit):
			order_info = order(self.code, int(self.unit))
			# self.portfolio_strategy_short += int(self.unit)
			self.break_price_short = current_price
			self.next_add_price = current_price + self.add_ratio * self.N[-1]
			self.n_out_price = current_price - 2*self.N[-1]
			self.p_out_price = current_price - current_price*0.07
			self.next_out_price = max(self.n_out_price,self.p_out_price)
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
		# rs_satisfied = self.rs_data.can_be_trade()

		# 每上涨0.5N，加仓一个单元
		if current_price < self.next_add_price: 
			return
		num_of_shares = cash/current_price
		# if num_of_shares < self.unit: 
		#     return
		order_info = order(self.code, int(self.unit))
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
		has_break_min = self.has_break_min(current_price ,self.system_low_short)
		# 若当前价格低于前out_date天的收盘价的最小值, 则卖掉所有持仓
		if not has_break_min:
			return
		# print min(price['close'])
		if self.portfolio_strategy_short > 0:
			# self.portfolio_strategy_short = 0
			order_info = order(self.code, - self.portfolio_strategy_short)
			print "离场！当前价：%s,最低价：%s，position:%s"%(current_price,self.system_low_short,self.portfolio_strategy_short)
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
		min_cur_price = min(self.system_low_short,n_out_price)
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
        value = "行业：%s,代码:%s,名称:%s,increase:%s,cur_rs:%s,ema_rs:%s"%(self.industry_name,self.security,self.name,self.increase,self.cur_rs,self.ema_rs)
        return value
