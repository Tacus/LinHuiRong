import BaseClass
class StockRSData(BaseClass):
	def __init__(self,code):
		super(StockRSData,self).__init__()
		self.init_data(code)
        pass

    def init_data(self,code):
    	self.security_code = code
		self.current_se_price = 0
		self.current_sh_price = 0

    def update_daily(self):
    	pass

    def update(self,curt_se_price,curt_sh_price):
    	self.current_se_price = curt_se_price
    	self.current_sh_price = curt_sh_price
    	print(self.tag,self.current_sh_price,self.current_se_price)
