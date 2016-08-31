# coding=utf-8
import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
class AdjustTimes:
    period = 120
    buyAdjustTimes = 6
    fMinDownRatio = 0.15
    sMinDownRatio = 0.1
    fastAvgDays = 5
    slowAvgDays = 10
    highDict = {}
    def __init__(self,enableLog = True,period = 120,buyAdjustTimes = 6,fMinDownRatio = 0.15,sMinDownRatio = 0.1,fastAvgDays = 5,slowAvgDays = 10):
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
        #今天停盘还是昨天停盘
        if(not dict.isnan() and not dict.paused):
            curPrice = dict.close
            factor =  dict.factor
            if(not factor == 1.0):
                self.removeHighDict(security)
                self.util.logPrint ("除权factor:%s，重新计算调整次数"%factor)
        else:
            return
        
        current_price =  data[security].high
        highDict = self.getHighDict(security)
        if highDict:
            lastRet = highDict['lastRet']
            adjustTimes = highDict['adjustTimes']
            lastAdjustPrice = highDict['lastAdjustPrice']
            maxPrice =  highDict['maxPrice']
            current_date = highDict['endDate']
            end_date = context.current_dt.date() - timedelta(1)
            start_date = current_date + timedelta(1)
            timeDt = context.current_dt.date() - current_date
            if(timeDt.days >= 0):
                if current_price>=maxPrice:
                    highDict['lastRet'] = True
                    highDict['adjustTimes'] = 0
                    highDict['lastAdjustPrice'] = current_price
                    highDict['maxPrice']=current_price
                    highDict['endDate'] = context.current_dt.date() - timedelta(1)
                    highDict['maxDate'] = context.current_dt.date() - timedelta(1)
                    self.util.logPrint ('code:%s, preMaxPrice:%s,current_price:%s,创回测开始日前三个月以来新高，重新计算调整',security,maxPrice,current_price)
                    return
                elif(adjustTimes > self.buyAdjustTimes):
                    self.util.logPrint ('调整次数超%s次~！',self.buyAdjustTimes)
                    self.removeHighDict(security)
                    #TODO 重新计算调整次数
                    return
                self.util.logPrint( "中继计算：security：%s,endDate：%s,lastRet：%s,adjustTimes%s",security,current_date,lastRet,adjustTimes)
                
                df = get_price(security, start_date = start_date ,end_date=end_date, fields='high', skip_paused=True)
                dateList = df.high.index.tolist()
                calculateDateList = self.getTradeDateList(dateList[0],dateList)
                
                lastRet,adjustTimes,lastAdjustPrice = self.calculatePreTimeOfAdjust(security,calculateDateList,lastRet,adjustTimes,lastAdjustPrice)
                
                highDict['lastRet'] = lastRet
                highDict['adjustTimes'] = adjustTimes
                highDict['lastAdjustPrice'] = lastAdjustPrice
                highDict['endDate'] = end_date
            return adjustTimes
        else:

            end_date = context.current_dt.date() - timedelta(1)
            dict = get_security_info(security)
            startDate = dict.start_date
            days = end_date - startDate 
            if days.days < self.period:
                df = get_price(security, start_date = startDate ,end_date=end_date, fields='high', skip_paused=True)
            else:
                df = get_price(security, end_date=end_date, fields='high', skip_paused=True,count=self.period)
            index = df.high.argmax()
            if not pd.isnull(index):
                price = df.high[index]
                self.util.logPrint ("Code:%s,maxPrice Date:%s" ,security,str(index.date()))
                if current_price >= price:
                    highDict = {}
                    highDict['lastRet'] = True
                    highDict['adjustTimes'] = 0
                    highDict['lastAdjustPrice'] = current_price
                    highDict['maxPrice']=current_price
                    highDict['endDate'] = end_date
                    highDict['maxDate'] = context.current_dt.date() - timedelta(1)
                    self.highDict[security] = highDict
                else:
                    #记录当前均价
                    # curAdjustPrice = get_price(security,end_date = index,frequency ='1d', fields = ['high'],count = 5)
                    # curAdjustPrice = max(curAdjustPrice.high)
                    calculateDateList = self.getTradeDateList(index,df.high.index.tolist())
                    lastRet,adjustTimes,lastAdjustPrice = self.calculatePreTimeOfAdjust(security,calculateDateList,True,0,price)
                    highDict = {}
                    highDict['lastRet'] = lastRet
                    highDict['adjustTimes'] = adjustTimes
                    highDict['lastAdjustPrice'] = lastAdjustPrice
                    highDict['maxPrice'] = price
                    highDict['endDate'] = end_date
                    highDict['maxDate'] = index.date()
                    self.highDict[security] = highDict
                    # self.setHighDict(security,lastRet,adjustTimes,lastAdjustPrice)
                    return adjustTimes

    def calculatePreTimeOfAdjust(self,security,calculateDateList,lastResult,current_adjustTimes,lastAdjustPrice = None):

        for i in range(len(calculateDateList)):
            current_date = calculateDateList[i]      
            bRet = lastResult
            dfTen = get_price(security,frequency='1d',end_date = current_date , fields='avg', count=self.slowAvgDays,skip_paused=True)
            avgTen = sum(dfTen.avg)/self.slowAvgDays
            dfFive = get_price(security,frequency='1d',end_date = current_date , fields='avg', count=self.fastAvgDays,skip_paused=True)
            avgFive = sum(dfFive.avg)/self.fastAvgDays

            print current_date,avgTen,avgFive
            # self.util.logPrint(avgFive,avgTen)
            curAdjustPrice = lastAdjustPrice
            if avgFive == avgTen:
                bRet = lastResult
            else:
                bRet = (avgFive - avgTen)>0
            if(bRet != lastResult):
                self.util.logPrint( "code:%s,均线交叉avgFive:%s ,avgTen:%s ",security,avgFive,avgTen)
                if(current_adjustTimes == 0):
                    # pass
                    # self.util.logPrint " 第一次调整不做幅度判断 符合调整"
                    current_adjustTimes = current_adjustTimes +1
                    self.util.logPrint ("1调整发生了:%s,代码：%s,调整次数:%s" ,str(current_date),security,current_adjustTimes),
                else:
                    if(current_adjustTimes < 5):
                        # self.util.logPrint "非第一次调整并且调整次数小于5"
                        if(bRet):
                            curAdjustPrice = get_price(security,end_date = current_date,frequency ='1d', fields = ['low'],count = 5,skip_paused=True)
                            curAdjustPrice = min(curAdjustPrice.low)
                            adjustRatio = ( curAdjustPrice - lastAdjustPrice) / lastAdjustPrice
                            adjustRatio = abs(adjustRatio)
                            if current_adjustTimes == 1 and adjustRatio > self.fMinDownRatio:                            
                                current_adjustTimes = current_adjustTimes +1
                            elif current_adjustTimes == 3 and adjustRatio > self.sMinDownRatio:
                                current_adjustTimes = current_adjustTimes +1
                            elif current_adjustTimes >4:
                                current_adjustTimes = current_adjustTimes +1
                            else:
                                curAdjustPrice = lastAdjustPrice
                            #记录当前均价
                            # self.util.logPrint "下跌幅度判断 下跌幅度大于15 符合调整"
                            self.util.logPrint ("2调整发生了:%s,代码：%s,调整次数:%s" ,str(current_date),security,current_adjustTimes),
                        elif not bRet:
                            if current_adjustTimes != 1 and current_adjustTimes != 3:
                                # self.util.logPrint "下跌中的上扬不做幅度判断 符合调整"
                                curAdjustPrice = get_price(security,end_date = current_date,frequency ='1d', fields = ['high'],count = 5,skip_paused=True)
                                curAdjustPrice = max(curAdjustPrice.high)
                                current_adjustTimes = current_adjustTimes +1
                                self.util.logPrint ("3调整发生了:%s,代码：%s,调整次数:%s" ,str(current_date),security,current_adjustTimes),
                    else:
                        # self.util.logPrint( "非第一次调整并且调整次数大于5 符合调整")
                        current_adjustTimes = current_adjustTimes +1
                        self.util.logPrint ("4调整发生了:%s,代码：%s,调整次数:%s" ,str(current_date),security,current_adjustTimes),
            lastResult = bRet
            lastAdjustPrice = curAdjustPrice
        return lastResult,current_adjustTimes,lastAdjustPrice

        # self.util.logPrint( security,str(current_date),avgTen,avgFive,current_adjustTimes)
        # return lastResult,current_adjustTimes,lastAdjustPrice
        # self.util.logPrint (avgTen , avgFive)
                
    def removeHighDict(self,security):
        if self.highDict.has_key(security):
            del self.highDict[security]

    def getHighDict(self,security):
        if self.highDict.has_key(security):
            return self.highDict[security]

    @staticmethod
    def getTradeDateList(startObj,dataList):
        index = dataList.index(startObj)
        ret = dataList[index:]
        return ret
