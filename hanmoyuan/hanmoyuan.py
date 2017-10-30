# 选出昨日涨停的股票。 
# 1.去除收盘价高于40元的。
# 2.去除未开板的新股
# 3.去除60日均线在120日内涨幅超过1.4倍的高开5点以上(从最低点开始算？)两个条件合并一个条件
# 4.下单时间：9.32分后  （对应下面第12条，第1条）
# 5.每只买入1000股，
# 6.去除尾盘2.50后涨停股
# 7.去没开板的新股 去三个以上一字板股，近20天内涨幅》30%的
# 8. 大盘MA120线250日的最低值，如涨幅大于1.75倍，不做买入，(当前值大于)
# 9. 大盘MA120线250日的最低值，如涨幅大于2.2倍，清仓全部, 买入ETF股票。债券 
# 10.     买入排序  1，第一分钟换手大的，且收阳。2，每股收益高低排序，3净资产增涨率排序，  4，市值从小到大，
# 11.     已有股票，不再买入
# 翰墨缘  13:52:13
# 卖出：
# 情形1：20%止盈卖出（如买入后上涨）。记录买入后的股价峰值，用于止盈，每回撤3%，卖出50%，不足200股，清空。回落至盈利不足1%，清空该股.
# 情形2：止损卖出。亏损10%，止损
# 情形3：卖出尾盘10分钟内急拉涨停的

def initialize(context):
    g.initsecurity = get_index_stocks("000300.XSHG")[:100]
    # g.initsecurity = ["002131.XSHE"]
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 

def before_market_open(context):
    # log.info(dir(context.current_dt.time()))
    g.radio_1 = get_radio(context,"000300.XSHG",120,250)
    timestr = str(context.current_dt.date()) +" 09:32:00"
    g.times = datetime.datetime.strptime(timestr,"%Y-%m-%d %H:%M:%S")
    current_data = get_current_data()
    g.security = []
    if(g.radio_1 < 1.75):
        for security in g.initsecurity:
            security_data = current_data[security]
            if(not security_data.paused and not security_data.is_st and (security not in context.portfolio.positions)):
                radio = get_radio(context,security,60,120)
                if(radio < 1.4):
                    end_date = context.current_dt.date() - timedelta(1)
                    result = get_price(security,fields = ["close","high_limit"],end_date=end_date, frequency='1d', skip_paused=True,count = 1)
                    # log.info(end_date,result)
                    end_date = str(end_date)+" 14:51:00"
                    result_1 = get_price(security,fields = ["close"],end_date=end_date, frequency='1m', skip_paused=True,count = 1)
                    
                    last_price = result["close"][0]
                    last_price_1 = result_1["close"][0]
                    high_limit = result["high_limit"][0]
                    
                    limit = last_price == high_limit
                    limit_1 = last_price_1 == high_limit
                    less = last_price <= 40
                    
                    price_data = get_price(security,  end_date = context.current_dt, frequency = "1d", fields = ["close"], skip_paused = True, count = 20)
                   
                    min_price = price_data["close"].min()
                    ratio = (last_price - min_price)/min_price
                    # log.info(last_price,min_price,ratio,high_limit)
                    
                    ratio_fit = ratio < 0.3
                    if(ratio_fit and less and limit and limit_1):
                        g.security.append(security)
                        log.info("xx add security:",security)
        

#获取移动平均差值 ma(abs(MAx - MAy))
def get_radio(context,security,day1,day2):
    # 
    df_trade_days = get_price(security, count = day2,end_date = context.current_dt,frequency =  "1d",fields = ["close"], skip_paused = True)
    sum = 0
    minAvg = 9999
    for index  in range(0,day2):
        trade_date = df_trade_days.index[index]
        df1 = get_price(security, count = day1,end_date = trade_date,frequency =  "1d",fields = ["close"], skip_paused = True)
        # df2 = get_price(security, count = day1,end_date = trade_date,frequency =  "1d",fields = ["close"], skip_paused = True)
        ma1 = df1['close'].mean()
        # log.info(security,ma1)
        if(ma1 < minAvg):
            minAvg = ma1
        if(index == day2 -1):
            # log.info(minAvg,ma1,day1)
            return (ma1 - minAvg) /minAvg

def handle_data(context, data):
    current_data = get_current_data()
    for (security,position) in context.portfolio.positions.items():
        # print(type(position),position)
        if(g.radio_1 > 2.2):
            order_target_value(security, 0)
        else:
            check_sell(position,current_data,context)
            
    for security in g.security:
        check_buy(context,security,current_data)
    pass

def check_sell(position, current_data,context):
    security = position.security
    value = position.value
    cost = position.avg_cost * position.total_amount
    ratio = (value - cost)/cost
    # log.info(ratio,value,cost,position.avg_cost,position.total_amount)
    if(ratio <= -0.1 or ratio>0.2):
        order_target_value(security, 0)
        
def check_buy(context,security, current_data):
    # dir(context.current_dt.time())
    delta = context.current_dt - g.times
    seconds = delta.total_seconds()
    if(seconds >0):
        if(security not in context.portfolio.positions):
            order_target(security,1000 )
            log.info("买入",security)
