# coding=utf-8
import pandas as pd
import datetime
from datetime import *
from MyUtil import *
from kuanke.user_space_api import *
#import datetime.timedelta

class MyMacd:
    # 实测环境每天执行 ，handler_data 9.30调用 则只能取到昨天价格
    macdFiled = 'avg'
    curMacdFiled = "open"
    macdSlowEmaModulus = 26.0
    macdFastEmaModulus = 12.0
    macdDEAModulus = 9.0
    macdM = 2.0
    fastModulus = 0
    slowModulus = 0
    deaModulus =  0
    macdDict = {}
    deathCountDict = {}
    macdPeriod = 60
    maxCache = 60

    def __init__(self,enableLog = True,macdFiled = "avg",curMacdFiled = "open",macdFastEmaModulus = 12.0,macdSlowEmaModulus = 26.0,
        macdDEAModulus = 9.0,macdM = 2.0,macdPeriod = 60,maxCache = 60):
        self.macdFiled = macdFiled
        # 实测环境每天执行 ，handler_data 9.30调用 则只能取到昨天价格
        self.curMacdFiled = curMacdFiled
        self.macdSlowEmaModulus = macdSlowEmaModulus
        self.macdFastEmaModulus = macdFastEmaModulus
        self.macdDEAModulus = macdDEAModulus
        self.macdM = macdM
        self.macdPeriod = macdPeriod
        self.fastModulus = self.macdM/self.macdFastEmaModulus+1
        self.slowModulus = self.macdM/self.macdSlowEmaModulus+1
        self.deaModulus =  self.macdM/self.macdDEAModulus+1
        self.maxCache = maxCache
        self.util = MyUtil(enableLog)

    def isMacdGoldCross(self,context,data,security):
        
        self.calculateMacdInfo(context,data,security)
        list = self.getLastTradeDayMacd(security,3)
        if(list and len(list)>2):
            prePreInfo = list[0]
            preInfo = list[1]
            curInfo = list[2]
            self.util.logPrint("isMacdGoldCross,curInfo:%s,preInfo:%s,dea:%s"
                            , curInfo["macd"],preInfo["macd"],curInfo["dea"])

            if((preInfo["macd"] <0 and curInfo["macd"] >0)
             or (prePreInfo["macd"]<=0 and preInfo["macd"] == 0 and curInfo["macd"] >0)):
                self.util.logPrint ('金叉')
                return True  
        return False

    def isMacdLowGoldCross(self,context,data,security):
        # 低位金叉
        self.calculateMacdInfo(context,data,security)
        list = self.getLastTradeDayMacd(security,3)
        if(list and len(list)>2):
            prePreInfo = list[0]
            preInfo = list[1]
            curInfo = list[2]
            self.util.logPrint("isMacdGoldCross,curInfo:%s,preInfo:%s,dea:%s"
                            , curInfo["macd"],preInfo["macd"],curInfo["dea"])

            if((preInfo["macd"] <0 and curInfo["macd"] >0 and curInfo["dea"]<0)
             or (prePreInfo["macd"]<=0 and preInfo["macd"] == 0 and curInfo["macd"] >0 and curInfo["dea"]<0)):
                self.util.logPrint ('金叉')
                return True  
        return False
        
    def isMacdHightGoldCross(self,context,data,security):
        pass

    def isMacdLowDeathCross(self,context,data,security):
        pass

    def isMacdHightDeathCross(self,context,data,security):
        #高位死叉
        self.calculateMacdInfo(context,data,security)
        list = self.getLastTradeDayMacd(security,3)
        if(list and len(list)>2):
            prePreInfo = list[0]
            preInfo = list[1]
            curInfo = list[2]
            self.util.logPrint("isMacdGoldCross,curInfo:%s,preInfo:%s,dea:%s"
                            , curInfo["macd"],preInfo["macd"],curInfo["dea"])

            if((preInfo["macd"] >0 and curInfo["macd"] < 0 and curInfo["dea"]>0)
             or (prePreInfo["macd"]>=0 and preInfo["macd"] == 0 and curInfo["macd"] < 0 and curInfo["dea"]>0)):
                self.util.logPrint ('死叉')
                return True  
        return False

    def calculateMacdInfo(self,context,data,security):
        dict = data[security]
        factor = 1.0
        if(not dict.isnan() and not dict.paused):
            curPrice = dict.close
            factor =  dict.factor 
        else:
            return None

        if(not factor == 1.0):
            self.removeTradeDayMacd(security)   
            self.util.logPrint ("除权factor:%s，重新计算macd",factor)
        lastSlowEma = 0
        lastFastEma = 0
        lastMacd = 0
        lastDea = 0
        currentSlowEma = 0
        currentFastEma = 0
        currentMacd = 0
        currentDea = 0
        currentDiff = 0
        macdDict = self.getLastTradeDayMacd(security)
        if not macdDict == None:
            lastDate = macdDict['date']
            lastSlowEma = macdDict['slowEma']
            lastFastEma = macdDict['fastEma']
            lastDea = macdDict['dea']
            timeDt = context.current_dt.date() - lastDate
            if(timeDt.days > 0):
                start_date = lastDate
                end_date = context.current_dt.date()
                df = get_price(security, start_date = start_date ,end_date=end_date, fields=[self.macdFiled], skip_paused=True)
                avgs = df[self.macdFiled]
                for i in range(len(avgs)):
                     # self.util.logPrint ("lastSlowEma:%s,lastFastEma:%s,lastDea:%s" ,lastSlowEma,lastFastEma,lastDea)
                    date = avgs.index[i].date()
                    curHisPrice = avgs[i]
                    currentSlowEma,currentFastEma,currentDea,currentMacd,currentDiff = self.caculateMacd(lastSlowEma,lastFastEma,lastDea,curHisPrice)
                    self.setLastTradeDayMacd(security,currentSlowEma,currentFastEma,currentDea,currentMacd,date)
                    lastSlowEma = currentSlowEma
                    lastFastEma = currentFastEma
                    lastDea = currentDea
                    lastMacd = currentMacd
                    # self.util.logPrint ("中继date:%s, currentMacd:%s,currentDiff:%s,currentDea:%s" ,str(avgs.index[i].date()),currentMacd,currentDiff,currentDea)
            # #当前已经计算过
            # else:
            #     return
            
        else:
            end_date = context.current_dt.date()
            dict = get_security_info(security)
            startDate = dict.start_date
            days = end_date - startDate 
            if days.days < self.macdPeriod:
                df = get_price(security, start_date = startDate ,end_date=end_date, fields=[self.macdFiled], skip_paused=True)
            else:
                df = get_price(security, end_date=end_date, fields=[self.macdFiled], skip_paused=True,count=self.macdPeriod)
        # self.util.logPrint (curPrice)
            avgs = df[self.macdFiled]
        # self.util.logPrint (len(avgs))
            for i in range(len(avgs)):
            # self.util.logPrint ("lastSlowEma:%s,lastFastEma:%s,lastDea:%s" ,lastSlowEma,lastFastEma,lastDea)
                curHisPrice = avgs[i]
                if i==0:
                   pass
                elif i == 1:
                    currentSlowEma = lastSlowEma + curHisPrice*self.slowModulus
                    currentFastEma = lastFastEma + curHisPrice*self.slowModulus
                    currentDiff =  currentFastEma - currentSlowEma
                    currentDea = lastDea + currentDiff*self.deaModulus
                    currentMacd = 5*(currentDiff - currentDea)
                else:
                    currentSlowEma,currentFastEma,currentDea,currentMacd,currentDiff = self.caculateMacd(lastSlowEma,lastFastEma,lastDea,curHisPrice)
                    # self.util.logPrint ("currentSlowEma:%s,currentFastEma:%s,currentMacd:%s" ,currentSlowEma,currentFastEma,currentMacd)
                lastSlowEma = currentSlowEma
                lastFastEma = currentFastEma
                lastDea = currentDea
                lastMacd = currentMacd
                date = avgs.index[i].date()
                # self.util.logPrint ("date:%s, currentMacd:%s,currentDiff:%s,currentDea:%s" ,str(avgs.index[i].date()),currentMacd,currentDiff,currentDea)
                self.setLastTradeDayMacd(security,currentSlowEma,currentFastEma,currentDea,currentMacd,date)
        # currentSlowEma,currentFastEma,currentDea,currentMacd,currentDiff = self.caculateMacd(lastSlowEma,lastFastEma,lastDea,curPrice)
        # self.setLastTradeDayMacd(security,currentSlowEma,currentFastEma,currentDea,currentMacd,context.current_dt.date())
        # # caculateMacd(lastSlowEma,lastFastEma,lastDea,curPrice)
        # # record(price = curPrice)
        # # record(macd=currentMacd,diff = currentDiff,dea = currentDea,stand = 0)
        # info = {}
        # info["currentMacd"] = currentMacd
        # info["lastMacd"] = lastMacd
        # info["currentDiff"] = currentDiff
        # info["currentDea"] = currentDea
        # return info        
        
    def caculateMacd(self,lastSlowEma,lastFastEma,lastDea,curPrice):
        currentSlowEma = lastSlowEma*(1-self.slowModulus) + curPrice*self.slowModulus
        currentFastEma = lastFastEma*(1-self.fastModulus) + curPrice*self.fastModulus
        currentDiff =  currentFastEma - currentSlowEma
        currentDea = lastDea*(1-self.deaModulus) + currentDiff*self.deaModulus
        currentMacd = 2*(currentDiff - currentDea)
        return currentSlowEma,currentFastEma,currentDea,currentMacd,currentDiff
        
        
    def setLastTradeDayMacd(self,security,slowEma,fastEma,Dea,Macd,date):
        if self.macdDict.has_key(security):
            securityList = self.macdDict[security]
            if(len(securityList) >= self.maxCache):
                del securityList[0]
            macdDict = {}
            macdDict["slowEma"] = slowEma
            macdDict["fastEma"] = fastEma
            macdDict["dea"] = Dea
            macdDict["date"] = date
            macdDict["macd"] = Macd           
            securityList.append(macdDict)
        else:
            securityList = list()
            macdDict = {}
            macdDict["slowEma"] = slowEma
            macdDict["fastEma"] = fastEma
            macdDict["dea"] = Dea
            macdDict["date"] = date
            macdDict["macd"] = Macd            
            securityList.append(macdDict)
            self.macdDict[security] = securityList
    def removeTradeDayMacd(self,security):
        if self.macdDict.has_key(security):
           del self.macdDict[security]
            
    def getLastTradeDayMacd(self,security,count = None):
        if self.macdDict.has_key(security):
            securityList = self.macdDict[security]
            ret = None
            total = len(securityList)
            if(count and total>=count):
                ret = securityList[total - count:]
            elif count:
                ret = securityList
            else:
                ret = securityList[len(securityList) - 1]
            return ret

    #return list
    def getAllTradeDayMacd(self,security):
        if self.macdDict.has_key(security):
            securityList = self.macdDict[security]
            return securityList


    def getCurDeathCount(self,security):
        iRet = 0
        if self.deathCountDict.has_key(security):
            iRet = self.deathCountDict[security]
        return iRet

    def setCurDeathCount(self,security,count):
        self.deathCountDict[security] = count

    def removeCurDeathCount(self,security):
        if self.deathCountDict.has_key(security):
            del self.deathCountDict[security]