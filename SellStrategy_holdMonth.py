# coding=utf-8

import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
class SellStrategy_holdMonth:
	def __init__(self,buyCtDict,holdDays = 30):
		self.util = MyUtil()
		self.buyCtDict = buyCtDict
		self.holdDays = holdDays

	def sell(self,context,security):		
		buyCtDict = self.buyCtDict[security]
		buyDate = buyCtDict["buyDate"]
		if buyDate == context.current_dt.date():
			
			return
		delta = context.current_dt.date() - buyDate
		if(delta.days>=self.holdDays):
			order_target(security, 0)
			del self.buyCtDict[security]			

