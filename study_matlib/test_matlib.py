# coding=utf-8
import datetime
import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
# import matplotlib.finance as fin
# import numpy as np

# x,step = np.linspace(0,5,10,True,True)

# ax1=plt.subplot2grid((4,1),(0,0),rowspan=3)
# ax2 = plt.subplot2grid((4,1),(3,0),sharex = ax1)
# series = pd.Series(x)
# series.plot(ax = ax1,legend=True,style = "r--",)
# print(series)
# plt.show()

# # plt.subplot(1,2,1)
# # plt.plot(x, y, 'r--')
# # plt.subplot(1,2,2)
# # plt.plot(y, x, 'g*-');

# ts=pd.Series(np.random.randn(5), index=(pd.date_range('2018-1-2', periods=5)))
# print("\n", ts)
# ts.plot(title="series figure", label="normal")
# ts_cumsum=ts.cumsum()       #累积求合
# ts_cumsum.plot(style="r--", title="cumsum", label="cumsum")
# plt.legend()
# plt.tight_layout()
# plt.show()
# print(pd.date_range('2018-1-2', periods=5))
# print(list(ts))
# print(ts[1], ts.describe())

def __str__(self):
        value = "行业：%s,代码:%s,名称:%s,increase:%s,cur_rs:%s,ema_rs:%s"%(self.industry_name,self.security,self.name,self.increase,self.cur_rs,self.ema_rs)
        return value