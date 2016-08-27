import pandas as pd
import numpy as np
# import matplotlib as talib
import talib
import datetime
from  MyMacd import *
from AdjustTimes import *
from MyUtil import *
from jqdata import *
def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    # 000001(股票:平安银行)
    # g.security = get_all_securities(["stock"]).index
    g.security = get_index_stocks('000300.XSHG')

    # enable_profile()
    # g.security = ['002573.XSHE']
    # g.security = get_security_info('000300.XSHG')
    g.maxBuyStocks = 10
    g.buyAdjustTime = 7

    g.volumeRatio = 0.1

    g.sellProfitRatio = 0.15
    
    g.macd = MyMacd(False)
    g.adjustTims  = AdjustTimes(False)
    g.util = MyUtil()

    set_option('use_real_price', True)
    g.highDict = {}
    # log.info(g.security)
    
    g.sellCtDict = {}
    g.sellAdjustTime = 3
    g.sellFastAvgDays= 3
    g.sellSlowAvgDays= 5

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    securities = g.security
    for security in securities:
        adjustTimes = g.adjustTims.getTimesOfAdjust(context,data,security)
        g.util.logPrint("code:%s,adjustTimes:%s",security,adjustTimes)
        if not adjustTimes== None:
            buyFit = adjustTimes == g.buyAdjustTime
            if(buyFit):
                checkBuySit(security,context,data)

    sellStocksMethod(context,data) 
    
def sellStocksMethod(context,data):
    for code in context.portfolio.positions:
        dict = data[code]
        if(not dict.isnan() and not dict.paused):
        #   if g.sellCtDict.has_key(code):
            sellCtDict = g.sellCtDict[code]
            buyDate = sellCtDict["buyDate"]
            adjustTime = sellCtDict["adjustTime"]
            endDate = sellCtDict["endDate"]
            lastRet = sellCtDict["lastRet"]
            if buyDate == context.current_dt.date():
                continue
            fastAvg = get_price(code,end_date = endDate, fields = ['avg'],count = g.sellFastAvgDays,skip_paused = True)
            fastAvg = sum(fastAvg.avg)/g.sellFastAvgDays
            slowAvg = get_price(code,end_date = endDate, fields = ['avg'],count = g.sellSlowAvgDays,skip_paused = True)
            slowAvg = sum(slowAvg.avg)/g.sellSlowAvgDays
            if(fastAvg == slowAvg):
                bRet = not lastRet
            else:
                bRet = (fastAvg - slowAvg) >0
            if bRet != lastRet :
                g.util.logPrint ("卖出判断：%s,code:%s adjustTime time:%s",str(context.current_dt.date()),code,adjustTime)
                adjustTime = adjustTime +1
                if(adjustTime == g.sellAdjustTime):
                    order_target(code, 0)
            sellCtDict["adjustTime"] = adjustTime
            sellCtDict["lastRet"] = bRet
            sellCtDict["endDate"] = context.current_dt.date()
        else:
            continue
def checkBuySit(security,context,data):
    if security in context.portfolio.positions:
        return
    tenVolume = get_price(security,end_date = context.current_dt,frequency ='1d', fields = ['volume'],count = 10,skip_paused=True)
    volumeRatioTen = tenVolume['volume'].sum()/10
    fiveVolume = get_price(security,end_date = context.current_dt,frequency ='1d', fields = ['volume'],count = 5,skip_paused=True)
    # if 
    volumeRatioFive = fiveVolume['volume'].sum()/5
    if volumeRatioTen ==0 :
        g.util.logPrint( '十日均线为0', security)
        volumeRatioTen = 1
    g.util.logPrint ('%s,code:%s,5/10 量比：%s',str(context.current_dt.date()),security,volumeRatioFive/volumeRatioTen)
    if(volumeRatioFive/volumeRatioTen > g.volumeRatio):
        macdFit = g.macd.isMacd(context,data,security)
        g.util.logPrint("%s,code:%s,macdFit:%s",str(context.current_dt.date()),security,str(macdFit))
        if(macdFit):
            #20天均线上扬
            # lastEndDate = context.current_dt - timedelta(1)
            # lastAvg= get_price(security, end_date=None, frequency='1d', fields='avg',  count=20)
            # lastAvg = lastAvg.avg.sum()/20
            # curAvg = get_price(security, end_date=context.current_dt, frequency='1d', fields='avg',  count=20)
            # curAvg = curAvg.avg.sum()/20
            # if(curAvg - lastAvg)>0:
            curPrice = data[security].open
            curTotalSts = len(context.portfolio.positions)
            if curTotalSts == g.maxBuyStocks:
                return
            perCash = 1.0/(g.maxBuyStocks - curTotalSts)
            count = context.portfolio.cash*perCash/ curPrice
            order(security, count)
            sellCtDict = {}
            sellCtDict["buyDate"] = context.current_dt.date()
            sellCtDict["adjustTime"] = 0
            sellCtDict["endDate"] = context.current_dt.date()
            sellCtDict["lastRet"] = True
            g.sellCtDict[security] = sellCtDict