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
    macdPeriod = 60

    def __init__(self,enableLog = True,macdFiled = "avg",curMacdFiled = "open",macdFastEmaModulus = 12.0,macdSlowEmaModulus = 26.0,
        macdDEAModulus = 9.0,macdM = 2.0,macdPeriod = 60):
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
        self.util = MyUtil(enableLog)

    def isMacd(self,context,data,security):
        dict = data[security]
        if(not dict.isnan() and not dict.paused):
            curPrice = dict.close
            factor =  dict.factor 
            return self.recursionCalMacd(context,security,curPrice,factor)
        
        return False
        
    #当前停牌 当前退市 当前未上市
    def recursionCalMacd(self,context,security,curPrice,factor):
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
                    curHisPrice = avgs[i]
                    currentSlowEma,currentFastEma,currentDea,currentMacd,currentDiff = self.caculateMacd(lastSlowEma,lastFastEma,lastDea,curHisPrice)
                    lastSlowEma = currentSlowEma
                    lastFastEma = currentFastEma
                    lastDea = currentDea
                    lastMacd = currentMacd
                    date = avgs.index[i].date()
                    self.setLastTradeDayMacd(security,lastSlowEma,lastFastEma,lastDea,end_date)
                    # self.util.logPrint ("中继date:%s, currentMacd:%s,currentDiff:%s,currentDea:%s" ,str(avgs.index[i].date()),currentMacd,currentDiff,currentDea)
                 
        else:
            self.util.logPrint ("start caculate macd")
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
                if i == len(avgs) - 1:
                    self.setLastTradeDayMacd(security,currentSlowEma,currentFastEma,currentDea,end_date)
                    
                lastSlowEma = currentSlowEma
                lastFastEma = currentFastEma
                lastDea = currentDea
                lastMacd = currentMacd
                # self.util.logPrint ("date:%s, currentMacd:%s,currentDiff:%s,currentDea:%s" ,str(avgs.index[i].date()),currentMacd,currentDiff,currentDea)
       
        currentSlowEma,currentFastEma,currentDea,currentMacd,currentDiff = self.caculateMacd(lastSlowEma,lastFastEma,lastDea,curPrice)
        
        # caculateMacd(lastSlowEma,lastFastEma,lastDea,curPrice)
        # record(price = curPrice)
        # record(macd=currentMacd,diff = currentDiff,dea = currentDea,stand = 0)
        
        #低位金叉
        #self.util.logPrint lastMacd, currentMacd,
        if(lastMacd <0 and currentMacd >=0):
            self.util.logPrint ('金叉')
            return True
            
        if(lastMacd >0 and currentMacd <=0):
            self.util.logPrint ('死叉')
        #高位金叉
        
        return False
        
    def caculateMacd(self,lastSlowEma,lastFastEma,lastDea,curPrice):
        currentSlowEma = lastSlowEma*(1-self.slowModulus) + curPrice*self.slowModulus
        currentFastEma = lastFastEma*(1-self.fastModulus) + curPrice*self.fastModulus
        currentDiff =  currentFastEma - currentSlowEma
        currentDea = lastDea*(1-self.deaModulus) + currentDiff*self.deaModulus
        currentMacd = 2*(currentDiff - currentDea)
        return currentSlowEma,currentFastEma,currentDea,currentMacd,currentDiff
        
        
    def setLastTradeDayMacd(self,security,slowEma,fastEma,Dea,date):
        if self.macdDict.has_key(security):
            securityDt = self.macdDict[security]
            macdDict = {}
            macdDict["slowEma"] = slowEma
            macdDict["fastEma"] = fastEma
            macdDict["dea"] = Dea
            macdDict["date"] = date
            securityDt.append(macdDict)
        else:
            securityDt = list()
            macdDict = {}
            macdDict["slowEma"] = slowEma
            macdDict["fastEma"] = fastEma
            macdDict["dea"] = Dea
            macdDict["date"] = date
            securityDt.append(macdDict)
            self.macdDict[security] = securityDt
    def removeTradeDayMacd(self,security):
        if self.macdDict.has_key(security):
           del self.macdDict[security]
            
    def getLastTradeDayMacd(self,security):
        if self.macdDict.has_key(security):
            securityDt = self.macdDict[security]
            macdDict = securityDt[len(securityDt) - 1]
            return macdDict