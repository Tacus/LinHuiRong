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
	g.firstDays = 120
	g.secondDays = 60
	g.thirdDays = 30
def handle_data(context, data):
	

	queryObj = query(valuation.code,valuation.pcf_ratio,).filter(valuation.pcf_ratio > 0).order_by(
        # 按市值降序排列
        valuation.pcf_ratio.desc()
    ).limit(500)

	fmtDf =  get_fundamentals(queryObj)
	securities = fmtDf.code.values.tolist()
	# get_current_data()
	end_date = context.current_dt - timedelta(1)
	firstPanel = get_price(securities, end_date = end_date, fields = "avg",count = g.firstDays)
	secondPanel = get_price(securities, end_date = end_date, fields = "avg",count = g.secondDays)
	thirdPanel = get_price(securities, end_date = end_date, fields = "avg",count = g.thirdDays)