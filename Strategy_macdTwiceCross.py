import pandas as pd
import numpy as np
# import matplotlib as talib
import talib
import datetime
from  MyMacd import *
from AdjustTimes import *
from BuyStrategy import *
from SellStrategy_MacdTwiceCross import *
from MyUtil import *
from jqdata import *
def initialize(context):
	set_option('use_real_price', True)
	# enable_profile()
	
	g.security = get_all_securities(["stock"]).index
	# g.security = get_index_stocks('000300.XSHG')
	# g.security = ['002573.XSHE']
	# g.security = get_security_info('000300.XSHG')
	
	
	#卖出的盈利比例
	g.sellProfitRatio = 0.15
	
	g.macd = MyMacd(False)
	g.adjustTims  = AdjustTimes(False)
	g.util = MyUtil()
	g.buyStrategy = BuyStrategy(g.macd,g.adjustTims)
	g.sellStrategy = SellStrategy_MacdTwiceCross(g.macd,g.adjustTims)

	
	g.sellCtDict = {}
	g.sellAdjustTime = 3
	g.sellFastAvgDays= 3
	g.sellSlowAvgDays= 5

def handle_data(context, data):
	buyStocksMethod(context,data)
	sellStocksMethod(context,data)


def buyStocksMethod(context,data):
	for security in g.security:
		dict = data[security]
		curPrice = dict.close
		factor = dict.factor
		if(not dict.isnan() and not dict.paused):
			g.buyStrategy.commonBuyStrategy(context,security,factor)

def sellStocksMethod(context,data):
	for security in context.portfolio.positions:
		dict = data[security]
		if(not dict.isnan() and not dict.paused):
			curPrice = dict.close
			factor = dict.factor
			g.sellStrategy.sell(security,curPrice,factor)
		else:
			continue