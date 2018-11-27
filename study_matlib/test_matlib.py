# coding=utf-8
##先导入各种库
import datetime
import time
import pandas as pd
import talib
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
import matplotlib.finance as fin
import numpy as np

x = np.linspace(0, 5, 10)
# x = np.linspace(0, 5, 10,False)
y = x ** 2
y = np.zeros(10)


plt.figure()
plt.plot(x,y,'r--')
plt.xlabel("x")
plt.ylabel("y")
plt.title("hahah")
plt.show()

# plt.subplot(1,2,1)
# plt.plot(x, y, 'r--')
# plt.subplot(1,2,2)
# plt.plot(y, x, 'g*-');

ts=pd.Series(np.random.randn(5), index=(pd.date_range('2018-1-2', periods=5)))
print("\n", ts)
ts.plot(title="series figure", label="normal")
ts_cumsum=ts.cumsum()       #累积求合
ts_cumsum.plot(style="r--", title="cumsum", label="cumsum")
plt.legend()
plt.tight_layout()
plt.show()
print(pd.date_range('2018-1-2', periods=5))
print(list(ts))
print(ts[1], ts.describe())
