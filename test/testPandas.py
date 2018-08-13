# # coding: UTF-8
# import numpy as np
# import talib as tb
# import pandas as pd
import re
# # close = numpy.random.random(10)

# # print numpy.mean(close)

# np.array()
# output = talib.SMA(close,5)

# print output

    
def get_oversea_excelpath(filePath,file_name):
    match_name = file_name+r"_(.*)\..*"
    for p, d, fs in os.walk(filePath):
        for f in fs:
            match = re.match(match_name,f)
            if(match):
                return f
        break

file_name = "item"
match_name = file_name+r"_(.*)\..*"
print(match_name,file_name)
match = re.match(match_name,"item_xxx.xlx")

get_oversea_excelpath(filepath,file_name)

if(match):
	print("xxx111",match.group(1))
print("xxx222",match)


