# M4 其余 C++ 与 Lua 接口 三维度复审报告

- 审查范围：`git diff c354808..HEAD`（MPDLL 仓库 `d:\Git\CIV5\dyy\CIV5MPDLL`，排除 CvPlayer.* / CvCity.* / CvUnit.* / CvMinorCivAI.* / CvCityStateUAClasses.*，那些属其他代理）
  实际覆盖：`CvGame.cpp/h`、`CvDiplomacyAI.cpp`、`CvDealClasses.cpp`、`CvDealAI.cpp`、`CvEspionageClasses.cpp/h`、`CvTraitClasses.cpp/h`、`CvReligionClasses.cpp/h`、`CvTreasury.cpp`、`CvUnitCombat.cpp/h`、`CvUnitMovement.cpp`、`CvTechClasses.cpp`、`CvTradeClasses.cpp/h`、`CvGlobals.cpp/h`、`CvInfos.cpp/h`、`CvPolicyClasses.cpp/h`、`CvUnitClasses.cpp/h`、`CvBuildingClasses.cpp/h`、`CvPlot.cpp`、`CvAStar.cpp`、`CvTacticalAnalysisMap.cpp`、`CvTeam.cpp`、`CvVotingClasses.cpp`、`CvCultureClasses.cpp`、`CvPlayerAI.cpp`、`CvEconomicAI.cpp`、`CvWorldBuilderMapLoader.cpp`、`CvDllDatabaseUtility.cpp`、`Lua/CvLuaPlayer.cpp/h`、`Lua/CvLuaGame.cpp/h`、`Lua/CvLuaCity.cpp/h`、`Lua/CvLuaUnit.cpp/h`、`(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql`、`(1) CIV5MPDLL/CustomModOptions.xml`
- 审查日期：2026-10-02
- 结论：应修正 2 项 / 提示 6 项 / 确认无误 13 项

---

## 一、应修正（会导致实际缺陷）

### [B-1] 【中】本周期新增的 3 个 CvLuaPlayer 导出把对象自身当作用户第 1 参数，参数整体错位一格

- **文件**：`CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.cpp:8022`（`lIsEconomicAidAutoRenew`）、`8033-8034`（`lSetEconomicAidAutoRenew`）、`8046-8047`（`lTryBuyFoodFromVenice`）
- **维度**：B（Lua ↔ C++ 边界强制转换）/ C（联机广播参数错位）
- **证据**：

  ```cpp
  // CvLuaPlayer.cpp:8019  —— 这段是本次 diff 新增
  int CvLuaPlayer::lIsEconomicAidAutoRenew(lua_State* L)
  {
      CvPlayerAI* pkPlayer = GetInstance(L);   // 索引 1 = self（Player 对象）
      const int eMajor = lua_tointeger(L, 1);  // ← 应为 2
      ...
  }
  // CvLuaPlayer.cpp:8030
  int CvLuaPlayer::lSetEconomicAidAutoRenew(lua_State* L)
  {
      CvPlayerAI* pkPlayer = GetInstance(L);
      const int eMajor = lua_tointeger(L, 1);  // ← 应为 2
      const bool bRenew = lua_toboolean(L, 2); // ← 应为 3
      ...
  }
  // CvLuaPlayer.cpp:8043
  int CvLuaPlayer::lTryBuyFoodFromVenice(lua_State* L)
  {
      CvPlayerAI* pkPlayer = GetInstance(L);
      const int iFood = lua_tointeger(L, 1);   // ← 应为 2
      const int iGold = lua_tointeger(L, 2);   // ← 应为 3
      ...
  }
  ```

  参数约定（实例对象占索引 1，用户参数从索引 2 起）由框架代码确定：

  - `Lua/CvLuaScopedInstance.h:32` `GetInstance(lua_State* L, int idx = 1, ...)`；
  - `Lua/CvLuaScopedInstance.h:171` `GetStartingArgIndex() { return 2; }`；
  - `Lua/CvLuaScopedInstance.h:186` 实例版广播 `ProcessLuaArgForReflection(L, 2)`：索引 1 = self、索引 2 = 函数名字符串、用户参数从索引 3 起；
  - `NetworkMessageUtil.cpp:24` 序列化循环 `for (int i = 1; i <= num; i++)` 会把**索引 1（self）也序列化成第 0 个参数**，接收端按同一顺序压栈，故被调函数看到的仍是 `[self, 用户参数1, 用户参数2]`；
  - 同文件既有同类函数均从索引 2 取第一个用户参数，例如 `CvLuaPlayer.cpp:7470` `lInitUnit` 的 `lua_tointeger(L, 2)`；本次新增 514 行中 `lua_tointeger(L, 1)` 仅出现 3 次（即上述 3 处），另有 334 处用索引 2。

  调用点（SP 仓库）：

  ```lua
  -- DiploCityStatesStatus.lua:189
  local bAidAutoRenew = pCs:IsEconomicAidAutoRenew(iPlayer)      -- self=pCs, iPlayer 在索引 2
  -- DiploCityStatesStatus.lua:195
  pCs:SendAndExecuteLuaFunction("CvLuaPlayer::lSetEconomicAidAutoRenew", iPlayer, bNew)
  -- CityStateDiploPopup.lua:922
  pActivePlayer:SendAndExecuteLuaFunction("CvLuaPlayer::lTryBuyFoodFromVenice", iFood, iGoldToPay)
  ```

  `lua_tointeger` 作用于 Player 表（userdata/table 无 `__tonumber`）恒返回 0。

- **失效场景**：

  1. `pCs:IsEconomicAidAutoRenew(iPlayer)` 实际执行 `IsEconomicAidAutoRenew(0)` —— 无论玩家选谁，UI 勾选态永远是"该城邦对 0 号大国的自动续约状态"，与真实状态不符。
  2. `pCs:SendAndExecuteLuaFunction("...lSetEconomicAidAutoRenew", iPlayer, bNew)` 实际执行 `SetEconomicAidAutoRenew(0, (iPlayer != 0))`：`bNew`（索引 3）被忽略，写的是 0 号大国的记录，且 `bRenew` 几乎恒为 true。所有客户端一致地错（不构成不同步），但玩家的自动续约开关完全失效，并污染 0 号大国状态。
  3. `pActivePlayer:SendAndExecuteLuaFunction("...lTryBuyFoodFromVenice", iFood, iGoldToPay)` 实际执行 `TryBuyFoodFromVenice(0, iFood)`。以 `iFood = GrowthThreshold()*rate/100 = 200`、`iGoldToPay = 200*2 = 400` 为例（`CityStateDiploPopup.lua:915-917`），实际扣 **200 金**、加 **0 粮**、并消耗本回合冷却（`CvPlayer.cpp:17278-17284`），而 UI 仍弹出"+200 食物"的通知 —— 玩家花金买不到粮。

- **建议修复**（三处统一后移一位）：

  ```cpp
  const int eMajor = lua_tointeger(L, 2);            // lIsEconomicAidAutoRenew
  const int eMajor = lua_tointeger(L, 2);            // lSetEconomicAidAutoRenew
  const bool bRenew = lua_toboolean(L, 3);           // lSetEconomicAidAutoRenew
  const int iFood = lua_tointeger(L, 2);             // lTryBuyFoodFromVenice
  const int iGold = lua_tointeger(L, 3);             // lTryBuyFoodFromVenice
  ```

---

### [B-2] 【中】外交议价通知标题是悬垂指针（临时 `Localization::String` 已析构）

- **文件**：`CvGameCoreDLL_Expansion2/CvDiplomacyAI.cpp:20018`（使用点 `20022`、`20026`）
- **维度**：B（空/悬垂指针）
- **证据**：

  ```cpp
  // CvDiplomacyAI.cpp:20017-20023
  CvNotifications* pkNotifications = GET_PLAYER(eFromPlayer).GetNotifications();
  const char* szBargainTitle = Localization::Lookup("TXT_KEY_DIPLO_BARGAIN_BUTTON").toUTF8();
  if(iBargainResult == 1)
  {
      pkNotifications->Add(NOTIFICATION_GENERIC,
          Localization::Lookup("TXT_KEY_DIPLO_BARGAIN_SUCCESS").toUTF8(),
          szBargainTitle, iNoticeX, iNoticeY, -1);   // ← 已越出临时对象生存期
  }
  ```

  `Localization::Lookup` 按值返回 `Localization::String`；`toUTF8()` 返回指向该对象自身缓冲区的裸指针。全仓库取用该 API 的规范写法都是先绑定具名变量再调 `toUTF8()`（`CvGameCoreDLL_Expansion2/CvGameCoreUtils.h:481-484` 等 6 处），本处是唯一一处对临时对象直接取指针并跨语句使用的地方。同一段代码里 `Add()` 的两个实参又各自新建了 `Localization::String`，极可能复用同一块堆内存。

- **失效场景**：每次外交议价判定后，通知标题读到已释放内容（表现为标题空白/乱码；堆布局不利时该块已被其他分配覆写，属未定义行为）。触发频率低（需要外交议价成功/失败结算）但稳定存在。
- **建议修复**：

  ```cpp
  Localization::String strBargainTitle = Localization::Lookup("TXT_KEY_DIPLO_BARGAIN_BUTTON");
  ...
  pkNotifications->Add(NOTIFICATION_GENERIC, Localization::Lookup("TXT_KEY_DIPLO_BARGAIN_SUCCESS").toUTF8(), strBargainTitle.toUTF8(), ...);
  ```

  参考：`CvDealClasses.cpp` 中同类通知用的是具名 `Localization::String strDemote`，写法正确。

---

## 二、提示（不构成缺陷，供决策）

1. **【低】`m_iSpyPoints` 插在序列化流中段，破坏"旧 DLL 读新存档"** —— `CvTraitClasses.cpp:5069`（Read）、`5607`（Write）：`MOD_SERIALIZE_READ(164, kStream, m_iSpyPoints, 0)` 被放在 `m_iExtraSpies` 与 `m_iUnresearchedTechBonusFromKills` 之间，而不是流尾。新版 DLL 读旧存档正常（版本门控给默认值），但旧版 DLL 读新版存档会从该点起整体错位。同函数内既有 `MOD_SERIALIZE_READ(78, ...)`（`CvTraitClasses.cpp:5063-5065`）也是中段插入，且 `CvReligionClasses.cpp:190` 的 `m_vExtraBeliefs` 同样插在 `m_Beliefs.Read()` 之前，故本项风险与既有风格一致、实际影响有限；但本周期其他新成员（CvDiplomacyAI 的 `m_paiCSUAPlunderedNeutralTradeRoute`、CvPlayerEspionage 的 per-target 数组、CvEspionageSpy 的 3 个 bool）都做成了流尾追加，建议统一改为流尾追加以满足 CLAUDE.md 的"旧版 DLL 加载新版存档"要求。

2. **【低】`ChooseCSUAPantheonBelief` / `ChooseCSUABelief` 空表时返回未初始化值** —— `CvReligionClasses.cpp:6473-6476`、`6522-6525`：`int iNumChoices = MIN(beliefChoices.size(), 3);` 未做非空判断。当所有万神殿信条都已被认领（`IsInSomeReligion` 过滤后为空）时，`CvWeightedVector::ChooseFromTopChoices(0, ...)` 会先吃掉一次 `getJonRandNum(0,...)` 随机数，遍历循环不执行，落到 `CvAssertMsg(false,...)`（Release 为空操作）并 `return elem.m_Element` —— `elem` 是未初始化的局部 `WeightedElement`，返回垃圾 `BeliefTypes`。调用方 `CvReligionClasses.cpp:6423` 只判 `== NO_BELIEF`，拦不住垃圾值，会带着非法信条进入 `DoCityStateFaithPantheonPurchase`。既有的 `ChoosePantheonBelief`（`CvReligionClasses.cpp:5380-5383`）是同样的写法，属沿用既有风格；`ChooseCSUABelief` 的过滤条件只有"本宗教未持有"，实际几乎不可能为空。可达性低，故列为提示。

3. **【低】`DoCityStateFaith*PurchaseFromMajor` 只对 `eMajor` 做运行期校验，`eMinor` 仅断言** —— `CvGame.cpp:210-211`、`2192-2197`（及 `DoMinorFaithGiftFromMajor` 的 `GET_PLAYER(eMinor)`）：`CvAssertMsg` 在 Release 下被编译掉，若 Lua 传入越界 `eMinor`（如 `params.MinorID` 为 nil → 0 以外的越界值会被 `lua_tointeger` 转成 0，实际安全；真正越界只可能来自脚本 bug）会直接越界索引。当前所有 SP 调用点都传合法 `params.MinorID`（`ChooseBeliefPopup.lua:183/187`、`CityStateDiploPopup.lua:1308+`），故仅作提示。同理 `GetCityStateFaithBeliefPurchaseCost/PantheonPurchaseCost/IsCityStateFaithBeliefPurchased`（`CvGame.cpp:226+`、`257+`、`270+`）亦无 `eMinor` 运行期校验。

4. **【低】`AnyPlayerHasZOCRangeBonus` 的函数级静态缓存仅按回合号失效，未考虑读档/新开档** —— `CvUnitMovement.cpp:325-357`：`static int s_iCachedTurn = -1; static bool s_bCached = false;` 只以 `GC.getGame().getGameTurn()` 变化作为失效条件。同一进程内先载入 A 存档（第 N 回合）再载入 B 存档（同第 N 回合，或新开档恰好同为第 N 回合）时，会沿用上一局的缓存值。该值只用于决定 ZOC 扫描窗口是 3x3 还是 5x5，且在任何客户端都确定性重算，故不构成不同步，仅在上述读档序列下可能一回合内 ZOC 判定偏差。注释已声明"中途外交变化允许滞后一回合"，与项目既有缓存滞后容忍约定一致。

5. **【低】队伍级开放边界 → 玩家级开放边界的语义变化（本域调用点）** —— 本周期把 `IsAllowsOpenBordersToTeam` 改为 `IsAllowsOpenBordersToPlayer`：`CvDealClasses.cpp:2625`、`2987`（成交时只对 `eAcceptedFromPlayer` 单个玩家写入）、`3693`（解约），`CvUnitMovement.cpp:128`、`CvEspionageClasses.cpp:6087/6092`、`CvCultureClasses.cpp:2996/3232/3316/3391/4811`、`CvPlot.cpp`、`CvAStar.cpp:1126`（有 `ePlotOwner != NO_PLAYER` 守卫）、`CvTacticalAnalysisMap.cpp`（有 `isOwned()` 守卫）、`CvWorldBuilderMapLoader.cpp:1171-1172`。这是本周期引入的有意设计（`CvPlayer::IsAllowsOpenBordersToPlayer` 在 `m_bPlayerOBsValid==false` 时回退到旧的队伍级规则，旧存档行为不变）。但在队伍局中，成交只给单个玩家登记 OB，其队友不再自动获得 OB —— 若设计意图是"整队开放边界"，需在成交处对全队成员循环写入。该语义最终由 CvPlayer 域（M2/M3）裁定，此处仅提示本域调用点已随之切换。

6. **【低】`lTryDiplomacyBargain` 导出未按项目约定标注联机风险** —— `Lua/CvLuaPlayer.cpp:13314`（裸 RNG 消费接口）：`pkPlayerEspionage->TryDiplomacyBargain(eTargetPlayer)` 内部消耗 `GC.getGame().getJonRandNum`，本地直调会造成主客机 RNG 分叉。同批次新增的 `ChangeTotalImmigrantsReceived/Emigrated` 已在 `.cpp` 注明"raw setters / mods must not call them"，本函数（及 `lIsEconomicAidAutoRenew` 等纯读接口无此问题）缺少同类英文风险注释。当前 SP 的唯一调用路径是 `Game.DoDiplomacyBargain(g_iThem)`（`TradeLogic.lua:1801`），走 `sendFromUIDiploEvent` 广播，行为正确，故仅是注释约定偏差。

---

## 三、已核查确认无误项（防止重复劳动）

1. **所有 SP 字符串形式广播目标均已静态注册**：把 SP 仓库全部 `SendAndExecuteLuaFunction("CvLuaX::lY", ...)`（44 个去重目标）与本仓库全部 `REGIST_STATIC_FUNCTION(CvLuaX::lY)` 做程序化差集，结果为 0 缺失。含本周期新增的 `CvLuaGame::lSetPlotName/lRemovePlotName/lDoMinorFaithGiftFromMajor/lDoCityStateFaithBeliefPurchaseFromMajor/lDoCityStateFaithPantheonPurchaseFromMajor`、`CvLuaPlayer::lSetEconomicAidAutoRenew/lTryBuyFoodFromVenice`（后两者的注册存在，缺陷仅在其函数体内的索引）。
2. **函数引用形式广播目标全部已注册**：`city.SetNumRealBuilding`、`newCity.SetPuppet/SetProductionAutomated`、`pCity.ChangeResistanceTurns`、`pNewCargoUnit.PushMission/SetExperience/SetHasPromotion/SetLevel/SetMoves`、`pPlayer/pPlayer.InitUnit`、`pPlot.SetRevealed/ChangeVisibilityCount`、`pUnit.DoCommand/EndTrader/Kill/PushMission/SetMoves`、`plot.SetFeatureType/SetImprovementPillaged/SetImprovementType`、`Game.SetPlotExtraYield` 逐一核对，均已 `REGIST_STATIC_FUNCTION`。
3. **静态实例与实例对象的参数索引约定的区分正确**：`CvLuaStaticInstance.h:72`/`92` 静态实例（Game/Map）用 `ProcessLuaArgForReflection(L, 1)`（点号、无 self，用户参数从索引 1 起），故 `lSetPlotName`（`CvLuaGame.cpp:1962-1964` 读 1/2/3）、`lDoMinorFaithGiftFromMajor`（`2125-2127` 读 1/2/3）正确；`CvLuaGame::lDoDiplomacyBargain` 读索引 1，与 `Game.DoDiplomacyBargain(g_iThem)` 点号调用一致。
4. **外交议价的联机广播链路与 RNG 正确**：`Game.DoDiplomacyBargain` → `CvGame::DoFromUIDiploEvent`（`CvGame.cpp:5539`）只调 `gDLL->sendFromUIDiploEvent` → 各机 `CvDllNetMessageHandler::ResponseDiplomacyFromUI:240` → `GET_PLAYER(eOtherPlayer).GetDiplomacyAI()->DoFromUIDiploEvent(ePlayer, ...)`，`eFromPlayer` = 发起人（ActivePlayer）、`eMyPlayer` = 目标，故 `GET_PLAYER(eFromPlayer).GetEspionage()->TryDiplomacyBargain(eMyPlayer)` 取的是发起人的外交官、目标也是正确的，且 `getJonRandNum(100, "Diplomacy Bargain")`（`CvEspionageClasses.cpp` TryDiplomacyBargain 内）在所有客户端的同一条广播路径中一致执行，无 RNG 分叉。
5. **CvEspionageSpy 的 3 个新 bool 与 CvPlayerEspionage 的 per-target 数组序列化正确**：`CvEspionageClasses.cpp:122-124`/`152-154` 的 `MOD_SERIALIZE_READ/WRITE(164, ...)` 位于 `operator>>`/`operator<<` 流尾；`m_aiDiplomacyBargainCooldown/BuffTurn/Deal`（`EspionageClasses.h:274-276`，尺寸 `MAX_MAJOR_CIVS`）在 `4746+`（Read）与 `4821+`（Write）流尾追加，读写顺序一致；`Reset()`（`EspionageClasses.cpp:234-236`）初始化齐备。
6. **CvDiplomacyAI 的阿拉木图数组序列化与边界正确**：`m_paiCSUAPlunderedNeutralTradeRoute`（`short[MAX_MAJOR_CIVS]`）在 `CvDiplomacyAI.cpp:1604`（Read）/`1839`（Write）位于两个函数的**最后一行**，读写一致；`ChangeCSUAPlunderedNeutralTradeRoute`（`23653-23655`）对负值 clamp 到 0。
7. **`ApplySelectedMinorCivs` 的洗牌/空池处理正确**：`CvGame.cpp` 中 `iPool == 0` 时提前返回，`shuffleArray(&aPool[0], iPool, ...)` 不会对空 vector 取 `&v[0]`；且改为"只收集非 NULL 的 CvMinorCivInfo"后，`InitPlayers` 不再可能收到 NULL 的 `MinorCivTypes`（新增的 NULL 洞守卫在设计期与使用点双保险）。RNG 消耗次数虽与旧版不同，但所有客户端执行同一份代码，无分叉。
8. **CvTreasury 单位维护按晋升项不存在 -1 索引**：`CvTreasury.cpp:658` `getUnitCountFromHasPromotion((PromotionTypes)vEntries[i].m_iPromotion)` 的数据来自 `CvCityStateUAClasses.cpp:673` 的 `... inner join UnitPromotions on UnitPromotions.Type = PromotionType ...`，非法晋升名会被 join 过滤，`PromotionID` 必为合法值；`GetBuildingGoldMaintenance` 末尾（`CvTreasury.cpp:856-858`）对最终值 clamp `>= 0`，叠加 `GetCSUABuildingMaintenanceMod` 后也不会出现负维护费（维度 A 已封闭）。
9. **CvLuaGame 的若干防护正确**：`lGetBeliefsInReligion` 新增 NULL 守卫（宗教槽未创立时不崩溃）；`lGetImmigrationRegressand` 改为委托 `CvGame::GetImmigrationRegressand(ePlayer)`，后者内部 `if(iRtnValue < 0) iRtnValue = 0;`（`CvGame.cpp`）做了非负封锁；`Game.DoDiplomacyBargain` 走的是广播链路而非本地直改。
10. **`getCurrentEraCached()` 无语义风险**：`CvGame.cpp:94-102` 用 `mutable` 成员按回合号缓存世界纪元，纯确定性计算、不含 RNG；初值 `NO_ERA/-1` 保证首帧必然重算。
11. **CvAStar / CvTacticalAnalysisMap 的 OB 改造有守卫**：`CvAStar.cpp:1126` 有 `ePlotOwner != NO_PLAYER`，`CvTacticalAnalysisMap.cpp` 侧有 `pPlot->isOwned()`，不会对 `NO_PLAYER` 取 `GET_PLAYER`。
12. **SQL/XML 与 CacheResults 列名一致**：`Policies.SpyPoints`、`Traits.SpyPoints`、`Buildings.SpyPoints`、`Beliefs.SpyPoints` 由 SP 仓库 `Gameplay/SQL/SP_SpyPoints.sql` 补齐，列名与 `CvPolicyClasses.cpp:579`/`CvTraitClasses.cpp:30` 的 `GetInt("SpyPoints")` 完全一致；`NumInfluencePerEra`（`CvUnitClasses.cpp:263`）由 `(1) CIV5MPDLL/DB/UNITS/NewUnits_DDL.sql` 提供；`HappinessDecayEra`（`CvInfos.cpp:4953`）由 `(1) CIV5MPDLL/DB/RESOURCES/HappinessDecayEra.sql` 与 SP 同名文件提供；`Building_DomainEnemyCombatModifierPerGold` 由 `DLL_Buildings.sql` 提供。`UNIQUE_CITYSTATES.sql` 新增的 `CityStateUAEffect_GoldDonationGamble (Weight, Multiplier)` 与 `CvCityStateUAClasses.cpp:825/831-832` 的 `select Weight, Multiplier` + `GetInt(0/1)` 对应一致（其余 CSUA 子表由 M1 代理深入核对）。
13. **`CvGame::GetCityStateFaithBeliefPurchaseCost` 无溢出风险**：`gCustomMods.getOption("SP_FAITH_BELIEF_PURCHASE_COST", 2500) * getFaithPercent() / 100`，量级为 2500 × 数百 / 100，远小于 `int` 上限。

---

## 备注

- 本域最值得优先修的是 [B-1]：三个函数的参数索引错位会让"经济援助自动续约"与"威尼斯买粮"两个功能在运行时静默失效（不崩溃、不报错、不产生不同步），只能靠实际观察数值发现。
- [B-2] 为唯一的悬垂指针，且是全仓库唯一一处跨语句使用 `Localization::Lookup(...).toUTF8()` 的地方（其余 6 处均先绑定具名 `Localization::String`）。
- 其余维度 A 相关问题（`GetCSUAYieldPercentModifier`、`GetGoldDonationHappiness`、`GetCSUAGoldDonationGambleMultiplier` 的 RNG 等）位于 CvPlayer.cpp，属 M2/M3 代理域，本报告不重复。
