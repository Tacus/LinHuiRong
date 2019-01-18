#coding:utf-8
# 导入函数库
# import jqdatasdk
from jqdatasdk import *
import numpy as np  # we're using this for various math operations
from scipy import stats  # using this for the reg slope
import pandas as pd
import math
auth('18970349344', '159263')
# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)

    g.investment_set = 1  #选股池，1：沪深300指数  2：中证500
    
    # print(pd.show_versions())
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
    g.index_id = "000001.XSHG" # identifier for the SPY. used for trend filter.
    g.index_average_window = 100  # moving average periods for index filter
    
    # enable/disable trend filter.
    g.index_trend_filter = True  
    
    # Most momentum research excludes most recent data.
    g.exclude_days = 5  # excludes most recent days from momentum calculation
    
    # identifier for the cash management etf, if used.
    g.use_bond_etf = True
    g.bond_etf = "000300.XSHG" 
    
    # 1 = inv.vola. 2 = equal size. Suggest to implement 
    # market cap and inverse market cap as well. There's 
    # lots of room for development here.
    g.size_method = 2 
    
    
    run_monthly(my_rebalance, monthday = 1, time='open+1h', reference_security='000300.XSHG')

    # run_daily(my_record_vars,time='close', reference_security='000300.XSHG')
    # Create our dynamic stock selector - getting the top 500 most liquid US
    # stocks.
    
    if(g.investment_set == 1):
        inv_index = '000300.XSHG'
    elif(g.investment_set == 2):
        inv_index = '000905.XSHG'

    g.inv_set = get_index_stocks(inv_index)[-10:]
    
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
    # print(type(mom_means))
    # print(dir(mom_means))
    # Sort the momentum list, and we've got ourselves a ranking table.
    ranking_table = mom_means.order(ascending=True)
    # print(mom_means)
    # print(ranking_table)
    # ranking_table = mom_means.sort(1)
    # print(ranking_table)

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
         # Gets index history
        index_history = get_price(g.index_id,end_date = end_date,count = g.index_average_window,fields = ["close"])

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
    for security in context.portfolio.positions.keys:
        if (security not in final_buy_list):
            if (security != context.bond_etf):
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


def ewm(series,halflife=20, ignore_na=True, min_periods=0,
                         adjust=True):
    log = math.log(0.5)/halflife
    alpha = 1-math.exp(log)
    return calewm(series,alpha)

def calewm(series,alpha):
    lenght = len(series)
    i = 0
    totalWeight = 0
    weight = 0
    yt = 0
    while i < lenght:
        value = series[lenght-i-1]
        weight = math.pow(1-alpha,i)
        totalWeight += weight
        yt += value*weight
        i +=1
    return yt  
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
    returns = returns.apply(ewm,halflife=20, ignore_na=True, min_periods=0,
                         adjust=True)
    stddev = returns.std(bias=False).dropna()
    # stddev = returns.ewm(halflife=20, ignore_na=True, min_periods=0,
    #                      adjust=True).std(bias=False).dropna()
    return 1 / stddev.iloc[-1]
