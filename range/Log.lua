-- 获取职业名称
function getProName(pro)
  if pro == EPROFESSION_NOVICE then
    return "初心者"
  elseif pro == EPROFESSION_WARRIOR then
    return "剑士"
  elseif pro == EPROFESSION_KNIGHT then
    return "骑士"
  elseif pro == EPROFESSION_LORDKNIGHT then
    return "骑士领主"
  elseif pro == EPROFESSION_RUNEKNIGHT then
    return "符文骑士"
  elseif pro == EPROFESSION_CRUSADER then
    return "十字军"
  elseif pro == EPROFESSION_PALADIN then
    return "圣殿十字军"
  elseif pro == EPROFESSION_ROYALGUARD then
    return "皇家卫士"
  elseif pro == EPROFESSION_MAGICIAN then
    return "魔法师"
  elseif pro == EPROFESSION_WIZARD then
    return "巫师"
  elseif pro == EPROFESSION_HIGHWIZARD then
    return "超魔导士"
  elseif pro == EPROFESSION_WARLOCK then
    return "大法师"
  elseif pro == EPROFESSION_SAGE then
    return "贤者"
  elseif pro == EPROFESSION_PROFESSOR then
    return "智者"
  elseif pro == EPROFESSION_SORCERER then
    return "元素使"
  elseif pro == EPROFESSION_THIEF then
    return "盗贼"
  elseif pro == EPROFESSION_ASSASSIN then
    return "刺客"
  elseif pro == EPROFESSION_ASSASSINCROSS then
    return "十字刺客"
  elseif pro == EPROFESSION_GUILLOTINECROSS then
    return "十字切割者"
  elseif pro == EPROFESSION_ROGUE then
    return "流氓"
  elseif pro == EPROFESSION_STALKER then
    return "神行太保"
  elseif pro == EPROFESSION_SHADOWCHASER then
    return "逐影"
  elseif pro == EPROFESSION_ARCHER then
    return "弓箭手"
  elseif pro == EPROFESSION_HUNTER then
    return "猎人"
  elseif pro == EPROFESSION_SNIPER then
    return "神射手"
  elseif pro == EPROFESSION_RANGER then
    return "游侠"
  elseif pro == EPROFESSION_BARD then
    return "诗人"
  elseif pro == EPROFESSION_CLOWN then
    return "搞笑艺人"
  elseif pro == EPROFESSION_MINSTREL then
    return "宫廷乐师"
  elseif pro == EPROFESSION_DANCER then
    return "舞娘"
  elseif pro == EPROFESSION_GYPSY then
    return "冷艳舞姬"
  elseif pro == EPROFESSION_WANDERER then
    return "漫游舞者"
  elseif pro == EPROFESSION_ACOLYTE then
    return "服事"
  elseif pro == EPROFESSION_PRIEST then
    return "牧师"
  elseif pro == EPROFESSION_HIGHPRIEST then
    return "神官"
  elseif pro == EPROFESSION_ARCHBISHOP then
    return "大主教"
  elseif pro == EPROFESSION_MONK then
    return "武僧"
  elseif pro == EPROFESSION_CHAMPION then
    return "武术宗师"
  elseif pro == EPROFESSION_SHURA then
    return "修罗"
  elseif pro == EPROFESSION_MERCHANT then
    return "商人"
  elseif pro == EPROFESSION_BLACKSMITH then
    return "铁匠"
  elseif pro == EPROFESSION_WHITESMITH then
    return "神工匠"
  elseif pro == EPROFESSION_MECHANIC then
    return "机匠"
  elseif pro == EPROFESSION_ALCHEMIST then
    return "炼金术士"
  elseif pro == EPROFESSION_CREATOR then
    return "创造者"
  elseif pro == EPROFESSION_GENETIC then
    return "基因学者"
  end

  return ""
end

-- 获取来源名称
function getSourceName(source)
  if source == ESOURCE_NORMAL then
    return "无"
  elseif source == ESOURCE_PACKAGE then
    return "包裹"
  elseif source == ESOURCE_QUEST then
    return "任务"
  elseif source == ESOURCE_EQUIP then
    return "装备"
  elseif source == ESOURCE_CARD then
    return "插卡"
  elseif source == ESOURCE_ACTSKILL then
    return "技能"
  elseif source == ESOURCE_COMPOSE then
    return "合成"
  elseif source == ESOURCE_REWARD then
    return "奖励"
  elseif source == ESOURCE_MONSTERKILL then
    return "怪物击杀"
  elseif source == ESOURCE_GM then
    return "GM"
  elseif source == ESOURCE_FUBEN then
    return "副本"
  elseif source == ESOURCE_CHARGE then
    return "充值"
  elseif source == ESOURCE_LABORATORY then
    return "研究所"
  elseif source == ESOURCE_MAPTRANS then
    return "地图传送"
  elseif source == ESOURCE_HAIR then
    return "发型"
  elseif source == ESOURCE_STRENGTH then
    return "强化"
  elseif source == ESOURCE_SHOP then
    return "商店"
  elseif source == ESOURCE_SELL then
    return "出售"
  elseif source == ESOURCE_PICKUP then
    return "捡取"
  elseif source == ESOURCE_OFFLINE then
    return "离线"
  elseif source == ESOURCE_LVUP then
    return "升级"
  elseif source == ESOURCE_TRADE then
    return "交易"
  elseif source == ESOURCE_TRANSFER then
    return "继承"
  elseif source == ESOURCE_SEAL then
    return "封印"
  elseif source == ESOURCE_GUILDPRAY then
    return "祈祷"
  elseif source == ESOURCE_ENCHANT then
    return "附魔"
  elseif source == ESOURCE_GUILDCREATE then
    return "公会创建"
  elseif source == ESOURCE_GUILDLEVELUP then
    return "公会升级"
  elseif source == ESOURCE_RELIVE then
    return "复活"
  elseif source == ESOURCE_REPAIR then
    return "修复"
  elseif source == ESOURCE_STORE then
    return "仓库"
  elseif source == ESOURCE_MUSICBOX then
    return "点唱机"
  elseif source == ESOURCE_TOWER then
    return "无限塔"
  elseif source == ESOURCE_DOJOFIRST then
    return "道场首次通关"
  elseif source == ESOURCE_DOJOHELP then
    return "道场协助通关"
  elseif source == ESOURCE_MANUAL then
    return "冒险手册"
  elseif source == ESOURCE_ROB then
    return "掠夺证"
  elseif source == ESOURCE_WANTEDQUEST then
    return "看板"
  elseif source == ESOURCE_DONATE then
    return "公会捐赠"
  elseif source == ESOURCE_TREASURE then
    return "北森寻宝"
  elseif source == ESOURCE_FERRISWHEEL then
    return "摩天轮"
  elseif source == ESOURCE_DOG then
    return "单身狗"
  elseif source == ESOURCE_DECOMPOSE then
    return "装备分解"
  end

  return ""
end

