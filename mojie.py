import math
import talib
import numpy as np
import pandas as pd
from jqdata import *
from dateutil.relativedelta import relativedelta
def initialize(context):
	# g.securities = get_all_securities(["stock"]).index	
	g.securities = get_index_stocks('000906.XSHG')	

	# 先选取市现率最低500只，再从中选取半年内均值偏差最小的100只
	# ，接着再选出三个月内均值偏差最小的50只，
	# 然后是选出一个月内均值偏差最小的20只，最后用资金流选出若干只作为标的
# continuous price fallDown ;continunous volume fallDown ,continunous money inject
	g.firstFrequence = "180d"
	g.secondFrequence = "90d"
	g.thirdFrequence = "30d"

	g.holderSecurity = '000002.XSHG'


	g.maxStocks = 5

	run_monthly(buy_stock, 1,  time='14:45')
	# run_monthly(sell_stock, 1,  time='open')
def handle_data(context, data):
	sell_stock(context,data)
	pass

def sell_stock(context,data):
	for security in context.portfolio.positions:
# 		print data[security]
		if( not data[security].isnan() and not data[security].paused):
			sData = data[security]
			start_date = context.current_dt.date() - relativedelta(months = 3)
			start_date = start_date.replace(day = 1)
			end_date = context.current_dt - timedelta(context.current_dt.date().day)

			secondVDf = get_price(security,start_date = start_date , end_date = end_date,fields = "volume" )
			secondMDf = get_price(security,start_date = start_date, end_date = end_date,fields = "money" )		
			avg = secondMDf['money'].sum()/secondVDf['volume'].sum()
			close = sData.close
			print "code:%s,close:%s,avg:%s:"%(security, close,avg)
			if(close - avg >0):
				order_target(security, 0)
def buy_stock(context):	
	queryObj = query(valuation.code,valuation.pcf_ratio,).filter(valuation.pcf_ratio > 0,valuation.code.in_(g.securities)).order_by(
		# 按市值降序排列
		valuation.pcf_ratio.desc()
	).limit(500)

	fmtDf =  get_fundamentals(queryObj)
	securities = fmtDf.code.values.tolist()
	# get_current_data()
# 	print securities
# 	return 
	currentDate = context.current_dt.date() - timedelta(1)
	start_date = context.current_dt.date() - relativedelta(months = 6)
	start_date = start_date.replace(day = 1)
	end_date = context.current_dt - timedelta(context.current_dt.date().day)
	# end_date = end_date.replace(day = 1)

	firstVDf = get_price(securities,start_date = start_date , end_date = end_date ,fields = ["volume"] )
	if len(firstVDf) > 0:
		firstMDf = get_price(securities, start_date = start_date ,end_date = end_date,fields = ["money"] )
		avg = firstMDf['money'].sum()/firstVDf['volume'].sum()
		close = get_price(securities, end_date = currentDate ,fields = ["close"],count = 1 )
		currentDate = close.close.index[0]
		close = close.close.T
		close = close[currentDate]

		df = close / avg
		df = abs(df)
		df = df[pd.notnull(df)]
		df = df.order().head(100)
		securities = df.index.tolist()
		
		# print df
		# return
		start_date = context.current_dt.date() - relativedelta(months = 3)
		start_date = start_date.replace(day = 1)
		end_date = context.current_dt - timedelta(context.current_dt.date().day)

		secondVDf = get_price(securities,start_date = start_date , end_date = end_date,fields = "volume" )
		secondMDf = get_price(securities,start_date = start_date, end_date = end_date,fields = "money" )
		
		avg = secondMDf['money'].sum()/secondVDf['volume'].sum()

		df = close / avg
		df = abs(df)
		df = df[pd.notnull(df)]
		df = df.order().head(50)
		securities = df.index.tolist()

		start_date = context.current_dt.date() - relativedelta(months = 1)
		start_date = start_date.replace(day = 1)
		end_date = context.current_dt - timedelta(context.current_dt.date().day)

		thirdVDf = get_price(securities,start_date = start_date, end_date = end_date,fields = "volume" )
		thirdMDf = get_price(securities,start_date = start_date, end_date = end_date,fields = "money" )
		
		avg = thirdMDf['money'].sum()/thirdVDf['volume'].sum()
		df = close/ avg
		df = abs(df)
		df = df[pd.notnull(df)]
		df = df.order().head(20)
		securities = df.index.tolist()

# 		print securities
		tmpDf = get_price(g.holderSecurity , end_date = end_date,fields = "close",count = 5 )
		start_date = tmpDf.index[0]
		mDf = get_money_flow(securities, start_date = start_date, end_date = currentDate, fields=["net_pct_main",'sec_code'])
		mDf = mDf[mDf>0]
		mDf = mDf[pd.notnull(mDf.net_pct_main)]
# 		print mDf.net_pct_main.values
# 		print mDf.cumsum()
		
		tmp = mDf.groupby(['sec_code']).sum()
		securities = tmp.sort(columns = "net_pct_main",ascending = False).head(g.maxStocks).index
		for security in securities:
			value = 1./len(securities)*context.portfolio.cash
			order_target_value(security, value)