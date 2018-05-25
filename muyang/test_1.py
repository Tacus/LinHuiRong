import numpy as np
import time

t = time.time()
ct = ""
array = []
for x in xrange(1,1000000):
	array.append("xx")
	array.append("--")
	array.append(str(x))
	# ct += "%s%s%s"%("xx","--",str(x))

ret = ''.join(array)
t2 = time.time()
print(t2-t)