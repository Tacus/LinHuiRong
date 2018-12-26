"""

Since there seemed to be some interest in momentum models, I thought I'd make a more detailed and more configurable version. I wanted to show what parts are useful to modify and give some ideas for further research.

What is important to understand here is that it's not about maximizing the performance. It's about finding a robust approach, which is not overly dependent on exact parameters. We're trading broad concepts here, and in this case we're looking for robust ways to capture equity momentum.

Remember that the exact settings used for the backtest below are neither the 'best' nor 'worst'. If there is such a thing. It's meant to demonstrate a concept and teach a methodology. Work on it a bit, and I'm sure you can improve it.

The attached model has plenty of settings and comments in the code, which will hopefully help readers get started and experiment with momentum.

If you find things that could be improved here, that's great. Found an error? Please post it. This model is made to be shared and improved.

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
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume, CustomFactor, SimpleMovingAverage, Latest
from quantopian.pipeline.filters.morningstar import Q500US, Q1500US
from quantopian.pipeline.data import morningstar

import numpy as np  # we're using this for various math operations
from scipy import stats  # using this for the reg slope
import pandas as pd


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


def initialize(context):
    """
    Setting our variables. Modify here to test different
    iterations of the model.
    """
    
    # Investment Universe 1 = Q500US, 2 = Q1500US
    context.investment_set = 1
    
    
    # This version uses the average of two momentum slopes.
    # Want just one? Set them both to the same number.
    context.momentum_window = 60  # first momentum window.
    context.momentum_window2 = 90  # second momentum window
    
    # Limit minimum slope. Keep in mind that shorter momentum windows
    # yield more extreme slope numbers. Adjust one, and you may want
    # to adjust the other.
    context.minimum_momentum = 60  # momentum score cap
    
    # Fixed number of stocks in the portfolio. How diversified
    # do you want to be?
    context.number_of_stocks = 25  # portfolio size
    context.index_id = sid(8554) # identifier for the SPY. used for trend filter.
    context.index_average_window = 100  # moving average periods for index filter
    
    # enable/disable trend filter.
    context.index_trend_filter = True  
    
    # Most momentum research excludes most recent data.
    context.exclude_days = 5  # excludes most recent days from momentum calculation
    
    # Set trading frequency here.
    context.trading_frequency = date_rules.month_start()
    
    # identifier for the cash management etf, if used.
    context.use_bond_etf = True
    context.bond_etf = sid(23870) 
    
    # 1 = inv.vola. 2 = equal size. Suggest to implement 
    # market cap and inverse market cap as well. There's 
    # lots of room for development here.
    context.size_method = 2 
    
    

    # Schedule rebalance
    schedule_function(
        my_rebalance,
        context.trading_frequency,
        time_rules.market_open(
            hours=1))

    # Schedule daily recording of number of positions - For display in back
    # test results only.
    schedule_function(
        my_record_vars,
        date_rules.every_day(),
        time_rules.market_close())

    # Create our dynamic stock selector - getting the top 500 most liquid US
    # stocks.
    
    if(context.investment_set == 1):
        inv_set = Q500US()
    elif(context.investment_set == 2):
        inv_set = Q1500US()
    
    attach_pipeline(make_pipeline(inv_set), 'investment_universe')



def make_pipeline(investment_set): 
    """
    This will return the selected stocks by market cap, dynamically updated.
    """
    # Base universe 
    base_universe = investment_set 
    yesterday_close = USEquityPricing.close.latest

    pipe = Pipeline(
        screen=base_universe,
        columns={
            'close': yesterday_close,
        }
    )
    return pipe


def my_rebalance(context, data):
    """
    Our monthly rebalancing routine
    """

    # First update the stock universe. 
    context.output = pipeline_output('investment_universe')
    context.security_list = context.output.index

    # Get data
    hist_window = max(context.momentum_window,
                      context.momentum_window2) + context.exclude_days

    hist = data.history(context.security_list, "close", hist_window, "1d")

    data_end = -1 * context.exclude_days # exclude most recent data

    momentum1_start = -1 * (context.momentum_window + context.exclude_days)
    momentum_hist1 = hist[momentum1_start:data_end]

    momentum2_start = -1 * (context.momentum_window2 + context.exclude_days)
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
    buy_list = ranking_table[:context.number_of_stocks]
    final_buy_list = buy_list[buy_list > context.minimum_momentum] # those who passed minimum slope requirement

    # Calculate inverse volatility, for position size.
    inv_vola_table = hist[buy_list.index].apply(inv_vola_calc)
    # sum inv.vola for all selected stocks.
    sum_inv_vola = np.sum(inv_vola_table)

    # Check trend filter if enabled.
    if (context.index_trend_filter):
        index_history = data.history(
            context.index_id,
            "close",
            context.index_average_window,
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
            if (context.size_method == 1):
                weight = vola_target_weights[security]
            elif (context.size_method == 2):
                weight = (1.0 / context.number_of_stocks)
                print context.number_of_stocks
            order_target_percent(security, weight)
            equity_weight += weight
    
       

    # Fill remaining portfolio with bond ETF
    etf_weight = max(1 - equity_weight, 0.0)

    print 'equity exposure should be %s ' % equity_weight

    if (context.use_bond_etf):
        order_target_percent(context.bond_etf, etf_weight)

def my_record_vars(context, data):
    """
    This routine just records number of open positions and exposure level
    for display purposes.
    """
    etf_exp = 0.0
    pos_count = 0
    eq_exp = 0.0
    for position in context.portfolio.positions.itervalues():
        pos_count += 1
        if (position.sid == context.bond_etf):
            etf_exp += (position.amount * position.last_sale_price) / \
                context.portfolio.portfolio_value
        else:
            eq_exp += (position.amount * position.last_sale_price) / \
                context.portfolio.portfolio_value

    record(equity_exposure=eq_exp)
    record(bond_exposure=etf_exp)
    record(tot_exposure=context.account.leverage)
    record(positions=pos_count)
"""

Andreas,

1.In this version of Clenow Momentum strategy you introduced stock selection using two slopes with different periods and exclude_days parameter.
What is the idea behind those improvements and their influence on performance metrics ?

2.To my mind the code in line 176

data_end = -1 * context.exclude_days  
should be written

data_end = -1 * (context.exclude_days + 1)  
otherwise you will get a run-time error if context.exclude_days = 0

  Andreas Clenow  Apr 10, 2017
Hi Vladimir,

The main purpose with introducing these variables is to show common practices and what kind of things might be useful to tinker with. The aim is robustness.

The two slopes demonstrates a concept which could easily be built upon. It's quite a common approach, to weight different calculation windows for a momentum model. You could add more of them, you could add weighting factors, you could try punishing short term momentum in favor of long term, etc. It opens up for quite a bit of potential research.

The exclude_days variable is a very common approach seen in most academic literature on momentum. Most researchers exclude the last month's data to account for the snap-back effect. Some like using this, some not. There's plenty of research out there favoring either approach.

The exclude_days syntax is my mistake. You're absolutely correct. Thanks for spotting it, Vladimir!

  William Spratt  Apr 11, 2017
Andreas,

Excellent code, I follow both of your momentum posts and have learned a lot from your strategies, thank you for sharing all your work and ideas.

Would you, or anyone else following know how to add to the code a way to move to multiple tickers when SPY is below its MA trend?

For example, instead of just IEF, move evenly to IEF, AGG, GLD? Is that an easy code change?

# identifier for the cash management etf, if used.  
context.use_bond_etf = True  
context.bond_etf = sid(23870)  
  Pietro  Apr 11, 2017
Can anyone explain why every trades is executed at different time? 4:30, 4:35,...and even at 5:00
I see it in transaction details

  Andreas Clenow  Apr 11, 2017
Pietro: It has to do with the Quantopian slippage model, which limits how large part of the volume you can take. Unless you disable the slippage model, it won't let you take a large order at the market, if there wasn't really sufficient liquidity to do that without impact. The code at the moment simply enters market orders, and lets the executions land where they may. Feel free to modify.

William: Shouldn't be difficult. Just split the etf_weight into the number of funds you want to allocate to, and enter target_percent orders for them. Easily done.

  Warsame  Apr 12, 2017
@ Andreas thank you for sharing your expertise with us. It is very much appreciated. And your books are great.

Cheers,
Warsame

  Jack Brown  Apr 12, 2017
@Andreas - Greatly appreciate your work and supplying us a great example to build from!

  Andreas Clenow  Apr 12, 2017
Thanks, guys. Your comments are much appreciated. I'm looking forward to see what improvements the community can do on the model. Remember that it's just a base version, and leaves plenty of room for improvements.

  Greg Keating  Apr 13, 2017
@Andreas - One of the things I haven't seen mentioned or incorporated in any of the posts whether in this thread or the other but is mentioned in your book is in regards to the gap filter. I know you are focused on providing a broad concept here for others to work off of. Yet I am curious; are you purposely leaving that out of the code due to a revised methodology on your part? Or are you still using that as a filter in your own personal algorithms and it is again just something the community can incorporate into this code if they'd like. I also must say I've enjoyed learning from your book and appreciate how active of a member you have been here in the Quantopian forums. I have been actively using this methodology with some modifications to live trade for a few months now and therefore am always looking for ways to improve upon it.

  Andreas Clenow  Apr 18, 2017
Thanks, Greg.

The gap filter I used in Stocks on the Move is probably the one thing I get the most questions about. In particular after readers run simulations and, correctly, conclude that it seemingly has no actual impact on results over time. That's absolutely correct. It doesn't.

The only point of the gap filter is that it makes it easier to actually execute and follow the rules. Without a gap filter or similar, you will get some pretty scary looking entry signals at times. That's not visible on an equity curve like the one above, but it will have an impact on your ability to actually pull the trigger on a trade. The gap filter also takes you out of trades where something out of the ordinary happens. A large move up, or a large move down. Either way, the scenario changes and it's comfortable to exit. I call this type of rules comfort rules.

For those who didn't (yet..?) read Stocks on the Move: The gap filter rule described there stated that any stock is excluded from the valid investment universe if it had a close to close gap in excess of 15% in the the past 90 days. At least that's what I remember at the moment, without checking my own book... As stated, it doesn't change any results in any meaningful way over time, but it makes it easier to follow the rules by removing some scary setups.

And of course, my usual disclaimer: I'm never attempting to publish the best possible rules, or some sort of optimal Clenow Super Algo, which would obviously be quite silly despite the catchy name. My published research always aims to teach a concept and show valid methods of working. My intention is never that readers should simply take my rules and trade it, but rather to learn from it, take what they like, modify and change what they don't like, and make their own personal models. That's why I always publish all the rules.


"""