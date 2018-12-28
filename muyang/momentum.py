# 导入函数库
from jqdata import *
import numpy as np  # we're using this for various math operations
from scipy import stats  # using this for the reg slope
import pandas as pd

# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
      # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
      # 开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
      # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

    g.investment_set = 1  #选股池，1：沪深300指数  2：中证500
    
    
    # This version uses the average of two momentum slopes.
    # Want just one? Set them both to the same number.
    g.momentum_window = 60  # first momentum window.
    g.momentum_window2 = 90  # second momentum window
    
    # Limit minimum slope. Keep in mind that shorter momentum windows
    # yield more extreme slope numbers. Adjust one, and you may want
    # to adjust the other.
    g.minimum_momentum = 60  # momentum score cap
    
    # Fixed number of stocks in the portfolio. How diversified
    # do you want to be?
    g.number_of_stocks = 25  # portfolio size
    g.index_id = sid(8554) # identifier for the SPY. used for trend filter.
    g.index_average_window = 100  # moving average periods for index filter
    
    # enable/disable trend filter.
    g.index_trend_filter = True  
    
    # Most momentum research excludes most recent data.
    g.exclude_days = 5  # excludes most recent days from momentum calculation
    
    # Set trading frequency here.
    g.trading_frequency = date_rules.month_start()
    
    # identifier for the cash management etf, if used.
    g.use_bond_etf = True
    g.bond_etf = sid(23870) 
    
    # 1 = inv.vola. 2 = equal size. Suggest to implement 
    # market cap and inverse market cap as well. There's 
    # lots of room for development here.
    g.size_method = 2 
    
    
    run_monthly(my_rebalance, monthday = 1, time='open+1h', reference_security='000300.XSHG')

    run_daily(my_record_vars,time='close', reference_security='000300.XSHG')
    # Create our dynamic stock selector - getting the top 500 most liquid US
    # stocks.
    
    if(g.investment_set == 1):
        inv_index = '000300.XSHG'
    elif(g.investment_set == 2):
        inv_index = '000905.XSHG'

    g.inv_set = get_index_stocks(inv_index)
    
def my_rebalance(context):
    # Get data
    hist_window = max(g.momentum_window,
                      g.momentum_window2) + g.exclude_days

    end_date = context.current_dt - timedelta(days = 1)
    panel = get_price(g.inv_set,end_date = end_date,count = hist_window,fields = ["close"])
    hist = panel.close
    data_end = -1 * g.exclude_days # exclude most recent data

    momentum1_start = -1 * (g.momentum_window + g.exclude_days)
    momentum_hist1 = hist[momentum1_start:data_end]

    momentum2_start = -1 * (g.momentum_window2 + g.exclude_days)
    momentum_hist2 = hist[momentum2_start:data_end]

    # Calculate momentum scores for all stocks.
    momentum_list = momentum_hist1.apply(slope)  # Mom Window 1
    momentum_list2 = momentum_hist2.apply(slope)  # Mom Window 2

    # Combine the lists and make average
    momentum_concat = pd.concat((momentum_list, momentum_list2))
    mom_by_row = momentum_concat.groupby(momentum_concat.index)
    mom_means = mom_by_row.mean()

    # Sort the momentum list, and we've got ourselves a ranking table.
    ranking_table = mom_means.sort_values(ascending=False)

    # Get the top X stocks, based on the setting above. Slice the dictionary.
    # These are the stocks we want to buy.
    buy_list = ranking_table[:g.number_of_stocks]
    final_buy_list = buy_list[buy_list > g.minimum_momentum] # those who passed minimum slope requirement

    # Calculate inverse volatility, for position size.
    inv_vola_table = hist[buy_list.index].apply(inv_vola_calc)
    # sum inv.vola for all selected stocks.
    sum_inv_vola = np.sum(inv_vola_table)

    # Check trend filter if enabled.
    if (context.index_trend_filter):
        index_history = data.history(
            g.index_id,
            "close",
            g.index_average_window,
            "1d")  # Gets index history
        index_sma = index_history.mean()  # Average of index history
        current_index = index_history[-1]  # get last element
        # declare bull if index is over average
        bull_market = current_index > index_sma

    # if trend filter is used, only buy in bull markets
    # else always buy
    if context.index_trend_filter:
        can_buy = bull_market
    else:
        can_buy = True


    equity_weight = 0.0 # for keeping track of exposure to stocks
    
    # Sell positions no longer wanted.
    for security in context.portfolio.positions:
        if (security not in final_buy_list):
            if (security.sid != context.bond_etf):
                # print 'selling %s' % security
                order_target(security, 0.0)
                
    vola_target_weights = inv_vola_table / sum_inv_vola
    
    for security in final_buy_list.index:
        # allow rebalancing of existing, and new buys if can_buy, i.e. passed trend filter.
        if (security in context.portfolio.positions) or (can_buy): 
            if (g.size_method == 1):
                weight = vola_target_weights[security]
            elif (g.size_method == 2):
                weight = (1.0 / context.number_of_stocks)
                print g.number_of_stocks
            order_target_percent(security, weight)
            equity_weight += weight
    
       

    # Fill remaining portfolio with bond ETF
    etf_weight = max(1 - equity_weight, 0.0)

    print 'equity exposure should be %s ' % equity_weight

    if (g.use_bond_etf):
        order_target_percent(g.bond_etf, etf_weight)


def slope(ts):
    """
    Input: Price time series.
    Output: Annualized exponential regression slope, multipl
    """
    x = np.arange(len(ts))
    log_ts = np.log(ts)
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, log_ts)
    annualized_slope = (np.power(np.exp(slope), 250) - 1) * 100
    return annualized_slope * (r_value ** 2)

def inv_vola_calc(ts):
    """
    Input: Price time series.
    Output: Inverse exponential moving average standard deviation. 
    Purpose: Provides inverse vola for use in vola parity position sizing.
    """
    returns = np.log(ts).diff()
    stddev = returns.ewm(halflife=20, ignore_na=True, min_periods=0,
                         adjust=True).std(bias=False).dropna()
    return 1 / stddev.iloc[-1]
