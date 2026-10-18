# M2 CvPlayer 的 CSUA 计算与 getter 群 三维度复审报告

- 审查范围：`git diff c354808..HEAD -- CvGameCoreDLL_Expansion2/CvPlayer.cpp CvGameCoreDLL_Expansion2/CvPlayer.h`（CvPlayer.cpp 新增 1824 行 diff，逐 hunk 全查；CvPlayer.h 为新接口声明），并向上追溯全部调用点（C++ + SP/世界强权 Lua + MPDLL Lua 导出）
- 审查日期：2026-10-02
- 结论：应修正 0 项 / 提示 4 项 / 确认无误 15 项

> 判定基线：本域聚焦「CvPlayer 内新增的 CSUA 计算与 getter」。共享文档预侦察的 6 个疑点全部核查完毕，**未发现可稳定复现的缺陷**；以下 4 条为决策性提示，均有 `文件:行号` 证据。

---

## 一、应修正（会导致实际缺陷）

无。

预侦察疑点 1~7 的判定结果如下（详见第二、三节）：

| 疑点 | 判定 |
| --- | --- |
| 1. `GetCSUAGoldDonationGambleMultiplier() const` 内消耗 RNG | 当前**不会**分叉（唯一调用点在广播路径），但作为设计脆弱点列入提示 [C-1] |
| 2. 洗牌 `shuffleArray(&aPool[0], ...)` | 不在本域文件（CvPlayer.cpp/h 无此调用），未涉及 |
| 3. `GetCSUAYieldPercentModifier()` 负值/单位/溢出 | 无负值来源、单位换算逐表核对全部正确、无现实溢出（见三节） |
| 4. `GetGoldDonationHappiness()` int 乘法 | 有 `iInterval <= 0` 守卫，乘法量级现实不可达（见三节） |
| 5. 阿拉木图 / 掠夺 战斗路径 | 不在 CvPlayer.cpp 计算域（GetMaxHitPoints 消费端） |
| 6. 布达佩斯 / 河内 固定伤害 | 本域仅 `GetCSAWoundedFixedDamage()` 纯透传（32761-32765），无运算 |
| 7. 摩纳哥赌金 / 基辅票 / 布加勒斯特移民 | 赌金见 [C-1]，移民见 [C-2]/三节，基辅票纯透传 |

---

## 二、提示（不构成缺陷，供决策）

### [C-1] 【中】`GetCSUAGoldDonationGambleMultiplier() const` 在 const getter 内推进同步 RNG，当前安全但为潜在雷区

- **文件**：`CvGameCoreDLL_Expansion2/CvPlayer.cpp:33136-33161`
- **维度**：C 联机（潜在）
- **证据**：
  ```cpp
  int CvPlayer::GetCSUAGoldDonationGambleMultiplier() const
  {
      ...
      const int iRoll = GC.getGame().getJonRandNum(iDenom, "Monaco gold donation gamble");
      ...
  }
  ```
  全部调用点（`grep` 全仓 + Lua）：**唯一** C++ 调用点 `CvMinorCivAI.cpp:10968`（`DoGoldGiftFromMajor` 内）；Lua 侧只有 `CvLuaPlayer::lGetMinorCivGoldGambleLastMultiplier`（`CvLuaPlayer.cpp:7403`）读取的是**已缓存的** `m_aiGoldGambleLastMultiplier`，**不经过 RNG**；SP 的 `CityStateDiploPopup.lua:1063` 也只读缓存。
  金礼路径为广播：`CvGame.cpp:11249 DoMinorGiftGold → gDLL->sendMinorGiftGold` → `CvDllNetMessageHandler.cpp:630-637 ResponseMinorCivGiftGold → DoGoldGiftFromMajor`，**所有客户端同序执行一次**，RNG 消耗一致。
- **失效场景（目前不成立，未来可能成立）**：若日后有 UI/tooltip/预览在本地客户端额外调用此 getter（名字像纯 getter、且是 `const`，极易被误用；同类 `GetMinorCivGoldGambleLastMultiplier` 才是给 UI 用的），则该机多推一次 RNG，之后所有 `getJonRandNum` 流全线错位 → 真·状态分叉。
- **建议**：不改行为，仅加防呆。把随机判定从 getter 中抽出为一次性执行函数（或在函数名/注释中显式标注"推进 RNG，禁止由 UI 调用"）。示例（英文注释）：
  ```cpp
  // ADVANCES THE SYNCED RNG - must be called exactly once per donation on all clients.
  // Do NOT call from UI / tooltip; UI must read GetGoldGambleLastMultiplier() instead.
  int CvPlayer::RollCSUAGoldDonationGambleMultiplier();
  ```

### [C-2] 【低】新增的 `GetEspionage()->UpdateSpies()` 可经 Lua 导出的本地专用刷新函数在单机侧执行，理论上造成 1 回合缓存偏差

- **文件**：`CvGameCoreDLL_Expansion2/CvPlayer.cpp:20290`（新增行，位于 `RefreshCSAllUAEffects` 内）；导出点 `Lua/CvLuaPlayer.cpp:3708 lRefreshCSAlliesFriends`；SP 调用点 `Gameplay/Lua/Misc/CSUA_RefreshOnLoad.lua:9-17`
- **维度**：C 联机（时序/缓存）
- **证据**：`RefreshCSAlliesFriends()`（CvPlayer.cpp:20143）既在 `doTurn()`（CvPlayer.cpp:5422，全机执行）被调用，又通过 `CvLuaPlayer.cpp:3708` **导出给 Lua**；SP 的 `CSUA_RefreshOnLoad.lua` 在 `LoadScreenClose` 里对每个主要玩家直接 `pPlayer:RefreshCSAlliesFriends();`（**无 `SendAndExecuteLuaFunction`，本地执行**）。本域新增的 `UpdateSpies()` 会重算 `CvCityEspionage::m_aiRate`（`CvEspionageClasses.cpp:1880`），而 `m_aiRate` 参与真实间谍进度累积（`CvEspionageClasses.cpp:4893`）。
- **失效场景**：MP 读档时，仅读档机对全部玩家的 `m_aiRate` 做本地重算，其余机沿用存档内的旧值，直到各自 `doTurn` 重算为止 → 该窗口内两侧 `m_aiAmount += m_aiRate` 可能不同。
- **不确定说明**：该偏差由 `doTurn`（全机）在下一次触发时收敛，属 1 回合瞬态；按既有约定 `[[csua-cache-lag-tolerance]]`（1 回合瞬态且无崩溃的缓存偏差默认保留不改）**倾向不修**。另外 `CSUA_RefreshOnLoad.lua` 本意即在读档后本地重算（CSUA 状态不序列化），此为新引入的副作用。仅列作知会，不建议因此改动。

### [C-3] 【低】两处"乘法型百分比"无下界封锁，依赖 SQL 数据非负

- **文件**：`CvGameCoreDLL_Expansion2/CvPlayer.cpp:32728`（`GetCSLandXPPerTurn`）、`CvPlayer.cpp:10023`（`getProductionModifier` 的 Mbanza Kongo 段）
- **维度**：A 非负
- **证据**：
  ```cpp
  // 32728 (Sidon)
  iXP = iXP * (100 + iMod) / 100;          // iMod = GetCSAMilitaryXPPerTurnModifier()
  // 10023 (Mbanza Kongo)
  iTempMod = iPerCity * getNumCities();
  iMultiplier += iTempMod;
  ```
- **失效场景**：若 `MilitaryXPPerTurnModifier <= -100`，`iXP` 变 0 或翻负；若 `UnitProductionModifierPerCity` 为负，则 `iMultiplier` 被削减。当前 SP 数据均为正（`CSUA.xml:208 = 100`、`:498 = 10`、`:504 = 4`），**无负输入，不构成缺陷**；仅提示未来改数据时注意，或补 `max(0, ...)`。

### [C-4] 【低】`HasCSUAEffect` 对 `pMinorAI` 未判空（同类写法不一致，但当前不可触发）

- **文件**：`CvGameCoreDLL_Expansion2/CvPlayer.cpp:33195-33196`
- **维度**：B 空指针
- **证据**：`CvMinorCivAI* pMinorAI = GET_PLAYER(eMinor).GetMinorCivAI();` 紧跟 `GC.getMinorCivInfo(pMinorAI->GetMinorCivType())`，**无判空**；而同一作者、同一模式的 `HasCSUABeliefPurchaseUA`（`CvPlayer.cpp:33020-33021`）**有**判空。
- **失效场景**：`m_pMinorCivAI` 在 `CvPlayer::init` 中对**每个**玩家无条件 `FNEW`（`CvPlayer.cpp:621`），故 `isMinorCiv()` 为真时该指针必非空，实际不会崩。属健壮性/一致性提示，可顺手补 `if (!pMinorAI) continue;`。

---

## 三、已核查确认无误项（防止重复劳动）

1. **`GetCSUAYieldPercentModifier()`（`CvPlayer.cpp:18262-18510`，250 行累加器）——负值、单位、溢出三项全过。**
   - **无负值来源**：所有计数（`GetNumCSFriends/Allies/PoliciesOwned`、缓存计数）恒 ≥0；`GetHappiness()-GetUnhappiness()` 在 18279-18280 夹到 ≥0；各处 `if (iCap > 0 && ...)`、`if (iPerCity > 0)`、`if (iHappy > 0)` 守卫齐全；Kuala Lumpur 在 18444 有 `if (m_iPerPopulation <= 0) continue;`（无除零）。
   - **单位换算逐表核对，全部正确**（对照同一批 SQL 列表注释 `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql`）：
     - 直接相加（basis points，100=1%）：Friend/Ally/Policy（SQL:609/617/625）、GreatWork、Literacy、BornGreatPerson、LeagueVote、LuxuryHappiness（SQL:773 明确 basis points）、Happiness（SQL:674 明确 basis points，Cap 为 percent 故 ×100，代码 18285 正确）。
     - ×100 转换（plain percent）：GoldenAge（SQL:704）、SpecialCityCount（SQL:492）、BuildingClassGlobal（SQL:321）、Food per happy luxury、WorldWonder（SQL:529）、DiplomatAbroad（SQL:564）、UnknownInfluence（SQL:542）、SpecialCityPopulation（SQL:505）、CityStateTradeRouteGlobal（SQL:556）、CulturePerWarPeace、InternationalLandTradeRoutePerEra（SQL:761）——与代码一一对应。
     - Cap 比较在 plain percent 域内完成后再 ×100（18388-18390、18401-18403、18416-18418），语义正确。
   - **无现实溢出**：单次乘积量级最大者为 Kabul `iRoutes(≤数十) * mod(个位) * (era+1)(≤9) * 100 ≈ 10^5`，远低于 2^31。

2. **`GetGoldDonationHappiness()`（`CvPlayer.cpp:18246-18252`）**：有 `if (iInterval <= 0) return 0;`（18250）；`(m_iTotalGoldDonated / iInterval) * GetHappinessPerGoldDonated()` 需累计捐赠 > 2^31/每单位快乐 ≈ 10^12 才溢出，现实不可达。累计增长是 Dubai UA 的设计（`CvMinorCivAI.cpp:10997 ChangeTotalGoldDonated`）。

3. **`GetCSUATradeRouteGoldModifier(const TradeConnection&)`（`CvPlayer.cpp:18535-18622`）**：非国际路线在 18539 早退；Hormuz 有 `if (iSurplus > 0)`（18589）；Panama 有 `pOriginPlot && pDestPlot` 判空（18573）；所有表值语义为"加成"（正），无负源、无除零、无溢出。调用点 `CvTradeClasses.cpp:2664` 累加到以 100 为基的百分比，语义正确。

4. **移民三兄弟（`CvPlayer.cpp:18646-18676`）非负且有上限**：`GetCSUAImmigrationRateModifier` 返回 `perImmigrant * m_iTotalImmigrantsReceived`（计数 ≥0、SQL 正值），并以 `ImmigrationRateMax` 封顶（`iMax > 0 && iTotal > iMax`）；`GetCSUAEmigrationRateModifier` 同理以 `EmigrationRateMax` 封顶。二者在 `GetImmigrationRate`（19666-19667）中加/减后，于 19675 `if (iMoveOutCounterMod < 0) iMoveOutCounterMod = 0;` 封底，不会翻负。

5. **`GetImmigrationRate` 正负语义与旧 Lua 一致**：19663-19667 注释所述"A→B 与 B→A 得到同一乘数"经推导成立（`iMoveOutCounterBase` 互为相反数，分支选取同一 kMoveIn/kMoveOut），`rate_BA = -rate_AB`，方向正确（对照已移除的旧 Lua `NewCityRule.lua` 中 `thisPlayer:GetImmigrationRate(playerID)`，语义一致）。

6. **`DoInternationalImmigration()`（`CvPlayer.cpp:19729-19787`）+ `DoImmigration()`（19791-19873）联机确定（维度 C 通过）**：
   - 调用点 `CvPlayer.cpp:5503-5508` 位于 `doTurn()`（5382）内，`doTurn` 经 `setTurnActive`（22363/22446）∈ 同步回合模拟，全机执行。
   - 全程用**显式 `GetID()`**，不再依赖 `getActivePlayer()`（19738 注释即为此修复）；
   - 随机数用**同步 RNG** `GC.getGame().getJonRandNum`（19817/19821），且候选城市集合由 `CanImmigrantOut/In()`（游戏状态，非本地视角）决定，分支条件全机一致 → 消耗次数一致；
   - 有 `iRegressand <= 0` 早退守卫（19739），修正了旧 Lua 在 regressand=0 时 `iRegressand*2==0` 会每回合触发的隐患（注释 19733-19735）。
   - 与旧 Lua（`GameEvents.PlayerDoTurn` + `IsHuman()` 守卫）行为对齐，`isHuman()` 为全机一致的全局属性。

7. **`DoImmigrantCashReward()`（`CvPlayer.cpp:19695-19715`）**：有 `iReward <= 0 return`（19705，明确防止"破产倒扣"）、`iCapBase > 0` 才设上限；纯正收益，无负值。

8. **`GetGoldGambleLastMultiplier` 调用点/UI 一致**：`CvMinorCivAI.cpp:10970` 把本轮结果写入 `m_aiGoldGambleLastMultiplier[ePlayer]`（初始 -1，`MOD_SERIALIZE_READ_ARRAY(164,...)` 版本门控，`CvMinorCivAI.cpp:2122/2202`），消费端 `if (iMultiplier > 0) ChangeGold(...)`（10971-10972）——0 表示"未中奖"，不会造成 ×0 清零。

9. **`HasCSUABeliefPurchaseUA` / `HasCSUAFaithPantheonPurchaseUA`（33017/33103）**：均先 `isMinorCiv()`，再对 `pMinorAI`、`pkMinorCivInfo`、`szUAType`、`pUAEntry`、`pEffect` 逐级判空，健壮。

10. **`TryBuyFoodFromVenice`（`CvPlayer.cpp:17268-17286`）联机安全**：状态修改函数，经 `SendAndExecuteLuaFunction("CvLuaPlayer::lTryBuyFoodFromVenice", ...)` 由 UI 广播；`lTryBuyFoodFromVenice` 已 `REGIST_STATIC_FUNCTION`（`CvLuaPlayer.cpp:110`）；`m_iLastVeniceBuyFoodTurn >= getGameTurn()` 的冷却判断（17270）使重复执行天然幂等，避免同机二次扣金。序列化门控 164（`CvPlayer.cpp:30336` / `31248`，默认 -1）。

11. **`GetSpyPointsThreshold()`（15243-15246）**：`BASE * max(0, mod+100)/100` 有下界封锁；`ChangeSpyPoints`（15272-15291）的 `while` 条件含 `GetSpyPointsThreshold() > 0`，BASE 为 0 也不会死循环。

12. **开放边界玩家级改造（`CvPlayer.cpp:23096-23146`）存档兼容正确**：`IsAllowsOpenBordersToPlayer` 对 `ePlayer` 越界返回 false（23101-23103），数组 `REALLY_MAX_PLAYERS` 宽于 `MAX_PLAYERS`（写入按全宽初始化，1449-1451）；`m_bPlayerOBsValid`/`m_abPlayerOpenBorders` 均以 `MOD_SERIALIZE_READ(164, ...)` 读取（`31101-31102`），旧存档落到 `m_bPlayerOBsValid=false` → 走团队级回退（23103-23105），**不读脏数据**。

13. **序列化 Read/Write 顺序与门控一致**：新增成员（`m_iLastVeniceBuyFoodTurn`、`m_iNumWarPeacesCompleted`、`m_iNumTimesDeclaredWarOn`、5 个 spy 成员、移民总计数、开放边界组）的 Read（`CvPlayer.cpp:30336/30503-30513/31069-31070/31101-31102/31251` 等）与 Write（`31248/31383-31393/31835-31836/31868-31869` 等）位置、`#if` 归属、门控版本（164）逐一对应，无错位。移民总计数与 `m_aiImmigrationCounter` 的 `#if defined(MOD_INTERNATIONAL_IMMIGRATION_FOR_SP)` 归属一致。

14. **`GetResearchThresholdMod`（`CvPlayer.cpp:34281+`）重构未丢封装**：对照 `CvTechClasses.cpp` 旧内联实现（`iMod = worldInfo.GetNumCitiesTechCostMod() * GetMaxEffectiveCities(true)`，金库时代再 `* (goldenAgeMod+100)/100`），新函数语义一致；新增的 puppet 折扣（`iModPerCity * iNumPuppets ...`）在 `iEffectiveCities >= iNumPuppets` 时不会把 `iMod` 压成负数，Singapore 折扣（`iPercent` 夹到 100）最坏把 `iMod` 归 0，紧随其后的金库时代乘法沿用旧逻辑，无回归。

15. **其余新 getter 均为 0/正透传或已判空**：`GetCSUACoastalCityHappiness`/`GetCSUAHappinessPerFollowingCity`/`GetCSAWoundedFixedDamage`/`GetCSAMilitaryXPPerTurnModifier`/`GetCSACityAttackIgnoreBuildingDefensePercent` 等为 `m_pCityStateUA ? ... : 0` 纯透传；`GetCSUACapitalYieldModifierPerFollowingCity`（32831-32842）与 `GetCSUAHolyCityYieldModifierPerFollowingCity`（32867-32878）以 `HasCreatedReligion()`/`NO_RELIGION` 守卫，乘法量级小；`GetCSUALeagueVotesFromDoF`（33068-33075）对 `GetDiplomacyAI()` 判空。快乐侧（`GetHappinessFromMinorCivs` 内 Gangtok/Vancouver/Yerevan/Ur 段，`CvPlayer.cpp:15111-15146`）全部 `> 0` 守卫后按 `/100` 取整，只增不减。
