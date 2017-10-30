get_money_flow

get_money_flow(security_list, start_date, end_date, fields=None)
获取一只或者多只在一个时间段内的资金流向数据

参数

security_list: 一只代码或者一个代码的 list
start_date: 开始日期, 一个字符串或者 datetime.datetime/datetime.date 对象
end_date: 结束日期, 一个字符串或者 datetime.date/datetime.datetime 对象
fields: 字段名或者 list, 可选. 默认为 None, 表示取全部字段, 各字段含义如下：

字段名	含义	备注
date	日期	
sec_code	代码	
change_pct	涨跌幅(%)	
net_amount_main	主力净额(万)	主力净额 = 超大单净额 + 大单净额
net_pct_main	主力净占比(%)	主力净占比 = 主力净额 / 成交额
net_amount_xl	超大单净额(万)	超大单：大于等于50万股或者100万元的成交单
net_pct_xl	超大单净占比(%)	超大单净占比 = 超大单净额 / 成交额
net_amount_l	大单净额(万)	大单：大于等于10万股或则20万元且小于50万股或者100万元的成交单
net_pct_l	大单净占比(%)	大单净占比 = 大单净额 / 成交额
net_amount_m	中单净额(万)	中单：大于等于2万股或者4万元且小于10万股或则20万元的成交单
net_pct_m	中单净占比(%)	中单净占比 = 中单净额 / 成交额
net_amount_s	小单净额(万)	小单：小于2万股或者4万元的成交单
net_pct_s	小单净占比(%)	小单净占比 = 小单净额 / 成交额
返回

返回一个 pandas.DataFrame 对象，默认的列索引为取得的全部字段. 如果给定了 fields 参数, 则列索引与给定的 fields 对应.

示例

# 获取一只在一个时间段内的资金流量数据
get_money_flow('000001.XSHE', '2016-02-01', '2016-02-04')
get_money_flow('000001.XSHE', '2015-10-01', '2015-12-30', fields="change_pct")
get_money_flow(['000001.XSHE'], '2010-01-01', '2010-01-30', ["date", "sec_code", "change_pct", "net_amount_main", "net_pct_l", "net_amount_m"])

# 获取多只在一个时间段内的资金流向数据
get_money_flow(['000001.XSHE', '000040.XSHE', '000099.XSHE'], '2010-01-01', '2010-01-30')
# 获取多只在某一天的资金流向数据
get_money_flow(['000001.XSHE', '000040.XSHE', '000099.XSHE'], '2016-04-01', '2016-04-01')