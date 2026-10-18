# CSUA 审查报告：推罗（Tyre）

- 审查日期：2026-09-28
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模（**仅推罗部分**）：MPDLL 4 文件约 +109；SP 5 文件 +127（CSUA.xml +76 / CSUA.sql +1 / 三语文本各 +25）
- 结论摘要：实现路径清晰、消费点齐全、归属正确、三语文本齐备，**但发现 1 项高优先级功能缺陷（建筑对象疑似选错）与 1 项计数口径缺陷（同城双建筑被计两次）**，另有核弹绕过减免、金钱覆盖面、缓存滞后等提示项。**建议先与用户确认建筑对象，再决定是否修复。**
- **处置状态（2026-09-29）**：P1-1 已确认为 `WOOD_DOCK`/`SHIPYARD` 并修复；P1-2 判定「按建筑叠加」为设计内行为，保留；P2-1 判定核弹绕过合理，仅修注释；另新增伤害预览 UI 减免行。详见文末第七节。

> 术语：设计中的「魅力」= `YIELD_TOURISM`（旅游）。本 UA 未涉及。

---

## 一、改动清单（推罗部分）

### MPDLL

| 文件 | 推罗改动 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +10 | 新建 `CityStateUAEffect_SpecialCityDamageReduction` 表（`:415-423`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +24 | 枚举 `SPECIAL_CITY_CONDITION_IS_OTHER_CONTINENT`（`:126`）；结构体 `SpecialCityDamageReductionEntry`（`:157-162`）；两处 getter/Has 声明与成员（`:416-420`、`:585-589`、`:868-879`、`:1096-1100`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +47 | `IS_OTHER_CONTINENT` 解析（`:24`）/布尔判定（`:33`）/求值（`:152-162`）；减免表 `CacheResults`（`:925-941`）；`Reset`（`:1650`）；`ApplyEffect`（`:2063-2072`）；`HasSpecialCityDamageReduction`（`:2644-2647`） |
| `CvGameCoreDLL_Expansion2/CvCity.cpp` | +28 | `changeDamage` 伤害减免消费点（`:17196-17223`） |

> 同工作区另混有**新加坡**的 MPDLL 改动（`CvPlayer.cpp` +13、`CvTechClasses.cpp` +19、以及 `CvCityStateUAClasses.{h,cpp}`/`UNIQUE_CITYSTATES.sql` 中的对应 hunk），提交时需按城邦拆分。

新增接口名：

- 表 `CityStateUAEffect_SpecialCityDamageReduction (EffectType, SpecialCityType, Percent)` —— Percent 为**普通百分比**（40 = −40% 受伤）
- 条件类型 `IS_OTHER_CONTINENT`（布尔，无 Value）
- 结构体 `SpecialCityDamageReductionEntry`
- `CvPlayerCityStateUA::HasSpecialCityDamageReduction()` / `GetSpecialCityDamageReductions()`
- 消费点：`CvCity::changeDamage`（唯一）

### SP

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 | `MINOR_CIV_TYRE` → `CSUA_TYRE` 绑定（`:57`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +76 | 1 个 UA（`:1700-1706`）、2 个效果（`:453-463`）、2 个特殊城市类型（`:2027-2032`）与 And 条件（`:2095-2104`）、金钱计数修正（`:2193-2199`）、伤害减免（`:2269-2277`）、产能建筑类修正（`:2312-2337`） |
| `Gameplay/XML/Localization/TextInfos_{zh_CN,en_US,zh_Hant_HK}.xml` | 各 +25 | 3 个文本 Tag × 3 语言，追加于各文件末尾 |

---

## 二、效果设计与 XML 三方对照

| 对象 | 设计文本 | 实现 | 状态 |
| --- | --- | --- | --- |
| 盟友 | 码头、船坞 → 全国 +10% 产能 | `HARBOR`/`SEAPORT` × `YIELD_PRODUCTION` × 10（global） | **建筑对象待确认（见 P1-1）** |
| 盟友 | 沿海城市受到伤害 −40% | `SPECIAL_CITY_TYRE_COASTAL` × `Percent` 40 | 一致 |
| 盟友 | 每座与原始首都不同大陆的城市 → 全国 +5% 金钱 | `SPECIAL_CITY_TYRE_OTHER_CONTINENT` × `YIELD_GOLD` × 5（count） | 一致 |
| 朋友 | 码头、船坞 → 全国 +4% 产能 | `HARBOR`/`SEAPORT` × `YIELD_PRODUCTION` × 4（global） | **建筑对象待确认（见 P1-1）** |

数值三方一致（10 / 40 / 5 / 4）；盟友三条效果、朋友一条效果，划分正确。

---

## 三、问题清单

### P1-1　建筑对象疑似选错：「码头、船坞」≠「港口、海运码头」（需用户确认）

设计写的是**码头、船坞**，实现用的是 `BUILDINGCLASS_HARBOR`（`CSUA.xml:2315`）与 `BUILDINGCLASS_SEAPORT`（`:2321`）。但在 SP 的术语体系里，这四个词对应**四种不同建筑**：

| SP 显示名 | 建筑类 | 来源 |
| --- | --- | --- |
| 灯塔 | `BUILDINGCLASS_LIGHTHOUSE` | 政策文本 |
| **港口** | `BUILDINGCLASS_HARBOR` | 政策文本 |
| **码头** | `BUILDINGCLASS_WOOD_DOCK` | 政策文本 |
| **海运码头** | `BUILDINGCLASS_SEAPORT` | 政策文本 |
| **船坞** | `BUILDINGCLASS_SHIPYARD` | 政策文本 |

证据链：

1. **SP 自己的政策文本**：`TextInfos_zh_CN.xml:7370-7371`（`TXT_KEY_POLICY_COASTAL_ADMINISTRATION_HELP`）写明「灯塔、港口、码头使所在城市的产能和科研产出提高3%」「海运码头、船坞使所在城市的产能和科研产出提高5%」——五个词并列，互不相同。
2. **对应的实现映射**：`Gameplay/SQL/Policies/PoliciesEffect.sql:22-44` 把 3% 组映射为 `LIGHTHOUSE` / `HARBOR` / `WOOD_DOCK`，把 5% 组映射为 `SEAPORT` / `SHIPYARD`。即 **码头 = `WOOD_DOCK`、船坞 = `SHIPYARD`**。
3. **同作者的同类设计**：开普敦设计写「灯塔、**港口**、**海运码头**、国际自由港」，其实现（`CSUA.xml:1196-1240`）正是 `LIGHTHOUSE` / `HARBOR` / `SEAPORT` / `INTERNATIONAL_SEAPORT`——证明该设计者表达「Harbor/Seaport」时会用「港口/海运码头」，而非「码头/船坞」。
4. **建筑确实存在且可造**：`BUILDINGS.xml:2353`（`BUILDING_WOOD_DOCK`，`BUILDINGCLASS_WOOD_DOCK`，`TECH_FISHERY`）、`:2378`（`BUILDING_SHIPYARD`，`BUILDINGCLASS_SHIPYARD`，`TECH_STEAM_POWER`）。

**影响**：

- 若设计本意为 `WOOD_DOCK`/`SHIPYARD` → 实现挂错了建筑，效果完全不落在设计对象上（应改 `CSUA.xml:2315,2321,2328,2334`）。
- 无论哪种解读，**中文文本「码头或船坞」与 SP 内实际显示名存在歧义**：玩家在 UI 中看到的建筑叫「港口」「海运码头」，而 UA 描述说的是「码头或船坞」——而游戏里确实另有名为「码头」「船坞」的建筑。
- 英文文本 `TextInfos_en_US.xml:20243,20254,20262` 写的是 `Harbor or Seaport`，若按 SP 命名应为 `Wood Dock or Shipyard`。

**建议**：请用户确认「码头、船坞」指哪两组建筑，然后二选一：

- 若指 `WOOD_DOCK`/`SHIPYARD`：改 4 处 `BuildingClassType`，并把英文文本改为 `Wood Dock or Shipyard`（中文文本可保留）。
- 若确实指 `HARBOR`/`SEAPORT`：中文文本应改为「港口、海运码头」，英文保持 `Harbor or Seaport`。

### P1-2　同一城市同时拥有两类建筑时被计两次（+20% 而非 +10%）

`BuildingClassGlobalYieldModifiers` 的计数来自 `CvPlayer::getBuildingClassCount`（`CvPlayer.cpp:18334`），即**按建筑类逐个计数**，而接口自己的注释就写明：

> For one-per-city dummy buildings (city scale / corruption tiers) this equals the number of cities of that tier; **only use it with dummy building classes**.（`CvCityStateUAClasses.h:164-167`）

新加坡用这张表之所以安全，是因为规模假建筑每城恰好一个。推罗用的是**真实建筑**，而两组候选建筑都不互斥：

- `HARBOR` 与 `SEAPORT`：`Buildings.xml:1524-1526` 有 `Building_ClassesNeededInCity: BUILDING_SEAPORT ← BUILDINGCLASS_HARBOR`，即**拥有海运码头的城市必然已有港口**。
- `WOOD_DOCK` 与 `SHIPYARD`：二者无前置关系，且 `WOOD_DOCK` 在 `TECH_MARINE_ENGINEERING` 过期后**仍保留在城市中**（`Buildings.xml:2369`），工业时代城市可同时持有二者。

于是 `CSUA.xml:2312` 注释「每城唯一，计数即城市数」的假设不成立：一座同时拥有两类建筑的城市会贡献 **+10% + 10% = +20%**，与设计/文本的「每座城市 +10%」矛盾（朋友档同理，+8% 而非 +4%）。

**建议**：

- 若要严格「每城一次」：现有接口无法表达（`SpecialCityType` 条件枚举没有 `HAS_BUILDINGCLASS`）。需在 DLL 新增条件类型（如 `HAS_BUILDINGCLASS`，Value = 建筑类）+ 复用 `CityStateUAEffect_SpecialCityCountYieldModifiers`（该表已按城市计数），再在 SP 建一个 `SPECIAL_CITY_TYRE_PORT` 类型。
- 若接受「每建筑一次」：则需修正中英文文本措辞（如「每座拥有码头或船坞的城市」→「每处码头/船坞」），并修正 `CSUA.xml:2312` 与 `CvCityStateUAClasses.h:164-167` 的注释，说明本 UA 是有意把真实建筑类用于该表。

### P2-1　核弹伤害绕过 40% 减免（`setDamage` 直写）

`CvCity::changeDamage` 的减免只覆盖走 `changeDamage` 的伤害路径。实测该路径覆盖：

- 空袭：`CvUnitCombat.cpp:1379` `pCity->changeDamage(iDamage)`
- 近战/远程攻城：`CvUnitCombat.cpp:2312` `pCity->changeDamage(iAttackerDamageInflicted)`
- 火山爆发：`CvPlot.cpp:7032,7089`

但**核爆路径直接写绝对伤害**：`CvUnitCombat::ApplyNuclearExplosionDamage`（`CvUnitCombat.cpp:3276`）调用 `pkCity->setDamage(kEntry.GetFinalDamage())`，绕过 `changeDamage`，故沿海城市遭核弹时**不减伤**。

同时，SQL 建表注释（`UNIQUE_CITYSTATES.sql:415-416`）与结构体注释（`CvCityStateUAClasses.h:157-158`）都声称 "from all sources"，与实际不符。

**建议**：确认核弹是否应计入。若不需覆盖（核弹属稀有且强力的终结手段，其他 CSUA 亦无同类减免），至少修正注释措辞为「来自战斗/空袭/火山等经 changeDamage 的伤害」；若需覆盖，则在核爆路径对 `kEntry.GetFinalDamage()` 同样套用减免。

### P3-1　「全国 +5% 金钱」实际不含商路金钱

该加成走 `CvPlayer::GetCSUAYieldPercentModifier`（`CvPlayer.cpp:18315-18323`）→ `CvCity::GetBaseYieldRateModifier`（`CvCity.cpp:13605`），只作用于**城市金钱产出**。SP 中商路金走独立通路（`GetTradeConnectionValueTimes100`，见 `hormuz-csua-and-trade-gold-refactor`），不含在此修正内。

这是既有系统性口径（新加坡、开普敦等「全国 +X% 金钱」同此），**非本次引入**，仅记录：字面「全国金钱」的实际覆盖面小于玩家直觉。

### P3-2　计数缓存最多滞后 1 回合

`SPECIAL_CITY_TYRE_OTHER_CONTINENT` 的城市计数由 `CacheSpecialCityMatches`（`CvCityStateUAClasses.cpp:2572-2636`）在 `CvPlayer::RefreshCSAllUAEffects`（`CvPlayer.cpp:20106`）中每回合重建，而后者由 `RefreshCSAlliesFriends` → `CvPlayer::doTurn`（`CvPlayer.cpp:5418-5421`）触发。故当回合新建/失去城市、迁都等不会立即反映，最多滞后 1 回合。属既有容忍度内（见 `csua-cache-lag-tolerance`），仅记录。

### P3-3　产出加成无归因明细

产能与金钱加成经 `GetCSUAYieldPercentModifier` 汇入城市产出修正，tooltip 显示统一的 `TXT_KEY_PRODMOD_CITYSTATE_UA`（「来自城邦修正: N%」），不区分「每座码头 +10%」的构成。与绝大多数既有 CSUA 一致，非本次引入。归属判定正确（数值不依赖城市自身 → 走全局通路，符合 `csua-yield-tooltip-attribution`）。

### P3-4　伤害减免的整数截断

`iChange = iChange * (100 - iReduction) / 100`（`CvCity.cpp:17217`）为整数向下取整，小伤害（如 1 点）会被截为 0 再被 `if (iChange < 1) iChange = 1` 钳回 1，等于无减免。属设计内防护（保证命中至少造成 1 点），仅记录。

---

## 四、已验证无误项

1. **`IS_OTHER_CONTINENT` 口径正确**：用**该城市所有者自己**的原始首都坐标（`kPlayer.GetOriginalCapitalX/Y`），而非当前首都；原始首都不存在（坐标 −1）时 `return false` 失败关闭；比较 `getLandmass()`（连续陆块），与巴拿马跨大陆商路同口径（`CvCityStateUAClasses.cpp:152-162`）。
2. **`IS_COASTAL` 语义正确**：`CvCity::isCoastal()` → `plot()->isCoastalArea(-1)` → 以 `MIN_WATER_SIZE_FOR_OCEAN`(10) 为门槛（`CvPlot.cpp:1210-1224`），湖泊不计，与注释一致。
3. **减免只在受伤方向生效**：`if (iChange > 0)` 守卫，回血（`CvCity.cpp:2305` `changeDamage(-iHitsHealed)`）不受影响；多行命中累加后钳制 90；结果至少 1 点。
4. **效果归属正确**：减免存于**盟友玩家**的 `m_pCityStateUA`，落在盟友城市而非城邦自身；`GetPlayerCityStateUA()` 对城邦/蛮族返回 `NULL`（`CvPlayer.cpp:15444-15449`），故城邦自己的城市不吃该减免。
5. **盟友/朋友互斥且优先级正确**：`RefreshCSAllUAEffects`（`CvPlayer.cpp:20080-20087`）以 `IsAllies` 优先、`else if IsFriends` 择一 `ApplyEffect`，两条效果不会同时生效。
6. **表选择与语义匹配**：推罗「全国 +X% 产能」用**全局**表 `BuildingClassGlobalYieldModifiers`；对照墨尔本「为城市提供 10%」用**本地**表 `BuildingClassYieldModifiers`（`CSUA.xml:823-835`），选表逻辑一致。
7. **量纲正确**：`SpecialCityDamageReduction.Percent` 为普通百分比，消费端直接 `(100 - r)/100`；`SpecialCityCountYieldModifiers.YieldMod` 为普通百分比，消费端 `× YieldMod × 100` 转基点（因 `GetCSUAYieldPercentModifier` 末尾 `return iMod / 100`）。两处均无乘/除 100 抄错。
8. **缓存表已覆盖所需类型**：`CacheSpecialCityMatches` 按 `SpecialCityYieldModifiers` / `SpecialCityCountYieldModifiers` / `SpecialCityPopulationYieldModifiers` 三张表推导需缓存类型（`CvCityStateUAClasses.cpp:2581-2596`），`SPECIAL_CITY_TYRE_OTHER_CONTINENT` 被 count 表引用故已缓存；`SPECIAL_CITY_TYRE_COASTAL` 仅被减免表引用、走实时判定，不需要缓存（设计如此，且注释已说明）。
9. **SQL ↔ C++ 列序对齐**：`select SpecialCityTypes.ID as SpecialCityTypeID, Percent`（`CvCityStateUAClasses.cpp:930`）与 `entry.m_iSpecialCityType / m_iPercent`（`:937-938`）一一对应。
10. **建表存在且引用完整**：`CityStateUAEffect_SpecialCityDamageReduction` 在 `UNIQUE_CITYSTATES.sql:419` 建表，`EffectType`/`SpecialCityType` 均有外键引用；SP 侧 `CSUA.xml:2269-2277` 的行落在该元素内。
11. **XML 格式良好**：`CSUA.xml` 与三个 `TextInfos` 均通过 XML 解析校验。
12. **三语文本齐备且一致**：`TXT_KEY_CSUA_TYRE_HELP` / `TXT_KEY_EFFECT_CSUA_TYRE_ALLY_HELP` / `TXT_KEY_EFFECT_CSUA_TYRE_FRIEND_HELP` 在 `zh_CN`(`:18709-18733`) / `en_US`(`:20240-20264`) / `zh_Hant_HK`(`:18515-18539`) 各 3 条，数值（10 / 40 / 5 / 4）与盟友/朋友划分一致，均追加于各文件末尾。
13. **城邦绑定可解析**：`MINOR_CIV_TYRE` 与 `TXT_KEY_CITYSTATE_TYRE` 均由基础游戏提供（`Assets/DLC/Expansion2/Gameplay/XML/Civilizations/CIV5MinorCivilizations.xml` 等），SP 无需自建，与 `CSUA.xml:1702` 的 `Description` 匹配。
14. **无序列化需求**：`CvPlayerCityStateUA` 不参与 `Read`/`Write`（无 `MOD_SERIALIZE` 用法），`m_pCityStateUA` 在 `CvPlayer` 构造时 `FNEW`、析构 `SAFE_DELETE`、`init` 时 `Init`，效果每回合 `Reset` 后全量重建。本次新增成员为运行时状态，**无需版本门控**，DLL 版本号 164 保持不变，符合内测期规则（`dev-build-version-control`）。
15. **行尾格式保持**：SP 的 `CSUA.xml`/`CSUA.sql`/三语 `TextInfos` 全为 LF（CR=0）；MPDLL 的 `CvCityStateUAClasses.{h,cpp}`/`CvPlayer.cpp`/`UNIQUE_CITYSTATES.sql` 为 LF，`CvCity.cpp` 保持其原有的 **CRLF**（新增行经 `cat -A` 核验带 `^M`），无整篇翻转。
16. **构建产物不落后**：`(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll` 时间戳 2026-09-28 22:39，**晚于**全部相关源码（`CvPlayer.cpp` 22:13、`CvCityStateUAClasses.h` 22:35、`CvCityStateUAClasses.cpp`/`CvCity.cpp` 22:36、建表 SQL 22:34）。新加坡报告中的「DLL 早于源码」阻塞已消除。

---

## 五、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff`（导出至临时文件后分段读取，避免截断误判）。
- 交叉核对设计文本（`未完成\商业型-未完成.txt:8-12`、`1.城邦UA\商业型.txt` 推罗段）、SP XML 数据、三语文本三者数值与语义。
- **术语溯源**（本次关键）：`TextInfos_zh_CN.xml:7370-7371`（海事政策文本，五词并列）→ `Gameplay/SQL/Policies/PoliciesEffect.sql:22-44`（五词到建筑类的映射）；对照开普敦 `CSUA.xml:1196-1240` 的设计用词与实现类。
- 回读引擎侧被调用函数确认语义：`CvCity::changeDamage`（`CvCity.cpp:17191`）、`CvPlayer::GetCSUAYieldPercentModifier`（`:18235`）、`CvCity::IsSpecialCityType`（`:23888`）、`CvPlayerCityStateUA::CacheSpecialCityMatches`（`CvCityStateUAClasses.cpp:2572`）、`CvPlayer::GetPlayerCityStateUA`（`:15444`）、`CvPlayer::RefreshCSAllUAEffects`（`:20054`）、`CvCity::isCoastal`（`:9211`）/`CvPlot::isCoastalArea`（`CvPlot.cpp:1210`）。
- 枚举城市受伤路径：`grep changeDamage / setDamage` 全库扫描，确认核爆 `CvUnitCombat.cpp:3276` 为唯一绕过点。
- 核对建筑数据来源：`Buildings.xml:1232-1256`（Harbor）、`:1308-1329`（Seaport）、`:1515-1534`（Seaport ← Harbor 前置）、`:2353-2396`（Wood Dock / Shipyard）。
- 用 Python `xml.dom.minidom` 校验四个 XML 的格式良好性；用 `tr -dc '\r'` 逐文件统计 CR 数以确认行尾未翻转。
- 核对时间戳：`ls -l --time-style` 比对 DLL 与各源码。

---

## 六、当前状态与建议处理顺序

### 状态

- MPDLL 工作区：6 文件 +266 / −1（未 commit），**含新加坡与推罗两个城邦**（推罗约 +109）
- SP 工作区：5 文件 +291 / −0（未 commit），**含新加坡与推罗两个城邦**（推罗 +127）
- DLL 产物时间戳 2026-09-28 22:39，晚于全部相关源码
- 尚未构建模组；缓存数据库 `Civ5DebugDatabase.db` 中 `CSUA_TYRE` 相关数据为空（尚未加载新模组的正常状态）

### 建议顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | **确认 P1-1 建筑对象**（Wood Dock/Shipyard 还是 Harbor/Seaport） | 决策 |
| 2 | 按 P1-1 结论改 `BuildingClassType` 与英文文本，或改中文文本 | 小 |
| 3 | 确认 P1-2 计数口径（每城 vs 每建筑）；若每城则需新增 `HAS_BUILDINGCLASS` 条件类型 | 中（DLL） |
| 4 | 确认 P2-1 核弹是否需覆盖减免；否则修注释 | 小 |
| 5 | 实机验证（见下） | 小 |
| 6 | P3-1 / P3-3 平衡与归因评估 | 可选 |

### 实机验证步骤（建议）

1. 用世界编辑器放置推罗并结为盟友，**新开存档**（本次含建表 SQL）。
2. **产能加成**：使盟友一座沿海城市拥有港口/海运码头（或 Wood Dock/Shipyard，取决于 P1-1 结论）→ 城市产出明细出现「来自城邦修正: +10%」；再补上第二类建筑 → 观察是 +10%（每城）还是 +20%（每建筑），据此确认 P1-2。
3. **沿海减伤**：让敌方攻击盟友沿海城市，对比同回合非沿海城市的同等攻击伤害，确认约为 60%。
4. **跨大陆金钱**：在另一大陆建城 → 城市产出明细金钱 +5%；迁都后观察是否切换（缓存最多滞后 1 回合）。
5. **朋友档**：降为朋友关系 → 只剩 +4% 产能，无减伤、无金钱。
6. **负例**：与推罗无关系 → 城市产出明细不应出现「来自城邦修正」条目。
7. 数据库校验：`SELECT * FROM CityStateUAEffect_SpecialCityDamageReduction;` 应有 1 行（Percent=40）。

### 需注意的连带事项

- **工作区混有新加坡改动**：SP 与 MPDLL 两侧的 `CSUA.xml`/`CSUA.sql`/三语文本/`CvCityStateUAClasses.{h,cpp}`/`UNIQUE_CITYSTATES.sql` 均同时含新加坡与推罗 hunk。若按城邦拆分提交，需逐 hunk 分离（`CvPlayer.cpp`、`CvTechClasses.cpp` 为新加坡专属，推罗不涉及）。
- **API 说明库未同步**：按既有约定（CSUA 全部完成前不更新），本次未更新 `d:\Git\CIV5\dyy\Civ5-MPDLL-API说明`；待 CSUA 全部完成后统一重写。

---

## 七、审查后处置（2026-09-29）

用户裁决与对应改动如下。

### 7.1　P1-1 建筑对象 → 确认为 `WOOD_DOCK` / `SHIPYARD`（已修复）

**裁决**：设计文本「码头、船坞」即 SP 中名为「码头」「船坞」的建筑，非「港口」「海运码头」。

改动：

- SP `Gameplay/XML/CSUA/CSUA.xml`：盟友/朋友共 4 行 `BuildingClassType` 由 `BUILDINGCLASS_HARBOR` / `BUILDINGCLASS_SEAPORT` 改为 `BUILDINGCLASS_WOOD_DOCK` / `BUILDINGCLASS_SHIPYARD`；相邻注释改为「每处码头/船坞→全国产能+X%（按建筑逐个计数，同城两类叠加为+2X%）」。
- SP 三语文本 `TextInfos_{zh_CN,en_US,zh_Hant_HK}.xml`：`TXT_KEY_CSUA_TYRE_HELP` / `TXT_KEY_EFFECT_CSUA_TYRE_ALLY_HELP` / `TXT_KEY_EFFECT_CSUA_TYRE_FRIEND_HELP` 由「每座拥有码头或船坞的**城市**使全国+10%产能」改为「每**处**码头、船坞使全国+10%产能」；英文由 `Harbor or Seaport` 改为 `Wood Dock or Shipyard`。

### 7.2　P1-2 计数口径 → 保留「按建筑叠加」（不修行为）

**裁决**：同城同时拥有码头与船坞时叠加为 +20%（朋友 +8%）属设计内行为，保留。

改动：仅同步注释口径，避免后续误读为「每城唯一」：

- SP `CSUA.xml`：推罗效果块注释说明「按建筑逐个计数，同城两类叠加」。
- MPDLL `CvCityStateUAClasses.h:164-167`：`BuildingClassGlobalYieldModifierEntry` 注释放宽——不再写「only use it with dummy building classes」，改为说明真实建筑类亦可用、按建筑逐个计数（同城两类建筑计两次），并补上推罗用例。

### 7.3　P2-1 核弹绕过 → 保留绕过（仅修注释）

**裁决**：核弹伤害不经 `changeDamage`、不吃 40% 减免，合理，保留行为。

改动（全部为注释，无行为变更）：

- MPDLL `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql`：建表注释删除 "from all sources"，补注「仅 `changeDamage` 路径生效，核爆直写 `setDamage` 故绕过」。
- MPDLL `CvCityStateUAClasses.h:157-161`：结构体注释同上修正。
- MPDLL `CvCity.cpp` `changeDamage`：注释补一句说明核爆绕过。

### 7.4　新增：单位对城市伤害预览 UI 的减免行与提示

**需求**：预览需体现减免，并给出提示。

改动：

- MPDLL 新增 Lua 接口 `CvLuaCity::GetCSUADamageReductionPercent()`（`MOD_SP_UNIQUE_CITYSTATE` 门控），对应 `CvCity::GetCSUADamageReductionPercent() const`——汇总命中行的 `Percent` 并钳制 90，无减免返回 0。`CvCity::changeDamage` 重构为复用该函数（行为等价）。
- SP `UI/InGame/WorldView/EnemyUnitPanel.lua`：计算 `iMyDamageInflicted` 后、钳制到城市最大 HP 前，按 DLL 同序（基础伤害 → 固定增减 → 百分比减免，至少 1 点）套用减免；在 `TheirCombatResultsStack` 增加一行「城邦伤害减免 −40%」，并挂 `SetToolTipString` 提示。
- SP 三语文本新增 `TXT_KEY_EUPANEL_CSUA_DAMAGE_REDUCTION_SP` 与 `TXT_KEY_EUPANEL_CSUA_DAMAGE_REDUCTION_TT_SP`（追加于各文件末尾）。

**说明**：该接口为纯 getter，无序列化成员，**无需版本门控**，DLL 版本号仍为 164。UI/Gameplay Lua 支持热读取，读档即生效；但新 Lua 接口依赖新 DLL，需先编译替换 DLL 再进游戏。

### 7.5　未处置项

- P3-1（金钱不含商路金）、P3-3（无归因明细）：既有系统性口径，非本次引入，保留。
- P3-2（缓存滞后 1 回合）、P3-4（整数截断至少 1 点）：设计容忍范围内，保留。
