# 导入函数库
import jqdata
import math
# 初始化函数，设定基准等等
def initialize(context):
    enable_profile()
    g.initsecurity = ["000560.XSHE"]
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
      # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
      # 开盘时运行
    # run_daily(market_open, time='open', reference_security='000300.XSHG')
      # 收盘后运行
    # run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
    g.ma5_dict = {}
    
## 开盘时运行函数
def before_market_open(context):
    log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    g.security = []
    current_data = get_current_data()
    for security in g.initsecurity:
        security_data = current_data[security]
        if(not security_data.paused and not security_data.is_st):
            close_data = attribute_history(security, 7, '1d', ['close'])
            # 取得过去五天的平均价格
            MA5 = close_data['close'][2:].mean()
            MA5_1 = close_data['close'][1:6].mean()
            MA5_2 = close_data["close"][:5].mean()
            close_data = attribute_history(security, 12, '1d', ['close'])
            MA10 = close_data['close'][2:].mean()
            MA10_1 = close_data['close'][1:11].mean()
            MA10_2 = close_data['close'][:10].mean()
            close_data = attribute_history(security, 22, '1d', ['close'])
            MA20 = close_data["close"][2:].mean()
            MA20_1 = close_data['close'][1:21].mean()
            MA20_2 = close_data['close'][:20].mean()
        
            ma_abs_five = get_ma_absdellta(context,security,5,10,50)
            ma_abs_ten = get_ma_absdellta(context,security,10,20,50)
            
            max_delta_five = max(abs(MA10 - MA5),abs(MA10_1 - MA5_1)) - min(abs(MA10 - MA5),abs(MA10_1 - MA5_1))
            max_delta_ten = max(abs(MA20 - MA10),abs(MA20_1 - MA10_1)) - min(abs(MA20 - MA10),abs(MA20_1 - MA10_1))
            b_value = (max_delta_five<(ma_abs_five*3/10) )and( max_delta_ten<(ma_abs_ten*3/10))
            
            
            close_data = attribute_history(security, 41, '1d', ['close'])
            MA40 = close_data["close"][1:].mean()
            MA40_1 = close_data['close'][:40].mean()
            close_date = attribute_history(security, 61, '1d', ['close'])
            MA60 = close_data["close"][1:].mean()
            MA60_1 = close_data['close'][:60].mean()
            
            atan_five = math.atan((MA5/MA5_1 - 1)*100)*180/3.1416
            atan_five_1 = math.atan((MA5_1/MA5_2 - 1)*100)*180/3.1416
            atan_ten = math.atan((MA10/MA10_1 - 1)*100)*180/3.1416
            atan_ten_1 = math.atan((MA10_1/MA10_2 - 1)*100)*180/3.1416
            atan_twt = math.atan((MA20/MA20_1 - 1)*100)*180/3.1416
            atan_twt_1 = math.atan((MA20_1/MA20_2 - 1)*100)*180/3.1416
            atan_ft = math.atan((MA40/MA40_1 - 1)*100)*180/3.1416
            atan_st = math.atan((MA60/MA60_1 - 1)*100)*180/3.1416

            b_angle_1 = (atan_five+atan_ten+atan_twt)>30
            b_angle_2 = atan_five >= atan_five_1 and atan_ten>=atan_ten_1 and atan_twt >= atan_twt_1
            b_angle_3 = atan_five > 0 and atan_ten >0 and atan_twt >0 and atan_ft >=0 and atan_st >=0

            # print("security:%s,ma_abs_five：%s,ma_abs_ten:%s,max_delta_five:%s,max_delta_ten:%s,MA40:%s,MA60:%s,atan_five:%s,"%(security,
            #                                                                                                         ma_abs_five,
            #                                                                                                         ma_abs_ten,
            #                                                                                                         max_delta_five,
            #                                                                                                         max_delta_ten,
            #                                                                                                         MA40,
            #                                                                                                         MA60,atan_five))

            # log.info(security,b_angle_1,b_angle_2,b_angle_3)
            if(b_value and b_angle_1 and b_angle_2 and b_angle_3):
                g.security.append(security)
                g.ma5_dict[security] = MA5
                log.info("xx add security:",security)

def handle_data(context, data):
    current_data = get_current_data()
    for security,position in context.portfolio.positions.iteritems():
        # print(type(position),position)
        check_sell(position,current_data,context)
        
    for security in g.security:
        check_buy(context,security,current_data)



def check_sell(position, current_data,context):
    security = position.security
    current_price = current_data[security].last_price
    high_price_df = get_price(security, start_date=position.init_time,fields = ["high"],end_date=context.current_dt, frequency='1m',skip_paused=True)
    high_price = high_price_df["high"].max()
    if(current_price <=high_price*(1-0.05)):
        order_target_value(security,0)

def check_buy(context,security, current_data):    
    current_price = current_data[security].last_price
    ma5 = g.ma5_dict[security]
    # b_ret = current_price < ma5 * 1.03
    b_ret = True
    cur_pos = len(context.portfolio.positions)
    
    if(cur_pos != 10 and b_ret and  security not in context.portfolio.positions):
        cash = context.portfolio.available_cash
        order_value(security,cash )
        log.info("买入",security)
        

#获取移动平均差值 ma(abs(MAx - MAy))
def get_ma_absdellta(context,security,day1,day2,num):
    # 
    df_trade_days = get_price(security, count = 50,end_date = context.current_dt,frequency =  "1d",fields = ["close"], skip_paused = True)
    sum = 0
    for index  in range(0,num):
        trade_date = df_trade_days.index[index]
        df1 = get_price(security, count = day1,end_date = trade_date,frequency =  "1d",fields = ["close"], skip_paused = True)
        df2 = get_price(security, count = day2,end_date = trade_date,frequency =  "1d",fields = ["close"], skip_paused = True)
        ma1 = df1['close'].mean()
        ma2 = df2["close"].mean()
        sum += abs(ma2 - ma1)

    # log.info(sum/num)
    return sum/50

    # log.info(type(df),single)

    # log.info(type(single),dir(single))
    # get_price(security, count = 10, end_date = context.current_dt,frequency =  "1d",fields = ["close"], skip_paused = True)
  