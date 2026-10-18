# CSUA 审查报告：摩加迪沙（Mogadishu）

- 审查日期：2026-10-01
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 9 文件 **+225 / −12**；SP 5 文件 **+113 / −0**
- 结论摘要：三条盟友效果与一条朋友效果**逐条对得上设计稿**，**未发现功能性缺陷**。实现方式为**复用既有 YieldToYieldViaTRToUCS 表 + 新建 1 张全国商路修正表 + 扩展 CityStateUAEffects 一列**，三处消费点各司其职。有 **2 个待拍板项**（其中 1 项为文本口径）、**5 项非缺陷提示**。

> **关于设计稿末句「并生成报告」**：本报告按任务指令理解——「审查摩加迪沙并生成（本）报告」，未将其实现为游戏内效果。若该句确为设计稿要求（例如中断科研协定时生成一条通知/日志），请告知，另需明确「报告」的形式与触发时机。

---

## 一、改动清单

### MPDLL

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +21 / −2 | ① `CityStateUAEffects` 新增列 `ResearchAgreementBreakBonusPercent`（`:136-138`）；② `CityStateUAEffect_YieldToYieldViaTRToUCS` 新增列 `RequireRouteToThisCS default 1`（`:305-310`）；③ 新建表 `CityStateUAEffect_CityStateTradeRouteYieldModifiersGlobal`（`:447-458`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +26 / −0 | `YieldToYieldViaTRToUCSEntry` 加 `m_bRequireRouteToThisCS`（`:65`）；新结构体 `CityStateTradeRouteYieldModifierGlobalEntry`（`:98-104`）；`CvCityStateUAEffectEntry` / `CvPlayerCityStateUA` 的 getter、成员与解析声明 |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +56 / −1 | 构造函数初始化、`CacheResults` 读列与读新表、`ApplyEffect` 聚合、`Reset` 清空、`GetResearchAgreementBreakBonusPercent`、`HasCityStateTradeRouteYieldModifiersGlobal`、`YieldToYieldViaTRToUCSRequiresRouteToThisCS` |
| `CvGameCoreDLL_Expansion2/CvCity.cpp` | +21 / −3 | `GetYieldRateFromUCSConversion`（`:15250-15278`）按 `RequireRouteToThisCS` 分派两种商路判定 |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +14 / −0 | `GetCSUAYieldPercentModifier` 新落点（`:18414-18427`）：商路数 × YieldMod × 100 |
| `CvGameCoreDLL_Expansion2/CvDealClasses.cpp` | +39 / −4 | `#include`；`DoCancelDealsBetweenTeams` 传 aggressor（`:3391`）；`DoCancelDealsBetweenPlayers` / `DoEndTradedItem` 加 `eWarAggressor` 形参并透传；RA 中断奖励块（`:3771-3803`） |
| `CvGameCoreDLL_Expansion2/CvDealClasses.h` | +6 / −2 | 两个函数签名加 `eWarAggressor = NO_PLAYER` 默认参数 |
| `CvGameCoreDLL_Expansion2/CvTradeClasses.cpp` | +40 / −0 | 新增 `CvPlayerTrade::HasInternationalTradeRouteFromCity`（`:3122-3160`） |
| `CvGameCoreDLL_Expansion2/CvTradeClasses.h` | +2 / −0 | 新函数声明 |

### SP

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 / −0 | 城邦绑定 `MINOR_CIV_MOGADISHU` → `CSUA_MOGADISHU`（`:60`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +37 / −0 | 2 个效果（`:443-452`）、1 个 UA 条目（`:1678-1685`）、1 行 YieldToYieldViaTRToUCS（`:2363-2371`）、2 行 CityStateTradeRouteYieldModifiersGlobal（`:2372-2383`） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +25 / −0 | 3 个文本 Tag（`:20347-20371`） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +25 / −0 | 3 个文本 Tag（`:18816-18840`） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +25 / −0 | 3 个文本 Tag（`:18622-18646`） |

### 效果设计（已核对与三语文本、XML 三方一致）

| 对象 | 设计文本 | 实现 |
| --- | --- | --- |
| 盟友① | 盟友每有一条通往城邦的国际商路，全国金钱 +5% | `CityStateUAEffect_CityStateTradeRouteYieldModifiersGlobal` × `EFFECT_CSUA_MOGADISHU_ALLY`：GOLD / 5，经 `GetCSUAYieldPercentModifier` 以 `城邦商路数 × 5%` 输出（全国） |
| 盟友② | 盟友的城市如果有发出国际商路，该城市 20% 的金钱将转化为文化 | `CityStateUAEffect_YieldToYieldViaTRToUCS` × ALLY：GOLD→CULTURE / 20 / **`RequireRouteToThisCS=0`**，逐城 |
| 盟友③ | 盟友的科研协定若因对方宣战而中断，将获得相当于正常结束 2 倍的奖励 | `CityStateUAEffects.ResearchAgreementBreakBonusPercent = 200`，在 `DoEndTradedItem` 的 RA 中断分支按 `正常奖励 × 200%` 发放 |
| 朋友① | 朋友每有一条通往城邦的国际商路，全国金钱 +2% | 同表 × `EFFECT_CSUA_MOGADISHU_FRIEND`：GOLD / 2（全国） |

设计稿来源：`1.城邦UA/海洋型.txt:18-23`（与 `未完成/海洋型-未完成.txt:1-6` 一致）。摩加迪沙在 `城邦类型.txt` 归类为海洋型，`MinorCivilizations.Type = MINOR_CIV_MOGADISHU`、`CSUA Type = CSUA_MOGADISHU`（见 [[citystate-name-type-mapping]]，该城邦无命名错位）。

---

## 二、问题清单

### 待拍板（需确认，非缺陷）

#### Q-1　朋友效果末句「并生成报告」的含义

- 位置：`未完成/海洋型-未完成.txt:6` 与 `1.城邦UA/海洋型.txt:23` 均为「朋友效果：朋友每有一条通往城邦的国际商路，全国金钱 +2%」，**设计稿原文并无「并生成报告」**；该短语只出现在本次审查请求中。
- 现状：SP/M DLL 侧均未实现任何「报告」生成（无通知、无日志 Tag）。
- 两种解读：① 本次任务指令「审查并生成（审查）报告」——则现状无需改动；② 设计稿新增需求，希望科研协定中断时（或每回合）生成一条游戏内报告——则需明确报告载体（`CvNotifications`？事件日志？）与触发时机，并补三语文本。
- 建议：确认为①，本报告即交付物。

#### Q-2　效果①的强度与是否设全国上限

- 位置：`CSUA.xml:2372-2377`（ALLY × GOLD × 5）；消费点 `CvPlayer.cpp:18425`（`城邦商路数 × 5 × 100`，并入 `GetCSUAYieldPercentModifier`）。
- 现象：全国金钱 **+5% × 通往城邦的国际商路条数**，**无上限**。
- 规模测算：商路槽位属稀缺资源（见 [[trade-route-opportunity-cost]]），玩家通常不会把全部槽位给城邦；中期常见 2~4 条 → **+10%~20%**，后期 6~10 条 → **+30%~50%**。距设计规则「加成类难以突破 100%」仍有较大余量，强度温和。
- 对照：仓库既有建筑效果 `Building_CityStateTradeRouteYieldModifiersGlobal`（`CvPlayer::GetCityStateTradeRouteYieldModifierGlobal`，`CvPlayer.cpp:18047-18055`）为同一机制（`值 × 城邦商路数`）、且同样无上限，属仓库惯例。
- 建议：维持现状（无上限）。若担忧后期叠加，可参照温哥华/马尼拉风格加上限，但**注意** cap 类字段当前在聚合层用加法而非取最大值（马尼拉报告 D2-2 遗留）。

### 提示（非缺陷）

#### P-1　效果②的「转化为」实为「额外产出」，金钱不减少

- 位置：`CvCity.cpp:15280-15281`，`iResult += (基础金钱 × 20) / 100`，注释明确「the original input yield is unchanged」。
- 说明：城市金钱产出**不减**，仅额外增加等量 20% 的文化基础产出。设计措辞「20% 的金钱将转化为文化」与实现存在字面差异，但这是**仓库既有惯例**——比布鲁斯（GOLD→SCIENCE 10%）、开普敦（GOLD→FOOD 20%）、科伦坡（FAITH→SCIENCE/TOURISM）同表同机制，均不改动源产出。
- 评价：与既有城邦口径一致，无需改动；若设计意图是「真·转化（金钱扣除）」，则三座既有城邦需一并重议，属全局决策而非本次问题。

#### P-2　效果①的商路数为**实时**计算，无每回合缓存

- 位置：`CvPlayer.cpp:18425` 每次调用 `GetNumberOfCityStateTradeRoutes()`（`CvTradeClasses.cpp:3445-3463`，遍历 `m_aTradeConnections` 全表）。
- 说明：与其他城邦「每回合缓存一次」的做法不同，此处**无缓存**。好处是商路建立/取消后**立即**生效（无 1 回合延迟）；代价是 `GetCSUAYieldPercentModifier` 热路径每次都扫描商路表。
- 评价：仅对**持有摩加迪沙效果**的玩家生效（`HasCityStateTradeRouteYieldModifiersGlobal()` 为空即短路），单次扫描约 30~60 条记录，开销可忽略。仓库既有建筑版同为实时计算，口径一致。仅记录。

#### P-3　效果②的「金钱」口径为基础产出，不含百分比修正

- 位置：`CvCity.cpp:15280`，`getBasicYieldRateTimes100(YIELD_GOLD, false, true) / 100`。
- 说明：取的是城市**基础**金钱（未叠加各种百分比修正），而非城市面板显示的最终金钱。与比布鲁斯/开普敦完全同款。
- 评价：口径一致，仅记录。

#### P-4　效果③的「对方宣战」包含防御条约拖入的宣战

- 位置：`CvTeam.cpp:1256` 是 `DoCancelDealsBetweenTeams` 的**唯一**调用点，位于 `DoDeclareWar` 内；`eTeam1 = GetID()` 即宣战方。因防御条约被自动拖入战争的 team（`CvTeam.cpp:1244`）同样走此路径，其 `GetID()` 视为宣战方。
- 评价：从被宣战方视角看，该 team 确实对其宣战，触发奖励**合理**。无建议。

#### P-5　效果③的奖励只给「非侵略方」，且只给一次

- 位置：`CvDealClasses.cpp:3774`，条件 `toPlayer.getTeam() != GET_PLAYER(eWarAggressor).getTeam()`。
- 核实：RA deal 含**两个** `TRADE_ITEM_RESEARCH_AGREEMENT` item（`CvDealAI.cpp:4023-4024` 双方各一），`DoEndTradedItem` 对每个 item 各调用一次、`toPlayer` 为该 item 所有者的 deal 对手方。因此：侵略者那个 item 的 `toPlayer` 落在宣战方 team → 不发放；被宣战方那个 item 的 `toPlayer` 是被宣战方 → 发放。**双方各评估一次，仅被宣战方获益一次**，无重复、无遗漏。正确。

#### P-6　Tooltip 归属符合既定口径

- 效果①为全国聚合型，经 `GetCSUAYieldPercentModifier` 由 `CvCity.cpp` 以 `TXT_KEY_PRODMOD_CITYSTATE_UA`（「来自城邦修正」）输出。
- 效果②为逐城型，经 `CvCity.cpp:14632` 以 `TXT_KEY_CITYVIEW_BASE_YIELD_TT_FROM_ALLY_CS_UA` 输出。
- 与 [[csua-yield-tooltip-attribution]] 口径一致。

---

## 三、已验证无误项

1. **城邦绑定与 Type 正确**：`MINOR_CIV_MOGADISHU` → `CSUA_MOGADISHU`（`CSUA.sql:60`），与 `CSUA.xml:1678-1685` 的 `CityStateUAs` 条目、`Description = TXT_KEY_CITYSTATE_MOGADISHU` 一致；无命名错位。
2. **三语文本齐全且语义一致**：`TXT_KEY_CSUA_MOGADISHU_HELP`（盟友三段 + 朋友一段）、`TXT_KEY_EFFECT_CSUA_MOGADISHU_ALLY_HELP`、`TXT_KEY_EFFECT_CSUA_MOGADISHU_FRIEND_HELP` 三语均存在，数值 5 / 20 / 2 与设计稿、XML 三方一致；均追加于各语言文件**末尾**，未打乱既有分组。
3. **盟友 / 朋友互斥且归属正确**：`RefreshCSAllUAEffects`（`CvPlayer.cpp:20101-20108`）以 `IsAllies` 优先、`else if IsFriends` 择一应用；盟友只得 +5%（不含 +2%），朋友只得 +2%，与设计一致。
4. **效果②的 `RequireRouteToThisCS=0` 分支可达**：`GetYieldRateFromUCSConversion` 的调用点（`CvCity.cpp:14284`）在 `getBaseYieldRate` 内**无条件**执行（仅受 `MOD_SP_UNIQUE_CITYSTATE && !bIgnoreFromOtherYield` 约束），外层**无**「必须通往本城邦」的门槛，故「任意国际商路」分支能被正常评估。
5. **既有城邦语义不被破坏**：`RequireRouteToThisCS` 默认值为 1；SP 侧科伦坡（`CSUA.xml:642-655`）、比布鲁斯（`:1075-1082`）、开普敦（`:1143-1156`）的既有行均**未指定**该列，取默认 1，保持「通往本城邦」语义。
6. **`HasInternationalTradeRouteFromCity` 实现正确**：与既有 `HasTradeRouteToPlayer`（`CvTradeClasses.cpp:3102-3120`）同构，额外以 `CvGameTrade::IsConnectionInternational`（`:542-558`，按**队伍**比较）判定国际，与仓库全站口径统一；空槽以 `IsTradeRouteIndexEmpty` 过滤；以 origin 坐标 + owner 定位起点城市，正确。
7. **`GetNumberOfCityStateTradeRoutes` 语义匹配**：统计 `m_eOriginOwner == 本玩家` 且 `dest` 为 minor civ 的商路（`CvTradeClasses.cpp:3445-3463`），即「玩家发出的通往城邦的商路条数」，与设计「每有一条通往城邦的国际商路」精确对应；通往城邦的商路必然跨 team，无需额外国际判定。
8. **效果③的 aggressor 传递链路正确**：`DoDeclareWar`（`CvTeam.cpp:1256`）→ `DoCancelDealsBetweenTeams(宣战方team, 被宣战方team)` → `DoCancelDealsBetweenPlayers(..., eWarAggressor=eFromPlayer)` → `DoEndTradedItem(..., eWarAggressor)`；其余调用点（`CvDealClasses.cpp:3172` 自然到期、`:3232` 主动取消、`:3548` 玩家死亡）均不传 aggressor（默认 `NO_PLAYER`），不会误触发。
9. **counter 在清零前读取**：`CancelResearchAgreement`（`CvTeam.cpp:1259`）在 `DoCancelDealsBetweenTeams`（`:1256`）**之后**执行；counter 的清零发生在玩家 `doTurn`（`CvPlayer.cpp:24064-24066`，RA flag 为假时归零），宣战瞬间 flag 仍在、counter 有效，奖励计算有数据来源。
10. **奖励公式与正常结束完全同构**：中断块（`CvDealClasses.cpp:3780-3800`）逐行复刻正常块（`:3740-3759`）的 `min(双方beaker) / DIVISOR × median%`，仅**额外**乘 `iPercent(200) / 100`，即「2 倍正常结束奖励」；`MOD_GLOBAL_SUZERAIN` 的附庸科学分支也一并复制，条件编译嵌套正确。
11. **无需版本门控**：`CvPlayerCityStateUA` 为纯运行时缓存（无 `Read`/`Write`，`RefreshCSAllUAEffects` 每回合 `Reset` + 全量 `ApplyEffect` 重建），本次未新增任何序列化成员，符合 CLAUDE.md 版本门控的适用条件。
12. **数据无重复主键**：`CSUA_MOGADISHU` / `EFFECT_CSUA_MOGADISHU_ALLY` / `EFFECT_CSUA_MOGADISHU_FRIEND` 全 SP 各仅一处定义；新表 `CityStateUAEffect_CityStateTradeRouteYieldModifiersGlobal` 仅摩加迪沙两行。
13. **DLL 已含本次改动**：`BuildOutput/VS2022_ReleaseWin32/CvGameCore_Expansion2.dll` 与 `(1) CIV5MPDLL/DLL/` 同名产物均 5334528 字节、时间 2026-10-01 01:11，晚于全部源文件（最晚 `CvCityStateUAClasses.cpp` / `CvPlayer.cpp` 01:08）；二进制内 `CityStateUAEffect_CityStateTradeRouteYieldModifiersGlobal`、`ResearchAgreementBreakBonusPercent`、`RequireRouteToThisCS` 各命中 1 次。
14. **行尾格式保持**：MPDLL 的 `CvCity.cpp`/`CvDealClasses.cpp`/`CvDealClasses.h`/`CvTradeClasses.cpp`/`CvTradeClasses.h` 维持 CRLF，`UNIQUE_CITYSTATES.sql`/`CvCityStateUAClasses.*`/`CvPlayer.cpp` 维持 LF；SP 五文件均 LF。`git diff --stat` 无整文件重写。
15. **引擎 API 用法正确**：`TechTypes eCurrentTech = toPlayer.GetPlayerTechs()->GetCurrentResearch()`，`NO_TECH` 时进 `changeOverflowResearch`、否则 `kTeam.GetTeamTechs()->ChangeResearchProgress(...)`，与正常结束路径逐字一致；`GetPlayerCityStateUA()` 已判空（`CvDealClasses.cpp:3776-3777`）。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff` / `git diff --numstat`，核对改动规模与行尾。
- 交叉核对 C++ 实现、XML 数据、三语文本、设计稿四者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvCity::GetYieldRateFromUCSConversion`（`CvCity.cpp:15212-15286`）及其调用点（`:14284`、`:14629`）；`CvPlayer::GetCSUAYieldPercentModifier`（`CvPlayer.cpp:18414-18428`）与既有建筑版 `GetCityStateTradeRouteYieldModifierGlobal`（`:18047-18055`）；`CvPlayerTrade::GetNumberOfCityStateTradeRoutes`（`CvTradeClasses.cpp:3445-3463`）、`HasTradeRouteToPlayer`（`:3102-3120`）、`HasInternationalTradeRouteFromCity`（`:3122-3160`）、`CvGameTrade::IsConnectionInternational`（`:542-558`）。
- 回读交易 / 外交链路确认 aggressor 语义：`CvGameDeals::DoCancelDealsBetweenTeams`（`CvDealClasses.cpp:3355-3395`）、`DoCancelDealsBetweenPlayers`（`:3398-3440`）、`DoEndTradedItem`（`:3598-3820`）、`CvTeam::DoDeclareWar` 唯一调用点（`CvTeam.cpp:1256`）、RA deal 建立（`CvDealAI.cpp:4023-4024`）、counter 维护（`CvPlayer.cpp:24046-24068`）。
- 以 `grep -a -o` 在 DLL 二进制中检索新表名 / 列名，确认产物包含本次改动。
- 与既有同类实现横向对照：建筑版 `Building_CityStateTradeRouteYieldModifiersGlobal`（同机制基准）、比布鲁斯 / 开普敦 / 科伦坡（同表 YieldToYieldViaTRToUCS 基准）。

---

## 五、当前状态与建议处理顺序

### 状态

- MPDLL 工作区：9 文件 **+225 / −12**（未 commit）；DLL 已重编，产物在 `BuildOutput/VS2022_ReleaseWin32/` 与 `(1) CIV5MPDLL/DLL/`（01:11）。
- SP 工作区：5 文件 **+113 / −0**（未 commit）。
- 游戏根目录 DLL（`Documents\My Games\Sid Meier's Civilization 5\CvGameCore_Expansion2.dll`，2026-08-11）与 MODS 目录**未更新**（未构建）。
- 文档滞后：`未完成/未完成清单.md` 海洋型仍列摩加迪沙；完成后海洋型未完成应剩 **2 项**（魁北克、拉古萨），总未完成 13 → 12。

### 建议顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | Q-1 确认「并生成报告」含义（任务指令 / 游戏内需求） | 无 |
| 2 | Q-2 效果①强度拍板（倾向维持无上限） | 无 |
| 3 | 覆盖根目录 DLL 或构建模组，按下述步骤实机验证 | 小 |
| 4 | 刷新 `未完成/未完成清单.md`（摩加迪沙 → 已完成，海洋型剩 2） | 小 |

### 实机验证步骤

1. **盟友效果①**：与摩加迪沙结盟，令本国有 N 条通往城邦（任意城邦）的国际商路，城市产出明细应出现「来自城邦修正: X%」条目，X = 5 × N；商路改道 / 取消后应**当回合即时**变化（无缓存延迟）；通往**非城邦**文明的商路**不计入**。
2. **盟友效果②**：任一发出国际商路（含通往城邦）的城市，其产出明细应出现 `TXT_KEY_CITYVIEW_BASE_YIELD_TT_FROM_ALLY_CS_UA` 条目，值 ≈ 基础金钱的 20%；**未**发出国际商路的城市**无**此条目。
3. **盟友效果③**：与摩加迪沙结盟后与他国签研究协定，令**对方**宣战中断；本方应获得约 2 倍于正常结束的 beaker（对比：己方主动宣战中断时**不**获得）。观察是否出现原版 RA 中断通知。
4. **朋友效果**：与摩加迪沙为朋友（非盟友），应仅见 +2% × 城邦商路数 的全国金钱修正，**无**效果②的文化条目、**无**效果③。
5. **断交负例**：与摩加迪沙断交后，上述全部条目应消失（验证 `RefreshCSAllUAEffects` 重建路径）。
6. **既有城邦回归**：与比布鲁斯 / 开普敦 / 科伦坡结盟，其「通往本城邦」的金钱转化应仍只在**有通往该城邦商路**的城市生效（验证 `RequireRouteToThisCS` 默认值 1 未破坏既有语义）。
