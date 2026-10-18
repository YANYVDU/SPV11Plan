# CSUA 审查报告：魁北克（Quebec）

- 审查日期：2026-10-01
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 5 文件 **+162 / −4**；SP 5 文件 **+143 / −0**
- 结论摘要：三条盟友效果与一条朋友效果**逐条对得上设计稿**，**未发现功能性缺陷**。实现方式为**新建 1 张全国 yield 修正表 + CityStateUAEffects 扩展 1 列 + CvCultureClasses 三处分母替换 + 复用既有 PurchasedBuildingXP 表**。有 **1 处应修正的无效文本 tag**、**1 项待确认的设计口径**、**5 项非缺陷提示**。

---

## 一、改动清单

### MPDLL

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +19 / −1 | ① `CityStateUAEffects` 新增列 `CultureVictoryProgressModifier`（`:190-197`）；② 新建表 `CityStateUAEffect_UnknownInfluenceYieldModifiers`（`:452-464`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +32 / −0 | 新结构体 `UnknownInfluenceYieldModifierEntry`（`:98-105`）；`CvCityStateUAEffectEntry` / `CvPlayerCityStateUA` 的 getter、成员与解析声明 |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +70 / −0 | `#include "CvCultureClasses.h"`；读列与读新表；构造初始化；`Reset` 清空；`ApplyEffect` 聚合；`GetCultureVictoryProgressModifier` / `HasUnknownInfluenceYieldModifiers` / `CacheUnknownInfluenceCount` |
| `CvGameCoreDLL_Expansion2/CvCultureClasses.cpp` | +21 / −3 | 新增静态函数 `GetVictoryProgressLifetimeCulture`（`:2815-2831`）；`GetInfluenceLevel` / `GetTurnsToInfluential` / `GetCivLowestInfluence` 三处分母替换（`:2848` / `:2926` / `:2999`） |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +20 / −0 | `GetCSUAYieldPercentModifier` 新落点（`:18386-18400`）；`RefreshCSAllUAEffects` 调 `CacheUnknownInfluenceCount`（`:20158-20161`） |

> **既有机制复用说明**：效果③所依赖的 `CvCity::GrantPurchasedBuildingXP` 与表 `CityStateUAEffect_PurchasedBuildingXP` **并非本次新增**，而是 2026-08-09 提交 `fa2c6d4`（「CSUA: CityStateUAEffect_PurchasedBuildingXP」，为瓦莱塔设计）的产物；`CvCity.cpp` 本次**零改动**。魁北克只是在 SP 侧向该表追加 6 行。

### SP

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 / −0 | 城邦绑定 `MINOR_CIV_QUEBEC_CITY` → `CSUA_QUEBEC`（`:61`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +67 / −0 | 2 个效果（`:451-460`）、6 行 `PurchasedBuildingXP`（`:757-792`）、1 个 UA 条目（`:1731-1737`）、2 行 `UnknownInfluenceYieldModifiers`（`:2323-2336`） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +25 / −0 | 3 个文本 Tag（`:20374-20398`） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +25 / −0 | 3 个文本 Tag（`:18843-18867`） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +25 / −0 | 3 个文本 Tag（`:18649-18673`） |

### 效果设计（已核对与三语文本、XML 三方一致）

| 对象 | 设计文本 | 实现 |
| --- | --- | --- |
| 盟友① | 计算其他文明对盟友的文化胜利进度时，盟友的累积文化值额外 +50% | `CityStateUAEffects.CultureVictoryProgressModifier = 50`，经 `GetVictoryProgressLifetimeCulture` 在 `GetInfluenceLevel` / `GetTurnsToInfluential` / `GetCivLowestInfluence` 三处**虚增目标玩家文化分母** |
| 盟友② | 每有一个文明对盟友的影响程度为默默无闻，盟友全国产能和食物 +4%（上限 40%） | `CityStateUAEffect_UnknownInfluenceYieldModifiers` × ALLY：PRODUCTION / 4 / cap 40，FOOD / 4 / cap 40；`CacheUnknownInfluenceCount` 每回合统计「对盟友影响等级为 `UNKNOWN` 的已 met 主要文明数」，经 `GetCSUAYieldPercentModifier` 以 `计数 × 4%`（每 yield 各自截断 40%）输出（全国） |
| 盟友③ | 盟友购买城墙、军营、城堡、军械所、兵工厂、军事基地时，全部存活陆军 +10 经验 | `CityStateUAEffect_PurchasedBuildingXP` × ALLY 6 行（WALLS / BARRACKS / CASTLE / ARMORY / ARSENAL / MILITARY_BASE，`DOMAIN_LAND` / `XP 10`），消费于既有 `CvCity::GrantPurchasedBuildingXP` |
| 朋友① | 计算其他文明对朋友的文化胜利进度时，朋友的累积文化值额外 +20% | 同盟友①，`EFFECT_CSUA_QUEBEC_FRIEND` 的 `CultureVictoryProgressModifier = 20` |

设计稿来源：`1.城邦UA/海洋型.txt:40-44`（与 `未完成/海洋型-未完成.txt` 一致）。魁北克在 `城邦类型.txt:22` 归类为海洋型，`MinorCivilizations.Type = MINOR_CIV_QUEBEC_CITY`、`CSUA Type = CSUA_QUEBEC`（见 [[citystate-name-type-mapping]]，该城邦无命名错位）。

---

## 二、问题清单

### 应修正

#### D-1　城邦名引用了不存在的文本 tag

- 位置：`CSUA.xml:1733` `<Description>TXT_KEY_CITYSTATE_QUEBEC</Description>`。
- 证据：游戏本体中魁北克的正确 tag 是 **`TXT_KEY_CITYSTATE_QUEBEC_CITY`**——`Assets/DLC/Expansion/Gameplay/XML/Civilizations/CIV5MinorCivilizations.xml:137-139` 的 `Description` / `ShortDescription` / `Adjective` 全部使用 `_CITY` 后缀。以 `grep -w` 全盘检索文明 5 安装目录，**`TXT_KEY_CITYSTATE_QUEBEC`（无 `_CITY`）零命中**。
- 对照：CSUA.xml 中其余城邦的 `<Description>` 一律等于 `TXT_KEY_CITYSTATE_` + `MinorCivilizations.Type` 后缀（Panama → `PANAMA_CITY`、Vatican → `VATICAN_CITY`），魁北克漏了 `_CITY`，是**孤例**。
- 影响评估：**当前无可见影响**。经查 UI 侧只消费 `CityStateUAs.Help`（`CityStateStatusHelper.lua:67-85`、`SelectCityStates.lua:128-131`、`CivilopediaScreen.lua:5061-5064`），**未消费 `Description`**；C++ 侧 `CvCityStateUAEntry::CacheResults`（`CvCityStateUAClasses.cpp:1364-1373`）只读 `AllyEffectType` / `FriendEffectType`（`Description` 由 `CvBaseInfo` 泛化解析但无人调用其 getter）。
- 判定：**隐患**（一旦将来 UI/日志采用 `Description` 即会整串显示 tag 原文），且与其余 57 个城邦口径不一致。
- 建议修复：`TXT_KEY_CITYSTATE_QUEBEC` → `TXT_KEY_CITYSTATE_QUEBEC_CITY`。

### 待拍板（需确认，非缺陷）

#### Q-1　效果①的实际影响面超出「文化胜利进度」字面

- 位置：`CvCultureClasses.cpp:2848 / 2926 / 2999`（三处分母替换）、`:2815-2831`（`GetVictoryProgressLifetimeCulture`）。
- 现象：实现手段是**虚增 `CvPlayerCulture::GetInfluenceLevel` 的分母**（目标玩家的 `GetJONSCultureEverGenerated` × 1.5）。`GetInfluenceLevel` 不只服务文化胜利判定，还被以下系统共用，**全部会一并受影响**：
  - 文化胜利判定本身（`GetNumCivsInfluentialOn` → `GetInfluenceLevel`，`:2948-2965`）——**这是设计目标，已覆盖**；
  - 间谍：监视时间（`:3078`）、城邦盟友中的间谍等级（`:3113`）、主要文明城市中的间谍等级（`:3144`）；
  - 非文化旅游加成：商路科技（`:3022`）、征服减时/减人口损失（`:3050`）；
  - **意识形态压力**：`iCulturalDominanceOverUs` 的双向影响力差（`:3601 / 3758 / 3862`）；
  - AI 外交态度（`CvDiplomacyAI.cpp:5265 / 16219`）、AI 交易意愿（`CvDealAI.cpp:1799`）、AI 文化冲刺目标（`CvPlayerCulture::WantsDiplomatDoingPropaganda`，`:3963`）。
- 分析：从字面看，设计稿只承诺「文化胜利进度」；但 Civ5 中「胜利进度」与「影响等级」本就是同一枚硬币——影响百分比既决定胜利进度，也决定上述全部衍生效果。用「inflate 文化分母」实现，就**必然**是「盟友整体文化更难被渗透」的全局语义。
- 评价：这未必是缺陷，甚至可能是更合理的整体设计（城邦联盟 → 文化主权）。但需要你确认：**接受「盟友的文化影响等级整体被抬高」这一更宽的影响面，还是要退回到只在胜利判定/进度显示处 inflate 的窄实现**。
- 备注：若选窄实现，改动点会从 3 处集中到 `GetNumCivsInfluentialOn` + UI 显示函数，但与「进度条与影响等级一致」的原版手感会脱节。

### 提示（非缺陷）

#### P-1　`GrantPurchasedBuildingXP` 的注释把通用机制写成了瓦莱塔专属

- 位置：`CvCity.cpp:19891` 注释 `// Valletta UA: buying a specified building class grants all units of a domain XP`。
- 说明：该函数**不区分 `EffectType` 来源**，按表 `CityStateUAEffect_PurchasedBuildingXP` 的 `BuildingClassType` 全局匹配；瓦莱塔（PAGODA / 空军）与魁北克（6 军建 / 陆军）共用同一函数。注释只提瓦莱塔，后续维护者读魁北克代码时会被误导。
- 建议（可选）：改为中性措辞，如 `// CSUA (Valletta / Quebec): buying a listed building class grants XP to all units of a domain`。

#### P-2　效果①与效果②存在隐性串联

- 位置：`CvCityStateUAClasses.cpp:2635-2637`，效果②的计数调用 `kOther.GetCulture()->GetInfluenceLevel(m_pPlayer->GetID())`；而该函数对**持有魁北克效果的玩家自己**（`m_pPlayer`）已应用 50% 文化虚增。
- 说明：即效果①天然使「其他文明对盟友的影响等级」更容易停留在 `UNKNOWN`，从而**放大效果②的触发数量**。这是自洽的正反馈（文化孤立 → 更多默默无闻 → 更多产能/食物），**不是 bug**，但属未点明的耦合。若设计上不希望二者互相加成，需要另设判据。
- 数值影响：50% 虚增只把百分比压低约 1/3，仅当某文明恰好卡在 `EXOTIC` 阈值附近才会翻转等级，边缘效应。

#### P-3　`GetInfluenceTrend` 故意不改、`GetTurnsToInfluential` 口径不对称

- 位置：`CvCultureClasses.cpp:2884-2910`（趋势，未改）、`:2913-2945`（回合预测，改了）。
- 趋势未改的**理由正确**：`GetInfluenceTrend` 比较 `InfluenceT2/ CultureT2` 与 `InfluenceT1/CultureT1`，两回合文化同乘一个因子会约掉（代码即 `InfluenceT2 × LastTurnCulture > LastTurnInfluence × CultureT2` 的交叉相乘），因此注释「deliberately left alone」成立。
- 回合预测的**处理不对称**：`iCulture` 取虚增后的值（达标门槛被抬高），但 `iCultPerTurn` 取未虚增的 `GetTotalJONSCulturePerTurn()`（真实增长）。结果是「还需多少回合」的预测值偏大。
- 评价：方向与设计一致（更难过线 → 回合更多），仅记录，不构成缺陷。

#### P-4　`GrantPurchasedBuildingXP` 按 `BuildingClass` 全局匹配，不区分 `EffectType`

- 位置：`CvCity.cpp:19900-19912`，遍历 `GetPurchasedBuildingXPEntries()` 全表、仅比对 `m_iBuildingClass == eBC`。
- 说明：`CvPlayerCityStateUA` 把所有来源的 effect 条目 `push_back` 进同一 vector，因此若**两个城邦对同一建筑类**各配一条 XP，购买一次会**重复命中两次**、经验翻倍。
- 风险现状：瓦莱塔（PAGODA）与魁北克（6 军建）**当前无交集，安全**。属架构脆弱点 / 未来陷阱，非现行 bug。若后续有城邦复用同一建筑类，需在匹配时同时比对来源 effect。

#### P-5　效果②的计数有 1 回合缓存滞后

- 位置：`CacheUnknownInfluenceCount` 由 `RefreshCSAllUAEffects` 调用，后者按注释「Called each turn and on ally/friend change」（`CvPlayer.cpp:20087`）触发。
- 说明：盟友关系变化会**立即**触发刷新，无滞后；真正的滞后只发生在「其他文明的文化/旅游跨过阈值、使 `UNKNOWN` 计数改变」的场合，最多 1 回合后才反映到产能/食物加成。
- 评价：符合 [[csua-cache-lag-tolerance]] 的既定容忍度（1 回合瞬态、无崩溃），保留不改。

---

## 三、已验证无误项

1. **城邦绑定与 Type 正确**：`CSUA.sql:61` 为 `UPDATE MinorCivilizations SET UAType = 'CSUA_QUEBEC' WHERE Type = 'MINOR_CIV_QUEBEC_CITY'`，与 `CSUA.xml:1731-1737` 的 `CityStateUAs` 条目、`MINOR_CIV_QUEBEC_CITY` 一致，无命名错位。
2. **「默默无闻」映射正确**：设计术语「默默无闻」= `INFLUENCE_LEVEL_UNKNOWN`（最低档），有 SP 自身文本佐证——`TextInfos_zh_CN.xml:5123` 的等级对照表写作「默默无闻：0，初具风情：1，口耳相传：2，广受称誉：3，无远弗届：4，绝对支配：5」。实现取 `INFLUENCE_LEVEL_UNKNOWN` 无误。
3. **效果①在文化胜利判定链路上生效**：`GetNumCivsInfluentialOn`（`CvCultureClasses.cpp:2948-2965`）→ `GetInfluenceLevel` → `GetVictoryProgressLifetimeCulture`，目标玩家为魁北克盟友时其累积文化被 ×1.5，`iPercent = iInfluenceOn × 100 / 虚增文化` 下降，更难达到 `INFLUENTIAL`。语义与设计「累计文化值额外 +50%」精确对应。
4. **三处分母替换完整且无遗漏**：本次 diff 恰好替换 3 处（`GetInfluenceLevel:2848`、`GetTurnsToInfluential:2926`、`GetCivLowestInfluence:2999`），与注释声明一致；`GetInfluenceTrend` 有意保留原值，理由见 P-3。
5. **盟友 / 朋友互斥且归属正确**：`RefreshCSAllUAEffects`（`CvPlayer.cpp:20116-20123`）以 `IsAllies` 优先、`else if IsFriends` 择一应用。盟友只得 +50%（不含 +20%），朋友只得 +20%，无 50+20 叠加。数值 50/20 = 2.5 倍，符合设计全局规则第 2 条（朋友为盟友的 2-3 倍）。
6. **效果①为累加式、可正确归零**：`m_iCultureVictoryProgressModifier += pEffect->GetCultureVictoryProgressModifier() * iChange`（`CvCityStateUAClasses.cpp:1999`），`Reset()` 中归零（`:1665`）；失去盟友身份后经每回合全量重建自动清除，无残留。
7. **效果②每 yield 各自截断、且短路**：`iTotal = 计数 × YieldMod`，仅 `iTotal > Cap` 时截断为 `Cap`（`CvPlayer.cpp:18397`）；`HasUnknownInfluenceYieldModifiers()` 为空即整体短路，未持有魁北克效果的玩家零开销。PRODUCTION 与 FOOD 各 40% 上限，与设计「上限 +40%」一致（理解为每 yield 各自 40%）。
8. **效果②计数口径正确**：`CacheUnknownInfluenceCount`（`CvCityStateUAClasses.cpp:2624-2641`）以 `iPlayer == 本玩家` 排除自身，跳过 `!isAlive()` 与 `!isHasMet()`，未 met 者返回 `NO_INFLUENCE_LEVEL` 不计入；仅统计 `MAX_MAJOR_CIVS` 内**主要文明**，城邦不计，与设计「每有一个文明」口径一致。
9. **效果③建筑类与设计一一对应**：6 行 `BUILDINGCLASS_` 分别对应设计稿「城墙 / 军营(兵营) / 城堡 / 军械所(军械库) / 兵工厂 / 军事基地」，无缺漏、无多余；`DomainType = DOMAIN_LAND` 与「全部存活陆军」一致。
10. **效果③的触发路径为「购买」**：`GrantPurchasedBuildingXP` 的两个调用点均在 `CvCity::Purchase` 内——金币购买建筑分支（`CvCity.cpp:20008`）与信仰购买建筑分支（`:20204`）；**建造完成**路径**不**调用，与设计「购买时」精确一致。`firstUnit/nextUnit` 遍历即为存活单位。
11. **效果③只作用于购买者本人**：函数以 `GET_PLAYER(getOwner())` 取该城所属玩家，即购买方，遍历的也是**该玩家自己**的单位；不会误发给其他玩家。
12. **无需版本门控**：`CvPlayerCityStateUA` 为纯运行时缓存（`RefreshCSAllUAEffects` 每回合 `Reset` + 全量 `ApplyEffect` 重建，无 `Read`/`Write`），本次**未新增任何序列化成员**，不触发 CLAUDE.md 的版本门控要求。`m_iCultureVictoryProgressModifier` / `m_vUnknownInfluenceYieldModifiers` / `m_iCachedUnknownInfluenceCount` 均已在构造函数（`:1521-1523`）与 `Reset`（`:1664-1667`）中初始化。
13. **数据无重复主键**：`CSUA_QUEBEC` / `EFFECT_CSUA_QUEBEC_ALLY` / `EFFECT_CSUA_QUEBEC_FRIEND` 全 SP 各仅一处定义；新表 `CityStateUAEffect_UnknownInfluenceYieldModifiers` 仅魁北克两行；`PurchasedBuildingXP` 的 6 行与瓦莱塔的 PAGODA 行不重叠。
14. **三语文本齐全且语义一致**：`TXT_KEY_CSUA_QUEBEC_HELP`、`TXT_KEY_EFFECT_CSUA_QUEBEC_ALLY_HELP`、`TXT_KEY_EFFECT_CSUA_QUEBEC_FRIEND_HELP` 在中、繁、英三语均存在，数值 50 / 4 / 40 / 10 / 20 与设计稿、XML 三方一致；均追加于各语言文件**末尾**，未打乱既有分组；使用 `[ICON_PRODUCTION]` / `[ICON_FOOD]` / `[ICON_CULTURE]` 提升可读性。
15. **注释为英文**：新增 C++ / SQL 注释均为英文，符合 [[sp-english-comments-only]]。
16. **DLL 已含本次改动**：`BuildOutput/VS2022_ReleaseWin32/CvGameCore_Expansion2.dll` 与 `(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll` 均 5336576 字节、时间 2026-10-01 02:22，晚于全部源文件（最晚 `CvCultureClasses.cpp` 02:20）；二进制内 `CultureVictoryProgressModifier`、`UnknownInfluenceYieldModifiers` 均可检索到。
17. **行尾格式保持**：MPDLL 的 `UNIQUE_CITYSTATES.sql` / `CvCityStateUAClasses.cpp` / `CvCityStateUAClasses.h` / `CvPlayer.cpp` 维持 LF，`CvCultureClasses.cpp` 维持 CRLF；SP 五文件维持 LF。`git diff --numstat` 均为小改动（+19/−1、+70/−0、+32/−0、+21/−3、+20/−0），无整文件重写。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff` / `git diff --numstat`，核对改动规模、行尾与提交状态。
- 交叉核对 C++ 实现、XML 数据、三语文本、设计稿四者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvPlayerCulture::GetInfluenceLevel`（`CvCultureClasses.cpp:2834-2881`）、`GetInfluenceTrend`（`:2884-2910`）、`GetTurnsToInfluential`（`:2913-2945`）、`GetNumCivsInfluentialOn`（`:2948-2965`）、`GetCivLowestInfluence`（`:2985-3017`），以及全部 `GetInfluenceLevel` 下游消费点（间谍 / 商路 / 征服 / 意识形态 / AI 外交）。
- 回读 `CvCity::GrantPurchasedBuildingXP`（`CvCity.cpp:19893-19913`）及其两个调用点（`:20008`、`:20204`），确认触发路径为购买、单位为购买者本人陆军。
- 以 `grep -a -o` 在 DLL 二进制中检索新表名 / 列名，确认产物包含本次改动。
- 以 `grep -w 'TXT_KEY_CITYSTATE_QUEBEC'` 全盘检索文明 5 安装目录与 SP 仓库，交叉验证 D-1；并核读 `CIV5MinorCivilizations.xml:137-139` 的官方 tag。
- 与既有同类实现横向对照：`CultureVictoryProgressModifier` 对照 Ur 的 `WorldWonderHappiness`（同为 `CityStateUAEffects` 顶层标量列）；`UnknownInfluenceYieldModifiers` 对照 `Bucharest` 的 `WorldWonderYieldModifiers` / `DiplomatAbroad` 系列（同为「计数 × 每单位百分比 + 上限」结构）。

---

## 五、当前状态与建议处理顺序

### 状态

- MPDLL 工作区：5 文件 **+162 / −4**（未 commit）；DLL 已重编，产物在 `BuildOutput/VS2022_ReleaseWin32/` 与 `(1) CIV5MPDLL/DLL/`（02:22）。
- SP 工作区：5 文件 **+143 / −0**（未 commit）。
- 游戏根目录 DLL（`Documents\My Games\Sid Meier's Civilization 5\CvGameCore_Expansion2.dll`）与 MODS 目录**未更新**（未构建）。
- 文档滞后：`未完成/未完成清单.md` 海洋型仍列魁北克、拉古萨（`:27-28`），合计 46 / 12。魁北克完成后，海洋型应为 **13 / 1**、合计 **47 / 11**。

### 建议顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | 修 D-1（`CSUA.xml:1733` tag 补 `_CITY`） | 极小 |
| 2 | Q-1 影响面拍板（接受全局文化绝缘 / 收窄到胜利进度） | 无 |
| 3 | （可选）P-1 更新 `GrantPurchasedBuildingXP` 注释 | 极小 |
| 4 | 覆盖根目录 DLL 或构建模组，按下述步骤实机验证 | 小 |
| 5 | 刷新 `未完成/未完成清单.md`（魁北克 → 已完成，海洋型剩 1） | 小 |

### 实机验证步骤

1. **盟友效果①**：与魁北克结盟后，令另一主要文明对我方旅游；打开文化胜利/旅游界面，我方对其的**影响百分比**应比断盟时低约 1/3，达到「无远弗届（Influential）」所需回合数明显拉长。对照：断盟后百分比回弹。
2. **盟友效果②**：结盟后，对**我方影响等级为默默无闻（UNKNOWN）**的已 met 主要文明逐个计数（N），城市产出明细应出现「来自城邦修正: X%」，X = 4 × N（产能、食物各一，且各自 ≤ 40%）；让某文明的影响等级升到「初具风情」，计数应于**下一回合**减少 1、加成同步下降。
3. **盟友效果③**：结盟后购买城墙 / 军营 / 城堡 / 军械所 / 兵工厂 / 军事基地中任一，全国**所有陆军**（含已存在单位、不含海军/空军）应 +10 经验；**建造**（非购买）同一建筑**不应**给经验；连买两种清单内建筑应累计 +20。对照：瓦莱塔盟友购买宝塔应给**空军** +5（既有功能回归）。
4. **朋友效果**：与魁北克为朋友（非盟友），其文化虚增应为 ×1.2（而非 ×1.5），且**无**产能/食物加成、**无**购买经验。
5. **断交负例**：与魁北克断交后，上述全部效果应于关系变化当回合消失（验证 `RefreshCSAllUAEffects` 重建路径）。
6. **文本回归**：城邦外交界面 / 开局城邦选择列表 / 百科城邦页的 UA 说明应完整显示三段盟友效果 + 一段朋友效果（验证 `Help` 链）；若将来启用 `Description`，需先修 D-1。
