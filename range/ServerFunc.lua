-- ServerFunc.lua 服务器计算使用

math.randomseed( tonumber(tostring(os.time()):reverse():sub(1,6)) )

function CalcCameraSummonOdds(user, num, baseodds, isnight)
  if user == nil or baseodds == 0 then
    return false
  end
  local MaxOdds = 100000
  local odds = baseodds * math.pow(2, num + 1)
  if isnight then
    odds = odds / 2
  end
  if user:getMapID() == 9 then
    odds = odds / 2
  end
  odds = math.floor(odds);
  odds = odds < 1 and 1 or odds
  odds = odds > MaxOdds and MaxOdds or odds

  --print("---", odds, num, math.random(1, odds))
  if math.random(1, odds) == 1 then
    return true
  end

  return false
end

function CalcServerMonsterReload(NpcID, NpcType, Mapid, LifeTime, BeServerReloadTime)
  -- 草类植物
  if NpcID >= 40001 and NpcID <= 49999 then
    return BeServerReloadTime
  end
  
  if NpcID ==10017 or NpcID ==10056 or NpcID ==40014 or NpcID ==10015 or NpcID ==10037 then
    return BeServerReloadTime
  end
  
  -- mvp | mini
  if NpcType == 4 or NpcType == 5 then
    return BeServerReloadTime
  end

  if LifeTime<=10 then
     return 0
  end   
  
  --if PlayerNum<=10 then
    --if BeServerReloadTime/8<=1 then 
      -- reloadtime=0
    --else   
      -- reloadtime=math.floor(BeServerReloadTime/8)
    --end   
     --return reloadtime 
  --end   
  --if MonsterNum/PlayerNum>2 then
     --reloadtime=0
  --elseif MonsterNum/PlayerNum<=2 and MonsterNum/PlayerNum>1 then
     --reloadtime=0
  --else
     --reloadtime=0
  --end   

  return BeServerReloadTime
end

function CalcSpecEquipAttr(pEquip, equipID, refineLv)
  if pEquip == nil then
    return
  end
--测试精炼  精炼等级>=3,攻击+200;精炼等级>=5,攻击+400
  if equipID == 40327 then
    if refineLv >= 3 and refineLv < 5 then
      pEquip:setSpecAttr("Atk", 200)
    elseif refineLv >= 5 then
      pEquip:setSpecAttr("Atk", 400)
    end
  end
--测试精炼  精炼等级>=3,每提高一级精炼等级,攻击+10;精炼等级>=6,每提高一级精炼等级,攻击+20
	if equipID == 40328 then
		if refineLv >= 3 and refineLv < 6 then
			local atk = (refineLv-3)*10
			pEquip:setSpecAttr("Atk",atk)
		elseif refineLv >= 6 then
			local atk = 3*10 + (refineLv-6)*20
			pEquip:setSpecAttr("Atk",atk)
		end
	end
end

function CalcBreakSkillDamPer(pUser)
  if pUser == nil then
    return 0.1
  end

  local extra = 0
  local count_1 = pUser:getEquipedItemNum(42004)
  local count_2 = pUser:getEquipedItemNum(142004)
  local count_3 = pUser:getEquipedItemNum(20027)
  extra = extra + count_1 * 0.2 + count_2 * 0.2 +count_3*0.15

  --print(0.1+extra)
  return 0.1 + extra
end

-- calc seal-drop-equip refine lv
function CalcSealEquipRefineLv(quality)
  if quality ~= 1 then
    return 0
  end

  local random = math.random(1,100)
  if random >= 1 and random <= 25 then
    return 1
  elseif random >= 26 and random <= 50 then
    return 2
  elseif random >= 51 and random <= 75 then
    return 3
  elseif random >= 76 and random <= 100 then
    return 4
  end

  return 0
end

