# M1 CSUA数据类 三维度复审报告

- 审查范围：`git diff c354808..HEAD -- CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h`（本月 +1903 / +785 行）
- 审查日期：2026-10-02
- 结论：应修正 2 项 / 提示 3 项 / 确认无误 8 项

## 一、应修正（会导致实际缺陷）

### [A-1] 【中】Great Work 计数缓存对每个 (class,yield) 行重复累加，多个效果指向同一 GreatWorkClass 时产出加成被成倍放大
- **文件**：`CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp:2918-2942`（缓存）、`CvGameCoreDLL_Expansion2/CvPlayer.cpp:18293-18305`（消费者）、数据 `Super Power - Remaking of World Order (v 7)/Gameplay/XML/CSUA/CSUA.xml:2207-2261`
- **维度**：A 奖励端数值（缓存计数错误 → 奖励被放大，非预期收益）
- **证据**：`CacheGreatWorkCounts` 为「城市 × 条目」双层循环，内层对**每一个** entry 都对缓存累加一次该类 great work 数：

```cpp
for (int iCityIdx = 0; iCityIdx < m_pPlayer->getNumCities(); iCityIdx++)
{
    ...
    for (size_t i = 0; i < m_vGreatWorkYieldModifiers.size(); i++)
    {
        const GreatWorkYieldModifierEntry& e = m_vGreatWorkYieldModifiers[i];
        const int iClass = e.m_iGreatWorkClassType;
        if (iClass < (int)m_aiCachedGreatWorkCount.size())
            m_aiCachedGreatWorkCount[iClass] += pCity->GetCityBuildings()->GetNumGreatWorks((GreatWorkClass)iClass);
    }
}
```

`m_vGreatWorkYieldModifiers` 在 `ApplyEffect` 中按「生效效果数 × 每效果行数」`push_back`，**不做去重**（`CvCityStateUAClasses.cpp:2303-2312`）。SP 数据里 Ife(YIELD_FAITH) 与 Ur(YIELD_CULTURE) 各自定义了**同一组 4 个 class**：`GREAT_WORK_ART / ARTIFACT / LITERATURE / MUSIC`（`CSUA.xml:2209-2255`），Buenos Aires 又使用 `GREAT_WORK_MUSIC`（`CSUA.xml:2257-2261`）。
- **失效场景**：玩家同时是 Ife 与 Ur 的盟友 → 向量含 8 条（ART/ARTIFACT/LITERATURE/MUSIC 各出现 2 次）。`CacheGreatWorkCounts` 对每座城市把 ART 的 great work 数加 **2 次**，`m_aiCachedGreatWorkCount[ART]` = 真实值×2（若同时为 Buenos Aires 盟友，MUSIC 为 ×3）。消费者 `CvPlayer.cpp:18301-18302` 对 FAITH 的 4 条有效行分别取该缓存值并乘 `YieldMod(200)`，于是 Ife 的「+200 基点(=+2%)/件」实际翻倍。例：拥有 10 件 ART、同时盟友 Ife+Ur，本应 `10×2% = +20%` 信仰，实际 `20×2% = +40%`。
  边界：仅单个效果（如只盟 Ife）时 4 个 class 互不重复，计数正确；必须 ≥2 个效果引用同一 class 才触发，属现实中可达（可同时结盟多个城邦）。
- **建议修复**：与同文件 `CacheSpecialCityMatches`（`CvCityStateUAClasses.cpp:3155-3174`）的既有做法一致——先标记被引用的 class，再对每个 class 只累加一次：

```cpp
std::vector<bool> abReferenced(iMaxClass + 1, false);
for (size_t i = 0; i < m_vGreatWorkYieldModifiers.size(); i++)
{
    const int iClass = m_vGreatWorkYieldModifiers[i].m_iGreatWorkClassType;
    if (iClass >= 0 && iClass <= iMaxClass)
        abReferenced[iClass] = true;
}
for (int iCityIdx = 0; iCityIdx < m_pPlayer->getNumCities(); iCityIdx++)
{
    const CvCity* pCity = m_pPlayer->getCity(iCityIdx);
    if (!pCity || !pCity->GetCityBuildings()) continue;
    for (int iClass = 0; iClass <= iMaxClass; iClass++)
        if (abReferenced[iClass])
            m_aiCachedGreatWorkCount[iClass] += pCity->GetCityBuildings()->GetNumGreatWorks((GreatWorkClass)iClass);
}
```

> 说明：同文件的 `CacheSpecialCityMatches` 已显式用 `abReferenced` 避免「同一 type 多 yield 行导致重复计数」（`cpp:3155-3174`），可见作者已知此陷阱，`CacheGreatWorkCounts` 属遗漏，而非有意为之。

### [B-1] 【中】悉尼 ImmigrantCash 读取主表不存在的列，子表从未被查询 → 现金奖励永远为 0（死功能）
- **文件**：`CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp:617-618`（读取）、`CvGameCoreDLL_Expansion2/CvPlayer.cpp:19695-19715`（消费）、`(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql:658-662`、`CSUA.xml:2119-2125`
- **维度**：B 数据读取（读取不存在的列）
- **证据**：

```cpp
m_iImmigrantCashPercent = kResults.GetInt("ImmigrantCashPercent");
m_iImmigrantCashCapBase = kResults.GetInt("ImmigrantCashCapBase");
```

`kResults` 对应**主表** `CityStateUAEffects`（建表于 `UNIQUE_CITYSTATES.sql:45` 起，列清单见 45-660 区段）。该表**没有** `ImmigrantCashPercent` / `ImmigrantCashCapBase` 两列（全仓 grep `ImmigrantCash` 仅命中 C++ 与本子表）。实际数据存放于**子表** `CityStateUAEffect_ImmigrantCashReward(CashPercent, CashCapBase)`（`UNIQUE_CITYSTATES.sql:658-662`），SP 也写入该子表（`CSUA.xml:2119-2125`）。
子表引用完整性对账：C++ 引用的 53 个子表在 SQL 中均存在；SQL 中**唯一**未被 C++ 引用的子表恰为 `CityStateUAEffect_ImmigrantCashReward`。
- **失效场景**：`CvPlayer::DoImmigrantCashReward()`（`CvPlayer.cpp:19700-19701`）首句 `if (iCashPercent <= 0) return;`。由于列不存在，`Results::GetInt(const char*)` 取不到列位置（`DatabaseResults.h:94` 声明，实现在预编译库 `CvGameDatabase/lib/CvGameDatabaseWin32.lib`，无源码可读），Release 下按越界列处理返回 0 → `m_iImmigrantCashPercent` 恒为 0 → 悉尼的移民现金奖励**从未发放**；若 DB 层在 Debug 对越界列断言，则每次 `CacheResults` 触发断言。两种情况都是缺陷。
- **建议修复**：按其它子表的写法，在 `CacheResults` 中查询该子表（两列在 SQL/SP 侧均已就绪，改 C++ 最一致）：

```cpp
std::string strKeyImmCash("CityStateUAEffect_ImmigrantCashReward");
Database::Results* pResultsImmCash = kUtility.GetResults(strKeyImmCash);
if (pResultsImmCash == NULL)
    pResultsImmCash = kUtility.PrepareResults(strKeyImmCash, "select CashPercent, CashCapBase from CityStateUAEffect_ImmigrantCashReward where EffectType = ?");
if (pResultsImmCash != NULL)
{
    pResultsImmCash->Bind(1, GetType());
    if (pResultsImmCash->Step())
    {
        m_iImmigrantCashPercent = pResultsImmCash->GetInt(0);
        m_iImmigrantCashCapBase = pResultsImmCash->GetInt(1);
    }
}
```

## 二、提示（不构成缺陷，供决策）

1. **`ApplyEffect` 两个向量分支未乘 `iChange`**：`CvCityStateUAClasses.cpp:2064-2071`（KillMaxHpByPromotion）、`2164-2170`（GoldDonationGamble）直接 `push_back` 条目，未像其它分支那样 `* iChange`。当前 `ApplyEffect` 仅在 `CvPlayer.cpp:20221/20225` 以 `iChange=1` 调用（移除靠先 `Reset` 再全量重加），故无实际影响；但属隐藏陷阱——若将来支持 `iChange=-1` 增量移除，这两个向量会残留条目。
2. **`GetHolyCityYieldModifierPerFollowingCity` 缺 Release 守卫**：`CvCityStateUAClasses.cpp:1335`（entry 版）与 `:2635`（player 版）只有 `CvAssertMsg`，与同类 getter（`GetImprovementHappiness` `:1439`、`GetCapitalYieldModifierPerFollowingCity` `:2638`）的 `i<0 || i>=count` 兜底不一致。当前唯一调用链（`CvCityStateUAClasses.cpp:2126` 循环、`CvPlayer.cpp:32870` 经 `CvCity.cpp:13687`）均传合法 yield 索引，Release 下不越界；仅健壮性建议。
3. **内联 SQL 的 `PrepareResults` 返回值未判 NULL 即 `Bind`**（如 `CvCityStateUAClasses.cpp:958-961`、`:692-695`、`:628-631` 等）。仅当 SQL 准备失败时空指针崩溃，且与该文件既有写法一致；`CvSpecialCityTypeEntry` 对同类情况已用 `m_bConditionsInvalid` 兜底（`:79-86`、`:118-122`、`:128-132`）。一致性建议，非本次新增缺陷。

## 三、已核查确认无误项（避免重复劳动）

1. **`PopulateArrayByValue` / `Initialize2DArray` 分配的数组**：按类型表 MaxRows 定长（`CvDatabaseUtility.cpp:286-322`），getter 以合法 GC 类型索引访问且均有 `i>=0 && i<GC.getNumXxxInfos()` 守卫（如 `CvCityStateUAClasses.cpp:1439-1464`）；`-1`（NO_XXX）不会被当索引。
2. **新增缓存数组的定长与索引**：`m_aiCachedGreatWorkCount` 按 max class+1、`m_avCachedSpecialCityIDs` / `m_aiCachedSpecialCityPopulation` 按 max type+1 分配，访问端均有 `size()` 上界校验（`cpp:2910-2914`、`3110-3128`、`3247-3252`），无空容器取 `[0]`。
3. **`CvSpecialCityTypeEntry` 条件解析与判定**：全程 fail-closed——无行 / 全部解析失败 / 查询无法 prepare 都置 `m_bConditionsInvalid`；`EvaluateCondition` 对 `pCity==NULL`、原首都缺失(-1)、`CvGameTrade==NULL` 均判空（`cpp:52-237`）。
4. **缓存函数其它分支**：`ComputeLiteracyPercent` 除数 `iTotal>0` 守卫；`CacheWorkedHolySites` 对 `NO_IMPROVEMENT`、`CacheHappyLuxuryCount/CacheNationalWonderCount/CacheLuxuryHappiness/CacheWorldWonderCount/CacheLeagueVotes` 对「无效果 / 对象 NULL」提前返回；`CacheUnknownInfluenceCount/CacheDiplomatAbroadCount` 判 `isAlive/isHasMet/NO_PLAYER/isMinorCiv`（`cpp:2948-3099`、`3216-3238`）。
5. **`CacheSpecialCityMatches` 去重正确**：用 `abReferenced` 使「同一 type 多 yield 行」只统计一次，且 population 只累加一次（`cpp:3155-3192`）。
6. **缓存-应用生命周期**：`RefreshCSAllUAEffects` 先 `Reset` 再对每个生效效果 `ApplyEffect(+1)`，无重复叠加；`m_pCityStateUA` 不入档、每 doTurn 重建（非存档成员），故无需 `MOD_SERIALIZE` 版本门控。
7. **无联机面 / 无随机数**：本文件不含 `getJonRand*`、`shuffleArray`、`&aPool[0]`；`ApplyEffect` 只有 `+1` 调用点，无 const getter 内 RNG 分叉。
8. **子表名与列名对账**：C++ 引用的 53 个子表在 `UNIQUE_CITYSTATES.sql` 中均存在，无拼写错配；唯一「SQL 有、C++ 未引用」的子表即 [B-1] 的 `CityStateUAEffect_ImmigrantCashReward`。
