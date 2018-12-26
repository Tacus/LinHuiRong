# Implementation of the Stocks On The Move system by Andreas Clenow
# http://www.followingthetrend.com/stocks-on-the-move/

import numpy as np
import pandas as pd
import scipy.stats as stats
import time
from quantopian.pipeline import Pipeline
from quantopian.pipeline import CustomFactor
from quantopian.pipeline.data import morningstar
from quantopian.pipeline.factors import EWMA, Latest, SimpleMovingAverage
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.algorithm import attach_pipeline, pipeline_output

UniverseSize = 500
DailyRangePerStock = 0.001 # targeting 10bp of account value
RebalanceThreshold = 0.005 # don't rebalance if the difference is less than 50bp of account value

# This is the momentum factor, which is the 'slope' of an exponential regression
# (ie a linear regression of logarithms), multiplied the the R-Squared of that regression
class Momentum(CustomFactor):   
    inputs = [USEquityPricing.close] 
    window_length = 90
    def compute(self, today, assets, out, close):   
        x = pd.Series(range(0,self.window_length))
        log_close = np.log(close)
        scores = np.empty(len(close.T), dtype=np.float64)  
        for i in range(0,len(assets)):
            if (not np.all(np.isnan(log_close[:,i]))):
                y = np.copy(log_close[:,i])
                # interpolate NaN, not forward-looking since we are regressing anyway
                try:
                    mask = np.isnan(y)
                    y[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), y[~mask])
                    slope, _, r, _, _ = stats.linregress(x, y)
                    scores[i] = slope * 256.0 * r * r
                except:
                    scores[i] = -1000.0
                    log.error("Regression error!")
            else:
                scores[i] = -1000.0
        out[:] = scores

def descending_rank(a):
    return a.argsort()[::-1].argsort()

# This is the momentum factor, except only calculated for those stocks which will end up
# keeping within our set_screen.  
class MomentumOfTopN(CustomFactor):   
    inputs = [USEquityPricing.close, morningstar.valuation.shares_outstanding] 
    window_length = 90
    def compute(self, today, assets, out, close, shares):  
        # get our universe in here again because lame
        starting_caps = close[-1] * shares[-1]
        starting_caps[np.isnan(starting_caps)] = 0.0
        cap_ranks = descending_rank(starting_caps)
        x = pd.Series(range(0,self.window_length))
        log_close = np.log(close)
        scores = np.empty(len(close.T), dtype=np.float64)  
        for i in range(0,len(assets)):
            if (cap_ranks[i] < UniverseSize):
                if (not np.all(np.isnan(log_close[:,i]))):
                    y = np.copy(log_close[:,i])
                    # interpolate NaN, not forward-looking since we are regressing anyway
                    try:
                        mask = np.isnan(y)
                        y[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), y[~mask])
                        slope, _, r, _, _ = stats.linregress(x, y)
                        scores[i] = slope * 256.0 * r * r
                    except:
                        scores[i] = -1000.0
                        log.error("Regression error!")
                else:
                    scores[i] = -1000.0
            else:
                scores[i] = -1000.0
        out[:] = scores
        
class MarketCap(CustomFactor):   
    inputs = [USEquityPricing.close, morningstar.valuation.shares_outstanding] 
    window_length = 1
    def compute(self, today, assets, out, close, shares):       
        out[:] = close[-1] * shares[-1]

# the biggest absolute overnight gap in the previous 90 sessions
class MaxGap(CustomFactor):   
    inputs = [USEquityPricing.close] 
    window_length = 90
    def compute(self, today, assets, out, close):    
        abs_log_rets = np.abs(np.diff(np.log(close),axis=0))
        max_gap = np.max(abs_log_rets, axis=0)
        out[:] = max_gap

# the Average True Range over the last 20 sessions
class ATR(CustomFactor):
    inputs = [USEquityPricing.close,USEquityPricing.high,USEquityPricing.low]
    window_length = 21
    def compute(self, today, assets, out, close, high, low):
        hml = high - low
        hmpc = np.abs(high - np.roll(close, 1, axis=0))
        lmpc = np.abs(low - np.roll(close, 1, axis=0))
        tr = np.maximum(hml, np.maximum(hmpc, lmpc))
        atr = np.mean(tr[1:], axis=0)
        out[:] = atr

def initialize(context):
    context.spy = sid(8554)
    set_benchmark(context.spy)
    
    momentum = MomentumOfTopN()
    mkt_cap = MarketCap()
    max_gap = MaxGap()
    atr = ATR()
    latest = Latest(inputs=[USEquityPricing.close])
    mkt_cap_rank = mkt_cap.rank(ascending=False)
    universe = (mkt_cap_rank <= UniverseSize)
    momentum_rank = momentum.rank(mask=universe, ascending=False)
    sma100 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=100)

    pipe = Pipeline()
    pipe.add(momentum, 'momentum')
    pipe.add(max_gap, 'max_gap')
    pipe.add(mkt_cap, 'mkt_cap')
    pipe.add(mkt_cap_rank, 'mkt_cap_rank')
    pipe.add(sma100, 'sma100')
    pipe.add(latest, 'latest')
    pipe.add(atr, 'atr')
    pipe.add(momentum_rank, 'momentum_rank')
    # pre-screen all the NaN stuff, and crop down to our pseudo-S&P 500 universe
    pipe.set_screen(universe & 
                    (momentum.eq(momentum)) & # these are just to drop NaN
                    (sma100.eq(sma100)) &
                    (mkt_cap.eq(mkt_cap))
                   )    
    pipe = attach_pipeline(pipe, name='sotm')
    # do our work on Wednesdays, as in the books.
    schedule_function(func=allocate_1, 
                      date_rule=date_rules.week_start(days_offset=2),
                      time_rule=time_rules.market_open(minutes=60),
                      half_days=True)
    schedule_function(func=allocate_2, 
                      date_rule=date_rules.week_start(days_offset=2),
                      time_rule=time_rules.market_open(minutes=90),
                      half_days=True)
    schedule_function(func=allocate_3, 
                      date_rule=date_rules.week_start(days_offset=2),
                      time_rule=time_rules.market_open(minutes=120),
                      half_days=True)
    schedule_function(func=record_vars,
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_open(minutes=1),
                      half_days=True)
    schedule_function(func=record_vars,
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_close(),
                      half_days=True)
    schedule_function(func=cancel_all,
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_close(),
                      half_days=True)
    context.rebalance_needed = False
    set_slippage(slippage.FixedSlippage(spread=0.01))
    set_commission(commission.PerShare(cost=0.0035, min_trade_cost=0.35))
    
# This function trims down the Pipeline results to those stocks which allow our portfolio
# to hold.  Stocks which fall out of these criteria are sold.
# 1. In the top 20% of the stocks, ranked by their momentum
# 2. No recent gaps more than 15%, in either direction
# 3. Stock is trading above it's 100-session moving average.  Here we use the exponential 
#    moving average, I think the book might be using the simple moving average.
def filter_pipeline_results(results):
    # remove those whose momentum rank is not in the top 20%
    filtered = results[results['momentum_rank'] < 0.2*UniverseSize]
    # filter out gaps
    filtered = filtered[filtered['max_gap'] < 0.15]
    # filter out stocks under 100 EMA
    filtered = filtered[filtered['latest'] > filtered['sma100']]
    return filtered

def before_trading_start(context, data):
    results = pipeline_output('sotm').sort('momentum_rank')
    filtered = filter_pipeline_results(results)
    context.pool = filtered
    update_universe(filtered.index)

def sell_positions(context, data):
    cash_freed = 0.0
    s = ""
    for sid in context.portfolio.positions:
        position = context.portfolio.positions[sid]
        cash_worth = position.amount * position.last_sale_price
        # anything not in the pool of allowed stocks is immediately sold
        if ((sid not in context.pool.index)  &
            (sid in data)):
            s = s + "%s, " % sid.symbol
            order_target_percent(sid, 0.0)
            cash_freed = cash_freed + cash_worth
    log.info(s)
    return cash_freed

def desired_position_size_in_shares(context, data, sid):
    account_value = context.account.equity_with_loan
    target_range = DailyRangePerStock
    estimated_atr = context.pool['atr'][sid]
    return (account_value * target_range) / estimated_atr

def rebalance_positions(context, data):
    account_value = context.account.equity_with_loan
    cash_freed = 0.0
    s = ""
    for sid in context.portfolio.positions:
        position = context.portfolio.positions[sid]
        current_shares = position.amount
        if (sid in context.pool.index):
            target_shares = desired_position_size_in_shares(context, data, sid)
            sid_cash_freed = (current_shares - target_shares) * position.last_sale_price
            # only rebalance if we are buying or selling more than a certain pct of
            # account value, to save on transaction costs
            if ((abs(sid_cash_freed / account_value) > RebalanceThreshold) &
                (sid in data)):
                s = s + "%s (%d -> %d), " % (sid.symbol, int(current_shares), int(target_shares))
                order_target(sid, target_shares)
                cash_freed = cash_freed + sid_cash_freed
    log.info(s)
    return cash_freed

def should_rebalance(context):
    ret = context.rebalance_needed
    context.rebalance_needed = not context.rebalance_needed
    return ret

# This returns the global switch as to whether we can add any new positions,
# or only sell/rebalance positions.
def can_buy(context, data):
    latest = data[context.spy].close_price
    h = history(200,'1d','close_price')
    avg = h[context.spy].mean()
    return latest > avg

# This function is for adding new positions, by iterating through the 
# eligible stocks in order of momentum, and buying them if we have (anticipate
# having) enough cash to do so.
def add_positions(context, data, cash_available):   
    s = ""
    for i in range(0,len(context.pool)):
        sid = context.pool.index[i]
        if ((sid not in context.portfolio.positions) & (sid in data)):
            desired_shares = desired_position_size_in_shares(context, data, sid)
            cash_req = desired_shares * data[sid].close_price
            if ((cash_req < cash_available)):
                s = s + "%s (%d shares), " % (sid.symbol, int(desired_shares))
                order_target(sid, desired_shares)
                cash_available = cash_available - cash_req
    log.info(s)

def allocate_1(context, data):
    log.info("Selling...")
    cash_from_sales = sell_positions(context, data)
    
def allocate_2(context, data):
    if (should_rebalance(context)):
        log.info("Rebalancing...")
        cash_from_rebalance = rebalance_positions(context, data)

def allocate_3(context, data):
    if (can_buy(context, data)):
        log.info("Buying...")
        add_positions(context, data, context.portfolio.cash)
    else:
        log.info("Cannot buy, pass.")
                 
def record_vars(context, data):
    record(PctCash=(context.portfolio.cash / context.account.equity_with_loan))
    record(CanBuy=can_buy(context, data))
    pos_count = len([s for s in context.portfolio.positions if context.portfolio.positions[s].amount != 0])
    record(Stocks=(pos_count / 100.0)) # scale so that the other numbers don't get squished
    
def handle_data(context, data):
    pass

def cancel_all(context, data):
    sids_cancelled = set()
    open_orders = get_open_orders()
    for security, orders in open_orders.iteritems():  
        for oo in orders: 
            sids_cancelled.add(oo.sid)
            cancel_order(oo)
    n_cancelled = len(sids_cancelled)
    if (n_cancelled > 0):
        log.info("Cancelled %d orders" % n_cancelled)
    return sids_cancelled 