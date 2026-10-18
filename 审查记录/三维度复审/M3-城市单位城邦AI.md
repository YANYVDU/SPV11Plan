# M3 CvCity / CvUnit / CvMinorCivAI 钩子 三维度复审报告

- 审查范围：`git diff c354808..HEAD -- CvCity.cpp CvCity.h CvUnit.cpp CvUnit.h CvMinorCivAI.cpp CvMinorCivAI.h`（MPDLL 仓库 `d:\Git\CIV5\dyy\CIV5MPDLL`，分支 `EconomicAid`）
- 审查日期：2026-10-02
- 结论：应修正 0 项 / 提示 4 项 / 确认无误 18 项

> 说明：本域新增代码以"数据驱动的加成钩子"为主。绝大多数百分比/乘法路径的**消费端已有 `std::max(0, ...)` 封锁或 `iPercent <= 0` 提前返回**，且 CSUA 聚合值一律基于已同步状态按 delta 累加，因此维度 A 未发现"奖励变惩罚"的现实可达路径；维度 B 的乘法量级除 Monaco 赌金一处外均离 `INT_MAX` 有数个数量级；维度 C 的新增 Lua 写接口（信仰购买、经济援助自动续约、威尼斯买粮）经跨仓库核对**全部走 `SendAndExecuteLuaFunction` 广播**。故本域判定为 0 项应修正，仅列 4 项提示供决策。

---

## 一、应修正（会导致实际缺陷）

无。

本域逐条追查了共享背景文档第三节列出的全部高风险点中属于本文件域的部分（Budapest/Hanoi 固定伤害、Almaty 掠夺、Monaco 赌金、Sidon、Tyre、Ragusa、Ife、产出修正注入），均未发现"具体数值输入 → 具体错误结果"的可复现缺陷。

---

## 二、提示（不构成缺陷，供决策）

### [提示-1] Monaco 赌金 getter 为 const 且内含 RNG，当前仅两处调用点，后续接入 UI 即会主客机 RNG 分叉

- **文件**：`CvGameCoreDLL_Expansion2/CvPlayer.cpp:33136-33161`（定义，属 M2 域）、`CvGameCoreDLL_Expansion2/CvMinorCivAI.cpp:10968`（本域唯一逻辑调用点）
- **维度**：C 联机
- **证据**：

  ```cpp
  int CvPlayer::GetCSUAGoldDonationGambleMultiplier() const
  {
      ...
      const int iRoll = GC.getGame().getJonRandNum(iDenom, "Monaco gold donation gamble");
      ...
  }
  ```

  `CvMinorCivAI.cpp:10968` 在 `DoGoldGiftFromMajor` 内调用它；该方法的两处调用点为 `CvDiplomacyAI.cpp:13802`（AI 外交，全机 lockstep 执行）与 `CvDllNetMessageHandler.cpp:635`（`ResponseMinorCivGiftGold` 全客户端处理器），均在所有客户端以相同次数、相同顺序执行，故当前**不构成分叉**。
- **不确定原因/风险**：该函数签名是 `const` 且语义为"查询"，是 UI/tooltip 最容易被顺手调用的形态；一旦后续在 `CityStateDiploPopup.lua` 之类处读取它（当前只读的是 `GetMinorCivGoldGambleLastMultiplier`，无 RNG），RNG 流即分叉。建议把掷骰移出 getter，改由"全机确定执行"的一次性路径写入 `m_aiGoldGambleLastMultiplier`，getter 只读缓存值。

### [提示-2] Ragusa 本地快乐上限修正为裸百分比，数据转负时会压低上限（当前数据 +50，安全）

- **文件**：`CvGameCoreDLL_Expansion2/CvCity.cpp:12812-12816`
- **维度**：A 非负
- **证据**：

  ```cpp
  int iCapMod = pCityStateUA->GetLocalHappinessCapModifier();
  if (iCapMod != 0)
      iLocalHappinessCap = iLocalHappinessCap * (100 + iCapMod) / 100;
  ```

- **失效场景**：若 `LocalHappinessCapModifier <= -100`，`iLocalHappinessCap` 归零或转负，`GetLocalHappiness` 末尾 `if(iLocalHappinessCap < iLocalHappiness) return iLocalHappinessCap;` 会把该城本地快乐压到 0 以下（真实惩罚）。
- **当前数据**：`CSUA.xml` 中 Ragusa 该列为 `+50`，全表为正、无外部负输入，按共享文档"判定要求"**不算缺陷**。仅提示：若日后允许负值，需加下界把关。

### [提示-3] Hanoi `GetCSUACombatModifierInBorders` 仅对上界（-50）做了封顶，未封锁正值

- **文件**：`CvGameCoreDLL_Expansion2/CvUnit.cpp:19808-19825`
- **维度**：A 非负
- **证据**：

  ```cpp
  int iPenalty = pUA->GetEnemyCombatModifierInBordersPerBeenDoW() * kOwner.GetNumTimesDeclaredWarOn();
  if (iPenalty < -50) iPenalty = -50;
  return iPenalty;
  ```

- **失效场景**：数据列 `EnemyCombatModifierInBordersPerBeenDoW` 若被填成正数，则返回**不封顶的正值**，侵入方反而获得无上限战斗力加成（注释自称"returns a non-positive plain percent"，但代码不保证）。
- **当前数据**：`CSUA.xml` 为 `-10 / -50`（设计即负值），无现实路径。仅提示：可加 `if (iPenalty > 0) iPenalty = 0;` 与该函数"只产出惩罚"的契约对齐。

### [提示-4] Monaco 赌金赔付 `(iGold * iMultiplier) / 100` 存在理论 int 溢出（现实不可达）

- **文件**：`CvGameCoreDLL_Expansion2/CvMinorCivAI.cpp:10972`
- **维度**：B 溢出
- **证据**：

  ```cpp
  if (iMultiplier > 0)
      GET_PLAYER(ePlayer).GetTreasury()->ChangeGold((iGold * iMultiplier) / 100);
  ```

- **失效场景**：`iGold * iMultiplier` 溢出需单次赠金 `iGold > INT_MAX / iMultiplier`。最高倍率 `iMultiplier = 1000`（`CSUA.xml` 权重最大档），即需单次赠金 > 约 214 万金币。赠金上限受 `GoToTreasury`/UI 输入约束，远低于此值，**现实不可达**。列出仅为记录审查过程。

---

## 三、已核查确认无误项

### A. 产出/成长修正钩子（维度 A）

1. **`CvCity::getBaseYieldRateModifier` 消费端已封锁非负**（`CvCity.cpp:13445` 起，`14060` `iModifier += 100;`，`14091` `return std::max(0, iModifier);`）。本域新增的三处累加——`13647` `owner.GetCSUAYieldPercentModifier(eIndex)`、`13657` `owner.GetCSUAImmigrantYieldModifierFromImmigrants(eIndex)`、`13680` 首都按信教城市——均汇集到该 return，即使 CSUA 值为较大负数也只会把城市产出压到 0，**不会产出负值**。（此前预侦察记录"未 clamp"有误，已更正。）
2. **转换产出为最终值，且位置正确**：`getBasicYieldRateTimes100`（`CvCity.cpp:14238`）、`getJONSCulturePerTurn`（`10752`）、`GetFaithPerTurn`（`11064`）均把 `GetYieldRateFromUCSConversion(...)` 加在各自百分比修正**之后**，符合 `[[csua-yield-conversion-final-value]]`。
3. **`GetYieldRateFromUCSConversion` 无递归、无非法输入**（`CvCity.cpp:15255` 起）：源产出用 `getBasicYieldRateTimes100(iIn, false, true)`（`bIgnoreFromOtherYield=true`）阻断递归；`iPercent <= 0` 提前 `continue`；`iHasRouteToThisCS/iHasAnyIntlRoute` 用 -1 惰性缓存。Monaco 分支 `GetYieldToYield` 亦为 `iMod <= 0` 跳过。
4. **GP 比率消费端封锁**：`getTotalGreatPeopleRateModifier` 返回 `std::max(0, (iModifier + 100))`（`CvCity.cpp:10372`）；La Venta/Kiev 的 `GetCSUAGreatPersonRateModifierFrom*` 加在 city 级 getter（`10420` 起），无负值风险。
5. **Ife 信仰购买折扣**（`CvCity.cpp:6248-6263` GP 分支、`6309-6324` ALL OTHERS）：两分支位于互斥的 `if/else` 中；`iIfeClassMod < 0` 才应用，`-90` 封顶使 `(100 + iIfeClassMod) >= 10` 恒正；两处 `eUnitClass` 取值一致（GP 分支 `(UnitClassTypes)pkUnitInfo->GetUnitClassType()`，ALL OTHERS 分支 `pkUnitInfo->GetUnitClassType()`），无错索引。
6. **Ragusa 建筑级快乐加成为乘法**（`CvCity.cpp:12791`）：`iBCHappy * GetNumBuildingClass(...)`，`iBCHappy != 0` 才加，无溢出（量级极小）。
7. **Sidon 城防穿透**（`CvCity.cpp:17246-17256`）：`iIgnoreBuildingDefensePercent` 先 `>100→100`、再 `>0` 判定，结果 `if (iValue < 1) iValue = 1;` 封底。
8. **Tyre 伤害减免**（`CvCity.cpp:17296-17307` + `GetCSUADamageReductionPercent` `23984-24004`）：只对 `iChange > 0` 生效，减免百分比内部封顶 90，故 `(100 - iReduction) >= 10`，且 `if (iChange < 1) iChange = 1;`——治疗（负）不受影响，伤害不会降到 0 以下。

### B. 战斗与掠夺钩子（维度 A/B）

9. **`GetCombatModifierFromBuilding` 卫城宫殿块**（`CvUnit.cpp:19761-19788`）：`iPerGold != 0` 且 `iGold > 0` 才乘 `(iGold/100)`；数据 `iPerGold = -10` 属"敌方战斗力惩罚"语义，非奖励端。溢出需 `iGold > 2.1e10`，int 金币量级不可达。
10. **`GetCSUAFixedDamageScale`**（`CvUnit.cpp:19880-19901`）：`iNullifyPercent >= 0` 提前返回 100；`iScale = 100 + iNullifyPercent` 后双向 clamp `[0,100]`。
11. **`GetCSUADamageTakenScale`**（`CvUnit.cpp:19912-19940`）：`HasCombatDamageReductionVsNoTech()` 前置；逐行 `iScale * (100 - Percent) / 100` 并 `if (iScale < 0) iScale = 0;`。数据 `25`，无溢出。
12. **`GetCSUAKillMaxHpBonus`**（`CvUnit.cpp:19949-19977`）：`iKills <= 0` 提前返回；`m_iCachedSurplus <= 0` 的条目跳过（缓存赤字不扣 HP）；`iKills * surplus * percent / 100` 溢出需 `kills × surplus > 1e8`，不可达。
13. **Almaty 缓存与实际读取同源**（`CvCityStateUAClasses.cpp:3226-3236` 写 `m_vKillMaxHpByPromotion[i].m_iCachedSurplus`；`GetKillMaxHpByPromotionEntries()` `2607` 读同一 `m_vKillMaxHpByPromotion`），缓存并非写到一个被丢弃的副本，逻辑自洽。
14. **`GetMaxHitPoints` / `GetCurrHitPoints`**（`CvUnit.cpp:15239`、`15256-15258`）：Almaty 加成为纯加法；`GetCurrHitPoints` 返回 `(iCurr > 0) ? iCurr : 0`，上限缩水时不会产出负血。
15. **固定伤害干预链**（`CvUnitCombat.cpp`）：`InterveneInflictDamage`（`5008` 起）先算 `iAttacker/DefenderFixedDamageScale`；`BudapestWoundedFixedDamageIntervene`（`4875-4902`）受该 scale `/100` 缩放且 `getDamage() > 0` 前提；`MilanDamageReductionIntervene`（`4990-5005`）在全部加减之后按 `iScale/100` 缩放（`iScale` 0..100）；结尾 `piAttackInflictDamage <= 0 → 0` 兜底。伤害量级 ≪ `INT_MAX`。
16. **Almaty 掠夺商路**（`CvUnit.cpp:9774` 放行、`CvTradeClasses.cpp:3841-3887` 结算）：`canPlunderTradeRoute` 仅在"非交战"分支放开且 `pCSUA != NULL` 前置；`iCSUAGold *= (GetCurrentEra()+1)`（数据 200 × ≤8）、`changeExperienceTimes100(iCSUAXP * 100)`（数据 15）、意见惩罚 `> 0` 且未交战才计。均无越界/溢出/空指针。

### C. CvMinorCivAI 与联机（维度 B/C）

17. **新增数组全部有界初始化 + 版本门控序列化，读写顺序一致**：
    - 声明 `CvMinorCivAI.h:680,683,685,687,689,691,693` 全为 `[MAX_MAJOR_CIVS]`；
    - `Reset`（`CvMinorCivAI.cpp:1968-1980`）逐一初始化；`DoTurn`（`2381-2387`）逐回合复位 3 个"本回合已用"标志；
    - `Read`（`2112-2124`）与 `Write`（`2194-2203`）顺序**完全一致**，均为 `MOD_SERIALIZE_READ/WRITE_*ARRAY(164, ...)`。
    - 所有公开 setter/getter（`7775-8210`）带 `eMajor < 0 || eMajor >= MAX_MAJOR_CIVS` 守卫，无越界。
18. **新增 Lua 写接口均走广播，且 Lua 侧均传显式 eMajor**（跨仓库核对）：
    - 信仰购买：`ChooseBeliefPopup.lua:183/187` 用 `Game.SendAndExecuteLuaFunction("CvLuaGame::lDoCityStateFaith{Pantheon,Belief}PurchaseFromMajor", iActivePlayer, params.MinorID, g_BeliefID)`；对应 `CvLuaGame.cpp:88-89` 已 `REGIST_STATIC_FUNCTION` 注册（静态实例点号语法正确）。
    - 经济援助自动续约：`DiploCityStatesStatus.lua:195` `pCs:SendAndExecuteLuaFunction("CvLuaPlayer::lSetEconomicAidAutoRenew", iPlayer, bNew)`（`CvLuaPlayer.cpp:109` 已注册，`8030` 实现）；仅 `IsEconomicAidAutoRenew`（`8019`）为只读。
    - 威尼斯买粮：`CityStateDiploPopup.lua:922` `SendAndExecuteLuaFunction("CvLuaPlayer::lTryBuyFoodFromVenice", ...)`（`CvLuaPlayer.cpp:8046` 附近实现）。
    - 无任何本域新写接口在 SP 中被直接（未广播）调用；`GetMinorCivGoldGambleLastMultiplier`（`CvLuaPlayer.cpp:7403`，UI 读取）为纯只读、无 RNG。
19. **Monaco/Kathmandu 捐赠效果按"接收城邦自身 UA"判定**（`CvMinorCivAI.cpp:10905` `GetMinorUAGrantedEffect` + `10946/10961`），非玩家聚合态，避免了"对任意城邦赠金都触发"的误判；`DoGoldGiftFromMajor` 由 `CvDllNetMessageHandler.cpp:635`（全客户端）与 `CvDiplomacyAI.cpp:13802`（全机 lockstep）调用，输入均为同步状态。
20. **`DoElection` Master Spy +50**（`CvMinorCivAI.cpp:10634`）：`apSpy[ui] != NULL && m_eRank == SPY_RANK_MASTER_SPY` 双重守卫后才置 `iChange = 50`，无空指针。
21. **`GetCityStateFaithPantheonPurchaseCost` / `DoCityStateFaithPantheonPurchase`**（`7989` / `8026` 起）：成本翻倍循环带 `if (iCost > INT_MAX / 2) { iCost = INT_MAX; break; }` 防溢出；`iCost <= 0` 与 `GetFaith() < iCost` 双重校验；影响力奖励 `GetExcessHappiness() / 2` 且 `> 0` 才发放。
22. **`ChangeEconomicAidPoints`**（`7808-7812`）显式 `if (< 0) = 0` 封锁负值；`DoFriendship` 的 `m_aiEconomicAidPoints[ePlayer]++`（`6103`）每回合 +1，量级受回合数约束。

---

## 附：交叉域引用（供合并时去重）

- `CvPlayer.cpp:33136` `GetCSUAGoldDonationGambleMultiplier` 定义属 M2 域，本报告仅从调用方视角评估（提示-1）。
- `CvUnitCombat.cpp` 固定伤害干预、`CvTradeClasses.cpp` 掠夺结算属 M4 域，本报告仅确认其被本域钩子调用时无缺陷（确认项 15、16）。
