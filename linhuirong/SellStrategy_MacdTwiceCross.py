# coding=utf-8

import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
class SellStrategy_MacdTwiceCross:
	def __init__(self,macdCls,adjustTimeCls):
		self.macdCls = macdCls
		self.util = MyUtil()
		self.volumeRatio = 0.1

	def sell(self,context,security,factor):		
		bRet = self.macdCls.isMacdHightDeathCross(context,security,factor)
		self.util.logPrint("security:%s,isMacdHightDeathCross:%s",security,bRet)
		if(bRet):
			count = self.macdCls.getCurDeathCount(security)
			count = count+1
			self.util.logPrint("security:%s,DeathCount:%s",security,count)
			if(count >= 2):
				order_target(security,0)
				self.macdCls.removeCurDeathCount(security)
			else:
				self.macdCls.setCurDeathCount(security,count)
				

