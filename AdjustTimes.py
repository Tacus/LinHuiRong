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
            timeDt = context.current_dt.date() - current_date
            if(timeDt.days > 0):
                if current_price>maxPrice:
                    highDict['lastRet'] = True
                    highDict['adjustTimes'] = 0
                    highDict['lastAdjustPrice'] = current_price
                    highDict['maxPrice']=current_price
                    highDict['endDate'] = context.current_dt.date()
                    highDict['maxDate'] = context.current_dt.date()
                    self.util.logPrint ('code:%s, preMaxPrice:%s,current_price:%s,创回测开始日前三个月以来新高，重新计算调整',security,maxPrice,current_price)
                    return
                elif(adjustTimes > self.buyAdjustTimes):
                    self.util.logPrint ('调整次数超%s次~！',self.buyAdjustTimes)
                    self.removeHighDict(security)
                    #TODO 重新计算调整次数
                    return
                self.util.logPrint( "中继计算：security：%s,endDate：%s,lastRet：%s,adjustTimes%s",security,current_date,lastRet,adjustTimes)
                lastRet,adjustTimes,lastAdjustPrice = self.calculatePreTimeOfAdjust(security,context.current_dt.date(),current_date,lastRet,adjustTimes,lastAdjustPrice)
                
                highDict['lastRet'] = lastRet
                highDict['adjustTimes'] = adjustTimes
                highDict['lastAdjustPrice'] = lastAdjustPrice
                highDict['endDate'] = context.current_dt.date()
            return adjustTimes
        else:
            endDate = context.current_dt.date()
            df = get_price(security,end_date = endDate,frequency = '1d',fields = 'high',skip_paused=True,count = self.period)
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
                    highDict['endDate'] = context.current_dt.date()
                    highDict['endDate'] = context.current_dt.date()
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
                    highDict['endDate'] = context.current_dt.date()
                    highDict['maxDate'] = index.date()
                    self.highDict[security] = highDict
                    # self.setHighDict(security,lastRet,adjustTimes,lastAdjustPrice)
                    return adjustTimes

    def calculatePreTimeOfAdjust(self,security,end_date,current_date,lastResult,current_adjustTimes,lastAdjustPrice = None):

        dfTenVolume = get_price(security,frequency='10d',start_date =current_date ,end_date = end_date , fields=['volume'], skip_paused=True)
        dfFiveVolume = get_price(security,frequency='5d',start_date =current_date ,end_date = end_date , fields=['volume'], skip_paused=True)
        count = max(len(dfTenVolume),len(dfFiveVolume))
        tenCount = count*10
        fiveCount = count*5
        dfTenVolume = get_price(security,frequency='10d',end_date = end_date , fields=['volume'], skip_paused=True,count = tenCount)
        dfTenMoney = get_price(security,frequency='10d',end_date = end_date , fields=['money'], skip_paused=True,count = tenCount)
        avgTens = dfTenMoney.money/dfTenVolume.volume
        
        dfFiveVolume = get_price(security,frequency='5d',end_date = end_date , fields=['volume'], skip_paused=True,count = fiveCount)
        dfFiveMoney = get_price(security,frequency='5d',end_date = end_date , fields=['money'], skip_paused=True,count = fiveCount)
        avgFives = dfFiveMoney.money/dfFiveVolume.volume
        # print "start:%s,end:%sfive:%s,ten:%s"%(str(current_date),str(end_date),len(avgFives.index),len(avgTens.index))
        for i in range(len(avgFives)):
            avgFive = avgFives[i]
            avgTen = avgTens[i]
            bRet = lastResult
            curAdjustPrice = lastAdjustPrice
            curIndexDate = avgTens.index[i]
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
                    self.util.logPrint ("1调整发生了:%s,代码：%s,调整次数:%s" ,str(curIndexDate),security,current_adjustTimes),
                else:
                    if(current_adjustTimes < 5):
                        # self.util.logPrint "非第一次调整并且调整次数小于5"
                        if(bRet):
                            curAdjustPrice = get_price(security,end_date = curIndexDate,frequency ='1d', fields = ['low'],count = 5,skip_paused=True)
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
                            self.util.logPrint ("2调整发生了:%s,代码：%s,调整次数:%s" ,str(curIndexDate),security,current_adjustTimes),
                        elif not bRet:
                            if current_adjustTimes != 1 and current_adjustTimes != 3:
                                # self.util.logPrint "下跌中的上扬不做幅度判断 符合调整"
                                curAdjustPrice = get_price(security,end_date = curIndexDate,frequency ='1d', fields = ['high'],count = 5,skip_paused=True)
                                curAdjustPrice = max(curAdjustPrice.high)
                                current_adjustTimes = current_adjustTimes +1
                                self.util.logPrint ("3调整发生了:%s,代码：%s,调整次数:%s" ,str(curIndexDate),security,current_adjustTimes),
                    else:
                        # self.util.logPrint( "非第一次调整并且调整次数大于5 符合调整")
                        current_adjustTimes = current_adjustTimes +1
                        self.util.logPrint ("4调整发生了:%s,代码：%s,调整次数:%s" ,str(curIndexDate),security,current_adjustTimes),
            lastAdjustPrice = curAdjustPrice
            lastResult = bRet
        # self.util.logPrint( security,str(curIndexDate),avgTen,avgFive,current_adjustTimes)
        return lastResult,current_adjustTimes,lastAdjustPrice
        # self.util.logPrint (avgTen , avgFive)
                
    def removeHighDict(self,security):
        if self.highDict.has_key(security):
            del self.highDict[security]

    def getHighDict(self,security):
        if self.highDict.has_key(security):
            return self.highDict[security]

    # def setHighDict(self,security):
        # if self.highDict.has_key(security):
        #     return self.highDict[security]