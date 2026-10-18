# S2 SP 的 UI 层 Lua/XML 三维度复审报告

- 审查范围：`git diff a7c2416..HEAD -- "Super Power - Remaking of World Order (v 7)/UI/"`（31 文件，+2871/-290）
- 审查日期：2026-10-02
- 结论：应修正 2 项 / 提示 3 项 / 确认无误 1 类

---

## 一、应修正（会导致实际缺陷）

### [A-1] 【中】CSUA 建筑 tooltip 的盟友/朋友判定恒为 false：`minorPlayers` 以城邦 ID（整数）为键，却用城邦 Type（字符串）查询

- **文件**：`Super Power - Remaking of World Order (v 7)/UI/InGame/InfoTooltipInclude.lua:1468`（写入）与 `:1497`（读取）
- **维度**：A（显示口径错误——"生效档不标来源 / 未生效档标青色城邦名"的既定规则被破坏）
- **证据**：
  ```lua
  -- 1465-1470 写入：GetMinorCivType() 返回整数 ID（CvLuaPlayer::lGetMinorCivType 用 lua_pushinteger）
  for iPlayer = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
      local pPlayer = Players[ iPlayer ]
      if pPlayer ~= nil and pPlayer:IsMinorCiv() then
          minorPlayers[ pPlayer:GetMinorCivType() ] = pPlayer   -- 键 = 整数 ID
      end
  end
  ...
  -- 991-995 SQL：m.Type AS CivType —— MinorCivilizations.Type 是字符串（如 "MINOR_CIV_MONACO"）
  --          local strBase = "SELECT m.Type AS CivType, ... FROM MinorCivilizations m ..."
  -- 1495-1504 读取
  for i = 1, #csuaEntries do
      local entry = csuaEntries[i]
      local pMinor = minorPlayers[ entry.civType ]              -- 键 = 字符串 Type → 恒 nil
      local bAllies = pMinor ~= nil and iMajor >= 0 and pMinor:IsAllies( iMajor )  -- 恒 false
      local bFriends = pMinor ~= nil and iMajor >= 0 and pMinor:IsFriends( iMajor ) -- 恒 false
      csuaAddRow( entry, entry.ally, "TXT_KEY_CSUA_UI_ALLY", bAllies )
      if not bAllies then
          csuaAddRow( entry, entry.friend, "TXT_KEY_CSUA_UI_FRIEND", bFriends )
      end
  end
  ```
  佐证：`CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.cpp:7288` `lGetMinorCivType` → `lua_pushinteger`，返回的是 MinorCivTypes 整数；同仓库其它 SP UI（如 `CityStateStatusHelper.lua:59`、`CityBannerManager.lua:782`）均以它作 `GameInfo.MinorCivilizations[...]` 的**整数 ID** 下标，可反证其类型。
- **失效场景**：玩家与某城邦结盟后打开该城邦提供加成（如 CSUA `BuildingClassYieldModifiers`）的建筑 tooltip：
  - `bAllies` 恒为 false → 生效的盟友档仍被渲染成 `[COLOR_CYAN]<城邦名>盟友[ENDCOLOR]: +X%...` 的"来源标注"形态（本应"生效档不标来源"）；
  - 同时 `if not bAllies` 恒成立 → 盟友还会额外看到一条**朋友档**行，等于把两份档位文本一起展示，指示玩家当前处于更低的档位。
  - 具体输入：玩家与 Monaco 结盟 → 本该只显示 `[ICON_BULLET]+20%...`，实际显示 `[ICON_BULLET][COLOR_CYAN]摩纳哥盟友[ENDCOLOR]: +20%...` 以及 `[ICON_BULLET][COLOR_CYAN]摩纳哥朋友[ENDCOLOR]: +10%...`。
- **建议修复**：把 `minorPlayers` 改用城邦 Type 字符串作键（与 SQL 的 `m.Type` 一致），或读取时按 ID 查：
  ```lua
  -- 方案一（推荐）：写入时用 Type 字符串
  local kMinor = GameInfo.MinorCivilizations[ pPlayer:GetMinorCivType() ]
  if kMinor ~= nil then
      minorPlayers[ kMinor.Type ] = pPlayer
  end
  ```

### [A-2] 【中】EnemyUnitPanel：Milan CSUA 减伤占比直接 `/100` 未取整，战斗预览与血条出现小数伤害

- **文件**：`Super Power - Remaking of World Order (v 7)/UI/InGame/WorldView/EnemyUnitPanel.lua:462`、`:1181`、`:1185`、`:2869`
- **维度**：A（显示值口径与 DLL 不一致；且同文件内 Tyre 分支已明确用 `math.floor`）
- **证据**：
  ```lua
  -- 462（我 vs 城）：iTheirDamageInflicted 随后在 :541 SetText 显示、并传入 DoUpdateHealthBars(:489)
  local iMilanUnitScale = pMyUnit:GetCSUADamageTakenScale(nil, pCity)
  if iMilanUnitScale ~= 100 then
      iTheirDamageInflicted = iTheirDamageInflicted * iMilanUnitScale / 100   -- 无 floor
  end
  -- 1181 / 1185（单位 vs 单位）
  iMyDamageInflicted    = iMyDamageInflicted    * iTheirScale / 100
  iTheirDamageInflicted = iTheirDamageInflicted * iMyScale    / 100
  -- 2869（城 vs 单位）
  myCityDamageInflicted = myCityDamageInflicted * iMilanCityAttackerScale / 100
  ```
  对比同文件 Tyre 分支（`:438-441`）刻意使用了 `math.floor(... )`，并在注释中写明"Lua 的 `/` 是浮点除法，会把小数伤害泄漏进显示数值与血条预览"。Milan 分支未照做，属同文件内自相矛盾。
  佐证：DLL `CvUnit::GetCSUADamageTakenScale`（`CvUnit.cpp:19912`）以 `iScale = iScale * (100 - percent) / 100` 的**整数**除法返回，真实结算必为整数。
- **失效场景**：己方单位对城造成 30 点、Milan 缩放到 85 → 预览显示 `25.5`（`Controls.TheirDamageValue` 红色数字），血条按 25.5 绘制；真实结果为 25。非 100/50/20/10 之类的整除比例都会出现小数。
- **建议修复**：与 Tyre 分支统一取整：
  ```lua
  iTheirDamageInflicted = math.floor(iTheirDamageInflicted * iMilanUnitScale / 100)
  ```
  （若 `iMilanUnitScale` 可大于 100 可能产生负数语义，但 C++ 侧 iScale 只减不增，实际不会大于 100。）

---

## 二、提示（不构成缺陷，供决策）

1. **提示**：`TradeRouteHelpers.lua:186`（自 `_sp_s2.diff:2764`）`local iExtraX100 = iTotalX100 - iAfterModX100` 可能为负，被当作"额外收益"展示为负数；且 `iPctSum = iDomainMod + iRiverMod + iCSUAMod` 只覆盖 3 项百分比来源，其余大量修正（政策/信条/特性/建筑…）都被并入"Extra"一项。是否可接受取决于设计意图，**不确定**，故列为提示。`iAfterModX100` 另有 `math.max(100, ...)` 下限，当 `iBaseTotal` 很小时该下限会把差值外推为负，建议实测一个低基础值路线确认。
2. **提示**：`InGame.lua:93` 调试热键分支里第一处 `pPlot:ChangeVisibilityCount(team, -1, -1, true, true)` 仍是直接调用（本次 diff 的上下文行，未修改），而相邻的 `SetRevealed`/`ChangeVisibilityCount` 已改为广播。属**存量**代码，按纪律不列为缺陷；若有意统一联机口径可一并包装。
3. **提示**：新建 `ResourceTooltipGenerator.lua:96` `pYieldInfo = GameInfo.Yields[row.YieldType]` 后直接取 `pYieldInfo.IconString`（`:112`），未判空。`row.YieldType` 来自 `Resource_YieldChanges`，正常均合法，实际不可达；仅健壮性提示。

---

## 三、已核查确认无误项

1. **维度 C（联机）本域无真·不同步**。逐条核查了本域全部新增/修改的写操作调用点，均属下列两类之一：
   - **已改为 `SendAndExecuteLuaFunction` 广播**（且参数与静态签名匹配）：
     - `CityView/CityView.lua:2969/2981/2990/2991/2994`（`pCity.SetNumRealBuilding / SetPuppet / SetProductionAutomated / ChangeResistanceTurns`，函数引用形式）；
     - `PopupsGeneric/AnnexCityPopup.lua:24-25`（`newCity.SetPuppet / SetProductionAutomated`）；
     - `Popups/TradeRouteOverview.lua:443`（`pUnit.EndTrader`）；
     - `PlotName/PlotNamePopup.lua:115/120`（`"CvLuaGame::lSetPlotName" / "lRemovePlotName"`，经核 `CvLuaGame.cpp:76/78` 均为 `REGIST_STATIC_FUNCTION`）；
     - `InGame.lua:97/99/101`（`pPlot.SetRevealed / ChangeVisibilityCount`）；
     - `Popups/CityStateDiploPopup.lua:921`（`"CvLuaPlayer::lTryBuyFoodFromVenice"`，签名 `(iFood,iGold)` 匹配 `CvLuaPlayer.cpp:8043`）；
     - `CityStateDiploPopup.lua:1307/1321/1335/1347`（四个 `"CvLuaGame::lDoMinorFaithGiftFromMajor"`，经核为 `REGIST_STATIC_FUNCTION`）；
     - `ChooseBeliefPopup.lua:868/872`（`"CvLuaGame::lDoCityStateFaithPantheonPurchaseFromMajor"` / `lDoCityStateFaithBeliefPurchaseFromMajor`，均为 `REGIST_STATIC_FUNCTION`，且显式传入 `Game.GetActivePlayer()` 作为 eMajor）；
     - `OverviewAddendum/DiploCityStatesStatus.lua:2441`（`pCs:SendAndExecuteLuaFunction("CvLuaPlayer::lSetEconomicAidAutoRenew", iPlayer, bNew)`，参数与原 `SetEconomicAidAutoRenew(iPlayer,bNew)` 匹配，`pCs` 即城邦侧 Player）。
   - **虽是直接调用，但 DLL 内部已走网络通道**：
     - `CityStateDiploPopup.lua:997`（`Game.DoMinorEconomicAid(iActivePlayer, g_iMinorCivID, false)`，撤销经济援助）与未改动的 `:791`（发起经济援助）：`CvLuaGame::lDoMinorEconomicAid`（`CvLuaGame.cpp:2085`）内部转 `CvGame::DoFromUIDiploEvent(...)` → `gDLL->sendFromUIDiploEvent(...)`，即主客机一致的权威命令，**非**本地直改。属"改写方法位置"而非新引入风险。
     - `TradeLogic.lua:4179`（`Game.DoDiplomacyBargain(g_iThem)`）：`CvLuaGame::lDoDiplomacyBargain`（`CvLuaGame.cpp:1358`）同样转 `DoFromUIDiploEvent(FROM_UI_DIPLO_EVENT_HUMAN_DIPLOMACY_BARGAIN,...)` 网络通道；RNG 在宿主权威 handler 内消费，注释所述"multiplayer-safe"成立。
   - **UI 只读显示**（无需广播）：`EnemyUnitPanel.lua` 全部新增 CSUA 战斗预览、`CultureOverview.lua` 移民表/文化进度、`TradeRouteHelpers.lua`、`TopPanel.lua`、`ResourceTooltipGenerator.lua`、`EspionageOverview.lua` 间谍点表、`InfoTooltipInclude.lua`、`CivilopediaScreen.lua`、`DiploCorner.lua`、`DiploCityStatesStatus.lua` 勾选回读等。
2. **RNG 分叉风险核查**：本域 UI 未调用任何会消耗随机数的 getter。特别核查：
   - `CityStateDiploPopup.lua` 的 Monaco 赌金状态文本使用 `pMinor:GetMinorCivGoldGambleUsedThisTurn / GetMinorCivGoldGambleLastMultiplier`（结果态 getter），**未**触碰共享背景标记的 RNG getter `GetCSUAGoldDonationGambleMultiplier()`；全 UI 目录 grep 无 `GambleMultiplier`/`getJonRand`。
   - `EnemyUnitPanel.lua` 新增调用的 `GetCSUAFixedDamageScale / GetCSUADamageTakenScale / GetCSUADamageReductionPercent / GetCSUACombatModifier / GetCSACityAttackIgnoreBuildingDefensePercent / GetCSAWoundedFixedDamage` 经源码确认均为纯计算，无 `getJonRandNum`。
   - `TradeLogic.lua` 的 `GetDiplomacyBargainChance`（`CvEspionageClasses.cpp:3041`）为常量映射；`GetDiplomatTradeAdvice` → `IsDealWithHumanAcceptable` 经确认无 RNG。
3. **维度 B（溢出/崩溃）**：
   - `CultureOverview.lua:2078/2080` 对 `iImmigrationRegressand` 的除法有上游守卫 `if pPlayer ~= activePlayer and iImmigrationRegressand > 0 then`（`:2053`），**无除零**；`iImmigrationTurnsLeft` 的两个除法分别由 `ImmigrationRate > 0 / < 0` 守卫。
   - `EspionageOverview.lua` `RefreshSpyPointsMeter` 的 `iProgress / iThreshold` 有 `iThreshold > 0` 守卫。
   - `TradeRouteHelpers.lua` 对 `GetInternationalTradeRouteBaseValueDetail` 接 12 个返回值，与 Lua 封装 `CvLuaPlayer.cpp:4454`（push 12 个）**数量一致**，无 nil 算术。
   - `InfoTooltipInclude.lua` 新 CSUA 缓存刻意用 `DB.Query`（绕开该文件被 EUI `GameInfoCache` 遮蔽导致的"迭代后 `[key]` 失效"陷阱，见 `[[info-tooltip-gameinfocache-pitfall]]`），且 `pcall` 包裹、`YieldIcons` 已于 `:229` 定义，未见空值解引用。
   - `ChooseBeliefPopup.lua` `RefreshList` 中 `params.Mode` 仅在 `ShowHideHandler` 的 `params ~= nil` 分支内被调用；`SelectBelief` 的 `GameInfo.Beliefs[beliefID]` 使用的是**未遮蔽的全局 GameInfo**（该文件不遮蔽），`()` 迭代后再 `[key]` 索引安全。未见崩溃路径。
4. **其它**：`CityBannerManager.lua:1663-1691` 新增的 `RefreshCityStatePrestigeOnAllyChange` 同时挂 `Events.MinorAlliesChanged` 与 `GameEvents.MinorAlliesChanged`，为幂等的只读刷新，重复触发无害。`DiploCorner.lua`（新文件）`OnEndGameButton` 的 `math.random` 为本地调试按钮，使用 Lua 随机数而非 `Game.Rand`，不影响游戏状态流。
