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
def handle_data(context, data):
	
	end_date = context.current_dt - timedelta(1)
	panel = get_price(g.securities.tolist(), end_date = end_date, fields = ["close","volume"],count = g.lastingDays+1)
	closeDf = panel.close
	volumeDf = panel.volume
	queryObj = query(valuation.code,valuation.market_cap,valuation.pcf_rati,).order_by(
        # 按市值降序排列
        valuation.pcf_rati.desc()
    ).limit(500)
    
	return get_fundamentals(queryObj)


	code	代码	带后缀.XSHE/.XSHG	
	day	日期	取数据的日期	
	capitalization	总股本(万股)	公司已发行的普通股股份总数	
	circulating_cap	流通股本(万股)	公司已发行的境内上市流通、以人民币兑换的股份总数	
	market_cap	总市值(亿元)	总市值是指在某特定的时间内，交易所挂牌交易全部证券(以总股本计)按当时价格计算的证券总值	收盘价*总股本*交易币种兑人民币汇率
	circulating_market_cap	流通市值(亿)	指在某特定时间内当时可交易的流通股股数乘以当时股价得出的流通总价值。	收盘价*流通股数
	turnover_ratio	换手率(%)	指在一定时间内市场中转手买卖的频率，是反映流通性强弱的指标之一。	换手率=[指定交易日成交量(手)*100/截至该日的自由流通股本(股)]*100%
	pe_ratio	动态市盈率	每股市价为每股收益的倍数，反映投资人对每元净利润所愿支付的价格，用来估计的投资报酬和风险	市盈率（PE，TTM）=（在指定交易日期的收盘价*当日人民币外汇挂牌价*截止当日公司总股本）/归属于母公司股东的净利润。这里的“归属于母公司股东的净利润”指预测未来的净利润。
	pe_ratio_lyr	市盈率LYR	以上一年度每股盈利计算的静态市盈率. 股价/最近年度报告EPS	市盈率（PE）=（在指定交易日期的收盘价*当日人民币外汇牌价*截至当日公司总股本）/归属母公司股东的净利润。这里的“归属于母公司股东的净利润”是用上一年年报数据计算的净利润。比如今日是2016/7/26，取数据的时间段是14年年底到15年年底。
	pb_ratio	市净率	每股股价与每股净资产的比率	市净率=（在指定交易日期的收盘价*当日人民币外汇牌价*截至当日公司总股本）/归属母公司股东的权益。
	ps_ratio	市销率TTM	市销率为价格与每股销售收入之比，市销率越小，通常被认为投资价值越高。	市销率TTM=（在指定交易日期的收盘价*当日人民币外汇牌价*截至当日公司总股本）/营业总收入TTM
	pcf_rati
