-- 物品使用检测
-- return x ： x=0,可以使用; x=-1, 不可以使用,不需要提示; x=其他, 不可以使用, 提示msg id=x
function itemUserCheck(sUser, itemid, tUser)
  -- 苍蝇翅膀
  if sUser == nil then
    return 0
  end

  if Table_Item[itemid] == nil or Table_Item[itemid].Type == nil then
    return -1
  end

  -- 天地树叶子只能对死亡玩家使用
  if itemid == 5023 then
    if sUser:getSkillStatus() == 2 then
      return -1
    end
    if tUser == nil or tUser:isAlive() or tUser:isMyEnemy(sUser) then
      return -1
    end
    if tUser:isReliveByOther() then
      return 2509
    end
  end

  if itemid == 5024 then
    -- 不能再副本中使用
    local maptype = sUser:getRaidType()
    if maptype == 2 or maptype == 3 or maptype == 4 or maptype == 5 then
      return 112
    end
    -- 部分地图无法使用
    local mapid = sUser:getMapID()
    if mapid == 10001 or mapid == 3001 or mapid == 3003 or mapid == 1004 or mapid == 1005 or mapid == 1006 or mapid == 1002 or mapid == 3002 or mapid == 50001 or mapid == 50002 or mapid == 50003 or mapid == 50004 or mapid == 50005 or mapid == 50006 or mapid == 50007 or mapid == 50008 or mapid == 50009 or mapid == 50010 or mapid == 50011 or mapid == 50012 or mapid == 50013 or mapid == 50014 or mapid == 50015 or mapid == 50016 or mapid == 50017 or mapid == 50018 or mapid == 50019 or mapid == 50020 or mapid == 50021 or mapid == 50022 or mapid == 50023 or  mapid == 50024 then
      return 112
    end
    -- 技能吟唱无法使用
    if sUser:getSkillStatus() == 2 then
      return 3003
    end
    return 0
  end

  -- check arrow can use
  if Table_Item[itemid].Type == 43 then  
    local weapon = sUser:getWeaponType()
    if weapon ~= 210 then
      return 3051
    end
    local skill_lv = sUser:getSkillLv(127)

    if itemid == 12501 and skill_lv < 2 then
      return 3050
    end
    if itemid == 12502 and skill_lv < 5 then
      return 3050
    end
    return 0
  end

  -- in spec status
  local status = CommonFun.getBits(sUser:getAttr(EATTRTYPE_STATEEFFECT))
  local eType = Table_Item[itemid].Type
  local getStatus = {}

  if GameConfig.ItemsNoUseWhenRoleStates ~= nil then
    for key, val in pairs(GameConfig.ItemsNoUseWhenRoleStates) do
      for key2, val2 in pairs(val) do
        if val2 == eType then
          table.insert(getStatus, key)
        end
      end
    end
  end

  for key, val in pairs(getStatus) do
    if status[val] ~= nil and status[val] == 1 then
      return -1
    end
  end

  -- 掠夺许可证, buff 层数达到上限时不可使用
  if itemid == 5032 then
    if sUser:isBuffLayerEnough(EBUFFTYPE_ROBREWARD) then
      return 2510
    end
  end

  return 0
end

-- 药水恢复公式
function CalcItemHealValue(baseValue, sUser, formula)
  if sUser == nil or formula == nil then
    return 0
  end

  local hpRestoreSpd = sUser:getAttr(EATTRTYPE_ITEMRESTORESPD)
  local spRestoreSpd = sUser:getAttr(EATTRTYPE_ITEMSPRESTORESPD)
  local vit = sUser:getAttr(EATTRTYPE_VIT)
  local int = sUser:getAttr(EATTRTYPE_INT)

  if formula == 1 then
    return baseValue * (1 + hpRestoreSpd) * (1 + vit * 0.01)
  elseif formula == 2 then
    return baseValue * (1 + hpRestoreSpd) * (1 + vit * 0.015)
  elseif formula == 3 then
    return baseValue * (1 + hpRestoreSpd) * (1 + vit * 0.02)
  elseif formula == 4 then
    return baseValue * (1 + hpRestoreSpd) * (1 + vit * 0.025)
  elseif formula == 5 then
    return baseValue * (1 + spRestoreSpd) * (1 + int * 0.015)  
  end

  return baseValue
end

-- 物品使用后
function doAfterUsingItem(user, itemid)
  if user == nil then
    return
  end

  -- 部分道具使用后打断跟随
  local userdata = user:getUserSceneData()
  if userdata ~= nil then
    local item = {50001, 5024}
    for key, val in pairs(item) do
      if val == itemid then
        userdata:setFollowerID(0)
        break
      end
    end
  end
end

