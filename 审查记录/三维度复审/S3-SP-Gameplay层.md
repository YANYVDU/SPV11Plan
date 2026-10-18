# S3 SP 的 Gameplay 层（Lua/SQL/XML）+ 本地化 三维度复审报告

- 审查范围：`git diff a7c2416..HEAD -- "Super Power - Remaking of World Order (v 7)/Gameplay/"`（排除 `XML/CSUA/`），另含 `.civ5proj`
- 审查日期：2026-10-02
- 结论：应修正 3 项 / 提示 3 项 / 确认无误 12 项

---

## 一、应修正（会导致实际缺陷）

### [B-1] 【严重】卫星发射效果路径引用了「后声明的 local 函数」，运行时求值为 nil，卫星全局效果全部失效且单位不被消耗

- **文件**：`Super Power - Remaking of World Order (v 7)/Gameplay/Lua/Utility/UtilityFunctions.lua:165` 与 `:212`（定义见 `:226` / `:330`）
- **维度**：B（Lua 运行时错误，中断事件处理器；非 CTD）
- **证据**：

```lua
124: local function SatelliteLaunchEffects_Base(unit, city, player)
     ...
165:     SatelliteEffectsGlobal_Base(unit);      -- 该 local 在 226 行才声明

171: local function SatelliteLaunchEffects_MP(unit, city, player)
     ...
212:     SatelliteEffectsGlobal_MP(unit);        -- 该 local 在 330 行才声明

226: local function SatelliteEffectsGlobal_Base(unit)
330: local function SatelliteEffectsGlobal_MP(unit)
```

本次 diff 把原来的**全局** `SatelliteEffectsGlobal(unit)` 调用改成了 `SatelliteEffectsGlobal_Base(unit)`（见 diff 行 `-	SatelliteEffectsGlobal(unit);` / `+	SatelliteEffectsGlobal_Base(unit);`）。被调用的名字在同文件里是**后置声明的 `local function`**，Lua 词法作用域不向前可见，因此 165/212 行的引用在编译期被解析为**全局访问**；而 `local function` 只创建局部、从不写全局，故 `_G.SatelliteEffectsGlobal_Base` / `_G.SatelliteEffectsGlobal_MP` 恒为 `nil`。

我程序化扫描了本域全部 7 个 Lua 文件的 `local function` 前向引用，**仅此两处**命中（其余 `_Base/_MP` 配对均为先声明后引用，正常）。

- **失效场景**：任何卫星单位发射时（单机走 `_Base`，联机走 `_MP`），函数先把卫星建筑写入城市，随后在 165/212 行执行 `SatelliteEffectsGlobal_Base(unit)` → `attempt to call a nil value (global 'SatelliteEffectsGlobal_Base')`。调用方 `SatelliteLaunchingButton.Action` 中紧随其后的 `unit:SendAndExecuteLuaFunction(unit.Kill)` 与 AI 路径 `NewUnitsRules.lua` 的 `unit:Kill()` 都不再执行：
  - 天气/环境/反辐射/GPS/阿波罗/哈勃/天宫等**全球效果全部不生效**；
  - 发射单位**不被消耗**，可重复发射并重复叠加建筑。
  单机与联机均稳定复现。

- **建议修复**：在文件靠前（例如 124 行之前）加前向声明，或把 `_Base/_MP` 定义移到调用者之前：
  ```lua
  local SatelliteEffectsGlobal_Base
  local SatelliteEffectsGlobal_MP
  ```
  （或在 124 行前先声明再赋值）。

### [B-2] 【中】`AICanBeBoss` 删除了 `player:GetCapitalCity() ~= nil` 判空，AI 无首都时对 nil 取 `GetX()` 报错

- **文件**：`Super Power - Remaking of World Order (v 7)/Gameplay/Lua/Utility/UtilityFunctions.lua:56-57`
- **维度**：B（空值解引用）
- **证据**（diff，原代码对该 AI 的首都也做了判空，本次删除）：

```lua
-	if Players[Game.GetActivePlayer()] ~= nil and Players[Game.GetActivePlayer()]:GetCapitalCity() ~= nil and player:GetCapitalCity() ~= nil then
+			if (pPlayer:GetCapitalCity()) then
+				local HumanCapital  = pPlayer:GetCapitalCity()
+				local ThisAICapital = player:GetCapitalCity()          -- 未再判空
+				CapitalDistance = CapitalDistance + Map.PlotDistance(HumanCapital:GetX(), HumanCapital:GetY(), ThisAICapital:GetX(), ThisAICapital:GetY())
```

原版游戏 Lua 多处显式写作 `GetCapitalCity() ~= nil`（如 `Assets/DLC/DLC_07/.../TurnsRemaining.lua:516,1527`），说明该返回值确实可能为 nil。

- **失效场景**：`GetCapitalCity()` 返回 nil 的 AI（原首都已被占领等）被求值时，`ThisAICapital:GetX()` 触发 `attempt to index a nil value`。调用点包括 `NewHandicap.lua:425,439,455,792`（其中 455 行的 `NewPlayer`、792 行由 `AINeedEscortUnit` 透传的任意玩家均未被上层以「有首都」为前提守卫）。
- **建议修复**：恢复判空，例如
  ```lua
  local ThisAICapital = player:GetCapitalCity()
  if ThisAICapital ~= nil then
      CapitalDistance = CapitalDistance + Map.PlotDistance(HumanCapital:GetX(), HumanCapital:GetY(), ThisAICapital:GetX(), ThisAICapital:GetY())
  end
  ```

### [A-1] 【低】本月新增三语文本使用了未定义图标 `[ICON_GREAT_WORK_ART]`，会原样显示为标签

- **文件**（当前行号）：
  - `Gameplay/XML/Localization/TextInfos_en_US.xml:19409, 19420`
  - `Gameplay/XML/Localization/TextInfos_zh_CN.xml:17878, 17889`
  - `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml:17684, 17695`
- **维度**：文本/本地化（共享文档第三节明确要求报 ICON 拼写错误）
- **证据**：

```
[NEWLINE][ICON_BULLET]Each [ICON_GREAT_WORK_ART]Great Work or Artifact owned grants +2% [ICON_PEACE]Faith empire-wide
```

校验方式：从 `Assets/Gameplay/XML/GameInfo/CIV5IconFontMapping*.xml` + `Assets/DLC/*/Gameplay/XML/GameInfo/CIV5IconFontMapping*.xml` + 两仓库全部含 `<IconName>` 的 XML 汇总全部已定义图标名，逐一比对本月新增文本里出现的 38 种 `[ICON_*]`，**仅 `ICON_GREAT_WORK_ART` 无定义**（映射表只定义了 `ICON_GREAT_WORK`）。基线（a7c2416）三语文件中该 token 出现次数均为 0，确为本月新增。
- **失效场景**：相关城邦 UA 提示框内该处显示为字面量 `[ICON_GREAT_WORK_ART]`，破坏排版。三语同错。
- **建议修复**：三语文件各改为 `[ICON_GREAT_WORK]`。

---

## 二、提示（不构成缺陷，供决策）

### [提示-1] `Building_DomainEnemyCombatModifierPerGold` 的 -10 在 C++ 侧无下界，城邦国库 >1000 金时敌方战斗力归零、>2000 时翻负（跨域，建议交 S2 定夺）

- **文件**：`Gameplay/SQL/Buildings/BuildingEffect.sql:66-69`
- **证据**：SP 注入
  ```sql
  insert into Building_DomainEnemyCombatModifierPerGold (BuildingType, DomainType, Modifier)
  values ('BUILDING_CITYSTATE_RESOURCE', 'DOMAIN_LAND', -10), ('...','DOMAIN_SEA',-10), ('...','DOMAIN_AIR',-10);
  ```
  MPDLL `CvUnit.cpp:19786` 消费：`iModifier += iPerGold * (iGold / 100);`（`iPerGold=-10` ⇒ `iModifier = -gold/10`）。战斗修正按 `(100 + iModifier)/100` 使用，`gold≥1000` 即 -100%（战斗力归零），`gold>2000` 转负。
- **说明**：负号方向本身符合「敌方在城邦境内变弱」的设计意图；我**不确定**设计是否要求这一比例无上限（未在 `1.城邦UA/*.txt` 中核实对应条目）。C++ 侧的钳制属 S2 域。若设计确有上限，请在 C++ 对 `iModifier` 加下界（如 `std::max(iModifier, -50)`）。

### [提示-2] `DLL_Options.xml` 中 `SP_RELIGION_PRESSURE_SELF_FOUNDER_MOD` 对应的 CustomModOptions 行在 MPDLL 不存在 → 该 `<Update>` 静默无效

- **文件**：`Gameplay/XML/DLL_Options.xml:422`
- **证据**：全 MPDLL 仓库仅 `CvGameCoreDLL_Expansion2/CvReligionClasses.cpp:403,407` 以 `gCustomMods.getOption("SP_RELIGION_PRESSURE_SELF_FOUNDER_MOD", 33)` 引用该名，**未在 `CustomModOptions.xml` 声明任何行**（对比同批的 `SP_FAITH_BELIEF_PURCHASE_COST`、`SP_PANTHEON_BELIEF_PURCHASE_BASE_COST` 均已在 `CustomModOptions.xml:1203,1205` 声明）。
- **影响**：SP 的 `<Update><Where Name=...></Update>` 匹配 0 行，静默失效；由于代码默认值恰为 33、SP 也设 33，**当前无功能差异**。建议在 MPDLL 补声明该选项名，以免日后调值时误以为已生效。

### [提示-3] `UnitSpecialButtons.lua` 中 TokyoRaid 新增了一条原本被注释的 `PROMOTION_CARRIER_UNIT` 移除，属行为变更

- **文件**：`Gameplay/Lua/Misc/UnitSpecialButtons.lua:1435`
- **证据**：本月 diff 由注释行 `-- NewUnit:SetHasPromotion(...PROMOTION_CARRIER_UNIT..., false)` 变为**激活**的 `NewUnit:SendAndExecuteLuaFunction("CvLuaUnit::lSetHasPromotion", GameInfo.UnitPromotions["PROMOTION_CARRIER_UNIT"].ID, false)`，而原 `PROMOTION_NO_LUCK` 添加保持注释并存。
- **说明**：不确定这是本次「单机联机统一/移植」时的有意修正还是误将注释取消。若「东京急袭」按设计应保留载体属性，则应改回注释；请对照设计稿确认。

---

## 三、已核查确认无误项（列出我查了但没问题的，防止重复劳动）

1. **本地化三语完备性（高价值项）**：以「当前三语文件 Tag 集 − 基线 a7c2416 Tag 集」提取本月新增 Tag，三文件各得 **239 个**，且**三集合完全相等、无任何缺失**（程序化对称差为 0）。`SP_CivilopediaExtra.sql`（36 个 `TXT_KEY_PEDIA_EXTRA_*`）与 Everest Camp 的 3 个 Tag 亦三语齐全。
2. **本月新增 `SendAndExecuteLuaFunction` 方法名有效性**：提取域内全部 53 个被调方法名（含 `lChangeNumEstablishCorps`、`lSetMaxHitPointsChangeFromRazedCityPop`、`lSetCombatStrengthChangeFromKilledUnits`、`lSetRangedCombatStrengthChangeFromKilledUnits`、`lChangeNumArmeeTotalTimes100`、`lChangeNumCropsTotalTimes100`、`lClearSamePlotPromotions`、`lSetIsBatchMark`、`lChangeNumExoticGoods` 等生僻项），逐一在 MPDLL `Lua/CvLua*.cpp` 找到定义**且**在方法表（`Method(...)` / `REGIST_STATIC_FUNCTION(...)`）中注册 —— **无静默失效**。
3. **`Game.Rand` → `math.random` 改动是联机确定性修复，非缺陷**：`UnitSpecialButtons.lua` LuckyEButton（diff 行 789）与 `UnitSpecialButtons_SP8.lua` SacrificeMissionButton（diff 行 953）把本地 RNG 从 `Game.Rand` 改为 `math.random`；由于按钮只在行动端触发、判定结果随后通过 `SendAndExecuteLuaFunction` 广播（`lSetHasPromotion` / `lKill`），其他客户端不消耗该随机数 → 不再推进全局 RNG 流，正确。新增行中已无 `Game.Rand`/`GetRandNum` 残留（仅注释）。
4. **AI 路径与人类按钮的广播分派正确**：`SatelliteLaunchEffects`/`SatelliteEffectsGlobal`/`RemoveConflictFeatures`/`ImproveTiles`/`CarrierRestore` 均改为 `if bBroadcast and Game.IsGameMultiPlayer() then _MP else _Base`；`NewUnitsRules.lua` 与 `NewHandicap.lua` 的 AI 调用传 `false`（AI 由各客户端确定性模拟，本地执行正确），`UnitSpecialButtons.lua` 的人类按钮调用传 `true`（广播）。符合共享文档「仅状态修改需广播」的口径。
5. **`CarrierRestore` 删除全部 `LoadUnit` 调用不会导致死循环**（曾疑为漏改，已排除）：`while not pUnit:IsFull() do InitUnit(...) end` 依赖新单位被装载进航母才终止。核对 MPDLL：`CvPlayer::initUnit → CvUnit::initWithNameOffset` 在 `CvUnit.cpp:680` 调用 `setXY(...)`，`setXY` 在 `CvUnit.cpp:21429` 对 `shouldLoadOnMove(pNewPlot)==true` 时执行 `load()`；`shouldLoadOnMove`（`CvUnit.cpp:5453-5457`）对 `DOMAIN_AIR` 在非己方城市地块返回 `true`，而本函数已提前排除「航母在城市内」。故 `InitUnit` 会经 `setXY→load()` **自动装载**到航母，`IsFull()` 能变为真，循环正常终止。`_Base`(1055-1060) 与 `_MP`(1183-1187) 同理。
6. **`NewCityRule.lua` 删除的移民 Lua 模拟干净**：`InternationalImmigration`/`DoInternationalImmigration` 已整体移除（改由 C++ `CvPlayer::DoImmigration`，经 `DLL_Options.xml` 启用 `EVENTS_INTERNATIONAL_IMMIGRATION`，MPDLL `CustomModOptions.xml:1141` 已声明）。全仓无残留 Lua 调用（`CultureOverview.lua` 命中项均为本地变量名/TextKey，非函数调用）。
7. **`.civ5proj` 登记完整、无文件被误删**：本月新增的 `CSUA_RefreshOnLoad.lua`(VFS=True)、`SP_CivilopediaExtra.sql`、`SP_SpyPoints.sql`、`HappinessDecayEra.sql` 均已登记为 `OnModActivated/UpdateDatabase`；proj diff 仅新增、无删除；`SPInit.lua` 已 `include("CSUA_RefreshOnLoad")`。
8. **DLL_Options 其余新选项与 MPDLL 匹配**：`EVENTS_INTERNATIONAL_IMMIGRATION`(Class3)、`LUXURY_ERA_DECAY`(Class6)、`SP_FAITH_BELIEF_PURCHASE_COST`(Class5,2500)、`SP_PANTHEON_BELIEF_PURCHASE_BASE_COST`(Class5,500) 均在 MPDLL `CustomModOptions.xml` 有声明且被 `getOption(...)` 读取。
9. **GlobalDefines/Defines 名称匹配**：`MINOR_FRIENDSHIP_ANCHOR_MOD_ECONOMIC_AID`（`GlobalDefines.xml`）对应 MPDLL `CvGlobals.cpp:6173` 的 `getDefineINT`；`SPY_POINTS_THRESHOLD_BASE/INCREASE`（`SP_SpyPoints.sql`）对应 `CvGlobals.cpp:6242-6243`，默认 0→100/50 修复有效。
10. **`SP_SpyPoints.sql` 表定义无隐患**：`ALTER TABLE Buildings/Policies/Beliefs/Traits ADD COLUMN SpyPoints integer default 0`（默认 0，非负）；MPDLL 侧 `CvBuildingClasses.cpp:5399,5623`、`CvBeliefClasses.cpp` 等按此读取并 `ChangeSpyPointsPerTurn`。MPDLL 未自带该列 SQL，无重复建列冲突。
11. **`HappinessDecayEra.sql` 语义正确**：列由 MPDLL `(1) CIV5MPDLL/DB/RESOURCES/HappinessDecayEra.sql` 定义为 `text references Eras(Type)`，MPDLL `CvInfos.cpp:4953` 以 `GetText` 读为 `EraTypes`；SP 只做 `UPDATE ... = 'ERA_XXX'/NULL`，取值合法。
12. **Everest Camp 数值一致**：`Buildings.xml` 的 `Building_YieldModifiers`（YIELD_GOLD 50、YIELD_TOURISM 50，即 +50%）与三语 `TXT_KEY_BUILDING_EVEREST_CAMP_HELP`（" +50% Gold and +50% Tourism"）及 Kathmandu UA 文本一致；`Mountain=true` 对应「adjacent to a Mountain」；`PrereqEffect=EFFECT_CSUA_KATHMANDU_ALLY`。`Units_Civilian.xml`/`Units_Elite.xml` 新增的 `NumInfluencePerEra`（40/40/10）在 MPDLL `CvUnitClasses.cpp:263` 有对应读取列，无静默失效。
13. **`CSUA_RefreshOnLoad.lua` 不构成联机不同步**：`Events.LoadScreenClose` 各客户端各触发一次，对全体 major 玩家执行 `RefreshCSAlliesFriends()`。该调用是**从共享确定性状态重建**（CSUA 状态本就不序列化、每回合重建），各机结果一致，无需广播。
14. **`AICanBeBoss` 的多人化改造主体正确**：改为遍历所有存活人类玩家首都求平均（替代单一 `Game.GetActivePlayer()`），符合 `[[mp-broadcast-activeplayer-param]]` 精神；存在问题仅为上述 [B-2] 的判空缺失。
