#coding: utf-8
import jqdata
from jqdata import *
import pandas as pd
import numpy as np
import Utils
import talib as tb
from NewIndustryClass import *
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
import matplotlib.finance as fin


start_date = "2018-01-03"
end_date = "2018-11-13"

def get_mightlymarket_closes(datetime,count):
    codes = ["000001.XSHG","399006.XSHE","399005.XSHE"]
    panel = get_price(codes,end_date = datetime,count = count,fields = ["close"])
    df_close = panel["close"]
    series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
    max_value = -1
    max_code = None
    for code in codes:
        if(series_increase[code]>max_value):
            max_value = series_increase[code]
            max_code = code
    return df_close[max_code]

#获取交易日日期
trade_date=list(jqdata.get_trade_days(start_date=start_date,end_date=end_date))
count = 240
end_date = trade_date[-1]
security = "600588.XSHG"
history_data = get_price(security = security,end_date = end_date,count = count,fields = ['close','volume'])
series_market_closes = get_mightlymarket_closes(end_date,count)
df_close = history_data["close"]
df_volume = history_data["volume"]
series_increase = (df_close.iloc[-1] - df_close.iloc[0])/df_close.iloc[0]
# if(not data[security].paused):
increase = round(series_increase,4)
stock_close = df_close
series_rs = stock_close/series_market_closes
# print(stock_close,series_rs)

ema_rs = round(tb.EMA(np.array(series_rs),39)[-1],4)
volume = df_volume[-1]
cur_rs = round(series_rs[-1],4)
close_price = stock_close[-1]
stock_info = StockInfo(security,"234232","ceshi ","xxxx")
stock_info.set_data(increase,close_price,stock_close,cur_rs,ema_rs,volume)
new_industry = CustomIndustry("21313")
new_industry.add_stockinfo(stock_info)
new_industry.check_ema_rs(series_market_closes)
cur_rs = round(new_industry.cur_rs,2)
ema_rs = round(new_industry.cur_emars,2)

fig = plt.figure()
grid = plt.GridSpec(3, 1, hspace=0.15)
main_ax = plt.subplot(grid[0:2,0])
extra_ax = plt.subplot(grid[2,0], sharex=main_ax)
fig.subplots_adjust(bottom=0.2)
plt.grid()
plt.show()
