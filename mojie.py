import math
import talib
import numpy as np
import pandas as pd
from jqdata import *
def initialize(context):
	g.securities = get_all_securities(["stock"]).index	

	# 先选取市现率最低500只，再从中选取半年内均值偏差最小的100只
	# ，接着再选出三个月内均值偏差最小的50只，
	# 然后是选出一个月内均值偏差最小的20只，最后用资金流选出若干只作为标的
# continuous price fallDown ;continunous volume fallDown ,continunous money inject
	g.firstFrequence = "180d"
	g.secondFrequence = "90d"
	g.thirdFrequence = "30d"

	g.holderSecurity = '000002.XSHG'
def handle_data(context, data):
	

	queryObj = query(valuation.code,valuation.pcf_ratio,).filter(valuation.pcf_ratio > 0).order_by(
		# 按市值降序排列
		valuation.pcf_ratio.desc()
	).limit(500)

	fmtDf =  get_fundamentals(queryObj)
	securities = fmtDf.code.values.tolist()
	# get_current_data()
# 	print securities
# 	return 
	end_date = context.current_dt - timedelta(1)
	firstVDf = get_price(securities, end_date = end_date,frequency = g.firstFrequence ,fields = ["volume"],count = 1 )
	if len(firstVDf) > 0:
		firstMDf = get_price(securities, end_date = end_date,frequency = g.firstFrequence ,fields = ["money"],count = 1 )
		# firstAvg = firstMDf['money']
		avg = firstMDf['money']/firstVDf['volume']
		close = get_price(securities, end_date = end_date ,fields = ["close"],count = 1 )
		df = close.close - avg
		date = df.index[0]
		df = abs(df.T)		
		df = df.sort(columns = date).head(100)
		securities = df.index.tolist()

		secondVDf = get_price(securities, end_date = end_date,frequency = g.secondFrequence ,fields = "volume",count = 1 )
		secondMDf = get_price(securities, end_date = end_date,frequency = g.secondFrequence ,fields = "money",count = 1 )
		
		avg = secondMDf['money']/secondVDf['volume']
		close = get_price(securities, end_date = end_date ,fields = ["close"],count = 1 )
		df = close.close - avg
		df = abs(df.T)		
		df = df.sort(columns = date).head(50)
		securities = df.index.tolist()


		thirdVDf = get_price(securities, end_date = end_date,frequency = g.thirdFrequence ,fields = "volume",count = 1 )
		thirdMDf = get_price(securities, end_date = end_date,frequency = g.thirdFrequence ,fields = "money",count = 1 )
		
		avg = thirdMDf['money']/thirdVDf['volume']
		close = get_price(securities, end_date = end_date ,fields = ["close"],count = 1 )
		df = close.close - avg
		df = abs(df.T)		
		df = df.sort(columns = date).head(20)
		securities = df.index.tolist()

# 		print securities

		tmpDf = get_price(g.holderSecurity , end_date = end_date,fields = "close",count = 5 )
		start_date = tmpDf.index[0]
		mDf = get_money_flow(securities, start_date = start_date, end_date = end_date, fields=["net_pct_main",'sec_code'])
		mDf = mDf[pd.notnull(mDf.net_pct_main)]
		mDf = mDf[mDf>0]
		# mDf = mDf.net_pct_main.values.sum()
		print mDf.groupby("net_pct_main")