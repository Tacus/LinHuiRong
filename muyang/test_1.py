a = iter([1,2,"12312",3])
result = next(a,None)
while result:
    print(result)
    result = next(a,None)

