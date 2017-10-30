# coding=utf-8

import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
class SellStrategy_ProfitOrLoss15:
	def __init__(self):
		self.util = MyUtil()
		self.sellProfitRatio = 0.15

	def sell(self,context,security):
		pos = context.portfolio.positions[security]
		ratio = (pos.price - pos.avg_cost)/pos.avg_cost
		self.util.logPrint ("security:%s,profitRatio:%s,curPrice:%s,avg_cost:%s",security,ratio,pos.price,pos.avg_cost)
		if abs(ratio)>= self.sellProfitRatio:
			order_target(security, 0)
				

