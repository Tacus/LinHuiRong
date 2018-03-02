# # coding: UTF-8
# import numpy as np
# import talib as tb
# import pandas as pd

# close = np.random.random(10)
# print close,close.ptp()

# # np.array()
# output = tb.SMA(close,5)
# print "SMA:",output
# output = tb.MA(close,5)
# print "MA:",output


import sys
import pylab as pl
import talib as tb

# size = []
# for i in xrange(10000):
#     size.append(sys.getsizeof(size))

# pl.plot(size)
# pl.show()

print tb.get_functions()
print tb.get_function_groups()