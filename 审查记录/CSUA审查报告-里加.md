# CSUA 审查报告：里加（Riga）

- 审查日期：2026-09-26
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 3 文件 +21 / −3；SP 5 文件 +159 / −1
- 结论摘要：机制复用既有 CSUA 特殊城市类型体系，**未发现功能性缺陷**。里加是该体系两项机制的首次用例（同城匹配两个类型、纯 AND 条件类型），已逐一核对逻辑链路正确。发现 1 项**注释与代码行为矛盾**（"不叠加" vs 实际累加），里加正依赖累加，有误导后续维护者的风险，建议订正。另附实机验证步骤与数值强度提示。

---

## 一、改动清单

### MPDLL

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +2 | 新增枚举 `SPECIAL_CITY_CONDITION_IS_RIVER` / `IS_COASTAL`（`:98-99`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +17 / −1 | `ParseSpecialCityCondition` 增两分支（`:21-22`）；新增 `IsBooleanSpecialCityCondition`（`:26-31`）；条件行有效性判定放宽为「有值 或 布尔条件」（`:96-98`）；`EvaluateCondition` 增两分支（`:139-144`） |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +2 / −2 | 建表注释更新为已实现的条件类型清单 |

### SP

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 | 里加 `UAType` 绑定（`:51`，`MINOR_CIV_RIGA` → `CSUA_RIGA`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +89 / −1 | 1 个 UA（`:1578-1585`）、2 个效果（`:374-383`）、2 个特殊城市类型（`:1896-1901`）、1 条 Or 条件（`:1941-1945`）、2 条 And 条件（`:1948-1958`）、10 行产出修正（`:1985-2035`） |
| `Gameplay/XML/Localization/TextInfos_{en_US,zh_CN,zh_Hant_HK}.xml` | 各 +23 | 3 个文本 Tag × 3 语言，追加于各文件末尾 |

### 效果设计（已核对与三语文本、XML 三方一致）

| 对象 | 设计文本 | 实现 |
| --- | --- | --- |
| 盟友 | 沿河城市 +15% 金钱、食物 | `SPECIAL_CITY_RIGA_RIVER` × {GOLD, FOOD} × 15 |
| 盟友 | 沿河且沿海城市**额外** +15% 金钱、食物、文化、产能 | `SPECIAL_CITY_RIGA_RIVER_COASTAL` × {GOLD, FOOD, CULTURE, PRODUCTION} × 15（与上行叠加 → 金钱/食物合计 +30%） |
| 朋友 | 沿河城市 +6% 金钱、食物 | `EFFECT_CSUA_RIGA_FRIEND` × `RIVER` × {GOLD, FOOD} × 6 |

---

## 二、问题清单

### P1-1　"不叠加"注释与代码累加行为矛盾（里加正依赖叠加）

- 位置：
  - 代码：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvCity.cpp:13544-13557`
  - 注释 1：`SP/.../Gameplay/XML/CSUA/CSUA.xml:1959`（`……产出百分比加成（不叠加）`）
  - 注释 2：`CIV5MPDLL/(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql:338`（`… / 35 = +35% culture for cities of that type (no stacking).`）
- 现象：两处注释均称"不叠加"，但实现是**无 `break` 的累加**：

  ```cpp
  for (size_t i = 0; i < vSpecialCityMods.size(); i++)
  {
      if (vSpecialCityMods[i].m_iYieldType != (int)eIndex) continue;
      if (pCityStateUA->IsCachedSpecialCityTypeMatch(GetID(), vSpecialCityMods[i].m_iSpecialCityType))
          iModifier += vSpecialCityMods[i].m_iYieldMod;   // 累加：同城匹配多个类型时叠加
  }
  ```

  即**同一座城市匹配多个特殊城市类型时，同种产出的修正相加**。
- 背景：波哥大的两个类型产出不重叠（LUXURY→文化、EL_DORADO→旅游），故此前该矛盾不可观测；注释里的"不叠加"原意更可能是"不像 `SpecialCityCountYieldModifiers` 那样按城市数量放大"。
- 影响：**里加是本机制首个依赖跨类型叠加的用例**——沿河且沿海的城市需同时命中 `RIVER`（+15%）与 `RIVER_COASTAL`（+15%）才能得到设计要求的 +30% 金钱/食物。若后续维护者按注释"修正"为取最大值（`std::max`）或补 `break`，里加的金钱/食物会**静默腰斩为 +15%**。
- 建议：订正两处注释，明确"同城匹配多个类型时叠加"，并把里加 +30% 作为示例写入，与 `CSUA.xml:1998` 已写的"与上面叠加，合计金钱/食物+30%"对齐。

### P2-1　里加引入两项机制首次用例，建议实机各验证一次

- **首次"同城匹配两个特殊城市类型"**：`RIVER` 与 `RIVER_COASTAL` 对同一沿河沿海城市同时命中，用于验证叠加（见 P1-1）。
- **首次"纯 AND 条件类型"**：`SPECIAL_CITY_RIGA_RIVER_COASTAL` 在 Or 表中**无行**、仅在 And 表有 2 行，是本机制首个纯 AND 类型（此前 And 表恒为空）。
  - 代码层已核对不误伤：`CacheResults` 的 fail-closed 判定 `m_vConditionsOr.empty() && m_vConditionsAnd.empty()`（`CvCityStateUAClasses.cpp:119-123`）因 And 非空而不触发；`IsCityMatch` 对空 Or 表按"不限制"处理、要求 And 全中（`:159-174`），语义正确。
- 验证手段（沿用波哥大审查 7.4(2) 的 tooltip 方法，无需读存档；命中时代码执行 `BuildProdModHelpText`，在城市产出明细可见条目）：
  1. 与里加结盟，取一座**沿河**城市 → 产出明细应见金钱、食物各一条 +15%；
  2. 取一座**沿河且沿海**城市 → 金钱、食物应**各两条** +15%（合计 +30%），另有文化、产能各 +15%；
  3. 取一座**仅沿海（不沿河）**城市 → 不应出现任何相关条目；
  4. 与里加为**朋友**（非盟友）→ 沿河城市应见金钱、食物 +6%，沿海城市**无**额外条目。

### P2-2　UA 帮助文本与效果帮助文本内容重叠（既有模式，无需改动）

`TXT_KEY_CSUA_RIGA_HELP`（UA 级，含盟友 + 朋友两段）与 `TXT_KEY_EFFECT_CSUA_RIGA_ALLY_HELP` / `..._FRIEND_HELP`（效果级，各含一段）内容重叠，但二者服务于不同 UI 位置（城邦面板 vs 生效效果列表），与波哥大 / 布拉迪斯拉发写法一致；三语已同步，无需改动。

### P3-1　数值强度提示（非缺陷，供平衡参考）

盟友沿河且沿海城市金钱 / 食物 +30%，其中**食物百分比直接影响人口增长**，属较强成长加成；且里加两个类型的门槛（沿河 / 沿河 + 沿海）在河流入海口的城市极易同时满足，实际收益常按 +30% 计。设计如此，仅记录供后续平衡评估。

---

## 三、已验证无误项

1. **城邦绑定与基础数据存在**：`MINOR_CIV_RIGA` 在基础游戏存在（`Civ5DebugDatabase.db` 查询确认），其 `Description` 即 `TXT_KEY_CITYSTATE_RIGA`，与 `CSUA.sql:51` 的 UPDATE 匹配。
2. **描述 Tag 可解析**：`TXT_KEY_CITYSTATE_RIGA` 由基础游戏提供，`zh_CN` 与 `ZH_Hant_HK` 两套文本均有定义（`Assets/DLC/Expansion2/Gameplay/XML/Text/{zh_CN,ZH_Hant_HK}/CIV5GameTextInfos_CityStates_Expansion2.xml`），SP 无需自建。
3. **写法与既有城邦同构**：`CityStateUAs` 行采用 `<Description>TXT_KEY_CITYSTATE_*</Description>` + `<Help>TXT_KEY_CSUA_*_HELP</Help>`，与 Sydney / Hormuz / Vancouver / Ife / Yerevan / Bogota / Bratislava 七个既有条目完全一致。
4. **`IS_RIVER` 语义正确**：`pCity->plot()->isRiver()`（`CvCityStateUAClasses.cpp:141`）即水车 / 花园的"沿河"判定（`CvCity.cpp:21696` 同一写法），与设计"沿河城市"一致；且已先判 `plot() != NULL`。
5. **`IS_COASTAL` 语义正确**：`pCity->isCoastal()`（`:144`）默认参数 `-1`（`CvCity.h:411`）→ `GC.getMIN_WATER_SIZE_FOR_OCEAN()`（=10，基础游戏 `GlobalDefines.xml`）→ 仅 ≥10 格水体算沿海；而湖泊上限 `LAKE_MAX_AREA_SIZE` = 9，二者互补，故**湖泊被精确排除**，注释 "lakes excluded" 成立（非近似，是精确互补）。
6. **布尔条件无 `Value` 可正常解析**：SP XML 的 `IS_RIVER` / `IS_COASTAL` 行不带 `<Value>`；`CacheResults` 只对 `HAS_RESOURCE` / `HAS_FEATURE` 读取 `Value`（`:88-94`），并经 `IsBooleanSpecialCityCondition` 放行有效性判定（`:96-98`），不会被 fail-closed 误杀；`Value` 列在 SQL 中可空（`UNIQUE_CITYSTATES.sql:325-335`），插入无阻碍。
7. **纯 AND 类型不被 fail-closed 误伤**：见 P2-1；`m_vConditionsAnd` 非空使"两表皆空"判定不触发。
8. **盟友 / 朋友互斥且归属正确**：`RefreshCSAllUAEffects` 以 `IsAllies` 优先、`else if IsFriends` 择一应用（`CvPlayer.cpp:19936-19943`），盟友不再叠加朋友效果；效果存于**盟友玩家**的 `m_pCityStateUA`，城市级消费点取 `owner.GetPlayerCityStateUA()`（`CvCity.cpp:13490`），故加成落在盟友的城市而非城邦自身。
9. **每回合重建、无需版本门控**：`CvPlayerCityStateUA` 无 `Read` / `Write`，效果在 `RefreshCSAllUAEffects` 中 `Reset()` 后全量重建，随 `doTurn` 与盟友 / 朋友关系变化触发；本次新增数据不涉及存档序列化，无需版本门控。
10. **缓存覆盖两张效果表**：`CacheSpecialCityMatches` 由 `m_vSpecialCityYieldModifiers` 与 `m_vSpecialCityCountYieldModifiers` 共同求 `iMaxType` 并标记 `abReferenced`（`:2194-2221`），里加两个类型均被纳入；消费点 `IsCachedSpecialCityTypeMatch` 为纯查表。
11. **产出链路成立**：城市产出 = `iBaseYield × getBaseYieldRateModifier(eIndex) / 100`（`CvCity.cpp:14166-14171`）；`getBaseYieldRateModifier` 内先并入城市自身 `getYieldRateModifier`（含建筑 `Building_YieldModifiers`，`:13483`）再累加 CSUA 修正（`:13552`），故食物百分比加成与神庙等既有食物修正走同一路径，可正常作用于人口增长；贸易产出在修正之后相加（`:14178-14182`），故本加成不含商路金，与设计"城市 +15% 金钱"一致。
12. **数值三方一致**：设计文本（`未完成/海洋型-未完成.txt:34-37`）、SP XML、三语文本的 15 / 15、15 / 15 / 15 / 15、6 / 6 逐条对应，无偏差。
13. **行尾格式保持**：SP 的 CSUA.xml / CSUA.sql / 三个 TextInfos 文件均为 LF（CR=0）；`git diff --stat` 为纯新增（+159 / −1，唯一删除行为 And 表旧注释被替换），无整文件重写。
14. **DLL 已重编**：`CvCityStateUAClasses.{h,cpp}` 修改时间 23:34，`(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll` 时间戳 23:39，产物晚于源码，本次条件改动已进入 DLL。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff`。
- 交叉核对 C++ 实现、SQL 建表语句与注释、XML 数据、三语文本四者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvPlot::isCoastalArea`（`CvPlot.cpp:1210`）、`CvCity::isCoastal`（`CvCity.cpp:9211`）、`CvCity::getBaseYieldRateModifier`（`:13399`，累加点 `:13552`）、`CvCity::getYieldRateTimes100`（`:14166`）、`CvPlayer::RefreshCSAllUAEffects`（`CvPlayer.cpp:19910`）、`CvPlayerCityStateUA::ApplyEffect`（`CvCityStateUAClasses.cpp:1784-1803`）。
- 核对基础游戏 `GlobalDefines.xml`：`LAKE_MAX_AREA_SIZE` = 9、`MIN_WATER_SIZE_FOR_OCEAN` = 10。
- 查询缓存数据库 `Civ5DebugDatabase.db` 确认 `MINOR_CIV_RIGA` 存在；查询基础游戏 Assets 确认三语言 `TXT_KEY_CITYSTATE_RIGA` 定义。
- 遍历 `CvSpecialCityTypeEntry::CacheResults` / `IsCityMatch` 的全部返回路径，确认纯 AND 类型与布尔条件不受上一轮 fail-closed 加固影响。

---

## 五、当前状态与建议处理顺序

### 状态

- MPDLL 工作区：3 文件 +21 / −3（未 commit）；DLL 已重编，产物在 `(1) CIV5MPDLL/DLL/`（23:39）
- SP 工作区：5 文件 +159 / −1（未 commit）
- 游戏根目录 DLL（`Documents\My Games\Sid Meier's Civilization 5\CvGameCore_Expansion2.dll`）仍为 2026-08-11 旧版，**尚未覆盖**
- 尚未构建模组

### 建议顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | P1-1 订正"不叠加"注释（MPDLL SQL 与 SP XML 各 1 处） | 极小 |
| 2 | P2-1 实机按 4 步验证（叠加 / 纯 AND / 负例 / 朋友） | 小 |
| 3 | 覆盖根目录 DLL 或构建模组，使改动可测 | 小 |
| 4 | P3-1 平衡评估 | 可选 |
