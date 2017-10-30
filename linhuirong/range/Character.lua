-- ---------------------------------补丁---------------------------------

-- 功能 : 千人测试获取额外邮件奖励
-- 制定 : momo, 老陈    2016-10-12 取消
-- 日期 : 2016-06-16
function sendTestReward(user)
  --if user == nil then
  --  return
  --end

  --user:sendTestReward(1000)
end

-- 功能 : 刷新menu功能,修正老号没触发menu事件
-- 制定 : momo
-- 日期 : 2016-06-23
function Patch_2016_06_23(user)
  local version = 201606230000

  if user == nil then
    return
  end
  if user:hasPatchLoad(version) == true then
    return
  end

  local menu = user:getMenu()
  if menu == nil then
    return
  end

  menu:refreshNewMenu()
  user:addPatchLoad(version)
end

-- 功能 : 重置冒险手册追加数据
-- 制定 : 孙惠伟
-- 日期 : 2016-06-27
function Patch_2016_06_27(user)
  if user == nil then
    return
  end

  local version = 201606271429
  if user:hasPatchLoad(version) == true then
    return
  end

  local manual = user:getManual()
  if manual == nil then
    return
  end

  manual:patch1()
  user:addPatchLoad(version)
end

-- 功能 : 修正部分老账号头发为0, 颜色为0
-- 指定 : 时明毅
-- 日期 ：2016-07-08
function Patch_2016_07_08(user)
  if user == nil then
    return
  end

  local version = 201607081533
  if user:hasPatchLoad(version) == true then
    return
  end

  local hair = user:getHairInfo()
  if hair == nil then
    return
  end

  local userdata = user:getUserSceneData()
  if userdata == nil then
    return
  end

  if hair:getRealHairColor() == 0 then
    hair:useColorFree(3)
  end

  if hair:getRealHair() == 0 then
    if userdata:getGender() == 1 then
      hair:useHairFree(998)
    else
      hair:useHairFree(999)
    end
  end

  user:addPatchLoad(version)
end

-- 功能 : 刷新menu功能,修正老号没触发menu事件
-- 制定 : momo
-- 日期 : 2016-07-11
function Patch_2016_07_11(user)
  local version = 201607110000

  if user == nil then
    return
  end
  if user:hasPatchLoad(version) == true then
    return
  end

  local menu = user:getMenu()
  if menu == nil then
    return
  end

  menu:refreshNewMenu()
  user:addPatchLoad(version)
end

-- 功能 : 刷新地图area,修正因为地图配置修改导致老账户部分area无法激活
-- 制定 : 时明毅
-- 日期 : 2016-07-15
function Patch_2016_07_15(user)
  local version = 201607151100

  if user == nil then
    return
  end
  if user:hasPatchLoad(version) == true then
    return
  end

  local userdata = user:getUserSceneData()
  if userdata == nil then
    return
  end

  for key, value in pairs(Table_Map) do
    if userdata:isNewMap(key) == false then
      userdata:addMapArea(key)
    end
  end

  user:addPatchLoad(version)
end

-- 功能 : 版本合成未及时通知,导致版本错误引发采集任务出错,修正当前采集任务直接跳过
-- 制定 : 孙惠伟
-- 日期 : 2016-07-22
function Patch_2016_07_22(user)
  local version = 201607222259

  if user == nil then
    return
  end
  if user:hasPatchLoad(version) == true then
    return
  end

  local quest = user:getQuest()
  if quest == nil then
    return;
  end

  quest:patch_2016_07_22()

  user:addPatchLoad(version)
end

-- 功能 : 移除冒险技能-自动治疗&紧急恢复,并归还技能点
-- 制定 : momo
-- 日期 : 2016-08-03
function Patch_2016_08_03(user)
  local version = 201608031736

  if user == nil or user:getTempID() == 0 then
    return
  end
  if user:hasPatchLoad(version) == true then
    return
  end

  local manual = user:getManual()
  if manual == nil then
    return
  end

  local fighter = user:getCurFighter()
  if fighter == nil then
    return
  end

  local skill = fighter:getSkill()
  if skill == nil then
    return
  end

  local skillcfg_1 = Table_Skill[50000001]
  local mailcfg_1 = Table_Mail[1001]
  local skillcfg_2 = Table_Skill[50001001];
  local mailcfg_2 = Table_Mail[1002]
  if skillcfg_1 == nil or mailcfg_1 == nil or skillcfg_2 == nil or mailcfg_2 == nil then
    return
  end

  -- 自动治疗
  if skill:removeSkill(skillcfg_1.id, 0, ESOURCE_SHOP) == true then
    manual:addSkillPoint(skillcfg_1.Cost)
    sendMail(user:getTempID(), mailcfg_1.id)
  end

  -- 紧急恢复
  if skill:removeSkill(skillcfg_2.id, 0, ESOURCE_SHOP) == true then
    manual:addSkillPoint(skillcfg_2.Cost)
    sendMail(user:getTempID(), mailcfg_2.id)
  end

  user:addPatchLoad(version)
end

-- 功能 : 修复var 0-5点没更新的问题
-- 日期 : 2016-11-03
function Patch_2016_11_03(user)
  local version = 201611031130

  if user == nil or user:getTempID() == 0 then
    return
  end
  if user:hasPatchLoad(version) == true then
    return
  end

  local var = user:getVar()
  if var == nil then
    return
  end

  var:setVarValue(EVARTYPE_QUEST_WANTED, 0)
  var:setVarValue(EVARTYPE_QUEST_WANTED_RESET, 0)
  var:setVarValue(EVARTYPE_SEAL, 0)
  var:setVarValue(EVARTYPE_LABORATORY, 0)

  user:addPatchLoad(version)
end

-- 功能 : 冒险手册拍照增加奖励, 给予已达成拍照任务的玩家相应奖励
-- 日期 : 2016-11-17
function Patch_2016_11_17(user)
  local version = 201611171553

  if user == nil or user:getTempID() == 0 then
    return
  end

  if user:hasPatchLoad(version) == true then
    return
  end

  local manual = user:getManual()
  if manual == nil then
    return
  end

  manual:patch2()

  user:addPatchLoad(version)
end

-- ---------------------------------事件---------------------------------

function onLogin(user)
  -- 功能 : 千人测试获取额外邮件奖励
  --sendTestReward(user)

  -- 功能 : 刷新menu功能,修正老号没触发menu事件
  Patch_2016_06_23(user)

  -- 功能 : 重置冒险手册追加数据
  Patch_2016_06_27(user)

  -- 功能 : 修正部分老账号头发为0, 颜色为0
  Patch_2016_07_08(user)

  -- 功能 : 刷新menu功能,修正老号没触发menu事件
  Patch_2016_07_11(user)

  -- 功能 : 刷新地图area,修正因为地图配置修改导致老账户部分area无法激活
  Patch_2016_07_15(user)

  -- 功能 : 版本合成未及时通知,导致版本错误引发采集任务出错,修正当前采集任务直接跳过
  Patch_2016_07_22(user)

  -- 功能 : 移除冒险技能-自动治疗&紧急恢复,并归还技能点
  Patch_2016_08_03(user)

  -- 功能 : 修复var 0-5点没更新的问题
  Patch_2016_11_03(user)

  -- 功能: 冒险手册拍照增加奖励
  Patch_2016_11_17(user)
end

function onDailyRefresh(user)
  -- 功能 : 千人测试获取额外邮件奖励
  --sendTestReward(user)
end

