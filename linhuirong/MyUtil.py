# coding=utf-8

class MyUtil:
	enableLog = True
	def __init__(self,enableLog = True):
		self.enableLog = enableLog

	def logPrint(self,str,*arg):
		if(self.enableLog):
			print str%arg