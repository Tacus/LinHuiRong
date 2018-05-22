import numpy as np      
import pandas as pd
from pandas import Series,DataFrame
import random
import math
# 定义一个全局变量, 保存要操作的证券
security='600196.XSHG'
# 设置我们要操作的股票池, 这里我们只操作一支股票
set_universe([security])
set_benchmark('600196.XSHG')
#设置回测条件
set_commission(PerTrade(buy_cost=0.0008, sell_cost=0.0015, min_cost=5))
set_slippage(FixedSlippage(0))
#调整资金规模时的临界损失比例
loss=0.1
#调整资金规模时调整后的资金占当前资金的比例
adjust=0.8
#计算第一个N时取得股票数据的天数
days=20
#系统一入市时股票价格需要高于short_in天内的最高价
short_in=20
#系统二入市时股票价格需要高于long_in天内的最高价
long_in=55
#系统一离市时股票价格需要低于short_out天内的最低价
short_out=10
#系统二离市时股票价格需要低于long_out天内的最低价
long_out=20
#系统一和系统二的资金分配比例，系统一得到ratio*总资金，系统二得到（1-ratio）*总资金
ratio=0.7
#单一市场中的头寸规模限制
limit=4
#记录策略运行了多少天
pdn=0
#记录N值
N=[]
#记录系统一中股票的单位数
sys1=0 
#记录系统二中股票的单位数
sys2=0
#判断操作是对系统一还是系统二，值为‘True’是对系统一，‘False’是对系统二
short='False'
#用unit来保存一单位表示多少股票，默认值为1000
unit=1000
#记录系统一形成突破时的股票价格
break_price1=0 
#记录系统二形成突破时的股票价格
break_price2=0
#记录分钟
minutes=0

#计算股票的N值 
def Calcu_N(context,paused):
    #在策略运行了days-1天时，计算前days-1天的平均实际范围
    if pdn==days-1:
        #取出day-1天来得最高价，最低价，前一天的收盘价
        price=attribute_history(security,days-1,'1d', ('high','low','pre_close'),skip_paused=True)
        #如果不是所有的这day-1天都没有数据，算出这些天的实际范围的平均值
        TR=[]
        for i in range(0,days-1):
            h_l=price['high'][i]-price['low'][i]
            h_pdc=price['high'][i]-price['pre_close'][i]
            pdc_l=price['pre_close'][i]-price['low'][i]
            temp=max(h_l,h_pdc,pdc_l)
            TR.append(temp)
        ATR=np.mean(np.array(TR))
        N.append(ATR)
        
    #如果策略运行天数已经达到了days天
    else:
        #如果股票停牌，则将运行天数减1
        if paused==True:
            global pdn
            pdn=pdn-1
        #如果未停牌，则利用迭代，计算N值，并保存在列表N中
        else:
            price=attribute_history(security,1,'1d', ('high','low','pre_close'),skip_paused=True)
            h_l=price['high'][0]-price['low'][0]
            h_pdc=price['high'][0]-price['pre_close'][0]
            pdc_l=price['pre_close'][0]-price['low'][0]
            temp=max(h_l,h_pdc,pdc_l)
            TR.append(temp)
            ATR=np.mean(np.array(TR))
            N.append(ATR)
            
#止损
def Stop_Loss(current_price):
    #如果对系统一操作，则将突破价设置为系统一的突破价，如果是对系统二，则设置为系统二的
    if short=='True':
        break_price=break_price1
    else:
        break_price=break_price2
    #如果当前价格比上次的突破价低2N，则清空头寸
    #并相应的更改相应系统中的股票单位数
    if current_price<break_price-2*N[-1]:
        if short=='True':
            order(security,-sys1)
            global sys1
            sys1=0  
        else:
            order(security,-sys2)
            global sys2 
            sys2=0
            
#入市
def Sys_In(highest,day_in,context,current_price,cash):
    #取出day_in天以来的最高价
    price=attribute_history(security,day_in,'1d',('high','open'))
    #如果当前价格高于day_in天的最高价，则形成突破
    if current_price>max(price['high']) and current_price>=highest:
        #计算可以买的股票数量
        num_of_shares=cash/current_price
        #如果可以买的数量不小于一单位，且目前持有的股票数量未达到限制的数量，则买入
        if num_of_shares>=unit:
            if short=='True':
                if sys1<int(limit*unit):
                    order(security,+int(unit))
                    #买入后，相应的更新持有的股票数及突破价格
                    global sys1
                    sys1=sys1+int(unit)
                    global break_price1
                    break_price1=current_price
            else:
                if sys2<int(limit*unit):
                    order(security,+int(unit))
                    global sys2
                    sys2=sys2+int(unit)
                    global break_price2
                    break_price2=current_price
    
#增加单位    
def Sys_Add(day_in,context,current_price,cash):
    #根据short的值判断是对哪个系统操作，以对突破价格赋值
    if short=='True':
        break_price=break_price1
    else:
        break_price=break_price2
    #如果当前价格比上次的突破价格高0.5*N，则增加一单位
    if current_price>=break_price+0.5*N[-1]: 
        num_of_shares=cash/current_price
        if num_of_shares>=unit: 
            if short=='True':
                if sys1<int(limit*unit):
                    order(security,+int(unit))
                    global sys1
                    sys1=sys1+int(unit)
                    global break_price1
                    break_price1=current_price
            else:
                if sys2<int(limit*unit):
                    order(security,+int(unit))
                    global sys2
                    sys2=sys2+int(unit)
                    global break_price2
                    break_price2=current_price
    
# 离市
def Sys_Out(day_out,current_price,context):
    #取出day_out天以来的最低价
    price=attribute_history(security,day_out,'1d',('high','low'),skip_paused=True)
    #如果股票当前价格比day_out天的最低价低，则清空系统内的头寸
    #并将相应系统的头寸数量置为0
    if current_price<min(price['low']):
        if short=='True':
            if sys1>0:
                order(security,-sys1)
                global sys1
                sys1=0
        else:
            if sys2>0:
                order(security,-sys2)
                global sys2
                sys2=0

#每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    global minutes
    minutes=minutes+1
    price=attribute_history(security,minutes,'1m',('high','price','open'),skip_paused=True)
    #取得从今天开盘为止的最高价
    highest=max(price['open'])
    #用paused保存股票是否停牌
    paused=data[security].paused
    #用dt保存当前时间
    dt=context.current_dt
    #保存当前股票价格
    current_price=data[security].price
    #保存资产组合的总值
    value=context.portfolio.portfolio_value
    #在每天开市时将策略运行时间加1
    if dt.hour==9 and dt.minute==30:
        global minutes
        minutes=0
        global pdn 
        pdn=pdn+1
        #在运行时间达到days-1天时计算头寸单位
        if pdn==days-1:
            Calcu_N(context,paused)
    #运行时间达到days天时开始执行各种买卖操作
    if pdn>=days:
        if pdn==days:
            global break_price1
            break_price1=current_price*5+1
        #如果股票不停牌
        if paused==False:
            #取得当前现金
            cash=context.portfolio.cash
            #如果空仓了
            if sys1==0 and sys2==0:
                #调整资金规模
                if context.portfolio.portfolio_value<(1-loss)*context.portfolio.starting_cash:
                    cash=adjust*cash
                    value=adjust*value
            #每点价值量（yuan per point）
            ypp=1.0
            #价值量波动性 value volatility
            vv=ypp*N[-1]
            #计算一单位的数量
            global unit
            unit=value*0.01/vv
            #将short置为‘True’，对系统一进行操作
            global short
            short='True'
            #如果系统一没有头寸，并且当前价格比上次的突破价低，入市
            if sys1==0:
                #入市
                Sys_In(highest,short_in,context,current_price,ratio*cash)
            #如果已经有了头寸，则进行止损或者增加单位
            else:
                #止损
                Stop_Loss(current_price)
                #增加单位
                Sys_Add(short_in,context,current_price,ratio*cash)    
            #离市
            Sys_Out(short_out,current_price,context)
            #将short置为‘False’，对系统二进行操作
            global short
            short='False'
            if sys2==0:
                #入市
                Sys_In(highest,long_in,context,current_price,(1-ratio)*cash)
            else:
                Stop_Loss(current_price)
                Sys_Add(long_in,context,current_price,(1-ratio)*cash)
            #离市
            Sys_Out(long_out,current_price,context)   