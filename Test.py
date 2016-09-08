import math
import talib
import numpy as np
import pandas as pd
from MyMacd import *
current_VolumeRatio = {}
def initialize(context):
    # 定义一个全局变量, 保存要操作的
    # 000001(:平安银行)
    g.choicenum = 4
    # 初始化此策略
    # 设置我们要操作的池, 这里我们只操作一支
    # set_universe([g.security])
    set_option('use_real_price', True)
    g.buy = [0] * 4
    g.buyday = {}
    K1 = 50
    D1 = 50
    global K1,D1
    g.kvalue = {}
    g.dvalue = {}
   

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    #首先判断是否需要卖
    # context.portfolio.positions[security].sellable_amount > 0:
    # security = '002573.XSHE'
    # volumeRatio = Volume_Ratio_Index(security,context.current_dt)
    # print volumeRatio
    # return
    log.info("Today have %d stock" % len(context.portfolio.positions))
    if (len(context.portfolio.positions) == 0):
        print "do nothing"
    else:
        for stock in context.portfolio.positions:
            current_data = get_current_data()
            price = data[stock].close
            high  = data[stock].high
            log.error("before oneday %s,chicangtime %d isPaused %s" % (stock, g.buyday[stock], current_data[stock].paused))
            if g.buyday[stock] > 30:
                if(profit(price, context.portfolio.positions[stock].avg_cost) > 0.15) and (high/price > 1.02):
                    if current_data[stock].paused:
                        log.error("when sell stock %s paused" % stock)
                        continue
                    log.error("selling %s,chicangtime %d isPaused %s" % (stock, g.buyday[stock], current_data[stock].paused))
                    order_target(stock, 0)
                elif(profit(price, context.portfolio.positions[stock].avg_cost) > 0.15):
                    g.buyday[stock]=g.buyday[stock]+1
                    continue
                else:
                    if current_data[stock].paused:
                        log.error("when sell stock %s paused" % stock)
                        continue
                    log.info("in zhisun30 %s,chicangtime %d isPaused %s" % (stock, g.buyday[stock], current_data[stock].paused))
                    ret = order_target(stock, 0)
                    # if ret!=None :
                        # del g.buyday[stock]
            else:
                if(profit(price, context.portfolio.positions[stock].avg_cost) <= -0.07):
                    if current_data[stock].paused:
                        log.error("when sell stock %s paused" % stock)
                        continue
                    log.error("seling(-7)  %s,chicangtime %d" % (stock, g.buyday[stock]))
                    ret = order_target(stock, 0)
                    # if ret!=None :
                        # del g.buyday[stock]
                    continue
                else:
                    g.buyday[stock]=g.buyday[stock]+1
                   
   
    buyNum = len(context.portfolio.positions)
    if(buyNum == 4):
        log.warn("Now has %d stocks, no need to buy stock" % buyNum)
    else:
        stocks = get_all_securities(['stock'], context.current_dt)
    # 去除不必要的列
        stocks = stocks.drop(['start_date', 'end_date', 'type', 'name'], 1)
   
        date=context.current_dt.strftime("%Y-%m-%d")
 #选择换手率小于2的,市值小于600
    # 查询条件
        queryCondition = query(
            valuation.code, valuation.circulating_market_cap, valuation.pe_ratio, valuation.pb_ratio, valuation.turnover_ratio
        ).filter(
            valuation.circulating_market_cap < 600,
            valuation.turnover_ratio < 2
        ).order_by(
        # 按流通市值降序排列
            valuation.circulating_market_cap.desc()
        ).limit(
        # 最多返回100个
            100
        )    
    #获取符合查询条件的
        df = get_fundamentals(queryCondition, date)
     #   去除ST
        # 去除停牌
        buylist =unpaused(list(df['code']))
   
        st=get_extras('is_st', buylist, start_date=date, end_date=date, df=True)
    #buylist=list(st[st==False].index) 这是日期
        buylist=list(st[st==False])  ##这个是代码
        g.security = buylist
        cashForOneStock = context.portfolio.cash/(g.choicenum-buyNum)
        log.info("allMoney is: %f, usedMoney is: %f cashForOneStock is: %f" %(context.portfolio.cash, context.portfolio.capital_used,cashForOneStock))
    #print list(st[st==False].index[:g.choicenum])
        for stock in buylist:
            test = isKDJ(context, data, stock)
            if(test):
                increase = getStocksByIncrease(stock, 1,2,data)
                if increase:
                    macd = isMacd(context,data,stock)
                    if macd:
                        volumeRatio = Volume_Ratio_Index(stock,context.current_dt)
                        if volumeRatio <1:
                            price = data[stock].close
                            canBuyNum = cashForOneStock/price
                            current_data = get_current_data()
                            if current_data[stock].paused:
                                log.error("stock %s paused" % stock)
                            log.error("buy %s Money is %f, buyNum is: %f, buyPrice is %f" %(stock, cashForOneStock, canBuyNum, price))
                            order_target(stock, canBuyNum)
                            g.buyday[stock]=1
                            continue
                else:
                    continue
            else:
                continue
               
       
        # increase = getStocksByIncrease(stock, 1,2,data)
        # if increase:
        #     print "CCCCCCCCCCCCCCCCCCCCC"
       
        # test = isKDJ(context, data, stock)
        # if(test == True):
        #     print "aaaaaaaaaaaaaaaaaaaaaaaa"
        #     #判断涨幅
        # else:
        #     continue
       
     
   
    #选择KDJ金叉
   
   
    #stocksList = list(stocks.index)
    #st=st.loc[date]
    #buylist=list(st[st==False].index)
   
    #首先判断是否持仓已满
 
   
   # for stockmaketcap in stocksList.turnover_ratio:
    #    print stockmaketcap
   
   # for stockcode in  stocksList.code:
    #    print stockcode
    #    price = data[stockcode].open
        # 获取这只昨天收盘价
    #    last_close = data[stockcode].close
       
  #      print price, last_close
   
    #选择涨幅1-3的
       #
   
   
    # 选择macd金叉
   
    #选择 KDJ金叉
   
   
    #判断是否需要卖
    #判断持仓天数和盈利
   
    #判断盈亏
   
    #判断和最高点差异
   
   
   
   
   
   
   
   
   
    # 取得过去五天的平均价格
   
    # 取得上一时间点价格
 
    # 取得当前的现金
def profit(price, cost):
    return (price-cost)/cost
       

# def isMacd(stock):
#     prices = attribute_history(stock, 40, '1d', ('close'))
#     macd = MACD(prices['close'].values, fastperiod=12, slowperiod=26, signalperiod=9)
#     if macd < 0:
#         return False
#     else:
#         return True


# # 定义MACD函数  
# def MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9):
#     '''
#     参数设置:
#         fastperiod = 12
#         slowperiod = 26
#         signalperiod = 9

#     返回: macd - signal
#     '''
#     macd, signal, hist = talib.MACD(prices,
#                                     fastperiod=fastperiod,
#                                     slowperiod=slowperiod,
#                                     signalperiod=signalperiod)
#     return macd[-1] - signal[-1]

   
   
#返回涨幅在一定范围内的,涨幅在low 和high范围内的
def getStocksByIncrease(stock, low, high, data):
    # 得到当前价格
    price = data[stock].close
   
    # 获取这只昨天收盘价
    close_price = history(2, unit='1d', field='close', security_list=stock)
    last_close = close_price[stock][0]
    last_close1 = close_price[stock][1]
    print ("today's price %f, close_price %s，close_price1:%s"% (price , last_close,last_close1))
   
    if price/last_close >= 1.0 and price/last_close <= 1.03:
        print ("----------OK--------------- zhang %s " % ((price/last_close)*100-100))
        return True
    else:
        print ("----------not OK--------------- die %s " % ((price/last_close)*100-100))
        return False


def unpaused(stockspool):
    current_data=get_current_data()
    return [s for s in stockspool if not current_data[s].paused]
   
#定义KDJ计算函数，输入为基期长度count、平滑因子a，输出为KDJ指标值。
#K1为前一日k值,D1为前一日D值,K2为当日k值,D2为当日D值,J为当日J值
def KDJ(stock,count,a,b,K1,D1):
    # print ("in KDJaaaaa %f,%f" % (K1,g.kvalue[stock]))
    h = attribute_history(stock, count, unit='1d',fields=('close', 'high', 'low'),skip_paused=True)
    # 取得过去count天的最低价格
    low_price = h['low'].min()
    # 取得过去count天的最高价格
    high_price = h['high'].max()
    # 取得当日收盘价格
    current_close = h['close'][-1]
    if high_price!=low_price:
        #计算未成熟随机值RSV(n)＝（Ct－Ln）/（Hn-Ln）×100
        RSV = 100*(current_close-low_price)/(high_price-low_price)
    else:
        RSV = 50
   
    #当日K值=(1-a)×前一日K值+a×当日RSV
    K2=(1-a)*K1+a*RSV
    #当日D值=(1-a)×前一日D值+a×当日K值
    D2=(1-b)*D1+b*K2
    #计算J值
    J2 = 3*K2-2*D2
   
    return K1,D1,K2,D2,J2
   

def isKDJ(context, data, stock):
    if g.kvalue.has_key(stock):
        K1=g.kvalue[stock]
        D1=g.dvalue[stock]
    else:
        K1 =50
        D1 =50
        g.kvalue[stock] = 50
        D1=g.dvalue[stock] =50
    # print ("in isKDJ first: %f, %f " % (K1,g.kvalue[stock]))
    count = 5
    #设定k、d平滑因子a、b，不过目前已经约定俗成，固定为1/3
    a = 1.0/3
    b = 1.0/3
    #history是取得所有的数据
    close_price = history(count, unit='1d', field='close', security_list=stock)
    # print "acccccccccccccccccccccccccccccccccccc"
    # print close_price[stock] ##这个就是stock五天的收盘价
    # print "bccccccccccccccccccccddddddddddddd"
    if not math.isnan(close_price[stock][0]):
        K1,D1,K2,D2,J2 = KDJ(stock,count,a,b,K1,D1)
       
        g.kvalue[stock] = K2
        g.dvalue[stock] = D2
        if K2<50 and D2<50 and K1< D1 and K2>D2:
            # print "金叉 买买买买买"
            return True
        else:
            # print "没有金叉"
            return False
       

       
        #K1 =K2
        #D1 = D2
       
   
                   
       
def Volume_Ratio_Index(security,date):
    dateKey = date.strftime("%Y-%m-%d")
    volumeRatioFive = 0
    if(not current_VolumeRatio.has_key(dateKey)):
        start_date = date - datetime.timedelta(6)
        end_date = date
        fiveVolume = get_price(security, start_date, end_date, '1d', ['volume'])
        volumeRatioFive = fiveVolume['volume'].sum()/5
        current_VolumeRatio[dateKey] = volumeRatioFive
    #
    else:
        volumeRatioFive = current_VolumeRatio[dateKey]
    #前一天每分钟成交量
    df = history(1, '1d', 'volume', [security])
    lastDateTtime = date - datetime.timedelta(1)
    lastVolume = df[security][0]
    
    return lastVolume/volumeRatioFive*1.0
