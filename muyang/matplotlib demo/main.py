#!/usr/bin/env python

import datetime
import numpy

from jq import *
from plot import show_plots


all_logs = []

def parse_splitted_log(splitted_log):
    trade_time = datetime.datetime.strptime(splitted_log[0].strip(),'%Y-%m-%d %H:%M:%S')
    oper_detail = splitted_log[2].split(' ')
    if oper_detail[0].strip() == 'Buying':
        buying = True
    else:
        buying = False
    security = oper_detail[1].strip()
    item = {'security' : security, 'buying' : buying, 'trade_time' : trade_time}
    all_logs.append(item)
    return item


def find_time_index(list, item):
    n = len(list)
    for i in range(n):
        if (datetime.datetime.strptime(list[i], '%Y-%m-%d') >= item):
            return i
    return n - 1


def show_all_logs(latest_item = {}):
    if (all_logs):
        security = all_logs[0]['security'] # FIXME
        df = get_price_data(security)
        date_tickers = [str(i).split(' ')[0] for i in df.index]
        n = len(date_tickers)
        if latest_item:
            idx = find_time_index(date_tickers, latest_item['trade_time'])
            x1 = idx - 25
            x2 = idx + 15
        else:
            time_line = []
            for item in all_logs:
                time_line.append(item['trade_time'])
            tmp = numpy.array(time_line)
            x1 = find_time_index(date_tickers, tmp.min()) - 1
            x2 = find_time_index(date_tickers, tmp.max()) + 1

        o = df['open']
        h = df['high']
        l = df['low']
        c = df['close']
        v = df['volume']

        operations = []
        for item in all_logs:
            idx = find_time_index(date_tickers, item['trade_time'])
            operations.append((idx, item['buying']))

        show_plots(security+" Daily Candlestick Chart", date_tickers, o, h, l, c, v, operations, x1, x2)
    else:
        print('还没输入数据')


init_jqdata()

input_mode = False # 连续输入模式
prompt = "\n请输入一行交易日志, 或输入 'i' 进入连续输入模式, 或输入 'p' 画总图, 或输入 'q' 退出:\n"

while True:
    if (input_mode):
        log_line = input()
    else:
        log_line = input(prompt)

    if not log_line:
        continue
    if log_line == 'q':
        break
    if log_line == 'i':
        input_mode = True
        continue
    if log_line == 'p':
        input_mode = False
        show_all_logs()
        continue

    splitted_log = log_line.split(' - ')
    if len(splitted_log) < 3:
        print("非法输入!")
        continue

    try:
        latest_item = parse_splitted_log(splitted_log)
    except (ValueError, IndexError):
        print("非法输入!")
    else:
        if not input_mode:
            show_all_logs(latest_item)
