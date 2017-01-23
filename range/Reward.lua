-- 获取怪物概率加成
function getNpcExtraRatio(npczone)
  local curtime = os.time()
  local ratio = 1

  -- 无限塔怪物
  if npczone == ENPCZONE_ENDLESSTOWER then
    local starttab = {year=2015, month=7, day=1, hour=0, min=0}
    local endtab = {year=2015, month=9, day=1, hour=0, min=0}

    local starttime = os.time(starttab)
    local endtime = os.time(endtab)
    if curtime > starttime and curtime < endtime then
      ratio = 4
    end
  end

  return ratio
end

-- 获取地图概率加成
function getMapExtraRatio(npc)
  local curtime = os.time()
  local ratio = 1
  local mapid = npc:getMapID()
  
  -- 幽灵暴走活动
  if mapid == 8 or mapid == 9 then
    local starttab = {year=2016, month=10, day=30, hour=0, min=0}
    local endtab = {year=2016, month=11, day=1, hour=23, min=59}

    local starttime = os.time(starttab)
    local endtime = os.time(endtab)
    if curtime > starttime and curtime < endtime then
      if npc:getNpcID()== 10019 or npc:getNpcID()== 10020 or npc:getNpcID()== 10022 or npc:getNpcID()== 20004 or npc:getNpcID()==30004 then
        ratio = 5
      end
    end
  end

  return ratio
end

-- 无限塔概率计算
function calcTowerRewardRatio(npc)
  if npc == nil then
    return 1
  end

  -- 获取npc加成
  local ratio = getNpcExtraRatio(npc:getNpcZoneType())

  -- miniboss和mvp 系数为0.2
  if npc:getNpcType() == ENPCTYPE_MINIBOSS or npc:getNpcType() == ENPCTYPE_MVP then
    return ratio * 0.2
  end

  return ratio
end

-- 野外怪概率计算
-- ismvp:是否是mvp专属掉率
function calcMapRewardRatio(npc, user, isquest, ismvp)   --任务表中的reward不受影响
  if isquest == true then
    return 1
  end
  
  if npc == nil or user == nil then
    return 1
  end
  
  if npc:getNpcZoneType() == ENPCZONE_TASK then   --任务怪的掉落reward不受影响
    return 1
  end
  -- 草类怪掉落不受战斗时长和等级差影响
  if npc:getNpcID() >= 40001 and npc:getNpcID() <= 49999 then
    return 1
  end
  --尖叫曼陀罗掉落不受战斗时长和等级差影响
  if npc:getNpcID() >= 17000 and npc:getNpcID() <= 17002 then
    return 1
  end

  local ratio = getMapExtraRatio(npc)

  if npc:getNpcType() == ENPCTYPE_MINIBOSS or npc:getNpcType() == ENPCTYPE_MVP then
    return ratio
  end

  if ismvp then 
    return ratio
  end

  local newratio = ratio
  local sec1 = CommonFun.getAddictSec1()
  local sec2 = CommonFun.getAddictSec2()
  if (sec2 <= sec1) then
    return newratio
  end

  local sec = user:getAddictTime()
  if sec >= sec1 and sec <= sec2 then
    newratio = (1 - (0.95 / (sec2 - sec1) * (sec - sec1))) * ratio
  end
  if (sec > sec2 ) then
    newratio = 0.05 * ratio
  end

  local deltalv = npc:getLevel() - user:getLevel()
  return newratio * CommonFun.getReduceValue(deltalv)
end

-- 封印怪概率计算
function calcSealRewardRatio(membercount)
  return membercount / 5
end

