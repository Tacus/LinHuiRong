# coding=utf-8
import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
#import datetime.timedelta
#data 去的是昨天的停 还是当天 按天回测
# TODO 新 上 market days < period 有nan 产生
class MyMacd:
	# 实测环境每天执行 ，handler_data 9.30调用 则只能取到昨天价格
	# macdField = 'close'
	# macdSlowEmaModulus = 26.0
	# macdFastEmaModulus = 12.0
	# macdDEAModulus = 9.0
	# macdM = 2.0
	# fastModulus = 0
	# slowModulus = 0
	# deaModulus =  0
	# macdPeriod = 60
	# maxCache = 60
	deathCountDict = {}
	macdDict = {}

	def __init__(self,enableLog = True,macdField = "close",macdFastEmaModulus = 12.0,macdSlowEmaModulus = 26.0,
		macdDEAModulus = 9.0,macdM = 2.0,macdPeriod = 120,maxCache = 60):
		self.macdField = macdField
		# 实测环境每天执行 ，handler_data 9.30调用 则只能取到昨天价格
		self.macdSlowEmaModulus = macdSlowEmaModulus
		self.macdFastEmaModulus = macdFastEmaModulus
		self.macdDEAModulus = macdDEAModulus
		self.macdM = macdM
		self.macdPeriod = macdPeriod
		self.fastModulus = self.macdM/(self.macdFastEmaModulus+1)
		self.slowModulus = self.macdM/(self.macdSlowEmaModulus+1)
		self.deaModulus =  self.macdM/(self.macdDEAModulus+1)
		self.maxCache = maxCache
		self.util = MyUtil(enableLog)
	def isMacdGoldCross(self,context,security,curPrice,factor):
		
		self.calculateMacdInfo(context,security,curPrice,factor)
		list = self.getLastTradeDayMacd(security,3)
		if(list and len(list)>2):
			prePreInfo = list[0]
			preInfo = list[1]
			curInfo = list[2]
			self.util.logPrint("isMacdGoldCross,curInfo:%s,preInfo:%s,dea:%s"
							, curInfo["macd"],preInfo["macd"],curInfo["dea"])

			if((preInfo["macd"] < 0 and curInfo["macd"] >0)
			 or (prePreInfo["macd"]<=0 and preInfo["macd"] == 0 and curInfo["macd"] >0)):
				self.util.logPrint ('金叉')
				return True  
		return False

	def isMacdLowGoldCross(self,context,security,curPrice,factor):
		# 低位金叉
		self.calculateMacdInfo(context,security,curPrice,factor)
		list = self.getLastTradeDayMacd(security,3)
		if(list and len(list)>2):
			prePreInfo = list[0]
			preInfo = list[1]
			curInfo = list[2]
			# self.util.logPrint("isMacdLowGoldCross,curInfo:%s,preInfo:%s,dea:%s"
			#				 , curInfo["macd"],preInfo["macd"],curInfo["dea"])

			if((preInfo["macd"] <0 and curInfo["macd"] >0 and curInfo["dea"]<0)
			 or (prePreInfo["macd"]<=0 and preInfo["macd"] == 0 and curInfo["macd"] >0 and curInfo["dea"]<0)):
				self.util.logPrint ('金叉')
				return True  
		return False
		
	def isMacdHightGoldCross(self,context,security,curPrice,factor):
		pass

	def isMacdLowDeathCross(self,context,security,curPrice,factor):
		pass

	def isMacdHightDeathCross(self,context,security,curPrice,factor):
		#高位死叉
		self.calculateMacdInfo(context,security,curPrice,factor)
		list = self.getLastTradeDayMacd(security,3)
		if(list and len(list)>2):
			prePreInfo = list[0]
			preInfo = list[1]
			curInfo = list[2]
			# self.util.logPrint("isMacdHightDeathCross,curInfo:%s,preInfo:%s,dea:%s"
			#				 , curInfo["macd"],preInfo["macd"],curInfo["dea"])

			if((preInfo["macd"] >0 and curInfo["macd"] < 0 and curInfo["dea"]>0)
			 or (prePreInfo["macd"]>=0 and preInfo["macd"] == 0 and curInfo["macd"] < 0 and curInfo["dea"]>0)):
				self.util.logPrint ('死叉')
				return True  
		return False

	def calculateMacdInfo(self,context,security,curPrice,factor):
		if(not factor == 1.0):
			self.removeTradeDayMacd(security)   
			self.util.logPrint ("除权factor:%s，重新计算macd",factor)

		currentSlowEma = 0
		currentFastEma = 0
		currentMacd = 0
		currentDea = 0
		currentDiff = 0
		macdDict = self.getLastTradeDayMacd(security)
		if not macdDict == None:
			lastDate = macdDict['date']
			currentSlowEma = macdDict['slowEma']
			currentFastEma = macdDict['fastEma']
			currentDea = macdDict['dea']
			start_date = lastDate + timedelta(1)
			end_date = context.current_dt.date() - timedelta(1)
			# timeDt = end_date - start_date
			timeDt = end_date - lastDate
			#周一情况
			if(timeDt.days >= 0):
				df = get_price(security, start_date = start_date ,end_date=end_date, fields=[self.macdField], skip_paused=True)
				avgs = df[self.macdField]
				for i in range(len(avgs)):
					 # self.util.logPrint ("currentSlowEma:%s,currentFastEma:%s,currentDea:%s" ,currentSlowEma,currentFastEma,currentDea)
					date = avgs.index[i].date()
					curHisPrice = avgs[i]
					currentSlowEma,currentFastEma,currentDea,currentMacd = self.caculateMacd(currentSlowEma,currentFastEma,currentDea,curHisPrice)
					self.setLastTradeDayMacd(security,currentSlowEma,currentFastEma,currentDea,currentMacd,date)
					# self.util.logPrint ("中继date:%s, currentMacd:%s,currentDiff:%s,currentDea:%s" ,str(avgs.index[i].date()),currentMacd,currentDiff,currentDea)
			# #当前已经计算过
			# else:
			#	 return
			
		else:
			end_date = context.current_dt.date() - timedelta(1)
			dict = get_security_info(security)
			startDate = dict.start_date
			days = end_date - startDate 
			if days.days < self.macdPeriod:
				df = get_price(security, start_date = startDate ,end_date=end_date, fields=self.macdField, skip_paused=True)
			else:
				df = get_price(security, end_date=end_date, fields=self.macdField, skip_paused=True,count=self.macdPeriod)
			avgs = df[self.macdField]
			for i in range(len(avgs)):
				curHisPrice = avgs[i]
				if i==0:
					currentSlowEma = curHisPrice
					currentFastEma = curHisPrice
					# pass
				# elif i == 1:
				# 	currentSlowEma = currentSlowEma + (curHisPrice - currentSlowEma) * self.slowModulus
				# 	currentFastEma = currentFastEma + (curHisPrice - currentFastEma) * self.fastModulus
				# 	currentDiff =  currentFastEma - currentSlowEma
				# 	currentDea = currentDea + currentDiff*self.deaModulus
				# 	currentMacd = 2*(currentDiff - currentDea)
				else:
					currentSlowEma,currentFastEma,currentDea,currentMacd = self.caculateMacd(currentSlowEma,currentFastEma,currentDea,curHisPrice)
					# self.util.logPrint ("currentSlowEma:%s,currentFastEma:%s,currentMacd:%s" ,currentSlowEma,currentFastEma,currentMacd)
				date = avgs.index[i].date()
				self.setLastTradeDayMacd(security,currentSlowEma,currentFastEma,currentDea,currentMacd,date)
		
	def caculateMacd(self,lastSlowEma,lastFastEma,lastDea,curPrice):
		currentSlowEma = lastSlowEma*(1-self.slowModulus) + curPrice*self.slowModulus
		currentFastEma = lastFastEma*(1-self.fastModulus) + curPrice*self.fastModulus
		currentDiff =  currentFastEma - currentSlowEma
		currentDea = lastDea*(1-self.deaModulus) + currentDiff*self.deaModulus
		currentMacd = 2*(currentDiff - currentDea)

		# currentSlowEma = round(currentSlowEma,3)
		# currentFastEma = round(currentFastEma,3)
		currentDea = round(currentDea,3)
		currentMacd = round(currentMacd,3)
		return currentSlowEma,currentFastEma,currentDea,currentMacd
		
		
	def setLastTradeDayMacd(self,security,slowEma,fastEma,Dea,Macd,date):
		if self.macdDict.has_key(security):
			securityList = self.macdDict[security]
			if(len(securityList) >= self.maxCache):
				del securityList[0]
			macdDict = {}
			macdDict["slowEma"] = slowEma
			macdDict["fastEma"] = fastEma
			macdDict["dea"] = Dea
			macdDict["date"] = date
			macdDict["macd"] = Macd		   
			securityList.append(macdDict)
		else:
			securityList = list()
			macdDict = {}
			macdDict["slowEma"] = slowEma
			macdDict["fastEma"] = fastEma
			macdDict["dea"] = Dea
			macdDict["date"] = date
			macdDict["macd"] = Macd			
			securityList.append(macdDict)
			self.macdDict[security] = securityList
	def removeTradeDayMacd(self,security):
		if self.macdDict.has_key(security):
		   del self.macdDict[security]
			
	def getLastTradeDayMacd(self,security,count = None):
		if self.macdDict.has_key(security):
			securityList = self.macdDict[security]
			ret = None

			listLen = len(securityList)
			if(count and listLen>=count):
				ret = securityList[listLen - count:]
			elif count:
				ret = securityList
			else:
				ret = securityList[len(securityList) - 1]
			return ret

	#return list
	def getAllTradeDayMacd(self,security):
		if self.macdDict.has_key(security):
			securityList = self.macdDict[security]
			return securityList


	def getCurDeathCount(self,security):
		iRet = 0
		if self.deathCountDict.has_key(security):
			iRet = self.deathCountDict[security]
		return iRet

	def setCurDeathCount(self,security,count):
		self.deathCountDict[security] = count

	def removeCurDeathCount(self,security):
		if self.deathCountDict.has_key(security):
			del self.deathCountDict[security]