#coding: utf-8
from BaseClass import *
import talib as tb
import numpy as np
class StockInfo(BaseClass):
    def __init__(self,security,industry,industry_name,swl):
        self.security = security
        self.industry = industry
        self.swl = swl
        self.industry_name = industry_name
        pass
    def set_data(self,increase,close_price,close_prices,cur_rs,ema_rs,volume):
        self.increase = increase
        self.close_price = close_price
        self.close_prices = close_prices
        self.cur_rs = cur_rs
        self.ema_rs = ema_rs
        self.volume = volume

    def __str__(self):
        value = "行业：%s,股票代码:%s,increase:%s,cur_rs:%s,ema_rs:%s"%(self.industry_name,self.security,self.increase,self.cur_rs,self.ema_rs)
        return value
class CustomIndustry:
    def __init__(self,industry):
        self.industry = industry
        self.stock_infos = list()
    def init_data(self):
        pass

    def check_ema_rs(self,series_market_closes):
        values = self.cal_value()
        series_rs = values/series_market_closes
        ema_rs = tb.EMA(np.array(series_rs),39)
        # print(values,ema_rs,series_rs)
        self.cur_rs = series_rs[-1]
        self.cur_emars = ema_rs[-1]
        return self.cur_rs > self.cur_emars

    def add_stockinfo(self,stock_info):
        self.stock_infos.append(stock_info)
    def cal_value(self):
        # value = 0
        values = 0
        for index in range(len(self.stock_infos)):
            stock_info = self.stock_infos[index]
            # value += stock_info.close_price
            if(index == 0):
                values = stock_info.close_prices
            else:
                values += stock_info.close_prices
        # value = round(value/len(self.stock_infos),4)
        values = values/len(self.stock_infos)
        return values
    def __str__(self):
        text = ""
        for stock_info in self.stock_infos:
            text = text + str(stock_info)+";"
        return "CustomIndustry:"+text