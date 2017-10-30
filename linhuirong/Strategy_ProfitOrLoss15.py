import pandas as pd
import numpy as np
# import matplotlib as talib
import talib
import datetime
from  MyMacd import *
from AdjustTimes import *
from MyUtil import *
from BuyStrategy import *
from SellStrategy_ProfitOrLoss15 import *
from jqdata import *
def initialize(context):
	# 定义一个全局变量, 保存要操作的
	# 000001(:平安银行)
	set_option('use_real_price', True)
	g.security = get_all_securities(["stock"]).index
	# g.security = get_index_stocks('000300.XSHG')
	# enable_profile()
	# g.security = ['002573.XSHE']
	# g.security = get_security_info('000300.XSHG')
	#卖出条件的调整次数
	
	#卖出的盈利比例
	
	g.macdCls = MyMacd(False,macdFiled = "close")
	g.adjustTimeCls  = AdjustTimes(False)
	g.util = MyUtil()		
	g.buyStrategy = BuyStrategy(g.macdCls,g.adjustTimeCls)

	g.sellStrategy = SellStrategy_ProfitOrLoss15()
	
# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
	# securities = g.security
	# for security in securities:
	# security = '002573.XSHE'
	
	# g.macdCls.isMacdLowGoldCross(context, data,security)
	# tmp = g.macdCls.getAllTradeDayMacd(security)
	# print tmp
	# return
	# g.adjustTimeCls.getTimesOfAdjust(context, data,security)
	# tmp = g.adjustTimeCls.getHighDict(security)
	# print tmp	  
			
	buyStocksMethod(context,data)
	sellStocksMethod(context,data) 
def buyStocksMethod(context,data):
	for security in g.security:
		dict = data[security]
		curPrice = dict.close
		factor = dict.factor
		if(not dict.isnan() and not dict.paused):
			g.buyStrategy.commonBuyStrategy(context,security,curPrice,factor)

def sellStocksMethod(context,data):
	for security in context.portfolio.positions:
		dict = data[security]
		if(not dict.isnan() and not dict.paused):
			g.sellStrategy.sell(context,security)
		else:
			continue