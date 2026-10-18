# CSUA 审查报告：吉隆坡（Kuala Lumpur）

- 审查日期：2026-09-27
- 审查对象：工作区未提交改动（审查时尚未 commit；审查通过后提交）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 5 文件 +191 / −6；SP 5 文件 +117
- 提交：MPDLL `bd4f98c`、SP `4c592a0`
- 结论摘要：本城邦是该体系**三项机制的首次用例**——新增布尔条件 `IS_PUPPET`、新增「按人口计数的特殊城市产出修正」表、新增对科技阈值（`CvPlayerTechs::GetResearchCost`）的接入。**一审无严重问题**，一审提出 1 项一般问题（死代码 `m_iCachedPuppetPopulation`），已删除并复审通过。另有多项可选建议，见「二、问题清单」。

> 审查方式：由独立子代理完成（上下文与实现过程完全隔离，只拿到设计文本、方案文档路径与 `git diff`）。

---

## 一、改动清单

### MPDLL `bd4f98c`

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +16 / −2 | 新建 `CityStateUAEffect_SpecialCityPopulationYieldModifiers`；条件类型注释更新为已实现 `HAS_RESOURCE / HAS_FEATURE / IS_RIVER / IS_COASTAL / IS_PUPPET` |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +34 | 枚举 `SPECIAL_CITY_CONDITION_IS_PUPPET`、`SpecialCityPopulationYieldModifierEntry`、getter/成员、`CachePuppetStats()` 声明 |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +96 / −2 | `ParseSpecialCityCondition` / `IsBooleanSpecialCityCondition` / `EvaluateCondition` 三处接线；`CacheResults` 解析；`ApplyEffect` 累加；`Reset` 清零；`CacheSpecialCityMatches` 扩展人口累加；`CachePuppetStats()` |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +20 | `GetCSUAYieldPercentModifier` 人口段；`RefreshCSAllUAEffects` 缓存调用 |
| `CvGameCoreDLL_Expansion2/CvTechClasses.cpp` | +25 / −2 | `GetResearchCost` 傀儡折扣；新增 `#include "CvCityStateUAClasses.h"`（PCH 不含该头文件） |

### SP `4c592a0`

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 | 吉隆坡 `UAType` 绑定（`MINOR_CIV_KUALA_LUMPUR` → `CSUA_KUALA_LUMPUR`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +47 | 特殊城市类型 `SPECIAL_CITY_PUPPET` + 1 条 **And** 条件行 + 2 个效果（`PuppetNoTechCostPenalty=true` / `PuppetTechCostPartial=50`）+ 1 个 UA 行 + 人口表 2 行 |
| `Gameplay/XML/Localization/TextInfos_{en_US,zh_CN,zh_Hant_HK}.xml` | 各 +23 | 3 个 Tag × 3 语言，追加于各文件末尾 |

### 效果设计（已核对与三语文本、XML 三方一致）

| 对象 | 设计文本 | 实现 |
| --- | --- | --- |
| 盟友 | 傀儡城市不再提高科研阈值 | 主表列 `PuppetNoTechCostPenalty=true` → `iPuppetPartial=0` → 折扣 100% |
| 盟友 | 每 5 个傀儡城市的人口，全国文化 +2%、魅力 +1% | `SpecialCityPopulationYieldModifiers` × `SPECIAL_CITY_PUPPET` / `PerPopulation=5` × {CULTURE 2, TOURISM 1} |
| 朋友 | 傀儡城市只提高一半的科研阈值 | 主表列 `PuppetTechCostPartial=50` → 折扣 50% |

> 「魅力」映射为 `YIELD_TOURISM`（旅游），符合 SP 设计术语约定。

### 实现前的自主决策（计划已列明，用户批准计划即授权）

| 问题 | 决策 | 理由 |
| --- | --- | --- |
| 朋友效果奇数傀儡数取整 | **总量缩放**：1 个傀儡 = 半个城市成本 | 逐城取整会让 1 个傀儡退化成 0 收益，与「一半」语义不符 |
| 傀儡人口统计口径 | **与 `CvPlayer::GetNumPuppetCities()` 一致**（不额外排除未决/焚毁城） | 与科研折扣的傀儡数口径保持一致，避免同一 UA 内两套计数 |
| `SPECIAL_CITY_PUPPET` 是否通用复用 | **做成通用类型** | 人口缓存对所有被引用的特殊城市类型统一计算，后续「按傀儡数量」的城邦可直接复用 |

---

## 二、问题清单

### P2-1　`m_iCachedPuppetPopulation` / `GetCachedPuppetPopulation()` 是死代码 —— **已修复（删除）**

- 位置：`CvCityStateUAClasses.h:833` / `:1051`、`CvCityStateUAClasses.cpp:1372` / `:1579` / `:2550` / `:2554` / `:2563`
- 现象：人口效果实际读取的是 `m_aiCachedSpecialCityPopulation[SPECIAL_CITY_PUPPET]`（由 `CacheSpecialCityMatches` 按 `SPECIAL_CITY_PUPPET` 谓词统计，`CvPlayer.cpp:18390`）。两套口径完全等价（都是 `firstCity/nextCity` + `IsPuppet` + `getPopulation()`），傀儡人口缓存被另一条路径取代，留下一个永不被消费的成员/getter。
- 处理：删除成员与 getter；`CachePuppetStats()` 只维护傀儡数；相关注释同步（不再声称缓存了人口）。

### P3-1　朋友折扣整数截断（保留）

- 位置：`CvTechClasses.cpp:1631` `iModPerCity * iNumPuppets * 50 / 100`
- 现象：`iModPerCity` 为奇数（大地图会变小，如 25）且傀儡数为奇数时向下取整（25×1×50/100 = 12，而非 12.5），玩家略多付。
- 判断：实现清单只要求避免「1 个傀儡被整除成 0」，这一点已满足（先乘后除，40×1×50/100 = 20），影响可忽略。

### P3-2　`GetPuppetTechCostPartial()` 缺少取值钳制（保留）

- 位置：`CvTechClasses.cpp:1626`
- 现象：若将来数据误写成 >100，`iPuppetPartial` 变负，`(100 - iPuppetPartial) > 100` 会超额折扣，使科研成本低于「无傀儡」基线。
- 判断：当前数据为 50，不可达。

### P3-3　`#if defined(MOD_SP_UNIQUE_CITYSTATE)` 编译期恒真（保留）

- 位置：`CvTechClasses.cpp:1616`
- 现象：`MOD_SP_UNIQUE_CITYSTATE` 在 `CustomMods.h:983` 定义为运行期表达式 `gCustomMods.isSP_UNIQUE_CITYSTATE()`，故 `#if defined(...)` 永远成立，该块始终编译且始终执行。
- 判断：选项关闭时 CSUA 数据为空、`iPuppetPartial == 100` 直接跳过，功能上无影响；且与仓库多数 `.cpp` 的写法一致。

### P3-4　首回合瞬态（保留）

- 位置：`CvPlayer.cpp:20093/20097`
- 现象：缓存每回合重建，读档后首次 `doTurn` 前傀儡折扣与人口加成为 0。
- 判断：实现清单已声明为设计内行为（CSUA 不序列化）。

### P3-5　（复审追加修复）缓存调用点注释残留

- 位置：`CvPlayer.cpp`（`RefreshCSAllUAEffects` 中 `CachePuppetStats()` 调用点）
- 现象：注释仍写「cache the puppet count **and puppet population**」，与删除后的代码不符。
- 处理：已改为只描述傀儡数，并指明人口由 `CacheSpecialCityMatches` 缓存。

### P3-6　（复审追加）`CachePuppetStats()` 缺「无效果早退」

- 位置：`CvCityStateUAClasses.cpp` `CachePuppetStats()`
- 现象：无条件全城扫描，即使该玩家没有任何傀儡相关 CSUA（每个主要文明每回合一次 O(城市数)）。
- 处理：已补早退 `if (!IsPuppetNoTechCostPenalty() && GetPuppetTechCostPartial() <= 0) return;`，与同类 `Cache*` 方法惯例一致。该条件与消费端（`GetResearchCost` 的折扣分支）完全对应，不会漏算。

### P3-7　（复审提出）人口口径含焚毁中/未决傀儡城

- 现象：人口缓存累计 `getPopulation()`，**包含**焚毁中 / 未决的傀儡城（未排除 `IsRazing()` / `IsIgnoreCityForHappiness()`）。
- 判断：与科研折扣侧的 `GetNumPuppetCities()` 口径一致（内部自洽），且 `IsPuppet()` 本身已排除被吞并的城市。当前实现两侧都算焚毁傀儡，行为一致，无需修改；仅需确认是否符合设计预期。

### P3-8　（复审提出）实现清单文档未同步

- 位置：`SP V11/未完成/吉隆坡-实现清单.md:100`
- 现象：仍写着 `int m_iCachedPuppetPopulation` + getter。
- 处理：**未改动该文档**（避免动用户手写的方案单），仅在此说明，以免后续审查再次误判。

---

## 三、已验证无误项

- **折扣公式与位置**：`CvTechClasses.cpp:1631` 的折扣在 `:1637` 黄金时代行**之前**（必须在之前，否则朋友折扣会被黄金时代系数二次缩放）。盟友 `iPuppetPartial=0` → 全扣；朋友 `100-50=50` → 扣一半；无 CSUA 时 `=100` → 不进入分支，零影响。
- **精确抵消**：`GetMaxEffectiveCities(true)` 返回 `m_iMaxEffectiveCities + iNumPuppetCities − iNumNoResearchCostWLKDCity`（`CvPlayer.cpp:33967-33970`），每个傀儡恰好贡献 +1，故 `iModPerCity * iNumPuppets` **精确抵消**；`CachePuppetStats` 与 `GetNumPuppetCities` 口径一致（均不排除 razing/limbo，而 `GetMaxEffectiveCities` 也无条件加回 `iNumPuppetCities`）。实现清单「待确认 2」的口径担忧**实为一致，不是问题**（唯一例外是 `IsWLKDCityNoResearchCost` 特质，该特质在 SP 数据中未被任何条目使用，实际不可达）。
- **1 个傀儡不被吃掉**：先乘后除，40×1×50/100 = 20。
- **And/Or 判定**：`CSUA.xml` 在 **And 表**写了 `IS_PUPPET` 行，Or 表为空 → 只匹配傀儡；既不会触发 fail-closed 误判，也不会因 Or 表为空而退化成 fail-open（匹配所有城市）。
- **`IS_PUPPET` 三处接线齐全**：`ParseSpecialCityCondition`、`IsBooleanSpecialCityCondition`、`EvaluateCondition`（`pCity->IsPuppet()`，吞并中城市不qualify）。
- **basis point 换算**：人口表 `YieldMod` 存**普通百分比**，`CvPlayer.cpp:18391` 乘 100、`:18394` 除 100，与 Bogota Count 表同构；XML `PerPopulation=5 / CULTURE 2 / TOURISM 1` 与设计文本逐字吻合。
- **边界安全**：`PerPopulation<=0` 已挡（`CvPlayer.cpp:18389`）；`GetCachedSpecialCityPopulation` 有 `size()` 边界检查；`m_pCityStateUA` / `m_pPlayer` / `pCSUA` 均判空。
- **六处完整性**：构造函数初始化列表、`CacheResults` 解析、`ApplyEffect` 累加、`Reset` 清零、`RefreshCSAllUAEffects` 调用点、文本与 Help。
- **热路径**：`GetResearchCost` 与 `GetCSUAYieldPercentModifier` 均只读每回合缓存，未当场遍历城市；人口累加复用 `CacheSpecialCityMatches` 既有的城市循环，无额外扫描。
- **数据完整性**：SQL 列名/类型与 XML 完全对应；`SPECIAL_CITY_PUPPET` 已在 `CityStateUAEffect_SpecialCityTypes` 有行；`YIELD_CULTURE` / `YIELD_TOURISM` 外键有效；`TXT_KEY_CITYSTATE_KUALA_LUMPUR` 已确认来自本体。
- **UI 无需补枚举**：`CityStateStatusHelper.lua` 与 `CivilopediaScreen.lua` 都读 `CityStateUAEffects.Help`，不枚举子表。
- **单点应用**：`GetCSUAYieldPercentModifier` 全仓库仅 `CvCity.cpp:13605` 一处调用；旅游经 `CvCityCulture::CalculateBaseTourism` 走 `getBaseYieldRateModifier(YIELD_TOURISM)`，加成生效且 tooltip 走 `TXT_KEY_PRODMOD_CITYSTATE_UA`。
- **规范**：MPDLL 新增注释全英文；无序列化改动故无需版本门控；行尾保持（`CvTechClasses.cpp` 为 CRLF，其余 LF，无整篇翻转）。

---

## 四、验证方法

由独立子代理执行，未运行 MSBuild（编译由主流程单独完成）：

1. 两仓库 `git diff` 通读，核对设计文本逐条
2. 追踪 `GetResearchCost` 的折扣公式与 `GetMaxEffectiveCities(true)` 的构成，验证「精确抵消」
3. 核对 `CacheSpecialCityMatches` 的 And/Or 判定与 `iMaxType` / `abReferenced` 扩展
4. 三语言 Tag 与 C++/XML 引用程序化比对
5. 四个改动 XML 经 `ElementTree` 解析校验 well-formed
6. 行尾格式逐文件核对

编译验证：清 PCH 全量重建，`exit=0`，`error C` / `error LNK` 计数为 0。

---

## 五、当前状态与建议处理顺序

### 状态

- 已提交：MPDLL `bd4f98c`、SP `4c592a0`（均未 push）
- 已构建模组到 MODS 目录
- 一审无严重问题；1 项一般问题已删除修复，复审通过
- **未做实机验证**（实现期间用户不在）

### 建议顺序

1. 先做实机验证（重点：傀儡城市数是否不再推高科技成本、人口加成的 5 人口取整档位、吞并傀儡后是否立即退出两侧计数）
2. 再确认 P3-7 的人口口径（含焚毁中傀儡）是否符合设计预期
3. P3-8 的文档滞后可在下次维护该清单时一并修正
