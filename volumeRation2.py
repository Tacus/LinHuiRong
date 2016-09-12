import pandas as pd
import numpy as np
# import matplotlib as talib
import talib
import datetime

	# 最近2个交易日的成交均量是最近45个交易日成交均量的2倍
def initialize(context):
	set_option('use_real_price', True)
	g.security = get_all_securities(["stock"]).index

	#较长时间周期
	g.longPeriod = 45.0

	#较短时间周期
	g.shortPeriod = 2.0

	#倍率
	g.ratio = 2.0


def handle_data(context, data):
	securities = g.security
	for security in securities:
		dict = data[security]
		if(not dict.isnan() and not dict.paused):			
			volume_short = get_price(security,end_date = context.current_dt,frequency ='1d', fields = ['volume'],count = 2,skip_paused=True)
			volume_short_per = volume_short['volume'].sum()/g.shortPeriod
			volume_long = get_price(security,end_date = context.current_dt,frequency ='1d', fields = ['volume'],count = 45,skip_paused=True)
			volume_long_per = volume_long['volume'].sum()/g.longPeriod
			ratio = volume_short_per/volume_long_per
			if(ratio >= g.ratio):
				print "Code:%s,ratio：%s ,two days volume：%s,ForyFive days volume：%s"%(security,ratio,volume_short_per,volume_long_per)