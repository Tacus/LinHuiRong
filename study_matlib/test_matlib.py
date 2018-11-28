# coding=utf-8
import datetime
import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
# import matplotlib.finance as fin
import numpy as np

x,step = np.linspace(0,5,10,True,True)

ax1=plt.subplot2grid((4,1),(0,0),rowspan=3)
ax2 = plt.subplot2grid((4,1),(3,0),sharex = ax1)
series = pd.Series(x)
series.plot(ax = ax1,legend=True,style = "r--",)
print(series)
plt.show()

# plt.subplot(1,2,1)
# plt.plot(x, y, 'r--')
# plt.subplot(1,2,2)
# plt.plot(y, x, 'g*-');