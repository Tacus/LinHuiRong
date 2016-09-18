import numpy as np
from math import *


def initialize(context): 
    securities1 = get_index_stocks("000001.XSHG")
    securities2 = get_index_stocks("000002.XSHG")
    securities3 = get_all_securities(types="stock").index
    securities4 = get_index_stocks("399001.XSHE")
    securities5 = get_index_stocks("399106.XSHE")
    print len(securities1),len(securities2),len(securities3),len(securities4),len(securities5)