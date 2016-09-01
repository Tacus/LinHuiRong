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

	def sell(self,security,curPrice,factor):		
		bRet = self.macdCls.isMacdHightDeathCross(context,security,curPrice,factor)
		if(bRet):
			count = self.macdCls.getCurDeathCount(security)
			count = count+1
			if(count >= 2):
				order_target(code,0)
				self.macdCls.removeCurDeathCount(security)
			else:
				self.macdCls.setCurDeathCount(security,count)
				

