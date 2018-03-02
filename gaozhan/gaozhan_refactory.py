import talib as tl
import math as mt
from pandas import Series


def initialize(context):
    #用的是实际价格回测
    set_option('use_real_price', True)
    set_benchmark('000001.XSHG')
    set_commission(PerTrade(buy_cost=0.0008, sell_cost=0.0015, min_cost=5))
    set_slippage(PriceRelatedSlippage(0.002))
    log.set_level('order','error')
    #持仓中最多买入的股票个数
    g.buy_stock_count =10
    #每天最多买的股票数量
    g.max_buyNum=5
    #当天已经买的股票数量
    g.buyNum=0
    #用来保存持仓中的股票从买入到现在的最高价等
    g.buy_list_df=pd.DataFrame(columns=["security","days","maxprice","minprice"])

def before_trading_start(context):
    g.buyNum=0

#主调函数    
def handle_data(context, data):
    #print(context.current_dt)
    buy_stocks=[]
    position_count = len(context.portfolio.positions)
    if g.buyNum<5 and position_count<g.buy_stock_count:
        #选股
        buy_stocks = select_stocks(context,data)
        #调仓
        adjust_position(context,data, buy_stocks)
    else:
        adjust_position(context,data, buy_stocks)
        

#选股进股票池
def select_stocks(context,data):

    #获取所有股票的代码
    #stock_list= list(get_all_securities(['stock']).index)
    #过滤停牌和ST股票
    
    stock_list = filter_stock(context)
    #候选买入集
    waitForBuy=[]
    # 选股
    for security in stock_list:
        #获取日线数据
        h = attribute_history(security, 60, '1d', df=False)
        h_closePrice=list(h['close'][:])
        #XXCLOSE表示收盘价，XXOPEN表示开盘价，XXLow表示最低价，XXHIGH表示最高价
        #d1表示T-1，d2表示T-2，如此类推
        d1CLOSE, d2CLOSE, d3CLOSE, d4CLOSE, d5CLOSE= h["close"][-1],h["close"][-2],h["close"][-3],h["close"][-4],h["close"][-5]
        d1OPEN,  d2OPEN,  d3OPEN,  d4OPEN,  d5OPEN=  h["open"][-1], h["open"][-2], h["open"][-3], h["open"][-4], h["open"][-5]
        d1LOW,   d2LOW,   d3LOW,   d4LOW,   d5LOW=   h["low"][-1],  h["low"][-2],  h["low"][-3],  h["low"][-4],  h["low"][-5]
        d1HIGH,  d2HIGH,  d3HIGH,  d4HIGH,  d5HIGH=  h["high"][-1], h["high"][-2], h["high"][-3], h["high"][-4], h["high"][-5]
        #取分钟数据,并将最新一分钟K线的收盘价放入列表h_closePrice中，用于计算指标
        h_minute = attribute_history(security, 2, '1m', df=False)
        h_closePrice.append(h_minute['close'][-1])
        h_closePrice=np.array(h_closePrice)
        
        
        #ma5_1表示T-1的ma5,ma5_2表示T-2的ma5
        ma5_1=h_closePrice[-5:].mean()
        ma5_2=h_closePrice[-6:-1].mean()
        ma5_3=h_closePrice[-7:-2].mean()
        #意思同上
        ma10_1=h_closePrice[-10:].mean()
        ma10_2=h_closePrice[-11:-1].mean()
        ma10_3=h_closePrice[-12:-2].mean()
        #意思同上
        ma20_1=h_closePrice[-20:].mean()
        ma20_2=h_closePrice[-21:-1].mean()
        ma20_3=h_closePrice[-22:-2].mean()  
        #意思同上
        ma40_1=h_closePrice[-40:].mean()
        ma40_2=h_closePrice[-41:-1].mean()
        ma40_3=h_closePrice[-42:-2].mean()
        
        R1,R2,R3=ma5_1,ma10_1,ma20_1
        R4,R5=abs(R1-R2),abs(R2-R3)
        
        #如果不满足以下条件，不必要继续监测下面的条件了，提供速度
        if R1<R2:
            continue
        if R2<R3:
            continue

        
        R6,R7=[],[]
        for i in range(0,50):
            ma5,ma10,ma20=0,0,0
            if i==0:
                ma5=h_closePrice[-5:].mean()
                ma10=h_closePrice[-10:].mean()
                ma20=h_closePrice[-20:].mean()
            else:
                ma5=h_closePrice[-5-i:-i].mean()
                ma10=h_closePrice[-10-i:-i].mean()
                ma20=h_closePrice[-20-i:-i].mean()                
            
            r1,r2,r3=ma5,ma10,ma20
            r4,r5=abs(r1-r2),abs(r2-r3)
            R6.append(r4)
            R7.append(r5)
        
        R6=(np.array(R6)).mean()
        R7=(np.array(R7)).mean()
        
        R8_max=max(abs(ma5_1-ma10_1),abs(ma5_2-ma10_2))
        R8_min=min(abs(ma5_1-ma10_1),abs(ma5_2-ma10_2))
        R8=R8_max-R8_min
        
        R9_max=max(abs(ma10_1-ma20_1),abs(ma10_2-ma20_2))
        R9_min=min(abs(ma10_1-ma20_1),abs(ma10_2-ma20_2)) 
        R9=R9_max-R9_min
        
        R10=R8<R6*9/10 and R9<R7*9/10 and R1>R2 and R2>R3
        #如果不满足以下条件，不必要继续监测下面的条件了，提供速度
        if R10==False:
            continue        
        
        #角度MA5:=ATAN((R1/REF(R1,1)-1)*100)*180/3.1416;
        R1_ref1=ma5_2
        R1_ref2=ma5_3
        ang_ma5_1=math.atan((R1/R1_ref1-1)*100)*180/3.1416
        ang_ma5_2=math.atan((R1_ref1/R1_ref2-1)*100)*180/3.1416
        #角度MA10:=ATAN((R2/REF(R2,1)-1)*100)*180/3.1416;
        R2_ref1=ma10_2
        R2_ref2=ma10_3
        ang_ma10_1=math.atan((R2/R2_ref1-1)*100)*180/3.1416
        ang_ma10_2=math.atan((R2_ref1/R2_ref2-1)*100)*180/3.1416
        #角度MA20:=ATAN((R3/REF(R3,1)-1)*100)*180/3.1416;
        R3_ref1=ma20_2
        R3_ref2=ma20_3
        ang_ma20_1=math.atan((R3/R3_ref1-1)*100)*180/3.1416
        ang_ma20_2=math.atan((R3_ref1/R3_ref2-1)*100)*180/3.1416
        #角度MA40:=ATAN((MA40/REF(MA40,1)-1)*100)*180/3.1416;
        R4_ref1=ma40_2
        R4_ref2=ma40_3
        ang_ma40_1=math.atan((ma40_1/R4_ref1-1)*100)*180/3.1416
        ang_ma40_2=math.atan((R4_ref1/R4_ref2-1)*100)*180/3.1416
        
        #R11:=角度MA5+角度MA10+角度MA20>120;
        R11=(ang_ma5_1+ang_ma10_1+ang_ma20_1)>120
        #R12:=角度MA5>REF(角度MA5,1) AND 角度MA10>REF(角度MA10,1) AND 角度MA20>REF(角度MA20,1);
        R12=(ang_ma5_1>ang_ma5_2) and (ang_ma10_1>ang_ma10_2) and (ang_ma20_1>ang_ma20_2)
        #R13:=角度MA40>0;
        R13=ang_ma40_1>0
        
        #R15:=C<R1*1.09
        R15=(d1CLOSE<R1*1.09)
        #R: R10 AND R11 AND R12 AND R13 AND R15;
        R=R10 and R11 and R12 and R13 and R15
        
        if R==True:
            waitForBuy.append(security)
        
    return waitForBuy



#调仓    
def adjust_position(context,data, buy_stocks):
    #更新持仓中的股票的z
    for security in context.portfolio.positions:
        
        security_list=list(g.buy_list_df['security'])
        if security not in security_list:
            continue

        index=g.buy_list_df.loc[g.buy_list_df['security']==security].index[0]
        maxprice=g.buy_list_df.ix[index,"maxprice"]

        h=attribute_history(security, 2, '1m', df=False)
        pre_high=h["high"][-1]
        pre_close=h["close"][-1]            
        
        if pre_close/maxprice-1<=-0.05:
            g.buy_list_df=g.buy_list_df.drop(index,axis=0)
            order_target(security, 0)
            position_count = len(context.portfolio.positions)
            print("卖出股票%s"%(security))
            continue
        
        if pre_high>maxprice:
            g.buy_list_df.ix[index,"maxprice"]=pre_high

                
    #若持仓持股数小于g.buy_stock_count，从股票池中买入，
    #直到持仓数量=g.buy_stock_count
    for security in buy_stocks:
        position_count = len(context.portfolio.positions)
        if g.buy_stock_count > position_count:
            value = context.portfolio.cash / (g.buy_stock_count-position_count)
            
            if (security not in context.portfolio.positions) and (g.buyNum<g.max_buyNum):
                
                _data=[security,0,0,9999]
                s=Series(_data,index=["security","days","maxprice","minprice"])
                g.buy_list_df=g.buy_list_df.append(s,ignore_index=True)                   
                
                order_target_value(security, value)
                g.buyNum+=1
                print("买入股票%s,今天已经买入%d个股票"%(security,g.buyNum))


#过滤停牌和ST的股票        
def filter_stock(context):
    #在市值表选择流通市值小于800亿的股票
    q = query(valuation.code, valuation.circulating_market_cap).filter(valuation.circulating_market_cap < 800) 

    df = get_fundamentals(q,date=context.current_dt.date())
    stock_list = list(df['code'])

    
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused 
    and not current_data[stock].is_st and 'ST' not in current_data[stock].
    name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
    
