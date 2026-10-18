# CSUA 审查报告：布宜诺斯艾利斯（Buenos Aires）

- 审查日期：2026-10-02
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 2 文件 **+34 / −5**；SP 5 文件 **+118 / −0**
- 权威设计稿：`d:\Git\CIV5\dyy\SP V11\1.城邦UA\文化型.txt:25-29`
- 结论摘要：四条效果的数据面（三条盟友 + 一条朋友）**已全部写入**，其中效果①（每城 +1 大音乐家点数）、效果②（每城市规模假建筑各 +1）、效果③（大音乐家不死亡 + 保留 50% 演唱会魅力）的实现路径与档位**均正确**。**发现 3 项应修正缺陷**：**A-1【严重】CSUA.xml 主表 `<CityStateUAs>` 缺少 `CSUA_BUENOS_AIRES` 条目，导致该城邦的全部效果均不会被加载（当前完全无效）**；**B-1【中】效果④ 数值 `YieldMod=5` 单位误用，实际为 +0.05%/杰作，设计为 +5%，差 100 倍，应为 500**；**C-1【中】效果③ 的「不死亡」判定未限定大音乐家，盟军的大艺术家/大作家创作杰作后同样不死亡**。另有 5 项提示（非缺陷）。

---

## 一、改动清单

### MPDLL

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `CvGameCoreDLL_Expansion2/CvUnit.cpp` | +28 / −5 | `createGreatWork()` 内新增布宜诺斯艾利斯分支（`:9917-9935`）：命中时置 `bNoDeathAfterGreatWork`、`SetGreatWork(NO_GREAT_WORK)`、`SetTourismBlastStrength(×retention/100)`；原 `DoGreatPersonExpended` + `kill(true)` 移入 `if (!bNoDeathAfterGreatWork)`（`:9937-9949`） |
| `CvGameCoreDLL_Expansion2/CvEconomicAI.cpp` | +6 / −0 | `GetBestGreatWorkCity()` 增 `eGreatWork == NO_GREAT_WORK` 提前返回 NULL（`:897-902`），配合效果③——已创作过杰作而存活的单位不再被 AI 指派去创作 |

> 注：`GPNoDeathAfterGreatWork` / `GPConcertTourismRetentionPercent` 两列与其 DB 建表注释在 MPDLL 属**已提交**内容（`(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql:54-55`；`CvCityStateUAClasses.h:321-322,552-553,829-830,1139-1140`；`CvCityStateUAClasses.cpp:285-286,424-425,1250-1251,1652-1653,1779-1780,2003-2004,2540-2541`），本次工作区未改动。

### SP

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 / −0 | 城邦绑定 `MINOR_CIV_BUENOS_AIRES` → `CSUA_BUENOS_AIRES`（`:71`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +75 / −0 | 2 个效果行（`:553-562`）+ `GreatPersonPoints` 1 行（`:575-579`）+ `BuildingGreatPersonPoints` 9 行（`:684-737`）+ `GreatWorkYieldModifiers` 1 行（`:2209-2214`）。**未新增主表 `<CityStateUAs>` 条目**（见 A-1） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +14 / −0 | 2 个文本 Tag（`:20634-20648`） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +14 / −0 | 2 个文本 Tag（`:19103-19116`） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +14 / −0 | 2 个文本 Tag（`:18909-18922`） |

### 效果设计对照表

| 对象 | 设计文本 | 实现 | 判定 |
| --- | --- | --- | --- |
| 盟友 ① | 盟友的城市 +1 大音乐家点数 | `CityStateUAEffect_GreatPersonPoints`：ALLY 行 `SPECIALIST_MUSICIAN = 1`；`CvCity::GetGreatPersonPointsFromUA`（`CvCity.cpp:12116-12127`）→ `CvCityCitizens.cpp:2316`（`×100`，即每城 1 点/回合） | **符合设计** |
| 盟友 ② | 盟友城市的每个城市规模假建筑各提供 1 大音乐家点数 | `CityStateUAEffect_BuildingGreatPersonPoints`：ALLY 7 档 `CITY_SIZE_TOWN…GLOBAL` 各 `Points=1`；`GetBuildingGreatPersonPointsForCity`（`CvCityStateUAClasses.cpp:2651-2665`）按 `pCity->GetNumBuildingClass()` **累加** | **符合设计**（假建筑累积制，见验证项 4） |
| 盟友 ③ | 盟友的大音乐家在产出音乐杰作后不会立刻死亡，而是丧失杰作产出能力并保留 50% 的演唱会魅力 | `GPNoDeathAfterGreatWork=true` + `GPConcertTourismRetentionPercent=50`；`CvUnit.cpp:9917-9949`：不 `kill`、`SetGreatWork(NO_GREAT_WORK)`、`SetTourismBlastStrength(×50/100)` | **数值/机制符合，但触发面过宽**（见 C-1） |
| 盟友 ④ | 盟友每个音乐杰作提高全国 5% 魅力 | `CityStateUAEffect_GreatWorkYieldModifiers`：ALLY `GREAT_WORK_MUSIC → YIELD_TOURISM`，`YieldMod=5`；路径 `CvCultureClasses.cpp:4701-4703` → `CvCity.cpp:13647` → `CvPlayer::GetCSUAYieldPercentModifier`（`CvPlayer.cpp:18293-18304`） | **路径正确、数值错**（见 B-1） |
| 朋友 ⑤ | 朋友城市规模达到小型城市时 +1 大音乐家点数，达到中型城市时额外 +1 | `CityStateUAEffect_BuildingGreatPersonPoints`：FRIEND `CITY_SIZE_SMALL=1`、`CITY_SIZE_MEDIUM=1`；FRIEND 效果行无其余数据 | **符合设计** |

设计稿来源：`1.城邦UA/文化型.txt:25-29`。`MINOR_CIV_BUENOS_AIRES` 确在文明 5 本体定义（`Assets/DLC/Expansion2/Gameplay/XML/Civilizations/CIV5MinorCivilizations.xml:668-676`），城邦类型 `MINOR_TRAIT_CULTURED`（文化型），与设计归类一致。

---

## 二、问题清单

### 应修正

#### A-1【严重】主表 `<CityStateUAs>` 缺少 `CSUA_BUENOS_AIRES` 条目：该城邦全部效果不生效

- 位置：`Gameplay/XML/CSUA/CSUA.xml:1636-2029`（`<CityStateUAs>` 区间）。
- 现象：`CSUA.sql:71` 已将 `MINOR_CIV_BUENOS_AIRES.UAType` 设为 `CSUA_BUENOS_AIRES`，但主表中**没有** `<Type>CSUA_BUENOS_AIRES</Type>` 记录（主表末条为 `CSUA_KYZYL`，`:2023-2027`）。
- 证据：
  - `CSUA.sql` 的 `UPDATE MinorCivilizations SET UAType` 共 **57** 条（唯一值 57 个），主表 `<CityStateUAs>` 仅 **56** 条 `CSUA_*` 记录，二者恰好差 1 条，缺的正是 `CSUA_BUENOS_AIRES`；
  - 全 SP 仓库检索 `CSUA_BUENOS_AIRES`，仅命中 `EFFECT_CSUA_BUENOS_AIRES_ALLY/FRIEND` 及其子表引用（`CSUA.xml:554-737,2209-2214`）与绑定行（`CSUA.sql:71`），**无 `<Type>CSUA_BUENOS_AIRES</Type>` 主记录**。
- 后果：加载时 `CvPlayer::RefreshCSAllUAEffects` 走 `pkMinorCivInfo->GetUAType()` → `GC.GetGameCityStateUAs()->GetEntryByType("CSUA_BUENOS_AIRES")`，返回 NULL 后 `continue`（`CvPlayer.cpp:20211-20217`）。因此 `EFFECT_CSUA_BUENOS_AIRES_ALLY/FRIEND` **永远不会被实例化**，其下的 `GreatPersonPoints` / `BuildingGreatPersonPoints` / `GreatWorkYieldModifiers` 数据全部无人引用。**该城邦当前 4 条效果均完全不生效**，与「UI 显示了效果、实际不触发」的错配。

- 建议修复：在 `<CityStateUAs>`（`CSUA.xml:2029` 的 `</CityStateUAs>` 之前）补一条：

```xml
<Row>
    <Type>CSUA_BUENOS_AIRES</Type>
    <Description>TXT_KEY_CITYSTATE_BUENOS_AIRES</Description>
    <Help>TXT_KEY_CSUA_BUENOS_AIRES_HELP</Help>
    <AllyEffectType>EFFECT_CSUA_BUENOS_AIRES_ALLY</AllyEffectType>
    <FriendEffectType>EFFECT_CSUA_BUENOS_AIRES_FRIEND</FriendEffectType>
</Row>
```

并补 `TXT_KEY_CSUA_BUENOS_AIRES_HELP`（三语，见 P-2）。

#### B-1【中】效果 ④ 数值 `YieldMod=5` 单位误用：实际 +0.05%/杰作，应为 500（+5%）

- 位置：`CSUA.xml:2209-2214`（`<YieldMod>5</YieldMod>`）；消费点 `CvPlayer.cpp:18293-18304`、`18261`。
- 现象：`GetCSUAYieldPercentModifier` 累加的是 **basis points**，函数末尾统一 `/100` 归一化为百分比（`CvPlayer.cpp:18261` 注释「Rate=100 => +1%」；各「plain percent」字段均在此处 `×100` 后再累加，如 `:18312 / :18348 / :18361`）。`GreatWorkYieldModifiers` 直接累加、**不乘 100**（`:18302`），故其 `YieldMod` 单位即 basis points：
  - Ife 设计「每个杰作 +2% 信仰」→ 表值 `200` → 2% ✓（可作单位标定）；
  - 布宜诺斯艾利斯设计「每个音乐杰作 +5% 魅力」→ 表值 `5` → **0.05%** ✗。
- 后果：效果 ④ 实际收益为设计的 **1/100**，等于失效（每个音乐杰作仅 +0.05% 旅游）。
- 建议修复：`CSUA.xml:2213` 的 `<YieldMod>5</YieldMod>` 改为 `<YieldMod>500</YieldMod>`。
- 交叉提示：乌尔（Ur）同表设计文本为「每件杰作或文物，全国 +1% 文化」（`1.城邦UA/海洋型.txt:65`），但表值同为 `200`（→ 2%）。若乌尔设计稿为准，则该处亦偏大 1 倍；不属本次范围，建议一并核对。

#### C-1【中】效果 ③ 的「不死亡」未限定大音乐家

- 位置：`CvUnit.cpp:9921-9935`（条件仅 `pCSUA->IsGPNoDeathAfterGreatWork()`），位于共用的 `createGreatWork()`（`CvUnit.cpp:9875`）内。
- 现象：`createGreatWork()` 是大艺术家/大作家/大音乐家**共用**的杰作创作入口（调用点 `CvUnitMission.cpp:1753` `MISSION_GREAT_WORK()`、`CvLuaUnit.cpp:1671`）。当前判定只看「玩家是否持有该 CSUA」，于是盟友的**大艺术家**（艺术杰作）、**大作家**（文学杰作）创作后同样进入 `bNoDeathAfterGreatWork` 分支：不 `kill`、被 `SetGreatWork(NO_GREAT_WORK)` 剥夺再创作能力。
- 后果：偏离设计「**大音乐家**在产出**音乐杰作**后不会死亡」。对艺术/文学伟人而言，「保留 50% 演唱会魅力」无意义（其 `OneShotTourism` 为 0、诞生时未设置 `TourismBlastStrength`），但「创作后不消耗」是实质且非预期的效果。
- 建议修复：在条件中限定杰作类别，例如复用同函数已算出的 `eClass`：

```cpp
GreatWorkClass eMusicClass = (GreatWorkClass)GC.getInfoTypeForString("GREAT_WORK_MUSIC");
if (pCSUA != NULL && pCSUA->IsGPNoDeathAfterGreatWork() && eClass == eMusicClass)
```

（`eClass` 在 `:9898` 由 `CultureHelpers::GetGreatWorkClass(eGreatWorkType)` 得到，作用域内可用。）

### 待拍板（需确认，非缺陷）

**无。** 三条盟友 + 一条朋友的档位、叠加口径均与设计稿字面一致，无待决策项。

### 提示（非缺陷）

#### P-1　改动尚未编译验证

- 说明：MPDLL（`CvUnit.cpp` / `CvEconomicAI.cpp`）与 SP 均为工作区未提交改动，未取编译日志。按 [[build-requires-game-closed]]，编译前需关闭文明 5；若改动触及 `CvGameCoreDLLPCH.h` 包含链则先清 `BuildTemp/VS2022_CvGameCore_Expansion2ReleaseWin32`。本报告为静态审查结论，实机行为待编译后验证。

#### P-2　三语文本缺主表 `Help`（随 A-1 一并补）

- 位置：`TextInfos_{en_US,zh_CN,zh_Hant_HK}.xml`。
- 说明：当前仅 `TXT_KEY_EFFECT_CSUA_BUENOS_AIRES_ALLY_HELP` / `_FRIEND_HELP` 两 Tag（三语齐全、末尾插入、语义一致）。主表 `Help` 引用的 `TXT_KEY_CSUA_BUENOS_AIRES_HELP`（城邦 UA 总述）尚未添加——与 A-1 主记录缺失同源，补主记录时需同时补该 Tag。

#### P-3　效果 ① 与 ② 相加，使每座盟友城市实际至少 +2 大音乐家点数

- 位置：`CvCityCitizens.cpp:2316-2317`（两行相加）。
- 说明：城市规模假建筑为**累积制**，任何城市都有 `CITY_SIZE_TOWN`（1 人口起，`SP_CityScales.sql:13-14`），故效果 ①（每城 +1）叠加效果 ②（TOWN 假建筑 +1）→ **每城最低 +2**，中型城市 +1+3=+4，80 人口 +1+7=+8。此结果**忠实于设计文本字面**（「盟友的城市 +1」与「每个城市规模假建筑各提供 1」是两笔），列为提示仅供确认是否为设计本意。

#### P-4　未完成清单状态与本实现一致（无需改动）

- 说明：`未完成/未完成清单.md` 仍将布宜诺斯艾利斯列为「未完成」，与该功能尚未提交、且当前 A-1 导致不生效的现状相符。待 A-1/B-1/C-1 修复并提交后，应同步将该城邦移出未完成（文化型未完成数 2 → 1）。

#### P-5　`CvCity::GetGreatPersonPointsFromUA` 存在未使用局部变量（既存）

- 位置：`CvCity.cpp:12119`（`const char* szType = GC.getSpecialistInfo(...)->GetType();` 声明后未使用）。
- 说明：属 Ife/Zurich 时期的**既存**代码，非本次引入，仅产生编译警告，无功能影响；如顺手清理可删该行。

---

## 三、已验证无误项

1. **城邦绑定与本体定义正确**。`MINOR_CIV_BUENOS_AIRES` 存在且为文化型（`CIV5MinorCivilizations.xml:668-676`，`MinorCivTrait = MINOR_TRAIT_CULTURED`）；`UAType='CSUA_BUENOS_AIRES'` 与效果 `Type`/`Description` 命名同构，无「_CITY」类后缀错位。
2. **效果 ① 接入点正确且为「每城」口径**。`CvCity::GetGreatPersonPointsFromUA`（`CvCity.cpp:12116-12127`）返回玩家级 `m_iGreatPersonPoints[SPECIALIST_MUSICIAN]`，在**每座城市**的 GPP 计算中经 `CvCityCitizens.cpp:2316` `×100` 计入（`Times100` 量纲，+1 点/回合），三处 GPP 来源（Specialists/Buildings/UA）叠加方式与既有 `GetGreatPersonPointsFromPolicies` 同构。
3. **效果 ② 计数口径正确**。`GetBuildingGreatPersonPointsForCity`（`CvCityStateUAClasses.cpp:2651-2665`）对每行匹配 `SPECIALIST_MUSICIAN` 的条目按 `pCity->GetNumBuildingClass(BuildingClassType)` 累加 `Points`——对城市规模假建筑天然给出「该城市拥有的规模假建筑数量 × 1」，实现设计「每个假建筑各 +1」。
4. **城市规模假建筑确为累积制，与设计措辞吻合**。`SP_CityScales.sql:13-32` 的 `CityScale_FreeBuildingClass` 按「ID ≥ N」授予，故 80 人口城市同时持有 `TOWN…GLOBAL` 共 7 个假建筑；朋友效果仅列 `SMALL/MEDIUM`，中型城市（同时持有 TOWN+SMALL+MEDIUM）得 +2，恰为设计「小型 +1、中型额外 +1」。
5. **效果 ③ 的 DB 面与序列化路径完整**。两列已在 `UNIQUE_CITYSTATES.sql:54-55` 建表（英文注释）；effect 级读取（`CvCityStateUAClasses.cpp:424-425`）、getter（`:1250-1251`）、player 级聚合（`ApplyEffect` `:2003-2004`，`GetGPConcertTourismRetentionPercent` 相加、`IsGPNoDeathAfterGreatWork` 计数 >0）、`Reset` 清零（`:1779-1780`）齐备；均为 DB 驱动的运行时数据，不新增序列化字段，**无需版本门控**。
6. **效果 ③ 的「丧失杰作产出能力」与「保留 50%」实现语义正确**。`SetGreatWork(NO_GREAT_WORK)` 使 `GetGreatWork()` 为空 → `canCreateGreatWork` 判假，单位不再能创作（UI 按 `GetGreatWork()` 隐藏按钮），同时不影响「演唱会」指令（`MISSION_TOURISM_BLAST` 不依赖该字段）；`SetTourismBlastStrength(GetTourismBlastStrength() * 50 / 100)` 把诞生时固化的旅游爆炸强度降为 50%，与设计「保留 50% 演唱会魅力」一致。
7. **效果 ④ 的消费路径真实存在（仅数值错）**。旅游非城市常规产出，但经 `CvCityCulture::CalculateBaseTourism`（`CvCultureClasses.cpp:4701-4703`）调用 `getBaseYieldRateModifier(YIELD_TOURISM, 0, &toolTipSink)`，其内部 `CvCity.cpp:13647` 调用 `GetCSUAYieldPercentModifier(YIELD_TOURISM)`，故 `GREAT_WORK_MUSIC → YIELD_TOURISM` 行会被读取并作用于该玩家所有城市的旅游，且随 `TXT_KEY_PRODMOD_CITYSTATE_UA` 进入 tooltip。数值问题见 B-1。
8. **盟友/朋友档位互斥且选择正确**。`CvPlayer::RefreshCSAllUAEffects`（`CvPlayer.cpp:20219-20226`）`IsAllies` 优先、`else if IsFriends` 择一 `ApplyEffect`；朋友 effect 行不含 ①②④ 数据，仅 ⑤ 生效，符合设计「朋友只共享城市规模点数」。
9. **效果 ④ 每回合缓存刷新已接**。`CacheGreatWorkCounts()` 在 `CvPlayer::RefreshCSAllUAEffects` 内每回合调用（`CvPlayer.cpp:20235`），为 `GetCachedGreatWorkCount(GREAT_WORK_MUSIC)` 提供平值，热路径不遍历城市，与 Ife 同构。
10. **CvEconomicAI 的配合同步修复正确**。`GetBestGreatWorkCity`（`CvEconomicAI.cpp:897-902`）对 `NO_GREAT_WORK` 提前返回 NULL，避免已创作而存活的单位被 AI 反复指派；各调用方（`CvHomelandAI.cpp:3299/3430/3560`、`CvPlayerAI.cpp:1106/1164/1203`）均判空处理，无解引用风险；同时使大音乐家改走 `GREAT_PEOPLE_DIRECTIVE_TOURISM_BLAST` 分支（`CvPlayerAI.cpp:1196-1198`），语义正确。
11. **注释全英文**。MPDLL 新增行（`CvUnit.cpp` / `CvEconomicAI.cpp`）注释均为英文，无 CJK；SP 改动集中在 `.sql` / `.xml` 数据文件，无注释。符合 [[sp-english-comments-only]]。
12. **三语文本齐全、末尾插入、语义一致**。`_ALLY_HELP` / `_FRIEND_HELP` 两个 Tag 在英/简/繁三文件各存在且仅一处，均追加于各文件 `</Language_*>` 之前（末尾），未打乱既有分组；三条盟友与一条朋友逐条对应，`[ICON_GREAT_MUSICIAN]` / `[ICON_GREAT_WORK]` / `[ICON_TOURISM]` / `[ICON_BULLET]` 图标标记使用得当。
13. **无新增序列化、无无关改动**。MPDLL 两文件 diff 全部集中于本次功能（`CvUnit.cpp` 的 5 处 `−` 为原 `if(IsGreatPerson()){...} kill(true)` 的结构重排，逻辑等价）；SP 侧 5 文件新增全部归属本功能。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff --numstat` / `git status --short`，核对改动规模与提交状态（MPDLL 2 文件 +34/−5；SP 5 文件 +118/−0，均未 commit）。
- 交叉核对 C++ 实现、XML 数据、三语文本、设计稿四者数值与语义。
- 追踪效果 ① ② 消费路径：`CvCityCitizens.cpp:2296-2327`（`GetGreatPersonPointsFromUA(_Building)` 两行 `×100`）→ `CvCity.cpp:12116-12133` → `CvCityStateUAClasses.cpp:2538,2651-2665`。
- 追踪效果 ③ 路径：`CvUnit.cpp:9875-9949` 全函数；确认 `createGreatWork()` 共用性（调用点 `CvUnitMission.cpp:1753`、`CvLuaUnit.cpp:1671`）；核对 `GPNoDeathAfterGreatWork` / `GPConcertTourismRetentionPercent` 在 DB/effect/player 三级的读取与聚合。
- 追踪效果 ④ 路径：`CvCultureClasses.cpp:4686-4786`（`CalculateBaseTourism`）→ `CvCity.cpp:13645-13654` → `CvPlayer.cpp:18293-18304`；并回读 `CvPlayer.cpp:18261,18308,18312,18348,18361` 注释与 `×100` 分支，标定 `YieldMod` 单位（basis points、末尾 /100），以 Ife「+2%=200」交叉验证。
- 以全仓检索 `CSUA_BUENOS_AIRES`（`grep`）确认主表 `<Type>` 缺失；以 `UPDATE ... UAType` 计数（57）与主表 `CSUA_*` 计数（56）对齐佐证唯一缺口；回读 `CvPlayer.cpp:20211-20217` 与 `CvCityStateUAClasses.cpp:1623-1630`（`GetEntryByType`）确认「主记录缺失 → 静默跳过」的加载语义。
- 回读 `SP_CityScales.sql` 与 `CitySizeBuildings.sql` 确认城市规模假建筑为累积授予、`GetNumBuildingClass` 口径有效；检索本体 `CIV5MinorCivilizations.xml` 确认城邦定义与类型。
- 检索本体 `NORMAL` 侧 `GREAT_WORK_MUSIC` 常量使用方式，为 C-1 修复给出可实现写法。

---

## 五、结论

布宜诺斯艾利斯（Buenos Aires）CSUA 的四条效果的数据面已全部落地：效果 ①（每城 +1 大音乐家点数）、效果 ②（每城市规模假建筑各 +1）、朋友效果 ⑤（小型/中型档位）的**口径与档位均与设计稿逐条对得上**；效果 ③（不死亡 + 保留 50% 演唱会）的 DB/序列化/引擎逻辑齐备；效果 ④（每音乐杰作 +5% 魅力）的消费路径真实存在。

**须修复 3 项**：

1. **A-1（严重）**：`CSUA.xml` 主表 `<CityStateUAs>` 缺 `CSUA_BUENOS_AIRES` 条目 → `GetEntryByType` 返回 NULL → **该城邦全部效果不生效**。必须补主记录（并补 `TXT_KEY_CSUA_BUENOS_AIRES_HELP` 三语）。
2. **B-1（中）**：效果 ④ 的 `YieldMod=5` 单位为 basis points（Ife 200=2% 可证），实际 +0.05%/杰作，应为 `500`（+5%）。
3. **C-1（中）**：效果 ③ 的「不死亡」判定应限定 `GREAT_WORK_MUSIC`，否则盟军的大艺术家/大作家创作杰作后同样不死亡。

其余 5 项均为提示（未编译验证、缺主表 Help Tag、效果 ①+② 叠加致每城最低 +2、未完成清单同步、既存未使用变量）。

建议处理顺序：先修 A-1（否则其余效果无从验证）→ B-1 → C-1 → 补三语 Help Tag，再按 [[build-project-paths]] 构建 SP V11 与 MPDDL（含关闭文明 5、必要时清 PCH 缓存）实机验证。重点验：**城邦面板是否显示 UA 总述且效果实际触发**（回归 A-1）、盟友大音乐家创作杰作后是否存活并能以 50% 强度开演唱会、盟友大艺术家/大作家创作后是否**照常消耗**（回归 C-1）、每个音乐杰作的旅游增量是否为 5%（回归 B-1）、朋友档仅得城市规模点数。
