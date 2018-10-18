    
from jqdata import jy
from jqdata import *
import pandas as pd

# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    # 000001(股票:平安银行)
    g.security = '000001.XSHE'
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)

#注意申万指数在2014年有一次大改,聚源使用的是为改变之前的代码,官网包含更改前和更改后的代码,如果遇到找不到的标的可以根据需求自行查找
#如801124 >>801121食品加工II


def get_sw_quote(code,end_date=None,count=None,start_date=None):
    '''获取申万指数行情,返回panel结构'''
    if isinstance(code,str):
        code=[code]
    days = get_trade_days(start_date,end_date,count)
    code_df = jy.run_query(query(
         jy.SecuMain.InnerCode,jy.SecuMain.SecuCode).filter(
        jy.SecuMain.SecuCode.in_(code)))
    
    print(code_df)
    code_df.drop(["InnerCode"],axis=1,inplace = True)
    print(code_df)
    df = jy.run_query(query(
         jy.QT_SYWGIndexQuote).filter(
        jy.QT_SYWGIndexQuote.InnerCode.in_(code_df.InnerCode),
        jy.QT_SYWGIndexQuote.TradingDay.in_(days),
        ))
    df2  = pd.merge(code_df, df, on='InnerCode').set_index(['TradingDay','SecuCode'])
    df2.drop(['InnerCode','ID','UpdateTime','JSID'],axis=1,inplace=True)
    return df2.to_panel()
    
    #股票做排序
def get_sw_industry_stocks(name):
    codes = get_industries(name);
    print(codes)
    for i in range(len(codes)):
        print(codes[i])
        securities = get_industry_stocks(codes[i])
        for single in securities:
            print(name,codes[i],single)

def handle_data(context,data):
    get_sw_industry_stocks("sw_l1")
    get_sw_industry_stocks("sw_l2")
    # code = get_industries(name='sw_l1').index[:5]
    # print(code)
    # df = get_sw_quote(code,end_date='2018-01-01',count=10)
#   print(df.major_axis)
#   print(df.minor_axis)
#   df.to_frame(True)
#   print(df.AShareTotalMV)
#   print(df)
    

