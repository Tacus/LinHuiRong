from BaseClass import *
class StockRSData(BaseClass):
	def __init__(self,code,period):
		super(StockRSData,self).__init__()
		self.init_data(code,period)

	def init_data(self,code,period):
		self.security_code = code
		self.current_se_price = 0
		self.current_sh_price = 0
		self.rs = []
		self.se_closes = []
		self.sh_closes = []
		self.today_rs_max = 0
		self.period = period
		self.pass_day = 0
		self.rs_satisfied = False
		self.can_betrade = False

	def set_rs_date(self,se_closes,sh_closes):
		self.se_closes = se_closes.tolist()
		self.sh_closes = sh_closes.tolist()
		self.rs = (se_closes / sh_closes).tolist()

	def update_daily(self,se_close,sh_close):
		self.se_closes.append(se_close)
		self.sh_closes.append(sh_close)
		self.today_rs_max = se_close/sh_close
		if(self.rs_satisfied or (10 >= self.pass_day and 0 != self.pass_day)):
			self.can_betrade = True
			self.pass_day += 1
		else:
			self.can_betrade = False
			self.pass_day = 0
		print(self.tag,self.pass_day,self.can_betrade,self.rs_satisfied)

	#if time is 14:59,record it
	def update(self,curt_se_price,curt_sh_price,date):
		self.current_se_price = curt_se_price
		self.current_sh_price = curt_sh_price
		current_rs_value = curt_se_price/curt_sh_price
		self.today_rs_max = max(self.today_rs_max,current_rs_value)
		if(date.hour == 14 and 59 == date.minute):
			self.rs.append(self.today_rs_max)
		self.check_rs_satisfied()


	def check_rs_satisfied(self):
		total = len(self.rs)
		max_close = max(self.se_closes[-self.period:])
		if(total >= self.period):
			rs_max = max(self.rs[-self.period:])
		else:
			rs_max = max(self.rs)

		if(self.today_rs_max >= rs_max and self.current_se_price < max_close):
			self.rs_satisfied = True
		else:
			self.rs_satisfied = False
	def can_be_trade(self):
		return self.can_be_trade