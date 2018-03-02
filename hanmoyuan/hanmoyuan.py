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

#level up
# 1.去除收盘价高于40元的。
# 2.去除60日均线在120日内涨幅超过1.4倍的高开5点以上
# 3.下单时间：9.32分后  （对应下面第10条，第1条）
# 4.每只买入1000股，
# 5.去除尾盘2.50后涨停股
# 6.去没开板的新股(上市不到60天) 去三个以上一字板股
# 7. 大盘MA120线250日的最低值，如涨幅大于1.75倍，不做买入，
# 8. 大盘MA120线250日的最低值，如涨幅大于2.2倍，清仓全部, 或者，大盘三天来跌幅>1%,也空仓，买入ETF股票。债券等  
# 9.去除20日内，涨幅>30% 或者，120日内最低价涨幅>1.7倍，清仓.(如果已有股票，也可        做为卖出条件)
# 10.买入排序 ： 
#           1，第一分钟换手大的>2%，如收阳，市价买入，下跌拐点向上1%买入（不拐头不买入）。
#           2，每股收益高低排序，
#           3 净资产增涨率排序，从高到底。
#           4利润同比增长，从高到低   
#           5，市值从小到大，
#           5, 税后净利润上升，市盈率下降。
#           6，现金流为正，
#           7,股息率高底排序
#           8，股东人数减少。
#           9未分配利润同比增长从高到低
#          11.已有股票，不再买入
#          12.五连阳减仓50%
# 前9条不分拆，第10条下的几个条件，可以分开写
# 卖出：
# 情形1：止盈卖出。记录买入后持仓股票的股价峰值，用于止盈，每回撤3%，卖出50%，不足200股，清空。卖出时爬取买一行情，如果挂单手数天于1000，则不必卖出
# 情形2：回落至盈利不足1%，清空该股
# 情形3：止损卖出。亏损15%，止损
# 情形4：卖出尾盘10分钟急拉3点以上的  尾盘10分涨停的
# 情形5：开盘涨停打开卖出 （如：601127   2017-10-18  2017-8-11日，冲高回落3%减仓）
# 翰墨缘  12:38:12
# 对于情形3  如果买入的股票在120内下跌50%，近20日内下跌（收盘价的最高和最低比值）大于20%以上的，不作止损，采用网格交易法：
        
#             网格高度定为10%，每下跌10%，买入200股，记录本次买入价，本次买入价格，本次买入获利10%，（冲高回落1%）卖出刚买入的200股 (循环操作)，记录本次卖出价，在此价格下跌大于6%，再买入200股，记录本次买入价，上涨5%卖出（循环操作）
# 翰墨缘  12:40:00
# 关于择时：
# 二八择时：1.二八曲线连续三天差值加大，汰弱取强


def initialize(context):
    # g.initsecurity = get_index_stocks("000300.XSHG")
    g.initsecurity = get_all_securities(types='stock').index()
    # g.initsecurity = ["002131.XSHE"]
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 

def before_market_open(context):
    # log.info(dir(context.current_dt.time()))
    result = history(1, unit='1d', field='close', security_list=g.initsecurity, df=True, skip_paused=False, fq='pre')
    result = result[result<40]
    g.radio_1 = get_radio(context,"000300.XSHG",120,250)
    timestr = str(context.current_dt.date()) +" 09:32:00"
    g.times = datetime.datetime.strptime(timestr,"%Y-%m-%d %H:%M:%S")
    current_data = get_current_data()
    g.security = []
    if(g.radio_1 < 1.75):
        for security in result:
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
                    price_data = get_price(security,  end_date = context.current_dt, frequency = "1d", fields = ["close"], skip_paused = True, count = 20)
                   
                    min_price = price_data["close"].min()
                    ratio = (last_price - min_price)/min_price
                    # log.info(last_price,min_price,ratio,high_limit)
                    
                    ratio_fit = ratio < 0.3
                    if(ratio_fit and limit and limit_1):
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
