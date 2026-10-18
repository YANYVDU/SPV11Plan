# CSUA 体系性能评估报告

评估对象：SP V11「城邦独特能力」（City-State Unique Ability）系统
评估场景：24 城邦 + 12 大文明 + 全图合计约 200 城市
评估方式：代码静态分析（未做运行时 profiling）
评估日期：2026-10-13

---

## 一、结论摘要

CSUA 的整体性能影响**可控，但在 200 城市规模下仍不干净**。系统在缓存设计上做得扎实——绝大多数重活已经被搬到「每回合一次」的 `RefreshCSAllUAEffects`，热路径基本只读 flat int。

评估当时存在**两处与玩家实际持有内容无关的无条件开销**（第四节问题 1、问题 3），以及若干个「按全局实体数循环」的放大点。前者已由三批优化清除（见下方更新）；后者依然存在——它们只对真正持有对应效果的玩家收费，但持有者每回合仍要全扫（见第七节）。

> **2026-10-13 更新**：下文「与玩家实际持有内容无关的无条件开销」已修复——问题 1 的短路由 `0636a34` 实现，UA Type → Entry 的线性查找由 `77fa9ad` 改为加载期一次性解析，`ApplyEffect` 的全部维度扫描由 `54c5893`、`ba6bc2e` 改为加载期存在性标志控制（各条目的状态标记见第四、五节）。本报告的耗时数字仍为静态估算，尚未用第六节的埋点实测校正。

分层判断（下表为**修复前**的静态估算；其中第 1 层贡献的约 2～5ms/回合已由三批优化消除，其余各行对应未优化项，见第七节）：

| 场景 | 影响 |
|---|---|
| 常规对局（玩家持有 0～3 个城邦效果） | 几乎无感，城市产出路径仅多 19 次廉价标志检查 |
| 大后期 200 城 + AI 密集评估 | 累计约 **100～300ms/回合**，占回合总时长的个位数百分比 |
| 最坏情况（玩家同时把 24 城邦全收为盟友） | 城市产出路径叠加 261 建筑类 + 56 资源 + 37 地块循环，单次城市产出计算可能慢一个数量级 |
| UI 全城列表刷新（经济总览等） | 约 **15～25ms/次刷新**，连续刷新会有可感卡顿 |

---

## 二、系统的规模参数（实测）

| 项目 | 数值 | 来源 |
|---|---:|---|
| 城邦数 / UA 定义 | 58 UA × 2 = **116 个 effect** | `CityStateUAEffects` 主表 |
| CSUA 相关数据表总数 | **57 张**（主表 + 58 UA + 55 子表 + SpecialCityTypes） | `Civ5DebugDatabase.db` |
| 子表总行数 | **449 行** | 同上 |
| 最大子表 | `BuildingClassYieldModifiers` **161 行**（乌尔独占 82 行，SQL 按国家奇观类展开） | 同上 |
| 次大子表 | `AdjacentImprovementYieldChanges` **43 行**（埃里温，SQL 按每个改良展开，含触发器追加） | 同上 |
| 全局建筑类数 | **261** | 同上 |
| 全局资源数 | **56** | 同上 |
| 全局改良数 | **50 行**（ID 0..50 且有空洞，info vector 按 ID 占位为 **51**） | 同上 |
| **产出类型数** | **17** | `CvGameCoreEnums.h`（`MOD_API_UNIFIED_YIELDS_MORE = true`） |
| 城邦槽位循环范围 | `MAX_MAJOR_CIVS` ～ `MAX_CIV_PLAYERS`（42 个槽位，实际 24 个存活城邦） | 各调用点 |

> **关键**：产出类型是 **17 而非原版的 9**。所有「× NUM_YIELD_TYPES」的乘法近乎翻倍，这是本报告所有估算的前提。

---

## 三、开销分层

### 第 1 层：每回合一次性刷新（已优化）

> **2026-10-13 更新**：本层的无效维度展开已由 `54c5893`、`ba6bc2e` 消除，详见本节末与第五节优化 3。以下为修复前的描述。

入口 `CvPlayer::RefreshCSAllUAEffects`（CvPlayer.cpp:20380），每玩家每回合重建效果表。

主要成本在 `CvPlayerCityStateUA::ApplyEffect`（CvCityStateUAClasses.cpp:2062）的**三重全量展开**：

```
BuildingClasses 261 × 17  = 4437
Resources        56 × 17  =  952
Improvements     50 × 17  =  850
                    合计 ≈ 6239 次数组查询 / 每个 effect
```

问题在于：**无论该 effect 是否用到这三张表，这段循环都会执行**。因为三个二维数组在 `Reset()`（CvCityStateUAClasses.cpp:1848 起）里被**无条件分配**，所以 `if (m_ppiBuildingClassYieldModifiers)` 判断恒为真。（此外还有 7 张一维子表每次同样全扫，见第五节优化 3。）

估算：12 玩家 × 平均 4 个城邦盟友 × 6239 ≈ **30 万次/回合 → 约 2～5ms/回合**。

该层优化前**可接受**（个位数毫秒）；加了存在性标志后，只有真正使用对应子表的 effect 才付这份钱，实际开销趋近于零。

### 第 2 层：每城市每产出的热路径（主要风险）

入口 `CvCity::getBaseYieldRateModifier`（CvCity.cpp:13467），函数内有 **19 处 CSUA 引用**。绝大多数带 `HasXXX()` 短路，对不持有该效果的玩家近乎零成本。

真正的放大点是**按全局实体数循环**的几块（仅在该玩家持有对应效果时激活）：

| 位置 | 城邦 | 循环规模 |
|---|---|---|
| CvCity.cpp:13562 | 乌尔 / 布拉格 / 埃里温 | **261 个建筑类** × `GetNumBuildingClass` |
| CvCity.cpp:13595 | 墨尔本 | **56 个资源** × `GetNumResourceLocal`（每个资源再扫城市地块） |
| CvCity.cpp:13648 | 安塔那那利佛 | **~37 个可工作地块** × `IsWorkingPlot` |
| CvCity.cpp:13669 | 热那亚 / 维尔纽斯 | `GetCSUAYieldPercentModifier` 15 段累加，各段长度与**持有 effect 数成正比** |

另有一个隐藏点：`GetCSUAYieldPercentModifier`（CvPlayer.cpp:18438）内部对持有摩加迪沙/喀布尔的玩家会调用 `GetNumberOfCityStateTradeRoutes()` / `GetNumberOfInternationalLandTradeRoutes()`——**每次遍历全部贸易连接**。由于该函数每城市每产出调用一次，形成 O(产出 × 城市 × 商路) 的三重放大。

### 第 3 层：每地块 / 每单位的超热路径

| 位置 | 说明 |
|---|---|
| CvPlot.cpp:9278 | `CvPlot::calculateYield` 的 **8 方向邻格循环**内，每次都遍历埃里温的 **43 条**相邻改良条目。`calculateYield` 是全图地块产出计算的底座，**命中面最广**。 |
| CvUnit.cpp:15239 | `CvUnit::GetMaxHitPoints`（全代码 213 处调用）→ `GetCSUAKillMaxHpBonus`。有缓存短路，**廉价，优化得当**。 |
| CvPlayer.cpp:25051 | `getNumResourceTotal` 的姆班扎刚果分支：在城市循环内叠加 `GetResourcePerCityEntries()` 条目循环。无条目时几乎零成本。 |

---

## 四、关键问题

### 问题 1：`GetYieldRateFromUCSConversion` 完全没有短路（最严重）

> **状态：已修复。** 短路由 `0636a34` 补上（`CvPlayerCityStateUA::HasUCSYieldConversion()`），函数内的城邦查表由 `77fa9ad` 改为 O(1) 索引。以下为修复前的描述。

- 位置：`CvCity::GetYieldRateFromUCSConversion`（CvCity.cpp:15279）
- 调用链：`getBasicYieldRateTimes100`（CvCity.cpp:14260）→ 每城市每产出调用一次；另有 CvCity.cpp:10774（文化）、11086（信仰）、14694

该函数从 15287 行起**直接开扫全部城邦**，对每个存活城邦执行一次 `CvCityStateUAXMLEntries::GetEntryByType`——而后者是 **58 项线性 `strcmp` 字符串比较**（CvCityStateUAClasses.cpp:756）。

```
24 城邦 × 58 项 strcmp ≈ 1400 次字符串比较 / 每次调用
```

**这跟玩家是否真的持有转化效果无关**——哪怕全图没有一个科伦坡 / 开普敦 / 摩加迪沙 / 摩纳哥盟友，这份开销照付。

粗算：200 城 × 17 产出 × 每回合若触发 3 次 ≈ **1400 万次 strcmp / 回合（约 40～70ms）**。

> 附带发现（2026-10-13 复核修正）：原报告把 `m_vYieldToYieldViaTRToUCS` 与 `m_vYieldToYield` 判为 `CvPlayerCityStateUA` 的**死字段**，结论有误——二者实为 `CvCityStateUAEffectEntry` 的成员（`CvCityStateUAClasses.h:666`、`:668`），在 `CacheResults` 中按 XML 填充，并由 `GetYieldToYieldViaTRToUCSTimes100` 一系 getter 读取，是活的。该函数确实是绕过玩家级累加、直接读 effect entry，与这两个容器无关，但容器本身并非死代码。

### 问题 2：`GetEntryByType` 是线性字符串查找

> **状态：查找已消除（`77fa9ad`）。** 全部调用点改为读加载期解析好的 `CvMinorCivInfo::GetCityStateUAIndex()` + O(1) `GetEntry()`。
>
> 同时修正原报告的根因判断：这里真正贵的不是 `strcmp`（每次遍历里最便宜的一环），而是**每调用扫 42 个城邦槽位**——每槽位 2 次 `GET_PLAYER` 加 `IsAllies` / `IsFriends`。索引化只去掉了字符串比较，**槽位扫描仍在**。`CvPlayer::HasCSUAEffect`（CvPlayer.cpp:33583，参数已是 effect id 而非字符串）每次被 `CvCity::canConstruct`（CvCity.cpp:3495）调用（仅当建筑带 `PrereqEffect`）仍要遍历所有城邦，这是原报告漏记的残余热点。

### 问题 3：`ApplyEffect` 的无效三维展开

> **状态：已处理（`54c5893`、`ba6bc2e`，对应第五节优化 3）。** 实现方式与下方建议略有出入：**只加了加载期存在性标志，没有改「按需分配」**——数组仍无条件分配，靠标志在 `ApplyEffect` 入口短路。覆盖 3 张二维表（BuildingClass / Resource / Improvement 的 YieldModifiers）与 7 张一维表（GreatPersonPoints、SpecialistPointRate、GreatPersonOneShotModifier、FaithGPClassCostModifier、ImprovementHappiness、BuildingClassHappiness、TradeRouteGoldPerSurplusResource）。以下为修复前的描述。

见第 1 层。每回合 30 万次数组查询中，绝大多数是该 effect 根本用不到的维度。

---

## 五、优化方案（按性价比排序）

### 优化 1：给 `GetYieldRateFromUCSConversion` 加玩家级短路 ★最高性价比

> **状态：已完成（`0636a34`）。** 实现与下列要点一致：在 `ApplyEffect` 累加、`Reset()` 清零；该标志只决定「是否值得扫」，效果判定仍走 `IsAllies` / `IsFriends` 实时查询，标志滞后只会多扫一次、不会漏效果。

新增玩家级标志「本玩家是否有任何 yield 转化效果」，无转化效果的玩家直接 O(1) 返回。**这一条即可消掉最大的无条件开销**。

实现要点：
1. `CvCityStateUAEffectEntry` 暴露两个向量 getter；
2. `CvPlayerCityStateUA` 新增 `m_iUCSYieldConversionCount` 计数器 + `HasUCSYieldConversion()`；
3. `ApplyEffect` 在 effect 含转化条目时累加该计数，`Reset()` 清零；
4. `CvCity::GetYieldRateFromUCSConversion` 开头查询该标志。

### 优化 2：UA Type → Entry 查找改为预计算 ID

> **状态：已完成（`77fa9ad`）。** 实现在 `CvMinorCivInfo` 上缓存行索引 `m_iCityStateUAIndex`，由新增的 `CvCityStateUAXMLEntries::ResolveMinorCivUAIndexes()` 在 `CvDllDatabaseUtility::PrefetchGameData` 中解析一次（此时 `MinorCivilizations` 与 `CityStateUAs` 均已加载）；缓存属于 Info 类、不进存档，无需版本门控。
>
> 遗留（已修复）：原实现把「空 UAType」（合法——城邦本就没有 CSUA）与「UAType 拼错 / 对应行未写入」（配置错误）都压成 `-1`，后者会静默失效。`ResolveMinorCivUAIndexes` 现已拆开两种情况：空 UAType 仍写 `-1` 并 `continue`；非空 UAType 匹配失败时写 `xml.log`（`LOGFILEMGR.GetLog("xml.log", 0)->Msg(...)`），日志含城邦 type 与拼错的 UAType 字符串。
>
> **更正**：原建议的「加 `CvAssertMsg` 即可暴露」在本工程**无效**——`CvAssert.h:30` 的 `#define CVASSERT_ENABLE` 被注释掉，全仓库无任何地方定义它，`CvAssertMsg` 在 Debug / Release 下都展开为空宏（`CvAssert.h:107` 起的 `#else` 分支）。修复保留了 `CvAssertMsg(false, ...)`（将来若开启断言可自动生效），真正起作用的暴露手段是 `xml.log` 日志。

消除所有 `strcmp` 热路径（问题 1、2 的共同根因）。可在 `CvMinorCivInfo` 上缓存 effect ID。

### 优化 3：`ApplyEffect` 的三维展开改为按需 ★已完成

> **状态：已完成（`54c5893`、`ba6bc2e`）。** 在 `CvCityStateUAEffectEntry` 上加 10 个加载期存在性标志（`Has*` getter），`CacheResults` 读出每张子表后置位，`ApplyEffect` 的每个 `GC.getNum*Infos()` 循环入口先查标志。
>
> 判定口径分两种：一维数组用新增的 `HasAnyNonZero` 扫描实际值（精确）；二维数组在 SQL 逐行填充时置位（「有行即真」，若某 effect 配了全 0 的行仍会视为存在——只损失优化收益，不影响正确性）。
>
> 未改「按需分配」：`CvPlayerCityStateUA::Reset()` 仍无条件分配这些数组，`ApplyEffect` 里的 `if (m_ppXxx)` 因此恒真、保留无害。报告原建议的两步里只做了第二步，收益已基本到手。
>
> **索引语义备注**（审查初稿曾在此误判，记录以免重蹈）：`GC.getNumImprovementInfos()` 一类的计数**不是「数据库行数」**，而是 info vector 的大小。`CvDllDatabaseUtility::PrefetchCollection`（CvDllDatabaseUtility.h:124）遇到 ID 空洞会 `push_back(NULL)` 占位，因此 vector 大小恒等于 `max(ID)+1`，与 `CvDatabaseUtility::MaxRows` 一致。`Improvements` 表虽有 50 行、缺 ID 27，vector 仍为 **51**，索引 50（`IMPROVEMENT_POLYNESIA_CITY_NE`）可正常访问。据此核对，本次所有 `HasAnyNonZero` 的长度参数与对应数组长度精确相等。

> **原建议**：先判断该 effect 是否真有对应子表数据（存在性标志），把每回合 30 万次降到接近零。实现见上方状态块。

---

## 六、验证方式

`3bed3c5` 已在 `getBaseYieldRateModifier`、`GetYieldRateFromUCSConversion`、`GetCSUAYieldPercentModifier` 以及 `RefreshCSAllUAEffects` 的各步加好 AI_PERF 计时器，输出到 `CSUA-perf.csv`。仅当 Config.ini 打开 `[Debug] AIPerfLog` 时记录（关闭时无 IO，但仍有非零开销，故不要在对局中长期开启）。

建议实测一轮 200 城对局，用实测值校正本报告各处的 ms 估算——尤其第四节问题 1 的「40～70ms」是推算而非实测。

三批优化（`0636a34`、`77fa9ad`、`54c5893`、`ba6bc2e`）落地后，**本报告尚未重新实测**。收益落点：优化 1 在 `GetYieldRateFromUCSConversion` 计时步，优化 2 / 3 在 `RefreshCSAllUAEffects` 的 `ApplyEffect` 步。建议同场景采两版数据（回退到 `3bed3c5` 前后对应提交即可），确认「无条件开销已清零」是实测结论而非代码推断——本报告此前已因静态推断误判过一次（见第五节优化 3 的索引语义备注）。

---

## 七、未处理项（后续候选）

三批优化清掉的都是「与玩家持有内容无关」的无条件开销。以下各项**只对真正持有对应效果的玩家收费**，但持有者每回合仍要全扫，是目前剩下的主要成本（细节见第三节对应条目）：

1. **城市产出路径的全局实体循环**（第 2 层）——乌尔 / 布拉格 / 埃里温的 261 建筑类、墨尔本 56 资源（每个再扫城市地块）、安塔那那利佛 37 可工作地块。
2. **`GetCSUAYieldPercentModifier` 内的商路遍历**（第 2 层）——摩加迪沙 / 喀布尔分支每次遍历全部贸易连接，形成 O(产出 × 城市 × 商路)。
3. **埃里温相邻改良**（第 3 层）——`CvPlot::calculateYield` 的 8 方向邻格内每次遍历 43 条条目，命中面最广，优先级最高。
4. **`HasCSUAEffect` 槽位扫描**（问题 2 的残余）——索引化只去掉了 `strcmp`，42 个城邦槽位扫描仍在。

另有一处**代码一致性**问题（非性能，未处理），以及一条已修复项：

- 优化 3 的两类判定口径不一致：一维数组「有非零值才真」，二维数组「有行即真」。若某 effect 在 `*_YieldModifiers` 里配了全 0 的行，仍会全扫 261×17——只损失优化收益，不影响正确性。
- 优化 2 的 UAType 配置错误静默失效——**已修复**：非空 UAType 匹配失败时写 `xml.log`。原建议的 `CvAssertMsg` 在本工程为空宏、不可用（原因见第五节优化 2）。

---

## 附录：涉及的关键文件

| 文件 | 作用 |
|---|---|
| `CvCityStateUAClasses.h` | CSUA 全部数据结构与接口声明 |
| `CvCityStateUAClasses.cpp` | effect 加载（`CacheResults`）、玩家级累加（`ApplyEffect`）、各项缓存 |
| `CvPlayer.cpp:20380` | `RefreshCSAllUAEffects` 每回合刷新 |
| `CvPlayer.cpp:18438` | `GetCSUAYieldPercentModifier` 每城市每产出 |
| `CvCity.cpp:13467` | `getBaseYieldRateModifier` 城市产出修正主函数 |
| `CvCity.cpp:15279` | `GetYieldRateFromUCSConversion` 转化效果（优化 1 目标） |
| `CvPlot.cpp:9278` | 埃里温相邻改良加成（每地块） |

> 表中及正文的行号已刷新为**当前值**（截至 `ba6bc2e`，2026-10-13）。三批优化（`0636a34`、`77fa9ad`、`54c5893`、`ba6bc2e`）落地后行号整体下移；若代码再变动，以函数名检索为准。
