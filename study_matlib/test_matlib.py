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