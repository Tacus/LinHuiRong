import math
import pandas as pd
# a = 21.3243859345
# # a = math.floor(a)
# # print a
# b = int(a)

# print b

# print("xx%s"%("hehe"))

# print(None)

dic2 = {'a':[1,2,3,4],'b':[5,6,7,8],"c":[0]*4}
df = pd.DataFrame(dic2)
print(df)
size = df.index.size
df = df.apply(min)
# print(df.iloc[:,0].siz)
print(size,df,df.div(size))
# print(df/len(df.index.size()))
