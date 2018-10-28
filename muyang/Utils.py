#coding: UTF-8
from jqdata import jy
from jqdata import *
import pandas as pd
import numpy as np
import talib as tb
def get_sw_quote(codes,end_date=None,count=None,start_date=None):
    '''获取申万指数行情,返回panel结构'''
    if isinstance(codes,unicode):
        codes=[codes]
    days = get_trade_days(start_date,end_date,count)
    code_df = jy.run_query(query(
         jy.SecuMain.InnerCode,jy.SecuMain.SecuCode,jy.SecuMain.ChiName).filter(
        jy.SecuMain.SecuCode.in_(codes)))
    
    df = jy.run_query(query(
         jy.QT_SYWGIndexQuote.InnerCode,jy.QT_SYWGIndexQuote.ClosePrice,jy.QT_SYWGIndexQuote.TradingDay).filter(
        jy.QT_SYWGIndexQuote.InnerCode.in_(code_df.InnerCode),
        jy.QT_SYWGIndexQuote.TradingDay.in_(days),
        ))
    offset = 0
    achive_count = len(df)
    while achive_count>0:
        offset += achive_count
        temp_df = jy.run_query(query(
             jy.QT_SYWGIndexQuote.InnerCode,jy.QT_SYWGIndexQuote.ClosePrice,jy.QT_SYWGIndexQuote.TradingDay).filter(
            jy.QT_SYWGIndexQuote.InnerCode.in_(code_df.InnerCode),
            jy.QT_SYWGIndexQuote.TradingDay.in_(days),
            ).offset(offset))
        achive_count = len(temp_df)
        df = df.append(temp_df,ignore_index = True)
        # print(df)
    df2  = pd.merge(code_df, df, on='InnerCode',copy = False).set_index(['TradingDay','SecuCode'])
    df2.drop(['InnerCode'],axis=1,inplace=True)
    return df2.to_panel()