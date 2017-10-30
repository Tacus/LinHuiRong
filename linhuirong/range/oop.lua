function class(classname, super)
	local superType = type(super)
	local cls
	if superType ~= 'function' and superType ~= 'table' then
		superType = nil
		super = nil
	end

	if superType == 'function' or (super and super.__ctype == 1) then
		-- inherited from native C++ Object
		cls = {}
		if superType == 'table' then
			-- copy fields from super
			for k,v in pairs(super) do cls[k] = v end
			cls.__create = super.__create
			cls.super = super
		else
			cls.__create = super
			cls.ctor = function() end
		end
		cls.__cname = classname
		cls.__ctype = 1

		function cls.new(...)
			local instance = cls.__create(...)
			-- copy fields from class to  native object
			for k, v in pairs(cls) do instance[k] = v end
			instance.class = cls
			instance:ctor(...)
			return instance
		end
	else
		-- inherited from Lua Object
		if super then
			cls = {}
			setmetatable(cls, {__index = super})
			cls.super = super
		else
			cls = {ctor = function() end}
		end
		cls.__cname = classname
		cls.__ctype = 2 --lua
		cls.__index = cls

		function cls.new(...)
			local instance = setmetatable({}, cls)
			instance.class = cls
			instance:ctor(...)
			return instance
		end
	end
	return cls
end

function string.split(str, delimiter)
    str = tostring(str)
    delimiter = tostring(delimiter)
    if (delimiter=='') then return false end
    local pos,arr = 0, {}
    -- for each divider found
    for st,sp in function() return string.find(str, delimiter, pos, true) end do
        table.insert(arr, string.sub(str, pos, st - 1))
        pos = sp + 1
    end
    table.insert(arr, string.sub(str, pos))
    return arr
end

function import(moduleName, currentModuleName)
    local currentModuleNameParts
    local moduleFullName = moduleName
    local offset = 1

    while true do
        if string.byte(moduleName, offset) ~= 46 then -- .
            moduleFullName = string.sub(moduleName, offset)
            if currentModuleNameParts and #currentModuleNameParts > 0 then
                moduleFullName = table.concat(currentModuleNameParts, ".") .. "." .. moduleFullName
            end
            break
        end
        offset = offset + 1

        if not currentModuleNameParts then
            if not currentModuleName then
                local n,v = debug.getlocal(3, 1)
                currentModuleName = v
            end

            currentModuleNameParts = string.split(currentModuleName, ".")
        end
        table.remove(currentModuleNameParts, #currentModuleNameParts)
    end
    return require(moduleFullName)
end

-- function myClass( base )
-- 	local mt = getmetatable(base)
-- 	local class = {}
-- 	class.ctor = false
-- 	setmetatable(class,
-- 		{
-- 			__index = base,
-- 			__call = function ( ... )
-- 				local r = mt.__call(...)
-- 				local ins_ret = {__base = r,}
-- 				setmetatable(ins_ret,
-- 					{
-- 						__index = function (t,k)
-- 							local ret_field = rawget(class,k)
-- 							if nil == ret_field then
-- 								ret_field = r[k]
-- 								if 'function' == type(ret_field) then
-- 									class[k] = ret_field
-- 								else
-- 									ins_ret[k] =ret_field
-- 								end
-- 							end
-- 							return ret_field
-- 						end,
-- 					})
-- 				if class.ctor then
-- 					class.ctor(ins_ret,...)
-- 				end

-- 				return ins_ret
-- 			end,
-- 		}
-- 	)
-- 	return class
-- end
