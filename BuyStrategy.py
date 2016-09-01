import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
class BuyStrategy:
	def __init__(self,macdCls,adjustTimeCls):
		self.macdCls = macdCls
		self.adjustTimeCls = adjustTimeCls
		self.buyAdjustTime = 6
		self.util = MyUtil()
	    self.volumeRatio = 0.1
		self.maxBuyStocks = 10

	def commonBuyStrategy(self,context,security,curPrice,factor):
		if security in context.portfolio.positions:
			self.util.logPrint("code:%s 已持仓",security)
		    return

		curTotalSts = len(context.portfolio.positions)
		if curTotalSts == self.maxBuyStocks:
			self.util.logPrint("code:%s 已满仓",security)			
		    return
		adjustTimes = self.adjustTimeCls.getTimesOfAdjust(context,data,security)
		# self.util.logPrint("code:%s,adjustTimes:%s",security,adjustTimes)
		if not adjustTimes== None:
		    buyFit = adjustTimes == self.buyAdjustTime
		    if(not buyFit):
		        return
		end_date = context.current_dt.date() - timedelta(1)
		tenVolume = get_price(security,end_date = end_date,frequency ='1d', fields = ['volume'],count = 10,skip_paused=True)
		volumeRatioTen = tenVolume['volume'].sum()/10
		fiveVolume = get_price(security,end_date = end_date,frequency ='1d', fields = ['volume'],count = 5,skip_paused=True)
		# if 
		volumeRatioFive = fiveVolume['volume'].sum()/5
		if volumeRatioTen ==0 :
		    self.util.logPrint( '十日均线为0 code:%s', security)
		    volumeRatioTen = 1
		if(volumeRatioFive/volumeRatioTen > self.volumeRatio):
		    macdFit = self.macdCls.isMacdLowGoldCross(context,security,curPrice,factor)
		    self.util.logPrint("code:%s,volumeRation:%s,macdFit:%s",security,volumeRatioFive/volumeRatioTen,str(macdFit))
		    if(macdFit):
		        #20天均线上扬
		        # lastEndDate = context.current_dt - timedelta(1)
		        # lastAvg= get_price(security, end_date=None, frequency='1d', fields='avg',  count=20)
		        # lastAvg = lastAvg.avg.sum()/20
		        # curAvg = get_price(security, end_date=context.current_dt, frequency='1d', fields='avg',  count=20)
		        # curAvg = curAvg.avg.sum()/20
		        # if(curAvg - lastAvg)>0:		        
		        perCash = 1.0/(self.maxBuyStocks - curTotalSts)
		        count = context.portfolio.cash*perCash/ curPrice
		        order(security, count)
		        return True