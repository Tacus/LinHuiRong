# coding=utf-8
import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
class AdjustTimes:
    period = 120
    buyAdjustTimes = 7
    fMinDownRatio = 0.15
    sMinDownRatio = 0.1
    fastAvgDays = 5
    slowAvgDays = 10
    highDict = {}
    def __init__(self,enableLog = True,period = 120,buyAdjustTimes = 7,fMinDownRatio = 0.15,sMinDownRatio = 0.1,fastAvgDays = 5,slowAvgDays = 10):
        self.period = period
        self.buyAdjustTimes = buyAdjustTimes
        self.fMinDownRatio = fMinDownRatio
        self.sMinDownRatio = sMinDownRatio
        self.fastAvgDays = fastAvgDays
        self.slowAvgDays = slowAvgDays
        self.highDict = {}
        self.util = MyUtil(enableLog)
    
    def getTimesOfAdjust(self,context,data,security):
        dict = data[security]
        if(not dict.isnan() and not dict.paused):
            curPrice = dict.close
            factor =  dict.factor
            if(not factor == 1.0):
                self.removeHighDict(security)
                self.util.logPrint ("除权factor:%s，重新计算调整次数"%factor)
        else:
            return
        
        current_price =  data[security].high
        if self.highDict.has_key(security):
            highDict = self.highDict[security]
            lastRet = highDict['lastRet']
            adjustTimes = highDict['adjustTimes']
            lastAdjustPrice = highDict['lastAdjustPrice']
            maxPrice =  highDict['maxPrice']
            current_date = highDict['endDate']
            if current_price>maxPrice:
                highDict['lastRet'] = True
                highDict['adjustTimes'] = 0
                highDict['lastAdjustPrice'] = current_price
                highDict['maxPrice']=current_price
                highDict['endDate'] = context.current_dt.date() + timedelta(1)
                self.util.logPrint ('%s，code:%s, preMaxPrice:%s,current_price:%s,创回测开始日前三个月以来新高，重新计算调整',str(context.current_dt.date()),security,maxPrice,current_price)
                return
            elif(adjustTimes > self.buyAdjustTimes):
                self.util.logPrint ('调整次数超%s次~！',self.buyAdjustTimes)
                #TODO 重新计算调整次数
                return
            self.util.logPrint( "中继计算：security：%s,endDate：%s,current_date：%s,lastRet：%s,adjustTimes%s",security,context.current_dt.date(),current_date,lastRet,adjustTimes)
            lastRet,adjustTimes,lastAdjustPrice = self.calculatePreTimeOfAdjust(security,context.current_dt.date(),current_date,lastRet,adjustTimes,lastAdjustPrice)
            
            highDict['lastRet'] = lastRet
            highDict['adjustTimes'] = adjustTimes
            highDict['lastAdjustPrice'] = lastAdjustPrice
            highDict['endDate'] = context.current_dt.date() + timedelta(1)
            return adjustTimes
        else:
            endDate = context.current_dt.date()
            df = get_price(security,end_date = endDate,frequency = '1d',fields = 'high',skip_paused=True,count = self.period)
            index = df.high.argmax()
            if not pd.isnull(index):
                price = df.high[index]
                self.util.logPrint ("%s,%s" ,str(context.current_dt.date()),str(index.date()))
                if current_price >= price:
                    highDict = {}
                    highDict['lastRet'] = True
                    highDict['adjustTimes'] = 0
                    highDict['lastAdjustPrice'] = current_price
                    highDict['maxPrice']=current_price
                    highDict['endDate'] = context.current_dt.date() + timedelta(1)
                    self.highDict[security] = highDict
                else:
                    #记录当前均价
                    # curAdjustPrice = get_price(security,end_date = index,frequency ='1d', fields = ['high'],count = 5)
                    # curAdjustPrice = max(curAdjustPrice.high)
                    currentDate = index.date() + timedelta(1)
                    lastRet,adjustTimes,lastAdjustPrice = self.calculatePreTimeOfAdjust(security,context.current_dt.date(),currentDate,True,0,price)
                    highDict = {}
                    highDict['lastRet'] = lastRet
                    highDict['adjustTimes'] = adjustTimes
                    highDict['lastAdjustPrice'] = lastAdjustPrice
                    highDict['maxPrice']=price
                    highDict['endDate'] = context.current_dt.date() + timedelta(1)
                    self.highDict[security] = highDict
                    return adjustTimes

    def calculatePreTimeOfAdjust(self,security,end_date,current_date,lastResult,current_adjustTimes,lastAdjustPrice = None):
        if(current_date > end_date):
            self.util.logPrint("%s，Code:%s,calculatePreTimeOfAdjust",str(current_date),security)
            return lastResult,current_adjustTimes,lastAdjustPrice
        dfTen = get_price(security,frequency='1d',end_date = current_date , fields=['avg'], count=self.slowAvgDays,skip_paused=True)
        avgTen = sum(dfTen.avg)/self.slowAvgDays
        
        dfFive = get_price(security,frequency='1d',end_date = current_date , fields=['avg'], count=self.fastAvgDays,skip_paused=True)
        avgFive = sum(dfFive.avg)/self.fastAvgDays
        bRet = lastResult
        curAdjustPrice = lastAdjustPrice
        if avgFive == avgTen:
            bRet = not lastResult
        else:
            bRet = (avgFive - avgTen)>0
        if(bRet != lastResult):
            self.util.logPrint( "%s，code:%s,均线交叉avgFive:%s ,avgTen:%s " ,str(current_date),security,avgFive,avgTen)
            if(current_adjustTimes == 0):
                # pass
                # self.util.logPrint " 第一次调整不做幅度判断 符合调整"
                current_adjustTimes = current_adjustTimes +1
                self.util.logPrint ("1调整发生了:%s,代码：%s,调整次数:%s" ,str(current_date),security,current_adjustTimes),
            else:
                if(current_adjustTimes < 5):
                    # self.util.logPrint "非第一次调整并且调整次数小于5"
                    adjustRatio = ( curAdjustPrice - lastAdjustPrice) / lastAdjustPrice
                    adjustRatio = abs(adjustRatio)
                    if(bRet):
                        if current_adjustTimes == 2 and adjustRatio > self.fMinDownRatio:
                            curAdjustPrice = get_price(security,end_date = current_date,frequency ='1d', fields = ['low'],count = 5,skip_paused=True)
                            curAdjustPrice = max(curAdjustPrice.low)
                            current_adjustTimes = current_adjustTimes +1
                        elif current_adjustTimes == 4 and adjustRatio > self.sMinDownRatio:
                            curAdjustPrice = get_price(security,end_date = current_date,frequency ='1d', fields = ['low'],count = 5,skip_paused=True)
                            curAdjustPrice = max(curAdjustPrice.low)
                            current_adjustTimes = current_adjustTimes +1
                        elif current_adjustTimes >4:
                            curAdjustPrice = get_price(security,end_date = current_date,frequency ='1d', fields = ['low'],count = 5,skip_paused=True)
                            curAdjustPrice = max(curAdjustPrice.low)
                            current_adjustTimes = current_adjustTimes +1
                        #记录当前均价
                        # self.util.logPrint "下跌幅度判断 下跌幅度大于15 符合调整"
                        self.util.logPrint ("2调整发生了:%s,代码：%s,调整次数:%s" ,str(current_date),security,current_adjustTimes),
                    elif not bRet:
                        # self.util.logPrint "下跌中的上扬不做幅度判断 符合调整"
                        curAdjustPrice = get_price(security,end_date = current_date,frequency ='1d', fields = ['high'],count = 5,skip_paused=True)
                        curAdjustPrice = max(curAdjustPrice.high)
                        current_adjustTimes = current_adjustTimes +1
                        self.util.logPrint ("3调整发生了:%s,代码：%s,调整次数:%s" ,str(current_date),security,current_adjustTimes),
                else:
                    # self.util.logPrint( "非第一次调整并且调整次数大于5 符合调整")
                    current_adjustTimes = current_adjustTimes +1
                    self.util.logPrint ("4调整发生了:%s,代码：%s,调整次数:%s" ,str(current_date),security,current_adjustTimes),
        current_date = current_date + timedelta(1)
        # self.util.logPrint( security,str(current_date),avgTen,avgFive,current_adjustTimes)
        return self.calculatePreTimeOfAdjust(security,end_date,current_date,bRet,current_adjustTimes,curAdjustPrice)
        # self.util.logPrint (avgTen , avgFive)
                
    def removeHighDict(self,security):
        if self.highDict.has_key(security):
            del self.highDict[security]
