# coding=utf-8

import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
class SellStrategy_threeFiveAvgCross:
	def __init__(self,buyCtDict):
		self.util = MyUtil()
		self.sellAdjustTime = 3
		self.sellFastAvgDays = 3
		self.sellSlowAvgDays = 5
		self.buyCtDict = buyCtDict


	def sell(self,context,security):		
		buyCtDict = self.buyCtDict[security]
		buyDate = buyCtDict["buyDate"]
		adjustTime = buyCtDict["adjustTime"]
		lastRet = buyCtDict["lastRet"]
		if buyDate == context.current_dt.date():
			return
		endDate = context.current_dt - timedelta(1)
		fastAvg = get_price(security,end_date = endDate, fields = ['avg'],count = self.sellFastAvgDays,skip_paused = True)
		fastAvg = sum(fastAvg.avg)/self.sellFastAvgDays
		slowAvg = get_price(security,end_date = endDate, fields = ['avg'],count = self.sellSlowAvgDays,skip_paused = True)
		slowAvg = sum(slowAvg.avg)/self.sellSlowAvgDays
		if(fastAvg == slowAvg):
			bRet = lastRet
		else:
			bRet = (fastAvg - slowAvg) >0
		if bRet != lastRet :
			self.util.logPrint ("卖出判断code:%s adjustTime time:%s",security,adjustTime)
			adjustTime = adjustTime +1
			if(adjustTime == self.sellAdjustTime):
				order_target(security, 0)
				del self.buyCtDict[security]
				return
		buyCtDict["adjustTime"] = adjustTime
		buyCtDict["lastRet"] = bRet
				

