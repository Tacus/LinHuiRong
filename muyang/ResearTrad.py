#1、价格强势股的当前价格是否需要实时计算？√
#2、海龟交易的计算起始日期是否是根据当前交易开始日期累计，还是往前推
#3、需要考虑停牌，上市交易天数过小,这时候是否需要参与交易
#4、止损部分：加仓三次，止损计算针对的是每次加仓时的数据，还是最后一次

#enable_profile()
from jqdata import jy
import jqdata
import numpy as np
import pandas as pd
import math

from sqlalchemy import or_
from jy_sw_industry_code import *

jydf = jy.run_query(query(jy.SecuMain))

index_list = ['OpenPrice','ClosePrice','InnerCode']


def initialize():
    # g为全局变量
    g.sw1_weight = 1
    g.sw2_weight = 3
    g.stock_weight = 6
    g.total_value = 1000000
    g.current_cash = g.total_value
    #个股均线周期
    g.avg_period_1 = 50 
    g.avg_period_2 = 150
    g.avg_period_3 = 200
    #个股涨幅周期
    g.min_increase_period = 250
    g.max_increase_period = 250
    #个股上市最小自然日
    g.stock_listDays = 300 #420
    #指数涨幅计算自然日区间
    g.industry_rangeDays = 120
    #个股涨幅计算自然日区间
    g.stock_rangeDays = 250 #250

    g.debug_stocks = ["300323.XSHE"]
    # g.debug_stocks = None
    g.stock_pool = []
    g.position_pool = {}
    init_turtle_data()
    # run_weekly(weekly_fun,"open")
    #计算N天内最从高价回落最多%M

#获取有效股票并更新有效股票历史数据 price_info,eps_info
def before_trading_start():
    g.stock_pool = get_valid_stocks(g.debug_stocks)
    for single in g.stock_pool:
        single.run_daily()

    for _,stock_info in g.position_pool.items():
        stock_info.run_daily()
    # return g.valid_stocks

def handle_data( data):
    for _,stock_info in g.position_pool.items():
        order = stock_info.start_process()
        if order != None and order.filled  > 0 and order.is_buy :
            stock_info.add_buy_count( order.filled)
        elif(order != None and order.filled > 0 and not order.is_buy):
            stock_info.reduce_buy_count( order.filled)
            count = stock_info.get_buy_count()
            if(count <= 0):
                del g.position_pool[stock_info.code]

    for single in g.stock_pool:
        order = single.start_process()
        if order != None and order.filled  > 0 and order.is_buy :
            single.set_buy_count( order.filled)
            g.stock_pool.remove(single)
            g.position_pool[single.code] = single
    #订单追踪

def init_turtle_data():
    # 系统1入市的trailing date
    g.short_in_date = 20
    # 系统2入市的trailing date
    g.long_in_date = 55
    # 系统1 exiting market trailing date
    g.short_out_date = 10
    # 系统2 exiting market trailing date
    g.long_out_date = 20
    # g.dollars_per_share是标的股票每波动一个最小单位，1手股票的总价格变化量。
    # 在国内最小变化量是0.01元，所以就是0.01×100=1
    g.dollars_per_share = 1
    # 可承受的最大损失率
    g.loss = 0.1
    # 若超过最大损失率，则调整率为：
    g.adjust = 0.8
    # 计算N值的天数
    g.number_days = 20
    # 最大允许单元
    g.unit_limit = 4
    # 系统1所配金额占总金额比例
    g.ratio = 0.8

    g.N = []

    #计算N天内最从高价回落最多%M
    g.rblh_d = 250
    g.rblh_r = 0.35


#获取有效的eps price条件股票
def get_valid_stocks(securitys = None):
    result = []
    for i in range(len(securitys)):
        security = securitys[i]
        fake_eps_info = {"code":security}
        stInfo = get_stock_info(None,fake_eps_info)
        if(stInfo != None):
            result.append(stInfo)

def get_stock_info(price_info,eps_info):
    code = eps_info["code"]
    exsit = False
    for code_,stock_info in g.position_pool.items():
        if(code == code_):
            stock_info.update_info(price_info,eps_info)
            exsit = True
            break
    if not exsit:
        return StockInfo(price_info,eps_info)

class StockInfo:
    #初始化，价格信息，eps信息
    def __init__(self, price_info,eps_info):
        self._init_data()
        self.update_info(price_info,eps_info)
    #更新价格
    def update_price_info(self,price_info):
        if(price_info == None):
            return
        self.value = price_info["value"]
        self.index = price_info["index"]
        self.weight = price_info["weight"]

    #更新eps信息
    def update_eps_info(self,eps_info):
        self.code = eps_info["code"]
        if(self.code == None):
            return
        if eps_info.has_key("eps_ratio2"):
           self.eps_ratio2 = eps_info["eps_ratio2"]
        if eps_info.has_key("security_name"):
           self.security_name = eps_info["security_name"]
        if eps_info.has_key("eps_ratio"):
           self.eps_ratio = eps_info["eps_ratio"]
        if eps_info.has_key("market_cap"):
           self.market_cap = eps_info["market_cap"]
        if eps_info.has_key("year_eps_ratio2"):
           self.year_eps_ratio2 = eps_info["year_eps_ratio2"]
        if eps_info.has_key("year_eps_ratio3"):
           self.year_eps_ratio3 = eps_info["year_eps_ratio3"]
        if eps_info.has_key("year_eps_ratio"):
           self.year_eps_ratio = eps_info["year_eps_ratio"]
    #更新
    def update_info(self,price_info,eps_info):
        self.update_price_info(price_info)
        self.update_eps_info(eps_info)

    #初始化
    def _init_data(self):
        self.N = []
        self.year_eps_ratio2 = None
        self.year_eps_ratio3 = None
        self.year_eps_ratio = None
        self.market_cap = 0
        self.portfolio_strategy_short = 0
        self.position_day = 0

    #每日更新当前数据信息
    def run_daily(self):
        #唐安琪通道最高最低价的周期不同
        df = attribute_history(self.code,g.short_in_date,"1d",("high","low"))
        self.system_high_short = max(df.high)
        self.system_low_short = min(df.low[g.short_out_date:])

        df = attribute_history(self.code,g.long_in_date,"1d",("high","low"))
        self.system_high_long = max(df.high)
        self.system_low_long = min(df.low)
        self.calculate_n()
        if(self.portfolio_strategy_short!=0):
            self.position_day += 1

    #计算海龟系统N
    def calculate_n(self):
        # 需要考虑停牌，上市交易天数过小,这时候是否需要参与交易
        if(len(self.N) == 0):
            price = attribute_history(self.code, g.number_days*2, '1d',('high','low','close'))
            lst = []
            for i in range(0, g.number_days*2):
                if(np.isnan(price['high'][i])):
                    continue
                high_price = price['high'][i]
                low_price = price['low'][i]
                index = i
                if(i == 0):
                    index = 0
                else:
                    index = i-1
                last_close = price['close'][index]
                h_l = high_price-low_price
                h_c = high_price-last_close
                c_l = last_close-low_price
                # 计算 True Range 取计算第一天的前20天波动范围平均值
                True_Range = max(h_l, h_c, c_l)
                if(len(lst) < g.number_days):
                    lst.append(True_Range)
                else:
                    if(len(self.N) == 0):
                        current_N = np.mean(lst)
                        (self.N).append(current_N)
                    current_N = (True_Range + (g.number_days-1)*(self.N)[-1])/g.number_days
                    (self.N).append(current_N)
        else:
            price = attribute_history(self.code, 2, '1d',('high','low','close'))
            h_l = price['high'][0]-price['low'][0]
            h_c = price['high'][0]-price['close'][1]
            c_l = price['close'][1]-price['low'][0]
            # Calculate the True Range
            True_Range = max(h_l, h_c, c_l)
            # 计算前g.number_days（大于20）天的True_Range平均值，即当前N的值：
            current_N = (True_Range + (g.number_days-1)*(self.N)[-1])/g.number_days
            (self.N).append(current_N)
            del self.N[0]
    #是否突破新高
    def has_break_max(self,close,max_price):
        if(close > max_price):
            return True
        else:
            return False
    #是否创新低
    def has_break_min(self,close,low_price):
        if(close < low_price):
            return True
        else:
            return False

    def start_process(self,low,high):
        if(len(self.N) == 0):
            return
        self.calculate_unit()

        #TODO current_price
        cash = g.current_cash
        order_info = None
        if(self.portfolio_strategy_short == 0):
            order_info = self.try_market_in(current_price,cash)
        else:
            order_info = self.try_stop_loss(current_price)
            if(order_info != None):
                return order_info
            order_info = self.try_market_add(current_price, g.ratio*cash)
            if(order_info != None):
                return order_info
            order_info = self.try_market_out(current_price)
            if(order_info != None):
                return order_info
            # order_info = self.try_market_stop_profit(current_price)
            # if(order_info != None):
            #     return order_info
            self.set_appropriate_out_price(current_price)

        return order_info
    #6
    # 入市：决定系统1、系统2是否应该入市，更新系统1和系统2的突破价格
    # 海龟将所有资金分为2部分：一部分资金按系统1执行，一部分资金按系统2执行
    # 输入：当前价格-float, 现金-float, 天数-int
    # 输出：none
    #暂时只考虑一个系统运行情况
    def try_market_in(self,current_price, cash):
       #短时系统操作是否可以入市
        if(self.unit == 0):
            return
        has_break_max = self.has_break_max(current_price,self.system_high_short)
        if(not has_break_max):
            return
        num_of_shares = cash/current_price
        # if num_of_shares < self.unit:
        #     return
        if self.portfolio_strategy_short < int(g.unit_limit*self.unit):
            order_info = order(self.code, int(self.unit))
            # self.portfolio_strategy_short += int(self.unit)
            self.break_price_short = current_price
            self.next_add_price = current_price + self.N[-1]
            self.next_out_price = current_price - 2*self.N[-1]
            self.mark_in_price = current_price

            print "开仓！当前价：%s,最高价：%s,N:%s"%(current_price,self.system_high_short,self.N[-1])
            return order_info 
    #7
    # 加仓函数
    # 输入：当前价格-float, 现金-float, 天数-int
    # 输出：none
    def try_market_add(self,current_price, cash):
        # if(self.unit == 0):
        #     return
        break_price = self.break_price_short
        # 每上涨0.5N，加仓一个单元
        if current_price < self.next_add_price: 
            return
        num_of_shares = cash/current_price
        # if num_of_shares < self.unit: 
        #     return
        order_info = order(self.code, int(self.unit))
        # self.portfolio_strategy_short += int(self.unit)
        self.break_price_short = current_price
        self.next_add_price = current_price + self.N[-1]
        self.next_out_price = current_price - 2*self.N[-1]
        print "加仓！当前价：%s,上次突破买入价：%s，N:%s,unit:%s,position:%s"%(current_price,break_price,self.N[-1],self.unit,self.portfolio_strategy_short)
        return order_info
    #8
    # 离场函数
    # 输入：当前价格-float, 天数-int
    # 输出：none
    def try_market_out(self,current_price):
        # Function for leaving the market
        has_break_min = self.has_break_min(current_price ,self.system_low_short)
        # 若当前价格低于前out_date天的收盘价的最小值, 则卖掉所有持仓
        if not has_break_min:
            return
        # print min(price['close'])
        if self.portfolio_strategy_short > 0:
            # self.portfolio_strategy_short = 0
            order_info = order(self.code, -self.portfolio_strategy_short)
            print "离场！当前价：%s,最低价：%s，position:%s"%(current_price,self.system_low_short,self.portfolio_strategy_short)
            return order_info

    #15交易日涨幅小于20%退出
    def try_market_stop_profit(self,current_price):
        # Function for leaving the market
        if(self.position_day >=15 and (self.break_price_short - self.mark_in_price)/self.mark_in_price <0.2):
            print "%s交易日未满足涨幅20,入场价：%s,当前价:%s"%(self.position_day,self.mark_in_price,self.break_price_short)
            return order(self.code, -self.portfolio_strategy_short)

    #9
    # 止损函数
    # 输入：当前价格-float
    # 输出：none
    def try_stop_loss(self,current_price):
        # 损失大于2N，卖出股票
        break_price = self.break_price_short
        # If the price has decreased by 2N, then clear all position
        if current_price < self.next_out_price:
            # print break_price - 2*(g.N)[-1]
            # self.portfolio_strategy_short = 0  
            order_info = order(self.code, - self.portfolio_strategy_short)
            print "止损！当前价：%s,上次突破买入价：%s，N:%s,position:%s"%(current_price,break_price,self.N[-1],self.portfolio_strategy_short)
            return order_info

     #更新止损价格
    def set_appropriate_out_price(self,current_price):
        # Function for leaving the market
        self.next_out_price = max(self.next_out_price,current_price - 2*self.N[-1])

    #计算交易单位
    def calculate_unit(self):
        value = g.total_value
        # 计算波动的价格
        current_N = (self.N)[-1]
        dollar_volatility = g.dollars_per_share*current_N
        # 依本策略，计算买卖的单位
        self.unit = value*0.01/dollar_volatility
        # unit = new_unit - self.portfolio_strategy_short
        # if(unit >=100):
        #     self.unit = unit
        # else:
        #     self.unit = 0

    #加仓数量
    def add_buy_count(self,count):
        self.portfolio_strategy_short += count

     #减仓数量
    def reduce_buy_count(self,count):
        self.portfolio_strategy_short -= count

     #获得仓位数量
    def get_buy_count(self):
        return self.portfolio_strategy_short

     #设置仓位数量
    def set_buy_count(self,count):
        self.portfolio_strategy_short = count

    def __str__(self):
        # log.info("%s（%s）的排名为：%s,总分数为：%s,个股分数为：%s,最近两个季度eps增长率：%s%%,%s%%,市值：%s"%(self.code,
        # self.security_name,self.index,self.value, self.weight ,self.eps_ratio2,self.eps_ratio,self.market_cap))
        return ""