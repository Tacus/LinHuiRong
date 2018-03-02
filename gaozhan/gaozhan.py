# 导入函数库
import jqdata
import math
import numpy as np
import pandas as pd
# 初始化函数，设定基准等等
def initialize(context):
    enable_profile()
    # g.initsecurity = get_index_stocks("000300.XSHG")
    g.initsecurity =['002320.XSHE']
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
    g.varivble_dict = dict()
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
    df5 = history(security_list = g.initsecurity,unit = '1d', field = 'close',count =  6,df = False, skip_paused = False)
    df10 = history(security_list = g.initsecurity,unit = '1d', field = 'close',count =  11,df = False, skip_paused = False)
    df20 = history(security_list = g.initsecurity,unit = '1d', field = 'close',count =  21,df = False, skip_paused = False)
    df40 = history(security_list = g.initsecurity,unit = '1d', field = 'close',count =  41,df = False, skip_paused = False)
    df60 = history(security_list = g.initsecurity,unit = '1d', field = 'close',count =  61,df = False, skip_paused = False)
    for security in g.initsecurity:
        security_data = current_data[security]
        if(not security_data.paused and not security_data.is_st):
            close_data = df5[security]
            # 取得过去五天的平均价格
            single_dict = dict()
            g.varivble_dict[security] = single_dict
            MA5_1 = close_data[1:].mean()
            MA5_2 = close_data[:5].mean()
            single_dict["df5"] = close_data
            single_dict["MA5_1"] = MA5_1
            single_dict["MA5_2"] = MA5_1
            
            close_data = df10[security]
            MA10_1 = close_data[1:].mean()
            MA10_2 = close_data[:10].mean()
            single_dict["df10"] = close_data
            single_dict["MA10_1"] = MA10_1
            single_dict["MA10_2"] = MA10_2
            
            close_data = df20[security]
            MA20_1 = close_data[1:].mean()
            MA20_2 = close_data[:20].mean()
            single_dict["df20"] = close_data
            single_dict["MA20_1"] = MA20_1
            single_dict["MA20_2"] = MA20_2
            
         
            close_data = df40[security]
            MA40_1 = close_data[:40].mean()
            single_dict["df40"] = close_data
            single_dict["MA40_1"] = MA40_1
            # close_date = df60[security]
            # MA60 = close_data[1:].mean()
            # MA60_1 = close_data[:60].mean()
            # single_dict["df60"] = close_data
            # single_dict["MA60_1"] = MA60_1
            g.security.append(security)
            
            ma_abs_five = get_ma_absdellta(context,security,5,10,49)
            ma_abs_ten = get_ma_absdellta(context,security,10,20,49)
            single_dict["ma_abs_five"] = ma_abs_five
            single_dict["ma_abs_ten"] = ma_abs_ten

def handle_data(context, data):
    current_data = get_current_data()
    for security,position in context.portfolio.positions.iteritems():
        # print(type(position),position)
        check_sell(position,current_data,context)
        
    # for security in g.security:
    check_buy(context)



def check_sell(position, current_data,context):
    security = position.security
    current_price = current_data[security].last_price
    high_price_df = get_price(security, start_date=position.init_time,fields = ["high"],end_date=context.current_dt, frequency='1m',skip_paused=True)
    high_price = high_price_df["high"].max()
    if(current_price <=high_price*(1-0.05)):
        order_target_value(security,0)

def check_buy(context):
    current_data = get_current_data()
    cur_pos = len(context.portfolio.positions)
    if cur_pos != 10 :
        for security in g.security:
            security_data = current_data[security]
            if security not in context.portfolio.positions and not security_data.is_st:
                single_dict = g.varivble_dict[security]
                current_price = security_data.last_price
                close_data = single_dict['df5']
                # print(single_dict)
                ndarr = close_data[2:]
                ndarr = np.append(ndarr,current_price)
                MA5 = np.mean(ndarr)
                MA5_1 = single_dict['MA5_1']
                MA5_2 = single_dict['MA5_2']
                close_data = single_dict['df10']
                ndarr = close_data[2:]
                ndarr = np.append(ndarr,current_price)
                MA10 = np.mean(ndarr)
                MA10_1 = single_dict['MA10_1']
                MA10_2 = single_dict['MA10_2']
                close_data = single_dict['df20']
                ndarr = close_data[2:]
                ndarr = np.append(ndarr,current_price)
                MA20 = np.mean(ndarr)
                MA20_1 = single_dict['MA20_1']
                MA20_2 = single_dict['MA20_2']
                
                ma_abs_five = single_dict["ma_abs_five"]
                ma_abs_ten = single_dict["ma_abs_ten"]
                ma_abs_five = (ma_abs_five + abs(MA5 - MA10))/50
                ma_abs_ten = (ma_abs_ten + abs(MA10 - MA20))/50
                
                max_delta_five = max(abs(MA10 - MA5),abs(MA10_1 - MA5_1)) - min(abs(MA10 - MA5),abs(MA10_1 - MA5_1))
                max_delta_ten = max(abs(MA20 - MA10),abs(MA20_1 - MA10_1)) - min(abs(MA20 - MA10),abs(MA20_1 - MA10_1))
                b_value = (max_delta_five<(ma_abs_five*3/10) ) and ( max_delta_ten<(ma_abs_ten*3/10) and MA5 > MA10 and MA10 > MA20 )
                
                # log.info("security:%s,Ma5:%s,ma10:%s,ma20:%s"%(security,MA5,MA10,MA20))
                # log.info("security:%s,ma_abs_five:%s,ma_abs_ten:%s,current_price:%s"%(security,ma_abs_five,ma_abs_ten,current_price))
                # log.info("security:%s,max_delta_five:%s,max_delta_ten:%s,b_value:%s"%(security,max_delta_five,max_delta_ten,b_value))
                close_data = single_dict['df40']
                ndarr = close_data[1:]
                ndarr = np.append(ndarr,current_price)
                MA40 = np.mean(ndarr)
                MA40_1 = single_dict['MA40_1']
                # close_date = single_dict['df60']
                # ndarr = close_data[1:]
                # ndarr = np.append(ndarr,current_price)
                # MA60 = np.mean(ndarr)
                # MA60_1 = single_dict['MA60_1']
                
                atan_five = math.atan((MA5/MA5_1 - 1)*100)*180/3.1416
                atan_five_1 = math.atan((MA5_1/MA5_2 - 1)*100)*180/3.1416
                atan_ten = math.atan((MA10/MA10_1 - 1)*100)*180/3.1416
                atan_ten_1 = math.atan((MA10_1/MA10_2 - 1)*100)*180/3.1416
                atan_twt = math.atan((MA20/MA20_1 - 1)*100)*180/3.1416
                atan_twt_1 = math.atan((MA20_1/MA20_2 - 1)*100)*180/3.1416
                atan_ft = math.atan((MA40/MA40_1 - 1)*100)*180/3.1416
                # atan_st = math.atan((MA60/MA60_1 - 1)*100)*180/3.1416
        
                b_angle_1 = (atan_five+atan_ten+atan_twt)>30
                b_angle_2 = atan_five >= atan_five_1 and atan_ten>=atan_ten_1 and atan_twt >= atan_twt_1
                b_angle_3 = atan_five > 0 and atan_ten >0 and atan_twt >0 and atan_ft >=0
        
                # print("security:%s,ma_abs_five：%s,ma_abs_ten:%s,max_delta_five:%s,max_delta_ten:%s,MA40:%s,MA60:%s,atan_five:%s,"%(security,
                #                                                                                                         ma_abs_five,
                #                                                                                                         ma_abs_ten,
                #                                                                                                         max_delta_five,
                #                                                                                                         max_delta_ten,
                #                                                                                                         MA40,
                #                                                                                                         MA60,atan_five))
                # # log.info(security,b_angle_1,b_angle_2,b_angle_3)
                # b_ret = current_price < MA5 * 1.08
                # if(b_ret and b_value and b_angle_1 and b_angle_2 and b_angle_3):
                if(b_value and b_angle_1 and b_angle_2 and b_angle_3):
                    cash = context.portfolio.available_cash
                    order_value(security,cash )
                    log.info("买入",security)
        

#获取移动平均差值 ma(abs(MAx - MAy))
def get_ma_absdellta(context,security,day1,day2,num):
    # 
    df_trade_days = get_price(security, count = num,end_date = context.current_dt,frequency =  "1d",fields = ["close"], skip_paused = True)
    sum = 0
    for index  in range(0,num):
        trade_date = df_trade_days.index[index]
        df1 = get_price(security, count = day1,end_date = trade_date,frequency =  "1d",fields = ["close"], skip_paused = True)
        df2 = get_price(security, count = day2,end_date = trade_date,frequency =  "1d",fields = ["close"], skip_paused = True)
        ma1 = df1['close'].mean()
        ma2 = df2["close"].mean()
        sum += abs(ma2 - ma1)

    # log.info(sum/num)
    return sum

    # log.info(type(df),single)

    # log.info(type(single),dir(single))
    # get_price(security, count = 10, end_date = context.current_dt,frequency =  "1d",fields = ["close"], skip_paused = True)
