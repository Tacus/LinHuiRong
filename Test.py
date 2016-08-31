slow = 2/27.0
fast = 2/13.0
dea =  2/10.0

lastSlowEma = 20.0051851852
lastFastEma = 20.0969230769
lastDea = 0.0183475783476
curPrice = 21.14

currentSlowEma = lastSlowEma*(1-slow) + curPrice*slow
currentFastEma = lastFastEma*(1-fast) + curPrice*fast
currentDiff =  currentFastEma - currentSlowEma
currentDea = lastDea*(1-dea) + currentDiff*dea
currentMacd = 2*(currentDiff - currentDea)
currentSlowEma = round(currentSlowEma,4)
currentFastEma = round(currentFastEma,4)
currentDea = round(currentDea,4)
currentMacd = round(currentMacd,4)


print currentSlowEma,currentFastEma,currentDiff,currentDea,currentMacd