---------------------------- B格猫入侵 ----------------------------

BCatActivity = class()

local ECatState =
{
  ESTATE_IDLE          = 0,
  ESTATE_BEGIN_INFORM  = 1,
  ESTATE_CREATE_UFONPC = 2,
  ESTATE_PROCESS_1     = 3,
  ESTATE_CREATE_UFOMON = 4,
  ESTATE_PROCESS_2     = 5,
  ESTATE_LEAVE_INFORM  = 6,
  ESTATE_FINISH        = 7,
}

function CreateNpc(params)
  local npcLuaParam = getOneLuaParam()
  if npcLuaParam == nil then
    return nil
  end
  for key, value in pairs(params) do
    --print(key, value)
    npcLuaParam:addKeyValue(key, value)
  end
  return getNpcManager():createNpcLua(npcLuaParam)
end

-- BCat : 构造函数
function BCatActivity:ctor()
  --self.starttab = {hour=11, min=20}
  --self.endtab = {hour=20, min=50}

  self.startTime = 0
  self.endTime = 0

  self.start = false
  self.state = ECatState.ESTATE_IDLE
  self.mapid = 0
  self.npc = nil
  self.ufo_id = 1124         -- ufoidNPC
  self.ufo_disp_time = 1020    -- ufo消失时间
  self.ufo_monster_id = 30025 -- ufo monster id
  self.ufo_mon_disptime = 1920 -- ufo monster消失时间
  self.cat_fight_id = 10107   -- 战斗猫id
  self.cat_magic_id = 10108   -- 魔法猫id
  self.cat_cook_id = 10108    -- 厨艺猫id
  self.cat_disp_time = 1920     -- 猫消失时间

  self.inform_state = 0
  self.inform_time_1 = 1     -- 开始前第一次公告时间(秒)
  self.inform_time_2 = 60     -- 开始前第二次公告时间(秒)
  self.inform_time_3 = 110     -- 开始前第三次公告时间(秒)

  self.process_step_1 = 1020     -- 第一阶段持续时间(秒)

  self.leave_inform_state = 0
  self.leave_inform_time_1 = 1800     -- 结束前第一次公告时间(秒)
  self.leave_inform_time_2 = 1860     -- 结束前第二次公告时间(秒)
  self.leave_inform_time_3 = 1910     -- 结束前第三次公告时间(秒)

  -- B格猫地图坐标
  self.point = {
                [2] = {{0, 0, 59}, {0, 0, 40}, {-10, 0, 40}, {-10, 0, 59}},
                [3] = {{0, 0, 59}, {0, 0, 40}, {-10, 0, 40}, {-10, 0, 59}},
               }
  self.index = 1

  self.summontime = 0
  self.summondelay = 3      -- B格猫召唤间隔
  self.summonfirst = 0

  self.catcount = 0
end

-- BCat : 初始化
function BCatActivity:init(startTime, endTime)
  self.state = ECatState.ESTATE_BEGIN_INFORM
  self.start = true
  self.startTime = startTime
  self.endTime = endTime
  self.inform_state = 0
  self.summontime = 0
  self.summonfirst = 0
  self.catcount = 0
  self.leave_inform_state = 0

  cPlusLog("[B格猫入侵-初始化]")
end

-- BCat : 开始前公告
function BCatActivity:inform(cur)
  local starttime = self.startTime

  if self.inform_state == 0 and cur > starttime + self.inform_time_1 then
    self.inform_state = 1
    getScActMgr():sendBCatInform(882, self.mapid, 4)
    cPlusLog("[B格猫入侵-开始前通告] 第一次 msgid : 224")
    --print("BCatActivity.inform-1")
  end

  if self.inform_state == 1 and cur > starttime + self.inform_time_2 then
    self.inform_state = 2
    getScActMgr():sendBCatInform(882, self.mapid, 4)
    cPlusLog("[B格猫入侵-开始前通告] 第二次 msgid : 225")
    --print("BCatActivity.inform-2")
  end

  if self.inform_state == 2 and cur > starttime + self.inform_time_3 then
    self.inform_state = 3
    getScActMgr():sendBCatInform(882, self.mapid, 4)
    cPlusLog("[B格猫入侵-开始前通告] 第三次 msgid : 226")
    --print("BCatActivity.inform-3")
    self.state = ECatState.ESTATE_CREATE_UFONPC
  end
end

-- BCat : 创建UFO
function BCatActivity:createUFO()
  --print("BCatActivity.createUFO")

  if self.point[self.mapid] == nil then
    --print("BCatActivity.createUFO-1")
    self.state = ECatState.ESTATE_FINISH
    return;
  end

  local npcLuaParam = getOneLuaParam()
  if npcLuaParam == nil then
    self.state = ECatState.ESTATE_FINISH
    return
  end

  local param = {
    id = self.ufo_id,
    map = self.mapid,
    territory = 0,
    behavior = 3,
    disappeartime = self.ufo_disp_time,
    pos_x = self.point[self.mapid][4][1], pos_y = self.point[self.mapid][4][2], pos_z = self.point[self.mapid][4][3],
    search = 0,
  }
  self.npc = CreateNpc(param)
  if self.npc == nil then
    --print("BCatActivity.createUFO-2")
    self.state = ECatState.ESTATE_FINISH
    return
  end

  getScActMgr():sendBCatStart(self.mapid, self.startTime, self.endTime)

  cPlusLog("[B格猫入侵-创建UFO] npcid : "..self.npc:getNpcID().."pos : ("..self.npc:get_x()..", "..self.npc:get_y()..", "..self.npc:get_z())
  self.state = ECatState.ESTATE_PROCESS_1
end

-- BCat : UFO移动
function BCatActivity:UFOMove()
  if self.npc == nil then
    return
  end
  local moveaction = self.npc:getMoveAction()
  if moveaction == nil then
    return
  end

  if moveaction:empty() == false then
    return
  end
  if self.point[self.mapid] == nil then
    return
  end

  local npcai = self.npc:getNpcAI()
  if self.index >= #self.point[self.mapid] then
    self.index = 1
  end
  npcai:moveToPos(self.point[self.mapid][self.index][1], self.point[self.mapid][self.index][2], self.point[self.mapid][self.index][3])
  self.index = self.index + 1

  getScActMgr():sendBCatUFOPos(self.mapid, self.npc:get_x(), self.npc:get_y(), self.npc:get_z())
  cPlusLog("[B格猫入侵-UFO移动] npcid : "..self.npc:getNpcID().."移动到pos : ("..self.point[self.mapid][self.index][1]..
  ", "..self.point[self.mapid][self.index][2]..", "..self.point[self.mapid][self.index][3])

  --local log = string.format("[B格猫入侵-UFO移动] npcid : %s 移动到pos : (%s,%s,%s)",
  --self.npc:getNpcID(), self.point[self.mapid][self.index][1], self.point[self.mapid][self.index][2], self.point[self.mapid][self.index][3])
  --cPlusLog(log)
end

-- BCat : 第一阶段
function BCatActivity:summonCat(cur)
  if cur < self.summontime or self.npc == nil then
    return
  end

  self.summontime = cur + self.summondelay

  local cat_fight_param = {
    id = self.cat_fight_id,
    map = self.mapid,
    territory = 2,
    behavior = 3,
    disappeartime = self.cat_disp_time,
    pos_x = self.npc:get_x(), pos_y = self.npc:get_y(), pos_z = self.npc:get_z(),
    range = 5,
    search = 3,
  }
  local cat_magic_param = {
    id = self.cat_magic_id,
    map = self.mapid,
    territory = 2,
    behavior = 3,
    disappeartime = self.cat_disp_time,
    pos_x = self.npc:get_x(), pos_y = self.npc:get_y(), pos_z = self.npc:get_z(),
    range = 5,
    search = 3,
  }

  if self.summonfirst == 0 then
    for i = 0, 10 do
      if CreateNpc(cat_fight_param) ~= nil then
        self.catcount = self.catcount + 1
        cPlusLog("[B格猫入侵-猫猫召唤] 第一次召唤 npcid : "..self.cat_fight_id)
      end
      if CreateNpc(cat_magic_param) ~= nil then
        self.catcount = self.catcount + 1
        cPlusLog("[B格猫入侵-猫猫召唤] 第一次召唤 npcid : "..self.cat_magic_id)
      end
    end
    self.summonfirst = 1
  else
    local count = 0
    local usercount = getSceneMgr():getCreatureCount(SCENE_ENTRY_USER, self.mapid) * 2
    if self.catcount < 20 then
      count = 20 - self.catcount
    else
      if self.catcount < usercount * 2 then
        count = usercount * 2 - self.catcount
      end
    end
    if count > 6 then
      count = 6
    end

    if count ~= 0 then
      for i = 0, count do
        local rand = math.random(100)
        if rand < 50 then
          CreateNpc(cat_fight_param)
          cPlusLog("[B格猫入侵-猫猫召唤] 后续召唤 玩家人数"..usercount.."npcid : "..self.cat_fight_id)
          self.catcount = self.catcount + 1
        else
          CreateNpc(cat_magic_param)
          self.catcount = self.catcount + 1
          cPlusLog("[B格猫入侵-猫猫召唤] 后续召唤 玩家人数"..usercount.."npcid : "..self.cat_magic_id)
        end
      end
    end
  end

  cPlusLog("[B格猫入侵-猫猫召唤] pos : ("..self.npc:get_x()..", "..self.npc:get_y()..", "..self.npc:get_z()..")")
end

function BCatActivity:process1(cur)
  self:UFOMove()
  self:summonCat(cur)

  if cur > self.startTime + self.process_step_1 then
    self.state = ECatState.ESTATE_CREATE_UFOMON
    cPlusLog("[B格猫入侵-第一阶段结束]")
  end
end

-- BCat : 第二阶段
function BCatActivity:summonHighCat(cur)
  if self.npc == nil then
    return
  end
  if cur < self.summontime then
    return
  end

  self.summontime = cur + self.summondelay
  local count = 0
  local usercount = getSceneMgr():getCreatureCount(SCENE_ENTRY_USER, self.mapid) * 2
  if self.catcount < 20 then
    count = 20 - self.catcount
  else
    if self.catcount < usercount * 2 then
      count = usercount * 2 - self.catcount
    end
  end
  if count > 8 then
    count = 8
  end

  local cat_cook_param = {
    id = self.cat_cook_id,
    map = self.mapid,
    territory = 2,
    behavior = 3,
    disappeartime = self.cat_disp_time,
    pos_x = self.npc:get_x(), pos_y = self.npc:get_y(), pos_z = self.npc:get_z(),
    range = 5,
    search = 3,
  }
  --print(cat_cook_param.id, self.npc:getNpcID())
  if count ~= 0 then
    for i = 0, count do
      CreateNpc(cat_cook_param)
      self.catcount = self.catcount + 1
      cPlusLog("[B格猫入侵-猫猫高级召唤] 后续召唤 玩家人数"..usercount.."npcid : "..self.cat_cook_id)
    end
  end
  cPlusLog("[B格猫入侵-猫猫高级召唤] pos : ("..self.npc:get_x()..", "..self.npc:get_y()..", "..self.npc:get_z()..")")
end

function BCatActivity:UFOTurnMonster()
  if self.npc == nil then
    self.state = ECatState.ESTATE_FINISH
    return
  end

  local ufo_monster_param = {
    id = self.ufo_monster_id,
    map = self.mapid,
    territory = 2,
    behavior = 3,
    disappeartime = self.ufo_mon_disptime,
    pos_x = self.npc:get_x(), pos_y = self.npc:get_y(), pos_z = self.npc:get_z(),
    range = 5,
    search = 10,
  }

  self.npc:setClearState()

  self.npc = CreateNpc(ufo_monster_param)
  if self.npc == nil then
    self.state = ECatState.ESTATE_FINISH
    return
  end

  self.state = ECatState.ESTATE_PROCESS_2
end

function BCatActivity:process2(cur)
  if self.npc == nil then
    self.state = ECatState.ESTATE_FINISH
    cPlusLog("[B格猫入侵-第二阶段结束] UFO被击杀")
    return
  else
    if cur > self.endTime - self.leave_inform_time_1 - 5 then
      self.state = ECatState.ESTATE_LEAVE_INFORM
      cPlusLog("[B格猫入侵-第二阶段结束] UFO未被击杀")
      return
    end
  end

  self:summonHighCat(cur)
end

-- BCat : 失败后离开公告
function BCatActivity:leaveinform(cur)

  if self.leave_inform_state == 0 and cur > self.endTime - self.leave_inform_time_1 then
    self.leave_inform_state = 1
    getScActMgr():sendBCatInform(224)
    cPlusLog("[B格猫入侵-结束前通告] 第一次 msgid : 224")
    --print("BCatActivity.leaveinform-1")
  end

  if self.leave_inform_state == 1 and cur > self.endTime - self.leave_inform_time_2 then
    self.leave_inform_state = 2
    getScActMgr():sendBCatInform(224)
    cPlusLog("[B格猫入侵-结束前通告] 第二次 msgid : 224")
    --print("BCatActivity.leaveinform-2")
  end
  if self.leave_inform_state == 2 and cur > self.endTime - self.leave_inform_time_3 then
    self.leave_inform_state = 3
    getScActMgr():sendBCatInform(224)
    cPlusLog("[B格猫入侵-结束前通告] 第三次 msgid : 224")
    --print("BCatActivity.leaveinform-3")
    self.state = ECatState.ESTATE_FINISH
  end
end

-- BCat : 活动结束
function BCatActivity:finish(cur)
  if self.start == false then
    return
  end

  --print("BCatActivity.finish")
  if self.npc ~= nil then
    self.npc:setClearState()
  end

  cPlusLog("[B格猫入侵-结束]")
  self.start = false
  self.state = ECatState.ESTATE_IDLE
end

function BCatActivity:run(cur)
  if self.start == false then
    return
  end

  if self.state == ECatState.ESTATE_BEGIN_INFORM then
    self:inform(cur)
  elseif self.state == ECatState.ESTATE_CREATE_UFONPC then
    self:createUFO()
  elseif self.state == ECatState.ESTATE_PROCESS_1 then
    self:process1(cur)
  elseif self.state == ECatState.ESTATE_CREATE_UFOMON then
    self:UFOTurnMonster()
  elseif self.state == ECatState.ESTATE_PROCESS_2 then
    self:process2(cur)
  elseif self.state == ECatState.ESTATE_LEAVE_INFORM then
    self:leaveinform(cur)
  elseif self.state == ECatState.ESTATE_FINISH then
    self:finish(cur)
  end
end

---------------------------- 主循环 ----------------------------

local bcat = BCatActivity.new()

-- scene : check act status
function activitystatus(acttype, mapid, isStart, startTime, endTime)
  if acttype == EACTIVITYTYPE_BCAT then
    bcat.mapid = mapid
    if isStart == true then
      bcat:init(startTime, endTime)
    else
      bcat:finish()
    end
  end
end

-- scene : npcdie
function npcdie(npc)
  -- B格猫
  if bcat.start == true then
    if bcat.npc ~= nil and npc ~= nil and bcat.npc:getGUID() == npc:getGUID() then
      bcat.npc = nil
    end

    local npcid = npc:getNpcID()
    --print("npcdie npcid="..npcid)
    if npcid == bcat.cat_fight_id or npcid == bcat.cat_magic_id or npcid == bcat.cat_cook_id then
      if bcat.catcount > 0 then
        bcat.catcount = bcat.catcount - 1
      end
    end
    --print("npcdie catcount"..bcat.catcount)
  end

end

-- session : inform user act info when login
function active_user_online(user)
  if user == nil then
    return
  end

  -- B格猫入侵
  local cur = os.time()
  if bcat.start == true and cur > bcat.startTime and cur < bcat.endTime then
    getSeActMgr():sendActStatusUser(user, EACTIVITYTYPE_BCAT, bcat.mapid, cur, cur + bcat.endTime)
  end
end

-- session : act timer
--function active_session_timer(cur)
  -- B格猫入侵
  --local tab = os.date("*t", cur)
  --local curnow = tab.hour * 60 + tab.min
  --local starttime = bcat.starttab.hour * 60 + bcat.starttab.min
  --local endtime = bcat.endtab.hour * 60 + bcat.endtab.min
  --if curnow < starttime or curnow > endtime then
    --if bcat.start == true then
      --bcat.start = false
      --bcat.mapid = 2
      --getSeActMgr():sendActStatusScene(EACTIVITYTYPE_BCAT, bcat.mapid, bcat.start)
      --print("session-bcat-stop mapid="..bcat.mapid)
    --end
  --else
    --if bcat.start == false then
      --bcat.start = true
      --bcat.mapid = 2
      --getSeActMgr():sendActStatusScene(EACTIVITYTYPE_BCAT, bcat.mapid, bcat.start)
      --print("session-bcat-start mapid="..bcat.mapid)
    --end
  --end
--end

-- scene : act timer
function active_scene_timer(cur)
  -- B格猫入侵
  bcat:run(cur)
end

