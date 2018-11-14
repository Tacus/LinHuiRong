#!/usr/bin/env python

import datetime

import matplotlib.dates as mdates

from jqdatasdk import *

def init_jqdata():
    """登陆认证"""
    phone_number = ''
    while len(phone_number) < 1:
        phone_number = input('请输入您的聚宽帐号(即注册的手机号): ')

    password = ''
    while len(password) < 1:
        password = input('请输入您的登陆密码: ')

    auth(phone_number, password)


def get_price_data(security):
    """获取security的所有日线行情数据,不包括停牌时期"""
    info = get_security_info(security)
    df = get_price(security, info.start_date, info.end_date, skip_paused=True)
    return df
