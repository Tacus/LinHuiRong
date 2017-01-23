math.randomseed( tonumber(tostring(os.time()):reverse():sub(1,6)) )

function calcattr(curPoint, joblv, job, attr)
  return CommonFun.calAttrPoint(curPoint, joblv, job, attr)
end

-- skill param begin
SkillEntry = class("SkillEntry")
function SkillEntry:ctor(skillid, indexCount, pvp)
  self.skillIDAndLevel = skillid
  self.hitedCount = math.floor(indexCount/1000)
  self.hitedIndex = indexCount - self.hitedCount
  self.pvpMap = pvp
end
-- skill param end

-- logger
Logger = class("Logger")
function Logger.error(str)
  cPlusLogError(tostring(str))
end
-- logger

-- entry class begin
Entry = class("Entry")
function Entry:ctor(cPlus_pEntry)
  self.pEntry = cPlus_pEntry
  self.name = cPlus_pEntry:getName()
  self.BaseLv = cPlus_pEntry:getLevel()
  self.race = cPlus_pEntry:getRaceType()
  --self.boss = cPlus_pEntry:isBoss()
  self.randomByMath = false
  self.zoneType = 0
  local dsize = cPlus_pEntry:getBodySize()
  if dsize == 1 then
    self.shape = "S"
  elseif dsize == 2 then
    self.shape = "M"
  elseif dsize == 3 then
    self.shape = "L"
  end

  self.boss = false
  self.mini = false
  local npc = cPlus_pEntry:getNpcObject()
  if npc ~= nil then
    if npc:getNpcType() == 4 then
      self.mini = true
    elseif npc:getNpcType() == 5 then
      self.boss = true
    end
  end

  if npc ~= nil then
    self.zoneType = npc:getNpcZoneType()
  end
end

function Entry:GetProperty(attrname)
  if self.pEntry == nil then
    return nil
  end
  if self.pEntry:isValidAttrName(attrname) == false then
    local info = string.format("CommonFun 获得属性, 属性名称错误: %s", tostring(attrname))
    cPlusLogError(info)
    return nil
  end
  return self.pEntry:getStrAttr(attrname)
end

function Entry:IsEnemy(targetEntry)
  if targetEntry.pEntry == nil or self.pEntry == nil then
    return 0
  end
  return self.pEntry:isMyEnemy(targetEntry.pEntry)
end

function Entry:GetLernedSkillLevel(skillID)
  if self.pEntry == nil then
    return 0
  else
    return self.pEntry:getSkillLv(skillID)
  end
  return 1
end

function Entry:GetProfressionID()
  if self.pEntry == nil then
    return 0
  end
  return self.pEntry:getProfession()
end

function Entry:GetAttackSkillIDAndLevel()
  if self.pEntry == nil then
    return 0
  end
  return self.pEntry:getNormalSkill()
end

function Entry:DamageAlways1()
  if self.pEntry == nil then
    return false
  end
  return self.pEntry:bDamageAlways1()
end

function Entry:GetRandom()
  if self.randomByMath then
    return (math.random(0,99))
  end
  local value = self.pEntry:getRandomNum()
  return value
end

function Entry:IsImmuneSkill(skillid)
  if self.pEntry == nil then
    return false
  end
  return self.pEntry:isImmuneSkill(skillid)
end

function Entry:SelfBuffChangeSkill()
  return nil
end

function Entry:DefiniteHitAndCritical()
  return false
end

function Entry:IgnoreJinzhanDamage()
  return false
end

function Entry:IsFly()
  -- 客户端接口, 不处理
  return false
end

function Entry:GetArrowID()
  if self.pEntry == nil then
    return 0
  end
  return self.pEntry:getArrowID()
end

function Entry:GetEquipedWeaponType()
  if self.pEntry == nil then
    return 0
  end
  return self.pEntry:getWeaponType()
end

function Entry:AddBuffDamage(damage)
  if self.pEntry == nil or self.pEntry.addBuffDamage == nil then
    return
  end
  self.pEntry:addBuffDamage(damage)
end

function Entry:GetEquipedItemNum(itemid)
  if self.pEntry == nil or self.pEntry:getUserObject() == nil then
    return 0
  end
  return self.pEntry:getUserObject():getEquipedItemNum(itemid)
end

function Entry:GetJobLv()
  if self.pEntry == nil or self.pEntry:getUserObject() == nil then
    return 0
  end
  return self.pEntry:getUserObject():getJobLv()
end

-- entry class end

-- 伤害计算
function exeDamage(sUser, tUser, skillid, targetsNum)
  if (sUser == nil or tUser == nil or targetsNum <= 1000) then
    return 0
  end

  entry1 = Entry.new(sUser)
  entry2 = Entry.new(tUser)
  oSkill = SkillEntry.new(skillid, targetsNum, sUser:isOnPvp())
  oLogger = Logger.new()

  -- client 不参与计算的技能,随机数直接用math.random()随机
  if Table_Skill[skillid] ~= nil then
    if Table_Skill[skillid].Logic_Param ~= nil and Table_Skill[skillid].Logic_Param.no_select == 1 then
      entry1.randomByMath = true
    end
  end

  if (tUser:isImmuneSkill(skillid) == true) then
    return 0
  end

  local damage, damagetype = CommonFun.CalcDamage(entry1, entry2, oSkill, oLogger)
  if damagetype ~= nil then
    tUser:setTempDamageType(damagetype)
  end
  --print(damagetype, damage)
  return damage
end

-- 公式type -> get value
function calcFormulaValue(sUser, formulaType)
  if (sUser == nil) then
    return 0
  end

  entry1 = Entry.new(sUser)
  local value = CommonFun.GetFormulaValue(entry1, formulaType)
  return value
end

-- 吸血计算
function getSuckBlood(sUser, damage, skillid)
  if (sUser == nil) then
    return 0
  end

  entry1 = Entry.new(sUser)
  local value = CommonFun.CalcSuckBlood(entry1, damage, skillid)
  return value
end

-- buff 公式计算
function calcBuffValue(sUser, tUser, pParams, dtype)
  if sUser == nil or tUser == nil or pParams == nil then
    return 0
  end
  entry1 = Entry.new(sUser)
  entry2 = Entry.new(tUser)
  local value = CommonFun.calcBuffValue(entry1, entry2, dtype, pParams:getParams(1), pParams:getParams(2), pParams:getParams(3), pParams:getParams(4), pParams:getParams(5))
  if value ~= nil then
    return value
  end
  return 0
end

function calcBattlePoint(user, lv, profession, skillbt)
  if user == nil then
    return 0
  end

  local weapon = user:getWeaponType()

  local attr = {}
  local attrstart = 100 --EATTRTYPE_STR
  local attrend = 105 --EATTRTYPE_LUK
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getAttr(index)) - getNearNum(user:getTimeBuffAttr(index))
  end
  attrstart = 200 --EATTRTYPE_ATK
  attrend = 229 --EATTRTYPE_CRIPER
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getOtherAttr(index)) - getNearNum(user:getTimeBuffAttr(index))
  end
  attrstart = 300 --EATTRTYPE_REFINE
  --attrend = 301 --EATTRTYPE_MREFINE
  --attrend = 302 --EATTRTYPE_MOVESPDPER
  --attrend = 304 --EATTRTYPE_SKILLASPD
  --attrend = 306 -- EATTRTYPE_FLEEPER
  attrend = 312 -- EATTRTYPE_LUKPER
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getOtherAttr(index)) - getNearNum(user:getTimeBuffAttr(index))
  end
  attrstart = 400 --EATTRTYPE_SHOWATK
  attrend = 413 --EATTRTYPE_SHOWRESTORESPD
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getOtherAttr(index)) - getNearNum(user:getTimeBuffAttr(index))
  end

  return CommonFun.calcBattlePoint(attr, lv, profession, weapon, skillbt)
end

function calcUserAttrValue(user, lv, profession)
  if user == nil then
    return
  end

  local weapon = user:getWeaponType()

  local attr = {}
  local attrstart = 100 --EATTRTYPE_STR
  local attrend = 105 --EATTRTYPE_LUK
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getAttr(index))
  end
  attrstart = 200 --EATTRTYPE_ATK
  attrend = 229 --EATTRTYPE_CRIPER
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getOtherAttr(index))
  end
  attrstart = 300 --EATTRTYPE_REFINE
  --attrend = 301 --EATTRTYPE_MREFINE
  --attrend = 302 --EATTRTYPE_MOVESPDPER
  --attrend = 304 --EATTRTYPE_SKILLASPD
  --attrend = 306 --EATTRTYPE_FLEEPER
  attrend = 312 -- EATTRTYPE_LUKPER
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getOtherAttr(index))
  end
  attrstart = 400 --EATTRTYPE_SHOWATK
  attrend = 413 --EATTRTYPE_SHOWRESTORESPD
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getOtherAttr(index))
  end

  local total, extra = CommonFun.calcUserAttrValue(attr, lv, profession, weapon)
  for key, value in pairs(total) do
    user:setAttr(key, value)
  end
  for key, value in pairs(extra) do
    user:setPointAttr(key, value);
  end
end

function calcUserShowAttrValue(user, profession, oldlv, newlv)
  if user == nil then
    return
  end

  local attr = {}
  local attrstart = 100 --EATTRTYPE_STR
  local attrend = 105 --EATTRTYPE_LUK
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getBaseAttr(index))
  end
  local show = CommonFun.calcUserShowAttrValue(attr, profession, oldlv, newlv);
  for key, value in pairs(show) do
    user:setShowAttr(key, value)
  end
end

function calcUserShowAttrValuePro(user, lv, oldpro, newpro)
  if user == nil then
    return
  end

  local attr = {}
  local attrstart = 100 --EATTRTYPE_STR
  local attrend = 105 --EATTRTYPE_LUK
  for index = attrstart, attrend do
    attr[index] = getNearNum(user:getBaseAttr(index))
  end
  local show = CommonFun.calcUserShowAttrValuePro(attr, lv, oldpro, newpro);
  for key, value in pairs(show) do
    user:setShowAttr(key, value)
  end
end

function calcNpcAttrValue(npc)
  if npc == nil then
    return
  end

  local attr = {}
  local baseAttr = {}
  local attrstart = 100 --EATTRTYPE_STR
  local attrend = 105 --EATTRTYPE_LUK
  for index = attrstart, attrend do
    attr[index] = npc:getOtherAttr(index)
    baseAttr[index] = npc:getBaseAttr(index)
  end
  attrstart = 200 --EATTRTYPE_ATK
  attrend = 229 --EATTRTYPE_CRIPER
  for index = attrstart, attrend do
    attr[index] = npc:getOtherAttr(index)
  end
  attrstart = 300 --EATTRTYPE_REFINE
  attrend = 301 --EATTRTYPE_MREFINE
  for index = attrstart, attrend do
    attr[index] = npc:getOtherAttr(index)
  end

  attrstart = 305 -- EATTRTYPE_HITPER
  attrend = 312 -- EATTRTYPE_LUKPER
  for index = attrstart, attrend do
    attr[index] = npc:getOtherAttr(index)
    baseAttr[index] = npc:getBaseAttr(index)
  end

  attrstart = 400 --EATTRTYPE_SHOWATK
  attrend = 413 --EATTRTYPE_SHOWRESTORESPD
  for index = attrstart, attrend do
    attr[index] = npc:getOtherAttr(index)
  end

  local baseResult = {}
  baseResult = CommonFun.calcNpcAttrValue(baseAttr, attr, profession)

  local result = {}
  if npc:getNpcZoneType() == ENPCZONE_ENDLESSTOWER then
    result = CommonFun.calcEndlessTowerNpcAttrValue(attr, npc:getNpcType(), npc:getProfession(), npc:getEndlessLayer())
  elseif npc:getNpcZoneType() == ENPCZONE_LABORATORY then
    result = CommonFun.calcLaboratoryNpcAttrValue(attr, npc:getLevel(), npc:getProfession(), npc:getRoundID())
  elseif npc:getNpcZoneType() == ENPCZONE_SEAL then
    result = CommonFun.calcSealNpcAttrValue(attr, npc:getProfession(), npc:getSealType(), npc:getMapID())
  elseif npc:getNpcZoneType() == ENPCZONE_DOJO then
      result = CommonFun.calcDojoNpcAttrValue(attr, npc:getNpcType(), npc:getProfession(), npc:getDojoLevel())
  end

  -- 若有重复, 优先取副本属性
  for key, value in pairs(result) do
    baseResult[key] = value
  end

  for key, value in pairs(baseResult) do
    npc:setAttr(key, value)
  end
end

function getRaceParam(sUser, tUser)
  if (sUser == nil or tUser == nil) then
    return 0
  end

  local RaceToDamPer = {
    EATTRTYPE_BRUTEDAMPER, EATTRTYPE_DEMIHUMANDAMPER, EATTRTYPE_DEMONDAMPER, EATTRTYPE_PLANTDAMPER,
    EATTRTYPE_DEADLESSDAMPER, EATTRTYPE_FORMLESSDAMPER, EATTRTYPE_FISHDAMPER, EATTRTYPE_ANGLEDAMPER,
    EATTRTYPE_INSECTDAMPER, EATTRTYPE_DRAGONDAMPER }

  local RaceToResPer = {
    EATTRTYPE_BRUTERESPER, EATTRTYPE_DEMIHUMANRESPER, EATTRTYPE_DEMONRESPER, EATTRTYPE_PLANTRESPER,
    EATTRTYPE_DEADLESSRESPER, EATTRTYPE_FORMLESSRESPER, EATTRTYPE_FISHRESPER, EATTRTYPE_ANGLERESPER,
    EATTRTYPE_INSECTRESPER, EATTRTYPE_DRAGONRESPER }

  local race = tUser:getRaceType()
  local addP = 1
  if race > 0 and race < 11 then
    addP = 1 + sUser:getAttr(RaceToDamPer[race])
  end
  race = sUser:getRaceType()
  local delP = 1
  if race > 0 and race < 11 then
    delP = 1 - tUser:getAttr(RaceToResPer[race])
  end

  return addP * delP
end

function getBossParam(sUser, tUser)
  if (sUser == nil or tUser == nil) then
    return 0
  end

  local addP = 1
  if tUser:isBoss() then
    addP = 1 + sUser:getAttr(EATTRTYPE_BOSSDAMPER)
  end
  local delP = 1
  if sUser:isBoss() then
    delP = 1 - tUser:getAttr(EATTRTYPE_BOSSRESPER)
  end
  return addP * delP
end

function getElementParam(sUser, tUser, skill)
  if (sUser == nil or tUser == nil or skill == nil) then
    return 0
  end

  local atkType = skill:getAtkAttr() ~= 0 and skill:getAtkAttr() or sUser:getAttr(EATTRTYPE_ATKATTR)
  --local atkType = sUser:getAttr(EATTRTYPE_ATKATTR)
  local defType = tUser:getAttr(EATTRTYPE_DEFATTR)
  if atkType < 1 or atkType > 10 or defType < 1 or defType > 10 then
    return 1
  end
  local configParam = GameConfig.ElementRestrain[atkType][defType]

  local atkList = {
    EATTRTYPE_WINDDAMPER, EATTRTYPE_EARTHDAMPER, EATTRTYPE_WATERDAMPER, EATTRTYPE_FIREDAMPER,
    EATTRTYPE_NEUTRALDAMPER, EATTRTYPE_HOLYDAMPER, EATTRTYPE_SHADOWDAMPER, EATTRTYPE_GHOSTDAMPER,
    EATTRTYPE_UNDEADDAMPER, EATTRTYPE_POSIONDAMPER
  }
  local defList = {
    EATTRTYPE_BEWINDDAMPER, EATTRTYPE_BEEARTHDAMPER, EATTRTYPE_BEWATERDAMPER, EATTRTYPE_BEFIREDAMPER,
    EATTRTYPE_BENEUTRALDAMPER, EATTRTYPE_BEHOLYDAMPER, EATTRTYPE_BESHADOWDAMPER, EATTRTYPE_BEGHOSTDAMPER,
    EATTRTYPE_BEUNDEADDAMPER, EATTRTYPE_BEPOSIONDAMPER
  }
  local atkParam = 1
  local defParam = 1
  if atkType > 0 and atkType < 11 then
    atkParam = 1 +  sUser:getAttr(atkList[atkType])
    defParam = 1 - tUser:getAttr(defList[atkType])
  end

  return configParam * atkParam * defParam
end

function getBodyParam(sUser, tUser)
  if (sUser == nil or tUser == nil) then
    return 0
  end

  if sUser:isIgnoreBodyDam() then
    return 1
  end

  local bodyDam = {
    EATTRTYPE_SMALLDAMPER, EATTRTYPE_MIDDAMPER, EATTRTYPE_BIGDAMPER
  }
  local bodyRes = {
    EATTRTYPE_SMALLRESPER, EATTRTYPE_MIDRESPER, EATTRTYPE_BIGRESPER
  }
  local sbodysize = sUser:getBodySize()
  local tbodysize = tUser:getBodySize()

  local damParam = 1
  if tbodysize > 0 and tbodysize < 4 then
    damParam = 1 + sUser:getAttr(bodyDam[tbodysize])
  end
  local resParam = 1
  if sbodysize > 0 and sbodysize < 4 then
    resParam = 1 - tUser:getAttr(bodyRes[sbodysize])
  end

  return damParam * resParam
end

--计算怪物真正的掉落经验衰减比率
function calcNpBaseExpRatio(npc, realexp, dailyextra)
  local baseexp = npc:getBaseExp()
  if baseexp == 0 then 
    return 0
  end
  local dailyRatio = CommonFun.getDailyRatio(dailyextra)       
  if dailyRatio == 0 then
    return 0
  end

  local ratio = realexp / dailyRatio / baseexp
  return ratio
end

-- 计算怪物掉落base经验
function calcNpcDropBaseExp(user, npc, damage, killer, dailyextra, membercount)
  if user == nil or npc == nil then
    local info = string.format("[怪物掉落经验], 计算出现异常: %s, %s", tostring(nil), tostring(npc))
    cPlusLogError(info)
    return 0
  end

  local npclv = npc:getLevel()
  local deltalv = npc:getLevel() - user:getLevel()
  local npcbaseexp = npc:getBaseExp()
  local npctype = npc:getNpcType()
  local npczone = npc:getNpcZoneType()
  local npcmaxhp = npc:getAttr(EATTRTYPE_MAXHP)
  local layer = npc:getEndlessLayer()
  local mapid = npc:getMapID()
  local stype = npc:getSummonType()
--  local membercount = user:getTeamMemberCount()

  -- 参数
  local param = 0
  if npctype == ENPCTYPE_MONSTER then
    param = 7
  elseif npctype == ENPCTYPE_MINIBOSS then
    param = 35
  elseif npctype == ENPCTYPE_MVP then
    param = 70
  end

  if npczone ~= ENPCZONE_FIELD then
    npcbaseexp = npcbaseexp * param * npclv
  end

  return CommonFun.calcNpcDropBaseExp(damage, deltalv, npctype, npczone, npcmaxhp, npcbaseexp, 0, membercount, layer, mapid, stype, killer, dailyextra, 7)
end

-- 计算怪物掉落job经验
function calcNpcDropJobExp(user, npc, damage, killer, dailyextra, membercount)
  if user == nil or npc == nil then
    return 0
  end

  local npclv = npc:getLevel()
  local deltalv = npc:getLevel() - user:getLevel()
  local npcjobexp = npc:getJobExp()
  local npctype = npc:getNpcType()
  local npczone = npc:getNpcZoneType()
  local npcmaxhp = npc:getAttr(EATTRTYPE_MAXHP)
  local layer = npc:getEndlessLayer()
  local mapid = npc:getMapID()
  local stype = npc:getSummonType()
--  local membercount = user:getTeamMemberCount()

  -- 参数
  local param = 0
  if npctype == ENPCTYPE_MONSTER then
    param = 4
  elseif npctype == ENPCTYPE_MINIBOSS then
    param = 20
  elseif npctype == ENPCTYPE_MVP then
    param = 40
  end

  if npczone ~= ENPCZONE_FIELD then
    npcjobexp = npcjobexp * param * npclv
  end

  return CommonFun.calcNpcDropBaseExp(damage, deltalv, npctype, npczone, npcmaxhp, npcjobexp, 0, membercount, layer, mapid, stype, killer, dailyextra, 4)
end

function getNearNum(infNum)
  return math.floor(infNum * 1000 + 0.5) / 1000
end

-- 计算玩家死亡经验掉落
function calcUserDieDropBaseExp(user)
  if user == nil then
    return 0
  end
  local lv = user:getLevel()
  return CommonFun.calcUserDieDropBaseExp(lv);
end

-- 计算玩家离线时间
function calcUserOfflineTime(logintime, offlinetime)
  return CommonFun.calcUserOfflineTime(logintime, offlinetime)
end

-- 计算玩家离线经验
function calcUserOfflineExp(user, logintime, offlinetime)
  return CommonFun.calcUserOfflineExp(user:getLevel(), logintime, offlinetime)
end

-- 计算玩家离线job经验
function calcUserOfflineJobExp(user, logintime, offlinetime)
  return CommonFun.calcUserOfflineJobExp(user:getLevel(), logintime, offlinetime)
end

-- 计算抗击魔潮经验池扣除
function calcDailyExpSub(exp)
  return CommonFun.calcDailyExpSub(exp)
end

-- 计算装备强化所需费用
function calcEquipStrengthCost(lv, q, t)
  return CommonFun.calcEquipStrengthCost(lv, q, t)
end

-- 计算沉迷经验衰减
function calcAddictDropExp(sec, exp)
  return CommonFun.calcAddictDropExp(sec, exp)
end

-- 计算沉迷怪物掉落衰减
--function calcAddictDropItem(sec, ratio, deltalv)
--  return CommonFun.calcAddictDropItem(sec, ratio, deltalv)
--end

-- 计算沉迷怪物掉落衰减提示时间
function getAddictTipsTime()
  return CommonFun.getAddictSec1()
end

-- 计算公会祈祷所需贡献
function calcGuildPrayCon(prayid, praylv)
  return CommonFun.calcGuildPrayCon(prayid, praylv)
end

-- 计算公会祈祷所需货币
function calcGuildPrayMon(prayid, praylv)
  return CommonFun.calcGuildPrayMon(prayid, praylv)
end

--- 计算公会祈祷属性
function calcGuildPrayAttr(user, prayid, praylv)
  if user == nil then
    return
  end

  local cfg = Table_Guild_Faith[prayid]
  if cfg == nil then
    return
  end

  local result = CommonFun.calcGuildPrayAttr(prayid, praylv)

  for key, value in pairs(result) do
    user:setGuildAttr(key, value)
  end
end

