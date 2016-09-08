import math
import talib
import numpy as np
import pandas as pd
from jqdata import *
def initialize(context):
	g.securities = get_all_securities(["stock"]).index
	# g.securities = get_all_securities(["stock"])
	# print g.securities

	enable_profile()
# 	g.securities = ['000302.XSHG']
#持续天数
	g.lastingDays = 3
#下跌幅度控制
	g.priceFallRt = 0.1
#近N天的量与近一个月最低量相差比值
	g.volumeFallRt = 0.05
	
#最多持仓数
	g.maxBuyStocks = 10
	
	

# continuous price fallDown ;continunous volume fallDown ,continunous money inject
def handle_data(context, data):
	
	end_date = context.current_dt - timedelta(1)
	panel = get_price(g.securities.tolist(), end_date = end_date, fields = ["close","volume"],count = g.lastingDays+1)
	closeDf = panel.close
	volumeDf = panel.volume

	for security in closeDf.columns:
		curTotalSts = len(context.portfolio.positions)
		if(curTotalSts < g.maxBuyStocks):
			closeValues = closeDf[security].values
			volumeValues = volumeDf[security].values
			priceRet = checkPriceTrend(closeValues)
			if(priceRet):
				minVolume = get_price(security, end_date = end_date, fields = "volume",skip_paused = True, count = 30)
				minVolume = minVolume.volume.min()
				volumeRet = checkVolumeTrend(volumeValues,minVolume)
	# 			print security
	# 			continue
				if(volumeRet):
					start_date = volumeDf.index.tolist()[1]
					mFlowDf = get_money_flow([security], start_date, end_date, ["net_pct_main","net_pct_m","net_pct_s",])
					moneyRet = checkMoneyTrend(mFlowDf.net_pct_main.values)
					# g.util.logPrint()
					moneyRet = True
					if moneyRet:						
						perCash = 1.0/(g.maxBuyStocks - curTotalSts)*context.portfolio.cash
						order_target_value(security, perCash)
	
	for security in context.portfolio.positions:
		order_target(security,0)


def checkPriceTrend(priceList):
	startPrice = 0
	endPrice = 0
	for i in range(len(priceList)):
		if i == 0:
			startPrice = priceList[i]
			continue
		if i == len(priceList) - 1:
			endPrice = priceList[i]
		delta = priceList[i] - priceList[i-1]
		if (delta >0):
			return False
		
	ratio = (startPrice - endPrice)/startPrice
	if(ratio >= g.priceFallRt):
		return True


def checkVolumeTrend(volumeList,minVolume):
	endVolume = 0
	for i in range(len(volumeList)):
		if i == 0:
			continue
		if i == len(volumeList) - 1:
			endVolume = volumeList
		# print "volumee[%s]:%s,volumee[%s]:%s" %(i, volumeList[i],i-1,volumeList[i-1])
		delta = volumeList[i] - volumeList[i-1]
		if (delta >=0):
			return False

	ratio = (endVolume - minVolume)/minVolume
	if(abs(ratio) <= g.volumeFallRt):
		return True
			
def checkMoneyTrend(moneyList):
	for i in range(len(moneyList)):
		if (moneyList[i] <= 0):
			return False
	return  True