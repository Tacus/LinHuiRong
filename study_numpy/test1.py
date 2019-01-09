# -*- coding: utf-8 -*-      
       
# import urllib2      
# import urllib      
# import re      
# import thread      
# import time  
# import json
# url = "https://pan.baidu.com/share/hotrec?t=1511946207737&bdstoken=956a7a2d79a07563cc32d803f080e58c&channel=chunlei&clienttype=0&web=1&app_id=250528&logid=MTUxMTk0NjIwNzczOTAuNjc5MTkwMzE2MTMyNDA4"
# request = urllib2.Request(url)
# response = urllib2.urlopen(request,timeout = 10)
# resStr = response.read()
# print resStr
# # resStr = resStr.encode("utf-8") 
# # print "xxxx:"+resStr
import pandas as pd
import numpy as np
import math

def calewm(series,alpha):
    lenght = len(series)
    i = 0
    totalWeight = 0
    weight = 0
    yt = 0
    index = 0
    while i < lenght:
        value = series[lenght-i-1]
        if(not np.isnan(value)):
        	index += 1
	        weight = math.pow(1-alpha,index)
	        totalWeight += weight
	        yt += value*weight
        i +=1
    return yt

#halflife
# log = math.log(0.5)/halflife
# alpha = 1-math.exp(log)

#com
alpha = 1/(1+0.5)
#span

# alpha = 2(1+span)


df = pd.DataFrame({'B': [0, 1, 2, np.nan, 4]})
series = df.B
result = calewm(series,alpha)
print(result)

value = df.ewm(com=0.5)
print(value.mean())