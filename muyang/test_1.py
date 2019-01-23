import pandas as pd
import numpy as np
df=pd.DataFrame(np.random.rand(4,4), index=list('abcd'), columns=list('ABCD'))
# print(dir(df))
print('A' in df.columns)