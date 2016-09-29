# coding=utf-8
import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
class BuyStrategy_Delay:
    def __init__(self,macdCls,adjustTimeCls):
        self.macdCls = macdCls
        self.adjustTimeCls = adjustTimeCls
        self.buyAdjustTime = 6
        self.util = MyUtil()
        self.volumeRatio = 0.1
        self.maxBuyStocks = 10
        self.toBuyDict = {}

    def commonBuyStrategy(self,context,security,factor):
        if security in context.portfolio.positions:
            # self.util.logPrint("code:%s 已持仓",security)
            return

        curTotalSts = len(context.portfolio.positions)
        if curTotalSts == self.maxBuyStocks:
            # self.util.logPrint("code:%s 已满仓",security)            
            return

        df = self.getMarket_Cap(security)

        if len(df) < 1 :
            return
            
        adjustTimes = self.adjustTimeCls.getTimesOfAdjust(context,security,factor)
        # self.util.logPrint("code:%s,adjustTimes:%s",security,adjustTimes)
        if not adjustTimes== None:
            buyFit = adjustTimes == self.buyAdjustTime
            if(not buyFit):
                return
        if self.toBuyDict.has_key(security):
            days = self.toBuyDict[security]         
            if(days>=5):
                perCash = 1.0/(self.maxBuyStocks - curTotalSts)
                order_value(security, context.portfolio.cash*perCash)
            else:
                self.toBuyDict[security] = days +1
            return
        end_date = context.current_dt.date() - timedelta(1)
        curPrice = get_price(security,end_date = end_date,frequency ='1d', fields = 'close',count = 1,skip_paused=True)
        curPrice = curPrice.close[0]
        tenVolume = get_price(security,end_date = end_date,frequency ='1d', fields = ['volume'],count = 10,skip_paused=True)
        volumeRatioTen = tenVolume['volume'].sum()/10
        fiveVolume = get_price(security,end_date = end_date,frequency ='1d', fields = ['volume'],count = 5,skip_paused=True)
        volumeRatioFive = fiveVolume['volume'].sum()/5
        if volumeRatioTen ==0 :
            self.util.logPrint( '十日均线为0 code:%s', security)
            volumeRatioTen = 1
        if(volumeRatioFive/volumeRatioTen > self.volumeRatio):
            macdFit = self.macdCls.isMacdLowGoldCross(context,security,factor)
            self.util.logPrint("code:%s,volumeRation:%s,macdFit:%s",security,volumeRatioFive/volumeRatioTen,str(macdFit))
            if(macdFit):
                self.toBuyDict[security] = 1

    def getMarket_Cap(self,security):
        queryObj = query(valuation.code,valuation.market_cap).filter(valuation.market_cap<=100,valuation.code==security)
        return get_fundamentals(queryObj)

    def removeToBuyDict(self,security):
        del self.toBuyDict[security]