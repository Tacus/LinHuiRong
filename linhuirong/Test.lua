-- local tes = require "import"

-- local ord = string.byte
-- local sub = string.sub

-- local tes = ord("K")
-- tes = sub("123456789",3,4)
-- print (tes)


-- string = "Lua Tutorial"
-- -- replacing strings
-- print(string.find(string,"Tutorial1"))
-- reversedString = string.reverse(string)
-- print("The new string is",reversedString)
local a = tostring(os.time()):reverse():sub(1, 6)
math.randomseed(a)
		print(a)

-- print(math.rand())


	print(math.random(2))
for i=1,100 do
end