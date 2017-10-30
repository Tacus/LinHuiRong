import pandas as pd
import numpy as np
# import matplotlib as talib
import talib
import datetime
from  MyMacd import *
from AdjustTimes import *
from SellStrategy_holdMonth import *
from BuyStrategy import *
from MyUtil import *
from jqdata import *
def initialize(context):
    set_option('use_real_price', True)
    # enable_profile()
    g.security = get_all_securities(["stock"]).index
    # g.security = get_index_stocks('000300.XSHG')

    # g.security = ['002573.XSHE']
    # g.security = get_security_info('000300.XSHG')

    g.macd = MyMacd(False)
    g.adjustTims  = AdjustTimes(False)
    g.util = MyUtil()
    g.buyStrategy = BuyStrategy(g.macd,g.adjustTims)
    g.buyCtDict = {}    
    
    g.sellStrategy = SellStrategy_holdMonth(g.buyCtDict,30)

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    buyStocksMethod(context,data)
    sellStocksMethod(context,data)

def buyStocksMethod(context,data):
    for security in g.security:
        dict = data[security]
        curPrice = dict.close
        factor = dict.factor
        if(not dict.isnan() and not dict.paused):
            g.buyStrategy.commonBuyStrategy(context,security,factor)
    
def sellStocksMethod(context,data):
    for security in context.portfolio.positions:
        dict = data[security]
        if(not dict.isnan() and not dict.paused):
            g.sellStrategy.sell(context,security)
        else:
            continue 

#每个交易日结束运行
def after_trading_end(context):
    #得到当天所有订单
    orders = get_orders()
    for _order in orders.values():
        # log.info(_order.order_id)
        if _order.status == OrderStatus.held and not _order.is_buy:
            del g.buyCtDict[_order.security]
        elif  _order.status == OrderStatus.held and _order.is_buy:
            security = _order.security
            buyCtDict = {}
            buyCtDict["buyDate"] = context.current_dt.date()
            g.buyCtDict[security] = buyCtDict