#coding = utf-8
######### rs选股-海龟交易 #########
from jqdata import jy
from jqdata import *
import pandas as pd
import numpy as np
import Utils
import talib as tb
from StockRSData import *


def get_strong_market(datetime,count,frequency="1day"):
	# codes = ["000001.XSHG","399006.XSHE","399005.XSHE"]
	codes = ["000001.XSHG"]
	panel = get_price(codes,end_date = datetime,count = count,fields = ["close"],frequency=frequency)
	# df_close = panel["close"]
	# series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
	# max_value = -1
	# max_code = None
	# for code in codes:
	# 	if(series_increase[code]>max_value):
	# 		max_value = series_increase[code]
	# 		max_code = code
	# return df_close[max_code]
	return df_close

def handle_data(context,data):
	g.strategy.handle_data(context,data)

def initialize(context):
	set_benchmark('000300.XSHG')
	# 开启动态复权模式(真实价格)
	set_option('use_real_price', True)
	g.period = 240
	g.strategy = TurtleStrategy(g.period)
	# run_monthly(monthly_function,monthday = 1,time = "after_close")
	run_weekly(monthly_function,weekday = -1,time = "after_close")
	run_daily(daily_function,time = "before_open")

def daily_function(context):
	g.strategy.daily_function(context)
	

def monthly_function(context):
	g.strategy.monthly_function(context)
		
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

# 海龟交易策略
class TurtleStrategy(BaseStrategy):
	"""docstring for TurtleStrategy"""
	def __init__(self, trading_period):
		super(TurtleStrategy, self).__init__()

		# 获取N日股票数据
		self.trading_period = trading_period
		self.first_run = True  #是否选股后第一次运行
		self.tq_longperiod = 55
		self.tq_shortperiod = 20
		# 计算N值的天数
		self.number_days = 20
		self.new_industries = list()
	
	def pick_stocks(self,context):
		current_dt = context.current_dt
		end_date = current_dt
		start_date = current_dt - timedelta(days = 400)
		start_date = start_date.date()
		current_data = get_current_data()
		securities_df = get_all_securities()
		securities_df = securities_df[securities_df["start_date"] <= start_date]
		securities = securities_df.index.tolist()
		count = self.trading_period
		
		pick_result_list = self.pick_strong_stocks("sw_l1",securities,end_date,count)
		if( None != pick_result_list and 0 != len(pick_result_list)):
			self.insert_to_industrylist(pick_result_list)

	def insert_to_industrylist(self,pick_result_list):
		for industry_data in pick_result_list:
			self.insert_industry(industry_data)

	def insert_industry(self,industry_data_new):
		industry_data = self.get_industry(industry_data_new.industry)
		if(None != industry_data):
			industry_data.insert_stock_from_industry(industry_data_new)
		else:
			self.new_industries.append(industry_data_new)

	def get_industry(self,industry_code):
		for industry_data in self.new_industries:
			if industry_data.industry == industry_code:
				return industry_data

	def monthly_function(self,context):
		self.pick_stocks(context)

	def daily_function(self,context):
		# if(self.first_run or 0 == len(self.new_industries)):
		if(0 == len(self.new_industries)):
			return
		self.first_run = False
		count = self.trading_period
		end_date = context.current_dt - timedelta(days = 1)
		securities = list()
		for industry in self.new_industries:
			for stock_info in industry.stock_infos:
				securities.append(stock_info.code)
		history_data = get_price(security = securities,end_date = end_date,count = count,fields = ['close','volume','high','low'])
		current_data = get_current_data()
		series_market_closes = get_strong_market(end_date,count)
		df_close = history_data["close"]
		df_high = history_data["high"]
		df_low = history_data["low"]
		df_volume = history_data["volume"]
		series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]

		#获取今日该股最高价与上证最高价求得rs（未来函数）
		df = get_price("000001.XSHG",end_date = end_date,count = 1,frequency = "1d",fields = ("high"))
		sh_close = df.high[0] #TODO

		for industry in self.new_industries:
			for stock_info in industry.stock_infos:
				code = stock_info.code
				if(current_data[code].paused or df_close[code].empty):
					print("股票停牌退市或者当前数据异常" ,code,current_data[code].paused,df_close[code].empty)
					continue
				stock_closes = df_close[code]
				stock_highs = df_high[code]
				stock_lows = df_low[code]
				self.calculate_rs(stock_info,series_market_closes,stock_lows,stock_highs,stock_closes,stock_closes[-1],sh_close)
				self.calculate_n(stock_info,stock_lows,stock_highs,stock_closes)


	#计算rs数据
	def calculate_rs(self,stock_info,series_market_closes,stock_lows,stock_highs,stock_closes,se_close,sh_close):
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

		volume = 0
		cur_rs = round(series_rs[-1],4)
		close_price = stock_closes[-1]
		# stock_info.set_data(increase,close_price,stock_closes,cur_rs,cur_ema_rs,volume)
		stock_info.set_data(stock_strength,close_price,stock_closes,cur_rs,cur_ema_rs,volume)

		tq_longhighprice = max(stock_highs[-self.tq_longperiod:])
		tq_longlowprice = min(stock_lows[-self.tq_longperiod:])
		tq_shorthighprice = max(stock_highs[-self.tq_shortperiod:])
		tq_shortlowprice = min(stock_lows[-self.tq_shortperiod:])

		stock_info.daily_function(tq_longhighprice,tq_longlowprice,tq_shorthighprice,tq_shortlowprice,se_close,sh_close)
	#计算海龟系统N
	def calculate_n(self,stock_info,stock_lows,stock_highs,stock_closes):
		# 需要考虑停牌，上市交易天数过小,这时候是否需要参与交易
		 #计算海龟交易系统N
		length = int(self.number_days*1.5)
		if(len(stock_info.N) == 0):
			series_lowN = stock_lows[-length:]
			series_highN = stock_highs[-length:]
			series_closeN = stock_closes[-length:]
			# print(length,stock_closes)
			lst = []
			for i in range(0, length):
				# if(np.isnan(series_closeN[i])):
				# 	continue
				high_price = series_highN[i]
				low_price = series_lowN[i]
				index = i
				if(i == 0):
					index = 0
				else:
					index = i-1
				last_close = series_closeN[index]
				cur_close = series_closeN[i]
				h_l = high_price-low_price
				h_c = high_price-last_close
				c_l = cur_close-low_price
				# 计算 True Range 取计算第一天的前20天波动范围平均值
				True_Range = max(h_l, h_c, c_l)
				if(len(lst) < self.number_days):
					lst.append(True_Range)
				else:
					if(len(stock_info.N) == 0):
						current_N = np.mean(lst)
					else:
						current_N = (True_Range + (self.number_days-1)*(stock_info.N)[-1])/self.number_days
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
			current_N = (True_Range + (self.number_days-1)*(stock_info.N)[-1])/self.number_days
			if(current_N == 0):
				print("True_Range is zero:",h_l,h_c,c_l,cur_low,cur_high,cur_close,last_close,current_N,stock_info.code)
				return
			(stock_info.N).append(current_N)
			del stock_info.N[0]


	def start_trade(self,context,data):
		if(0 == len(self.new_industries)):
			return
		current_data = get_current_data()
		current_dt = context.current_dt
		sh_df = get_price("000001.XSHG",end_date = current_dt,frequency = "minute",fields="close",count=1)
		sh_close = sh_df.close[0]
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


	# 1.计算rps
	# 2.计算rs动能
	# 3.
	def pick_strong_stocks(self,name,securities,datetime,count):
		history_data = get_price(security = securities,end_date = datetime,count = count,fields = ['close','volume'])
		history_data_weekday = get_price(security = securities,end_date = datetime,count = 30,fields = ['close'],frequency="5day")
		codes = get_industries(name).index;
		panel_industry = Utils.get_sw_quote(codes,end_date=datetime,count=count)
		industry_closes = panel_industry.ClosePrice
		industry_names = panel_industry.ChiName
		series_market_closes = get_strong_market(datetime,30,frequency="5day")
		df_close = history_data["close"]
		df_close_weekday = history_data_weekday["close"]
		df_volume = history_data["volume"]
		# series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
		current_data = get_current_data()
		result = list()
		for i in range(len(codes)):
			industry_code = codes[i]
			if(not industry_code in industry_closes.columns):
				continue
			industry_name = industry_names[industry_code][-1]
			securities = get_industry_stocks(industry_code)
			stock_infos = list()
			for security in securities:
				if(not security in series_increase or current_data[security].paused):
					continue

				stock_close_weekday = df_close[security]
				rsmom_isup = isup_rs_monmentum(stock_close_weekday,series_market_closes)
				stock_close = df_close[security]
				# series_rs = stock_close/series_market_closes
				# cur_ema_rs = round(tb.EMA(np.array(series_rs),39)[-1],4)
				# increase = round(series_increase[security],4)
				stock_strength = get_price_rps(stock_close)
				volume = df_volume[security][-1]
				cur_rs = round(series_rs[-1],4)
				security_name = current_data[security].name
				stock_info = StockInfo(security,security_name,industry_code,industry_name)
				stock_info.set_data(stock_strength,cur_price,stock_close,cur_rs,cur_ema_rs,volume)
				stock_info.init_rs_data(series_rs)
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
					# print(stock_info)
					new_industry.add_stockinfo(stock_info)

			if(pick_count>0):
				new_industry.check_ema_rs(series_market_closes)
				result.append(new_industry)
		return result
	def isup_rs_monmentum(index_closes,stock_closes):
		return False

	#计算个股强度
	def get_price_rps(stock_close):
		cur_price = stock_close[-1]
		c60 = stock_close[-60]
		r60 = (cur_price - c60)/c60

		c120 = stock_close[-120]
		r120 = (c60 - c120)/c120
		
		c180 = stock_close[-180]
		r180 = (c120 - c180)/c180

		c240 = stock_close[-240]
		r240 = (r180 - c240)/c240
		stock_strength = ((1+r240*0.8)*(1+r180*0.8)*(1+r120*0.8)*(1+r60*1.6)-1)*100
		return stock_strength

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

    def insert_stock_from_industry(self,industry_data):
    	if(None == industry_data or 0 == len(industry_data.stock_infos)):
    		return

    	for stock_info in industry_data.stock_infos:
    		is_exsit = None != self.get_stockinfo(stock_info.code)
    		if(not is_exsit):
    			self.add_stockinfo(stock_info)
    def get_stockinfo(self,stock_code):
    	for stock_info in self.stock_infos:
    		if(stock_code == stock_info.code):
    			return  stock_info

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

