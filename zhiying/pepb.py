# 导入函数库
import jqdata
#设置
####################################################################################################
'''输入调仓月份'''
month_list = [1,2,3,4,5,6,7,8,9,10,11,12]
'''输入股票池,输入 'A' 则为全A股'''
stocklist = 'A'               #'000002.XSHG'
'''输入最大持仓数'''
chicangshu = 10
'''pb大于1.6是否卖出 True/False'''
maichu = True
'''输入仓位控制,每只股最多占仓位的1/n'''
cangwei = 10.0
'''输入按月运行还是按天运行,按天运行时,调仓月份必须是1-12  month/day'''
day_month = 'day'
'''如果按天运行,输入调仓周期'''
zhouqi = 10
#参数调整
##################################################################
'''pb/pe的阈值'''
pbe = 0.1
'''市净率的上下界'''
up = 0.8
down = 0
'''pb的卖出阈值'''
sup = 1.6
####################################################################################################    
g.now_day = 0
# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    set_slippage(PriceRelatedSlippage(0.002))
    if day_month == 'month':
        run_monthly(run_month, 1, time='open')
    else:
        run_daily(run_day, time='open')

def run_day(context):
    g.now_day =g.now_day + 1
    # print(g.now_day)
    date = context.current_dt.strftime("%Y-%m-%d")
    month = context.current_dt.month
    if g.now_day % zhouqi == 0 or g.now_day ==1:
        chicang = context.portfolio.positions.keys()
        buy_list = list(get_buy_list(context,date))
        if chicang and maichu==True:
            sell(chicang,date)
        new_buy_list = get_new_list(buy_list+chicang,date)
        for stock in chicang:
            if stock not in new_buy_list and len(new_buy_list)>=chicangshu:
                order_target(stock,0)
                print('超过持仓数,卖出落后股:  '+stock)
                # print(new_buy_list)
        new_chicang = context.portfolio.positions.keys()
        
        list2 = set(new_buy_list)
        # print(list2,new_chicang)
        if list2:
            cash = context.portfolio.total_value/(len(list2))
        else:
            cash = context.portfolio.total_value
        
        # get_information(chicang+buy_list)
        for stock in list2:
            if cash > context.portfolio.total_value/cangwei:
                new_cash  =  context.portfolio.total_value/cangwei
                order_target_value(stock,new_cash)
            else:
                order_target_value(stock,cash)
def run_month(context):
    date = context.current_dt.strftime("%Y-%m-%d")
    month = context.current_dt.month
    if month in month_list:
        chicang = context.portfolio.positions.keys()
        buy_list = list(get_buy_list(context,date))
        if chicang and maichu==True:
            sell(chicang,date)
        new_buy_list = get_new_list(buy_list+chicang,date)
        for stock in chicang:
            if stock not in new_buy_list and len(new_buy_list)>=chicangshu:
                order_target(stock,0)
                print('超过持仓数,卖出落后股:  '+stock)
                # print(new_buy_list)
        new_chicang = context.portfolio.positions.keys()
        
        list2 = set(new_buy_list)
        # print(list2,new_chicang)
        if list2:
            cash = context.portfolio.total_value/(len(list2))
        else:
            cash = context.portfolio.total_value
        
        # get_information(chicang+buy_list)
        for stock in list2:
            if cash > context.portfolio.total_value/cangwei:
                new_cash  =  context.portfolio.total_value/cangwei
                order_target_value(stock,new_cash)
            else:
                order_target_value(stock,cash)
def sell(stock_list,date):
    '''卖出pb大于1.6的股票'''
    df = get_fundamentals(query(
            valuation.code, valuation.pb_ratio
        ).filter(valuation.code.in_(stock_list),
            valuation.pb_ratio>sup
        ), date=date)
    sell_list = df.code.values
    for stock in sell_list:
        # print('sell',stock)
        order_target(stock,0)
        print('pb>1.6,sell',stock)

def get_buy_list(context,date):
    '''选股函数,获取符合条件的前10只股票'''
    l_date = datetime.datetime.strptime(date,'%Y-%m-%d')-datetime.timedelta(days=2)
    if stocklist == 'A':
        stock_list = list(get_all_securities(date=date).index)
    else :
        stock_list = get_index_stocks(stocklist, date=date)
    # print(len(stock_list))
    new_stock_list = filter_st_stocks(stock_list, l_date,date)
    df = get_fundamentals(query(
        valuation.code, valuation.pb_ratio, valuation.pe_ratio       #市净率(pb_ratio)市盈率(pe_ratio)
        ).filter(valuation.code.in_(new_stock_list),
        valuation.pb_ratio/valuation.pe_ratio >pbe,
        valuation.pb_ratio >down ,
        valuation.pb_ratio<up,
        ), date=date)
    df['pb/pe'] = df['pb_ratio'] /df['pe_ratio']
    df['pb/pe 分数'] = get_sh_list(df['pb/pe'],res = True)
    df['pb 分数'] = get_sh_list(df['pb_ratio'],res = False)
    df['总分'] = df['pb/pe 分数']+df['pb 分数']
    # last_df = df.sort_values(by='总分',ascending = True)  #py2
    last_df = df.sort('总分',ascending = True)              #py3
    buy_list = last_df[:chicangshu].code.values
    # if len(buy_list)>0:         #输出今日所筛选出的股票
    #     print(buy_list)
    return buy_list
     
def get_sh_list(datas,res=False):
    '''分数计算函数'''
    b_e_list = datas.tolist()
    a = sorted(b_e_list,reverse = res)
    fs_list = []
    for x in  b_e_list :
        fs =(len(b_e_list)-(a.index(x)+1)+1)/float(len(b_e_list))*100.0
        fs_list.append(fs)
    return fs_list
def get_new_list(stock_list,date):
    '''检查持仓股票分数是否落后'''
    df = get_fundamentals(query(
        valuation.code, valuation.pb_ratio, valuation.pe_ratio       #市净率(pb_ratio)市盈率(pe_ratio)
    ).filter(valuation.code.in_(stock_list),
        # valuation.pe_ratio > 0.1,
        # valuation.pb_ratio/valuation.pe_ratio >pbe,
        # valuation.pb_ratio >down ,
        # valuation.pb_ratio<up,
    ), date=date)
    df['pb/pe'] = df['pb_ratio'] /df['pe_ratio']
    df['pb/pe 分数'] = get_sh_list(df['pb/pe'],res = True)
    df['pb 分数'] = get_sh_list(df['pb_ratio'],res = False)
    df['总分'] = df['pb/pe 分数']+df['pb 分数']
    # last_df = df.sort_values(by='总分',ascending = True)  #py2
    last_df = df.sort('总分',ascending = True)              #py3
    # print(last_df)                  #检查数据结构,评分方式是否有问题
    buy_list = last_df[-chicangshu:].code.values
    if len(buy_list)>0:               #输出今日应当调仓/买入的所有股票
        print(buy_list)
    return buy_list
def filter_st_stocks(stocks, start_date, end_date):
    '''剔除st,停牌'''
    df = get_extras('is_st', stocks, start_date=start_date, end_date=end_date, df=True)
    if start_date == end_date:
        df = df + 0
        stocks = df[df == 0].dropna(inplace=False, axis=1).columns.tolist()
    else:
        mask = df.sum(axis=0)
        stocks = mask[mask == 0].index.tolist()
    return stocks
    