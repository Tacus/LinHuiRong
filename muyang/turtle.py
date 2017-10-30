# 导入函数库
import jqdata
import pandas as pd
# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    init_variables()    
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')

    #设置中间变量
def init_variables():

    g.dollars_per_share = 1

    #波动量x日平均平均值
    g.dict_truerange = {}

    #构建唐奇安上通道的天数
    g.uper_days = 20
    #构建唐奇安下通道天数
    g.down_days = 20

    #股票池
    g.stocks = ["300663.XSHE"]
    g.dict_break_price = {}

def before_trading_start(context):
    current_data = get_current_data()
    for security in g.stocks:
        security_data = current_data[security]
        if(not security_data.paused and not security_data.is_st):
             #计算波动平均值的值
            try_calculate_trunRange(context,security)

def handle_data(context,data):
    handle_trading(context,data)

#处理交易信号
def handle_trading(context,data):
    # log.info("truerange:",g.dict_truerange,"break_price:",g.dict_break_price)
    dt = context.current_dt 
    current_data = get_current_data()
    for security in g.stocks:
        security_data = current_data[security]
        if(not security_data.paused and not security_data.is_st):
            check_position(context,security)

    for (security,position) in context.portfolio.positions.items():
        security_data = current_data[security]
        if(not security_data.paused and not security_data.is_st):
            check_positioned(context,position)
            

def check_positioned(position, context):
    bRet = can_add_lots(context,security)
    if bRet :
        print(str.format("add %s signal appear！！！"%(security)))
   # market_add(current_price, g.ratio*cash, g.short_in_date)    
    bRet = can_out_tosell(context,security)
    if bRet :
        print(str.format("sell %s signal appear！！！"%(security)))
        
def check_position(context,security):
    bRet = can_enter_tobuy(context,security)
    if bRet :
        print(str.format("buy in %s signal appear！！！"%(security)))

# return True/False
# 如果股票处于持股状态，不可删除
# 从备选股票中删除指定股票
def delete_stock(context,security,stocks):
    if(stocks == None):
        stocks = g.stocks
    if(stocks != None and security in stocks and security not in context.portfolio.positions):
        stocks.remove(security)
    else:
        print("delete error！")

#回撤幅度
# 返回股票距离上一次出现同样价格(与当日高点相比)的天数,并返回期间最大回撤幅度
def get_last_same_price_days(context,security,N = 250):
    # 二、get_last_same_price_days(context,security):
    his_df= attribute_history(security, count = N, unit='1d',
        fields=['high', 'low'])
    last_price = his_df["high"][-1]
    df1 = his_df["high"]>last_price
    df2 = his_df["low"] < last_price
    df1 = df1[df1 == True]
    df2 = df2[df2 == True]
    df2 = df2.sort_index(ascending = False)
    recent_date = None
    for dt in df2.index:
        if (dt in df1):
            recent_date = dt
            break
    if(recent_date !=None):
        df = get_price(security, start_date = recent_date, end_date = context.current_dt, fields = ["high","low"], skip_paused = True)
        high = df["high"].max()
        low =df["low"].min()
        high_index = df.high.argmax()
        low_index = df.low.argmin()
        days = (context.current_dt - recent_date).days
        print recent_date,context.current_dt,days,high_index,low_index
        return days,(low - high)/high


#  判断股票是否符合海龟法则进场条件
#return True/False
def can_enter_tobuy(context,security):
    # Get the price for the past "in_date" days
    price = attribute_history(security, g.uper_days, '1d', ('close'))
    current_data = get_current_data()
    current_price = current_data[security].last_price
    # Build position if current price is higher than highest in past
    if current_price > max(price['close']):
        g.dict_break_price[security] = current_price
        return True
    else:
        return False


#判断股票是否符合海龟法则加仓条件 
#return True/False
def can_add_lots(context,security):
    # 每上涨0.5N，加仓一个单元
    if(g.dict_break_price.has_key(security)):
        break_price = g.dict_break_price[security]
        current_data = get_current_data()
        current_price = current_data[security].last_price
        if current_price >= break_price + 0.5*(g.truerange)[-1]: 
            g.dict_break_price[security] = current_price
            return True
        else:
            return False
    else:
        return False


#  return True/False
#  判断股票是否符合海龟法则离场条件
def can_out_tosell(context,security):
    # Function for leaving the market
    price = attribute_history(security, g.down_days, '1d', ('close'))
    # 若当前价格低于前out_date天的收盘价的最小值, 则卖掉所有持仓
    if current_price < min(price['close']):
        return True
    else:
        return False

#计算波动平均值
def try_calculate_trunRange(context,security):
    #还未计算波动值
    if not g.dict_truerange.has_key(security):
        g.dict_truerange[security] = []
        calculate_trueRange(context,security)
    else:
        price = attribute_history(security, 1, '1d',('high','low','close'))
        h_l = price['high'][0]-price['low'][0]
        h_c = price['high'][0]-price['close'][0]
        c_l = price['close'][0]-price['low'][0]
        # Calculate the True Range
        True_Range = max(h_l, h_c, c_l)
        last_truerange = g.dict_truerange[security][-1]
        current_N = (True_Range + (g.uper_days-1)*last_truerange)/g.uper_days
        g.dict_truerange[security].append(current_N)

def calculate_trueRange(context,security):
    end_date = context.current_dt.date() - timedelta(1)
    dict = get_security_info(security)
    startDate = dict.start_date
    days = end_date - startDate 
    if days.days < g.uper_days:
        df = get_price(security, start_date = startDate ,end_date=end_date, fields=("close","high","low"), skip_paused=True)
    else:
        df = get_price(security, end_date=end_date, fields=("close","high","low"), skip_paused=True,count=g.uper_days)
    for i in range(len(df)):
        if(i == 0):
            g.dict_truerange[security].append(df['close'].iloc[0])
        else:
            h_l = df['high'].iloc[i]-df['low'].iloc[i]
            h_c = df['high'].iloc[i]-df['close'].iloc[i]
            c_l = df['close'].iloc[i]-df['low'].iloc[i]
            True_Range = max(h_l, h_c, c_l)
            current_N = (True_Range + (g.uper_days-1)*(g.dict_truerange[security])[-1])/g.uper_days
            g.dict_truerange[security].append(current_N)

