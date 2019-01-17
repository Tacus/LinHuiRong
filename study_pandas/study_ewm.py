#coding:utf-8
import numpy as np
import pandas as pd
np.random.seed(2)
nums = np.random.randn(3)
print(nums)
series = pd.Series(nums)
result = series.pct_change(periods=2)
print(result)
# -0.47302468
# -2.19246293

# 4.125749