# coding=utf-8
import datetime
import jqdata
import time
import pandas as pd
import talib
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
import matplotlib.finance as fin

start_date = "2018-01-03"
end_date = "2018-08-04"
bt_id = "8b809e9b8faa72c5ed609a0c53be963f"

#获取下单信息
gt = get_backtest(bt_id)
dic = gt.get_orders()


#获取交易日日期
trade_date=list(jqdata.get_trade_days(start_date=start_date,end_date=end_date))
#获取这段时间内股票的数据
df=get_price('300323.XSHE',start_date=start_date,end_date=end_date,frequency='daily',fields=['open','high','low','close'])
#创建两个用于存储买入和卖出的信号的列表
buy_list=[(i['price'],i['time'],'买入'+str(i['price'])) for i in dic if (i['action']=='open' and i['time'] >= str(trade_date[0]))]
sell_list=[(j['price'],j['time'],'卖出'+str(j['price'])) for j in dic if (j['action']=='close' and j['time'] >= str(trade_date[0]))]
# print(buy_list,sell_list)
#进行K线绘制
##由有画图函数的需要将index更改为数字
t=range(len(df))
df['t']=pd.Series(t,index=df.index)
dtseries = pd.Series(df.index.values)
df=df.set_index('t')
N = []
lst = []

out_price_2Atr_list = []
out_price_2N_list = []


cur_max_out_price = 0
isPosition = False
cur_dict_pos = 0
cur_item = None

for i in range(0, len(df)):
    if(np.isnan(df['high'][i])):
        continue
    high_price = df['high'][i]
    low_price = df['low'][i]
    cur_close_price = df['close'][i]
    index = i
    if(i == 0):
        index = 0
    else:
        index = i-1
    last_close = df['close'][index]
    h_l = high_price-low_price
    h_c = high_price-last_close
    c_l = last_close-low_price
    curtTime = dtseries[i].date()
    # print(high_price,low_price,cur_close_price,last_close,curtTime)
    while cur_dict_pos < len(dic) and curtTime >= datetime.datetime.strptime(dic[cur_dict_pos]['time'][:10],"%Y-%m-%d").date():
        cur_item = dic[cur_dict_pos]
        cur_dict_pos +=1
    action_date = datetime.datetime.strptime(cur_item['time'][:10],"%Y-%m-%d").date()

    # 计算 True Range 取计算第一天的前20天波动范围平均值
    True_Range = max(h_l, h_c, c_l)
    # print(cur_dict_pos,curtTime,action_date,isPosition)
    if(len(lst) < 19):
        lst.append(True_Range)
        out_price_2Atr_list.append(float("Nan"))
        out_price_2N_list.append(cur_close_price)
        continue
    else:
        if(len(N) == 0):
            current_N = np.mean(lst)
        else:
            current_N = (True_Range + (20-1)*(N)[-1])/20
        out_price = high_price - 2*current_N
        (N).append(current_N)
        
        if(not isPosition or (isPosition and out_price > cur_max_out_price)):
            cur_max_out_price = out_price
        print(curtTime,cur_max_out_price,high_price,current_N,low_price)
        out_price_2Atr_list.append(cur_max_out_price)
    
    trade_price = cur_max_out_price
    if(action_date == curtTime):
        if(cur_item["action"] == 'open'):
            isPosition = True
            last_N = N[-1]
            price = cur_item["price"] - 2*last_N
            print(curtTime,cur_item["price"],cur_close_price)
            trade_price = price
        else:
            isPosition = False

    else:
        if(isPosition):
            trade_price = out_price_2N_list[-1]
    
    out_price_2N_list.append(trade_price)



#将获取到的下单列表里面的时间与df的index对应
##定义一个进行index转换的函数
def order_trans(L):
    out_list=[]
    for order in L:
        t0 = time.strptime(order[1][:10],'%Y-%m-%d')
        y,m,d = t0[0:3]
        t1=datetime.date(y,m,d)
        out_list.append((order[0],trade_date.index(t1),order[2]))
    return out_list
order_buy_list=order_trans(buy_list)
order_sell_list=order_trans(sell_list)
# print(order_buy_list,order_sell_list)
#开始绘图
plt.close()
fig = plt.figure(figsize(100,50),dpi=800,frameon=True)

ax1=plt.subplot2grid((8,3),(0,0),rowspan=3,colspan=1)
ax1.set_xlim(0,len(df))

o = list(df['open'].values)
h = list(df['high'].values)
l = list(df['low'].values)
c = list(df['close'].values)
for i,j,k in order_buy_list:
    ax1.annotate(k,xy=(j,c[j]-0.1),xytext=(j,c[j]-0.3),arrowprops=dict(facecolor='black',shrink=0.2),horizontalalignment='left',verticalalignment='top')
for i,j,k in order_sell_list:
    ax1.annotate(k,xy=(j,c[j]+0.1),xytext=(j,c[j]+0.3),arrowprops=dict(facecolor='black',shrink=0.2),horizontalalignment='left',verticalalignment='top')

# ax1.xaxis.set_major_formatter(mdate.DateFormatter('%Y-%m-%d'))
# plt.xticks(pd.date_range(start_date,end_date),rotation=90)
# print(pd.date_range(start_date,end_date))
# print(start_date,end_date)
quotes = zip(t, o, h, l, c)
df['ma10'] = pd.Series(talib.MAX(df['high'].values,20),index=df.index.values)
df['ma10'].plot(ax=ax1, legend=False)

df['ma11'] = pd.Series(talib.MIN(df['low'].values,20),index=df.index.values)
df['ma11'].plot(ax=ax1, legend=False)

df['ma12'] = pd.Series(out_price_2Atr_list,index=df.index.values)
df['ma12'].plot(ax=ax1, legend=False)
df['ma13'] = pd.Series(out_price_2N_list,index=df.index.values)
df['ma13'].plot(ax=ax1, legend=False)

fin.candlestick_ohlc(ax1,quotes, width=0.6, colorup='r', colordown='g')
plt.show()