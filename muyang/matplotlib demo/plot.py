#!/usr/bin/env python

import numpy

import matplotlib.ticker as ticker
import matplotlib.pyplot as plt

from mpl_finance import candlestick2_ohlc


def plot_main(ax, n, o, h, l, c, operations, arrow_len):
    candlestick2_ohlc(ax, o, h, l, c, width=0.6, colorup='red', colordown='cyan', alpha=1.0)

    for operation in operations:
        x = operation[0]
        if operation[1]:
            y = l[x] - arrow_len * 2.2
            dy = arrow_len
            clr='white'
        else:
            y = h[x] + arrow_len * 2.2
            dy = - arrow_len
            clr='yellow'
        ax.arrow(x, y, 0, dy, color=clr, width=0.4, head_length=arrow_len)


def plot_volume(ax, n, v):
    c=[]
    ec=[]
    for i in range(n):
        if i == 0:
            c.append('black')
            ec.append('red')
        else:
            if v[i] > v[i - 1]:
                c.append('black')
                ec.append('red')
            else:
                c.append('cyan')
                ec.append('cyan')
    ax.bar(range(n), v, color=c, edgecolor=ec)


def show_plots(title, date_tickers, o, h, l, c, v, operations, x1, x2, extra=[]):
    n = len(date_tickers)
    # x1,x2为横轴显示范围, x1d,x2d为横轴数据索引范围(0~n-1)
    x1d=x1
    x2d=x2
    if x1d<0:
        x1d=0
    if x2d >= n:
        x2d = n - 1

    ymin = numpy.array(l[x1d:x2d+1]).min()
    ymax = numpy.array(h[x1d:x2d+1]).max()
    height = ymax - ymin
    y1main = ymin - height * 0.12
    y2main = ymax + height * 0.12
    arrow_len = height * 0.04 # arrow_len = head_length

    fig = plt.figure()
    grid = plt.GridSpec(3, 1, hspace=0.15)
    main_ax = plt.subplot(grid[0:2,0])
    extra_ax = plt.subplot(grid[2,0], sharex=main_ax)
    fig.subplots_adjust(bottom=0.2)

    plot_main(main_ax, n, o, h, l, c, operations, arrow_len)

    def format_date(x,pos=None):
        if x<0 or x>len(date_tickers)-1:
            return ''
        return date_tickers[int(x-0.5)][2:]
    main_ax.xaxis.set_visible(False)
    main_ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    main_ax.axis((x1-0.5,x2+0.5,y1main,y2main))
    main_ax.set_facecolor("black")
    main_ax.set_title(title)

    # 如extra有数据, 则绘制在副图上, 否则把成交量绘制在副图上
    if len(extra) > 0:
        extra_ax.plot(range(n), extra)
        y1extra = numpy.array(extra[x1d:x2d+1]).min()
        y2extra = numpy.array(extra[x1d:x2d+1]).max()
    else:
        plot_volume(extra_ax, n, v)
        y1extra = 0.0
        y2extra = numpy.array(v[x1d:x2d+1]).max() * 1.08
        extra_ax.set_ylabel("Volume")
    extra_ax.axis(ymin=y1extra,ymax=y2extra)
    extra_ax.set_facecolor("black")

    plt.xticks(rotation=45)
    plt.yticks()

    plt.grid()
    plt.show()
