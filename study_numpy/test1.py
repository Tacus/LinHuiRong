# -*- coding: utf-8 -*-      
       
import urllib2      
import urllib      
import re      
import thread      
import time  
import json
url = "https://pan.baidu.com/share/hotrec?t=1511946207737&bdstoken=956a7a2d79a07563cc32d803f080e58c&channel=chunlei&clienttype=0&web=1&app_id=250528&logid=MTUxMTk0NjIwNzczOTAuNjc5MTkwMzE2MTMyNDA4"
request = urllib2.Request(url)
response = urllib2.urlopen(request,timeout = 10)
resStr = response.read()
print resStr
# resStr = resStr.encode("utf-8") 
# print "xxxx:"+resStr
