import jqdata
import pandas as pd
import numpy as np
from jqdata import jy
from jqdata import *
def get_sw_quote(codes,end_date=None,count=None,start_date=None):
    '''获取申万指数行情,返回panel结构'''
    if isinstance(codes,str):
        codes=[codes]
    days = get_trade_days(start_date,end_date,count)
    code_df = jy.run_query(query(
         jy.SecuMain.InnerCode,jy.SecuMain.SecuCode,jy.SecuMain.ChiNameAbbr).filter(
        jy.SecuMain.SecuCode.in_(codes)))
    print(code_df)
    df = jy.run_query(query(
         jy.QT_SYWGIndexQuote.InnerCode,jy.QT_SYWGIndexQuote.ClosePrice,jy.QT_SYWGIndexQuote.TradingDay).filter(
        jy.QT_SYWGIndexQuote.InnerCode.in_(code_df.InnerCode),
        jy.QT_SYWGIndexQuote.TradingDay.in_(days),
        ))
    df2  = pd.merge(code_df, df, on='InnerCode').set_index(['TradingDay','SecuCode'])
    df2.drop(['InnerCode'],axis=1,inplace=True)
    return df2.to_panel()

def handle_data(context,data):
#   date = context.current_dt - timedelta(days =1)
    panel_industry = get_sw_quote("801170",date,240)
#   industry_closes = panel_industry.ClosePrice
# #     history_data = get_price(security = "603713.XSHG",end_date = context.current_dt,count = 240,fields = ['close','volume'])
# #     print(history_data)
#   print(panel_industry,industry_closes)
    # securitylist = get_all_securities().index.tolist()
    # # print(securitylist)
    
    # df = history(5, "1d", "close", securitylist,skip_paused = True)
    # print(df)
    # print(type(df.apply(sum)))