"""
Simple equity momentum model by Andreas Clenow

Purpose: 
To capture momentum effect in US stock markets.
Implements two methods of reducing downside.
Index level trend filter, and minimum momentum.

Momentum analytic:
Uses annualized exponential regression slope, multiplied by R2, to adjust for fit.
Possibility to use average of two windows.

Settings:
* Investment universe
* Momentum windows (x2)
* Index trend filter on/off
* Index trend filter window
* Minimum required slope
* Exclude recent x days
* Trading frequency
* Cash management via bond etf, on off
* Bond ETF selection
* Sizing method, inverse vola or equal.


Suggested areas of research and improvements:
* Use pipeline to limit number of processed stocks, by putting the regression logic in there.
* Adding fundamental factors.
* Portfolio sizes
* Market cap weighting / inverse market cap weighting. (you may want to z-score and winsorize)
* Momentum analytic: There are many possible ways. Try simplifications and variations.


"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.factors import CustomFactor, SimpleMovingAverage, Latest
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.data import morningstar
 
import numpy as np
import pandas as pd
from scipy import stats
import talib
 
 
def _slope(ts):
    x = np.arange(len(ts))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, ts)
    # annualized_slope = np.power(np.exp(slope), 250)
    annualized_slope = (1 + slope)**250
    return annualized_slope * (r_value ** 2)      
        
        
class MarketCap(CustomFactor):   
    
    inputs = [USEquityPricing.close, morningstar.valuation.shares_outstanding] 
    window_length = 1
    
    def compute(self, today, assets, out, close, shares):       
        out[:] = close[-1] * shares[-1]
        
 
def make_pipeline(sma_window_length, market_cap_limit):
    
    pipe = Pipeline()  
    
    # Now only stocks in the top N largest companies by market cap
    market_cap = MarketCap()
    top_N_market_cap = market_cap.top(market_cap_limit)
    
    #Other filters to make sure we are getting a clean universe
    is_primary_share = morningstar.share_class_reference.is_primary_share.latest
    is_not_adr = ~morningstar.share_class_reference.is_depositary_receipt.latest
    
    # TREND FITLER ON    
    # We don't want to trade stocks that are below their 100 day moving average price.
    # latest_price = USEquityPricing.close.latest
    # sma = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=sma_window_length)
    # above_sma = (latest_price > sma)
    # initial_screen = (above_sma & top_N_market_cap & is_primary_share & is_not_adr)
    
    # TREND FITLER OFF  
    initial_screen = (top_N_market_cap & is_primary_share & is_not_adr)
    
    pipe.add(market_cap, "market_cap")
    
    pipe.set_screen(initial_screen)
    
    return pipe
 
def before_trading_start(context, data):
    context.selected_universe = pipeline_output('screen')
    update_universe(context.selected_universe.index)
 
def initialize(context):
    
    context.market = sid(8554)
    context.market_window = 200
    context.atr_window = 20
    context.talib_window = context.atr_window + 5
    context.risk_factor = 0.001
    context.sma_window_length = 100
    context.momentum_window_length = 90
    context.market_cap_limit = 500
    context.rank_table_percentile = .2
    context.significant_position_difference = 0.1
    context.min_momentum = 0.30
    
    
    
    attach_pipeline(make_pipeline(context.sma_window_length,
                                  context.market_cap_limit), 'screen')
     
    # Schedule my rebalance function
    schedule_function(rebalance,
                      date_rules.month_start(),
                      time_rules.market_open(hours=1))
    
    # Cancel all open orders at the end of each day.
    schedule_function(cancel_open_orders, date_rules.every_day(), time_rules.market_close())
 
 
def cancel_open_orders(context, data):
    open_orders = get_open_orders()
    for security in open_orders:
        for order in open_orders[security]:
            cancel_order(order)
    
    #record(lever=context.account.leverage,
    record(exposure=context.account.leverage)
 
def handle_data(context, data):    
    pass
    
def rebalance(context, data):
    
    highs = history(context.talib_window, "1d", "high")
    lows = history(context.talib_window, "1d", "low")
    closes = history(context.market_window, "1d", "price")
    
    estimated_cash_balance = context.portfolio.cash
    slopes = np.log(closes[context.selected_universe.index].tail(context.momentum_window_length)).apply(_slope)
    print slopes.order(ascending=False).head(10)
    slopes = slopes[slopes > context.min_momentum]
    ranking_table = slopes[slopes > slopes.quantile(1 - context.rank_table_percentile)].order(ascending=False)
 
    # close positions that are no longer in the top of the ranking table
    positions = context.portfolio.positions
    for security in positions:
        price = data[security].price
        position_size = positions[security].amount
        if security in data and security not in ranking_table.index:
            order_target(security, 0, style=LimitOrder(price))
            estimated_cash_balance += price * position_size
        elif security in data:
            new_position_size = get_position_size(context, highs[security], lows[security], closes[security])
            if significant_change_in_position_size(context, new_position_size, position_size):
                estimated_cost = price * (new_position_size - position_size)
                order_target(security, new_position_size, style=LimitOrder(price))
                estimated_cash_balance -= estimated_cost
            
    market_history = closes[context.market]
    current_market_price = market_history[-1]
    average_market_price = market_history.mean()
    
    # Add new positions.
    #if current_market_price > average_market_price:  ############ ac disabled market filter
    if 1 > 0: # dummy
        for security in ranking_table.index:
            if security in data and security not in context.portfolio.positions:
                new_position_size = get_position_size(context, highs[security], lows[security], closes[security])
                estimated_cost = data[security].price * new_position_size
                if estimated_cash_balance > estimated_cost:
                    order_target(security, new_position_size, style=LimitOrder(data[security].price))
                    estimated_cash_balance -= estimated_cost
    
     
def get_position_size(context, highs, lows, closes):
    average_true_range = talib.ATR(highs.ffill().dropna().tail(context.talib_window),
                                       lows.ffill().dropna().tail(context.talib_window),
                                       closes.ffill().dropna().tail(context.talib_window),
                                       context.atr_window)[-1] # [-1] gets the last value, as all talib methods are rolling calculations#
    return (context.portfolio.portfolio_value * context.risk_factor) / average_true_range
        
 
def significant_change_in_position_size(context, new_position_size, old_position_size):
    return np.abs((new_position_size - old_position_size)  / old_position_size) > context.significant_position_difference
        
