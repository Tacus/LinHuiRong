import pandas as pd
import numpy as np
import talib
from jqlib.technical_analysis import *
import datetime
#from MailSenderHTML import MailSenderHTML
#from datetime import datetime, timedelta



# ¹ýÂËÍ£ÅÆ¹ÉÆ±º¯Êý
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    stock_list = [stock for stock in stock_list if not current_data[stock].paused]
    return stock_list

#¹ýÂËÍËÊÐº¯Êý    
def delisted_filter(security_list):
    current_data = get_current_data()
    security_list = [stock for stock in security_list if not 'ÍË' in current_data[stock].name]
    return security_list

#¹ýÂËStº¯Êý
def st_filter(security_list):
    current_data = get_current_data()
    security_list = [stock for stock in security_list if not current_data[stock].is_st]
    return security_list


    
def candidate_stocks(context):
    date=context.current_dt.strftime("%Y-%m-%d")
    lst_000001 = get_index_stocks('000001.XSHG') # È«²¿ÉÏÊÐA¹ÉºÍB¹É
    lst_000002 = get_index_stocks('000002.XSHG',date='2009-05-01') # È«²¿ÉÏÊÐA¹É
    lst_000003 = get_index_stocks('000003.XSHG') # È«²¿ÉÏÊÐB¹É
    lst_399106 = get_index_stocks('399106.XSHE',date='2009-05-01') # ÉîÖ¤×ÛºÏÖ¸Êý£ºÔÚÉîÛÚÖ¤È¯½»Ò×ËùÖ÷°å¡¢ÖÐÐ¡°å¡¢´´Òµ°åÉÏÊÐµÄÈ«²¿¹ÉÆ±
    lst_399107 = get_index_stocks('399107.XSHE') # ÉîÖ¤A¹ÉÖ¸Êý
    lst_399108 = get_index_stocks('399108.XSHE') # ÉîÖ¤B¹ÉÖ¸Êý
    lst_index = list(set(lst_000002).union(set(lst_399106))) # get_index_stocks ·Ö±ðÈ¡ÉÏº£ÉîÛÚÈ«²¿¹ÉÆ±ºó×éºÏ
    log.info("Ó¢ÐÛÊýÁ¿: %s" % len(lst_index))
    scu0 = lst_index
    
    #¹ýÂËÍ£ÅÆ¡¢ÍËÊÐºÍstÅÆ¹É
    scu1 = filter_paused_stock(scu0)
    scu2 = delisted_filter(scu1)
    scu3 = st_filter(scu2)
    
    #²ÆÎñÑ¡¹É
    df = get_fundamentals(query(
                valuation.code
            ).filter(
                valuation.code.in_(scu3),
                valuation.market_cap <= 500
            ).limit(3888) #ÏÞÖÆ¹ÉÆ±³Ø¹ÉÆ±ÊýÁ¿
            , date=date
            )
    stock_list = list(df['code'])
    return stock_list

   

# ³õÊ¼»¯º¯Êý£¬Éè¶¨»ù×¼µÈµÈ
def initialize(context):
    # Éè¶¨»¦Éî300×÷Îª»ù×¼
    set_benchmark('000300.XSHG')
    # ¿ªÆô¶¯Ì¬¸´È¨Ä£Ê½(ÕæÊµ¼Û¸ñ)
    set_option('use_real_price', True)
    # Êä³öÄÚÈÝµ½ÈÕÖ¾ log.info()
    log.info('³õÊ¼º¯Êý¿ªÊ¼ÔËÐÐÇÒÈ«¾ÖÖ»ÔËÐÐÒ»´Î')

    
    g.t=1
    g.tc=3
    
    
    
    
    
    g.stocks_max_price=dict()
    
    # ¹ÉÆ±ÀàÃ¿±Ê½»Ò×Ê±µÄÊÖÐø·ÑÊÇ£ºÂòÈëÊ±Ó¶½ðÍò·ÖÖ®Èý£¬Âô³öÊ±Ó¶½ðÍò·ÖÖ®Èý¼ÓÇ§·ÖÖ®Ò»Ó¡»¨Ë°, Ã¿±Ê½»Ò×Ó¶½ð×îµÍ¿Û5¿éÇ®
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # ¿ªÅÌÇ°ÔËÐÐ
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    # ¿ªÅÌºóÔËÐÐ
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    # ÊÕÅÌºóÔËÐÐ
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
    
    
    
    
# ¿ªÅÌÇ°ÔËÐÐº¯Êý     
def before_market_open(context):
    
    # Êä³öÔËÐÐÊ±¼ä
    log.info('º¯ÊýÔËÐÐÊ±¼ä(before_market_open)£º'+ str(context.current_dt.time()))

    # ¸øÎ¢ÐÅ·¢ËÍÏûÏ¢£¨Ìí¼ÓÄ£Äâ½»Ò×£¬²¢°ó¶¨Î¢ÐÅÉúÐ§£©
    send_message('ÃÀºÃµÄÒ»Ìì~')
    
    # Òª²Ù×÷µÄ¹ÉÆ±
    g.security =candidate_stocks(context)
    
    
   
    # ÉèÖÃÊÖÐø·ÑÓëÊÖÐø·Ñ
    set_slip_fee(context) 
    
    
    
    

# ¿ªÅÌºóÔËÐÐº¯Êý     
def market_open(context):
    if g.t%g.tc==0:
           for stock in context.portfolio.positions:
               order_target(stock, 0)

    g.t+=1    

         
    
# ½»Ò×º¯Êý    
def handle_data(context, data):
    log.info('º¯ÊýÔËÐÐÊ±¼ä(market_open):'+str(context.current_dt.time()))
    
    #ÓûÂòÈë¹ÉÆ±³Ø
    g.buylist = []
    
    
    #ÂòÈë¹ÉÆ±ÊýÁ¿
    stocknum=10
    if context.portfolio.positions_value>context.portfolio.total_value*4/5:
       Cash = 0
    else:
       if  len(context.portfolio.positions) < stocknum:
           Num = stocknum - len(context.portfolio.positions)
           Cash=context.portfolio.available_cash/Num
       else:
           Cash = 0
    
    #Ñ¡¹É
    for stock in g.security: 
        
        
        #¼ÆËã5ÌìÊý¾Ý
        #»ñÈ¡5ÌìÊÕÅÌ¼Û¸ñ
        security_data_w = history(5*2, '1d', 'close' , stock, df=False, skip_paused=True)
        #¿ÕÁÐ·ÅÖÃÊÕÅÌ¼Û¸ñ
        ma05 = {}
        #½«ÊµÊ±¼Û¸ñ¼ÓÈëÊÕÅÌ¼Û¸ñÁÐ
        security_data_w[stock] = np.append(security_data_w[stock],data[stock].close)
        #¼ÆËã5ÌìMA
        ma05[stock] = talib.MA(security_data_w[stock], 5)
        #×òÌìMA5
        MA051 = ma05[stock][-1]
        #Ç°ÌìMA5
        MA052 = ma05[stock][-2]
        #´óÇ°ÌìMA5
        MA053 = ma05[stock][-3]
        #¼¼Êõ½ñÌìÊµÊ±½Ç¶È
        JDMA50 = ((MA051/MA052-1)*100)
        JDMA51 = math.atan(JDMA50)*180/math.pi
        #¼¼Êõ×òÌì½Ç¶È
        JDMA52 = ((MA052/MA053-1)*100)
        JDMA53 = math.atan(JDMA52)*180/math.pi
        
        
        
        #¼ÆËã10ÌìÊý¾Ý£¨ÆäËûÍ¬ÉÏ£©
        security_data_i = history(10*2, '1d', 'close' , stock, df=False, skip_paused=True)
        ma10 = {}
        security_data_i[stock] = np.append(security_data_i[stock],data[stock].close)
        ma10[stock] = talib.MA(security_data_i[stock], 10)
        MA011 = ma10[stock][-1]
        MA012 = ma10[stock][-2]
        MA013 = ma10[stock][-3]
        JDMA10 = ((MA011/MA012-1)*100)
        JDMA11 = math.atan(JDMA10)*180/math.pi
        JDMA12 = ((MA012/MA013-1)*100)
        JDMA13 = math.atan(JDMA12)*180/math.pi
        
        
        #¼ÆËã20ÌìÊý¾Ý£¨ÆäËûÍ¬ÉÏ£©
        security_data_e = history(20*2, '1d', 'close' , stock, df=False, skip_paused=True)
        ma20 = {}
        security_data_e[stock] = np.append(security_data_e[stock],data[stock].close)
        ma20[stock] = talib.MA(security_data_e[stock], 20)
        MA021 = ma20[stock][-1]
        MA022 = ma20[stock][-2]
        MA023 = ma20[stock][-3]
        JDMA20 = ((MA021/MA022-1)*100)
        JDMA21 = math.atan(JDMA20)*180/math.pi
        JDMA22 = ((MA022/MA023-1)*100)
        JDMA23 = math.atan(JDMA22)*180/math.pi
        
        
        CL = data[stock].close
        current_data = get_current_data()
        OP = current_data[stock].day_open




        
        #Ìõ¼þÑ¡¹É
        
        #5Ìì½Ç¶È¡¢10Ìì½Ç¶È¡¢20Ìì½Ç¶È¶¼´óÓÚ0
        #5ÌìÊµÊ±½Ç¶È´ó>5Ìì×òÌì½Ç¶È
        #10ÌìÊµÊ±½Ç¶È´ó>5Ìì×òÌì½Ç¶È
        #20ÌìÊµÊ±½Ç¶È´ó>5Ìì×òÌì½Ç¶È
        if  JDMA51>0 \
        and JDMA11>0 \
        and JDMA21>0 \
        and JDMA51>=JDMA53 \
        and JDMA11>=JDMA13 \
        and JDMA21>=JDMA23 \
        and (MA051-MA011)/MA011*100<2 \
        and CL>MA051>OP \
        and CL>MA011>OP: 

            g.buylist.append(stock)
    
    #log.info("¹ÉÆ±: %s" % g.buylist)        

            #Âú×ãÌõ¼þ,¼ÆËã×Ê½ðÊÇ·ñÐ¡ÓÚ×Ü×Ê½ðµÄ1/4,ÊÇ¾ÍPASS,²»ÊÇ¾Í¿ªÊ¼½»Ò×
            if context.portfolio.available_cash<context.portfolio.total_value/11:
                      
               pass
            
            elif stock in context.portfolio.positions:
            
               pass
            
            else:
               #ÂòÈë¹ÉÆ±
               order_value(stock, Cash)
        else:
            #²»Âú×ãÌõ¼þ
            pass
    
    
    
    
    
    


def set_slip_fee(context):
    # ½«»¬µãÉèÖÃÎª0
    set_slippage(FixedSlippage(0)) 
    # ¸ù¾Ý²»Í¬µÄÊ±¼ä¶ÎÉèÖÃÊÖÐø·Ñ
    dt=context.current_dt
    log.info(type(context.current_dt))
    
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5)) 
        
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
            
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
                
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))



## ÊÕÅÌºóÔËÐÐº¯Êý  
def after_market_close(context):
    log.info(str('º¯ÊýÔËÐÐÊ±¼ä(after_market_close):'+str(context.current_dt.time())))
    #µÃµ½µ±ÌìËùÓÐ³É½»¼ÇÂ¼
    trades = get_trades()
    for _trade in trades.values():
        log.info('³É½»¼ÇÂ¼£º'+str(_trade))
    log.info('Ò»Ìì½áÊø')
    log.info('##############################################################')        