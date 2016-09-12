import numpy as np
from math import *


def initialize(context): 
	securities1 = get_index_stocks("000001.XSHG")
	securities2 = get_index_stocks("000002.XSHG")
	securities3 = get_all_securities(types="stock").index
	print type(securities1),len(securities1),type(securities2),len(securities2),type(securities3),len(securities3),