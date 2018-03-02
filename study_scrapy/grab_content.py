#encoding:utf-8
import urllib2
import re
import threading
import sys
import time
import numpy as np

homePageUrl = "https://xueqiu.com"
pageUrl = "https://xueqiu.com/v4/statuses/public_timeline_by_category.json?since_id=-1&max_id=-1&count=10&category=-1"
# pageUrl = "http://xueqiu.com"
cookieCacheArray = []
cookieStr = None

class AISpider(object):
	"""docstring for AISpider"""
	def __init__(self, base_url):
		super(AISpider, self).__init__()
		self.base_url = base_url
		self.headers = {}
		self.headers['User-Agent'] = "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Mobile Safari/537.36"

	def start(self):
		pass
	def stop(self):
		pass
class CookieSpider(AISpider):
	# def __init__(self,base_url):
	# 	super(CookieSpider,self).__init__(base_url)
		
	def start(self):
		self.thread = threading.Thread(target = self.process,args =())
		self.thread.start()
	def process(self):
		while True:
			# httpHandler = urllib2.HTTPHandler(debuglevel=1)  
			# httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
			# opener = urllib2.build_opener(httpHandler,httpsHandler)
			# urllib2.install_opener(opener)
			request = urllib2.Request(self.base_url,None,self.headers)
			response = urllib2.urlopen(request,timeout = 10)
			cookies = response.headers["Set-Cookie"].split(",")
			global cookieStr
			cookieStr = ""
			for cookie in cookies:
				entry = cookie.split(";")[0]			
				cookieStr = cookieStr+";"+entry
			time.sleep(3600*24)
	def thread_join(self):
		self.thread.join()


class XueQiuDataSpider(CookieSpider):
	def __init__(self,base_url):
		super(XueQiuDataSpider,self).__init__(base_url)
		self.page = 1		

	def process(self):
		while True:
			if(cookieStr):
				# httpHandler = urllib2.HTTPHandler(debuglevel=1)  
				# httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
				# opener = urllib2.build_opener(httpHandler,httpsHandler)
				# urllib2.install_opener(opener)
				# print "xxxxxx"
				self.headers["Cookie"] = cookieStr
				request = urllib2.Request(self.base_url,None,self.headers)
				response = urllib2.urlopen(request,timeout = 10)
				print response.read()
				time.sleep(10)
if __name__ == "__main__":
	cookieHandler = CookieSpider(homePageUrl)
	cookieHandler.start()
	dataHandler = XueQiuDataSpider(pageUrl)
	dataHandler.start()
	cookieHandler.thread_join()
	dataHandler.thread_join()
