# CSUA 审查报告：波哥大与布拉迪斯拉发

- 审查日期：2026-09-26
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`
- 改动规模：MPDLL 9 个文件 +481 行；SP 5 个文件 +387 行
- 结论摘要：机制设计合理，逻辑链路完整，**未发现会导致崩溃或明显数值错误的问题**。发现 1 项健壮性缺陷（fail-open）、1 项性能隐患、1 项依赖脆弱点，以及若干冗余与一致性问题，建议修复。

---

## 一、改动清单

### MPDLL

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +91 | 新增 `CvSpecialCityTypeEntry`、`CvCityStateUASpecialCityTypeXMLEntries` 及两组效果结构体 |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +268 | 特殊城市类型解析/判定、两组效果读取与累积、按类型计数缓存 |
| `CvGameCoreDLL_Expansion2/CvCity.cpp` | +47 | `getBaseYieldRateModifier` 接入波哥大与布拉迪斯拉发；新增 `IsSpecialCityType` |
| `CvGameCoreDLL_Expansion2/CvCity.h` | +2 | `IsSpecialCityType` 声明 |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +16 | 波哥大「按匹配城市数全国加成」接入 `GetCSUAYieldPercentModifier`；`CacheSpecialCityCounts` 调用 |
| `CvGameCoreDLL_Expansion2/CvGlobals.cpp` / `.h` | +11 | 新 XMLEntries 的创建/销毁/访问器 |
| `CvGameCoreDLL_Expansion2/CvDllDatabaseUtility.cpp` | +2 | 新表 prefetch |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +44 | 5 张新表建表语句 |

### SP

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +2 | 波哥大、布拉迪斯拉发 `UAType` 绑定 |
| `Gameplay/XML/CSUA/CSUA.xml` | +235 | 两个 UA、4 个效果、特殊城市类型及条件、两组产出修正、布拉迪斯拉发伟人修正 |
| `Gameplay/XML/Localization/TextInfos_{en_US,zh_CN,zh_Hant_HK}.xml` | 各 +50 | 6 个文本 Tag × 3 语言 |

### 效果设计（已核对与文本一致）

**波哥大（CSUA_BOGOTA）**

| 对象 | 效果 | 实现 |
| --- | --- | --- |
| 盟友 | 开发黄金/白银/珍珠/宝石/琥珀/玉石其一的城市 +35% 文化 | `SpecialCityYieldModifiers` + `SPECIAL_CITY_BOGOTA_LUXURY` |
| 盟友 | 每拥有一座此类城市，所有城市 +5% 魅力 | `SpecialCityCountYieldModifiers`（玩家级） |
| 盟友 | 拥有黄金国的城市 +100% 魅力 | `SpecialCityYieldModifiers` + `SPECIAL_CITY_BOGOTA_EL_DORADO` |
| 朋友 | 同上文化 +15%、黄金国 +40% 魅力 | 对应 FRIEND 效果行 |

**布拉迪斯拉发（CSUA_BRATISLAVA）**

| 对象 | 效果 | 实现 |
| --- | --- | --- |
| 盟友 | 首都及第二首都 +50% 文化 | `CapitalAndSecondCapitalCultureModifier`（城市级） |
| 盟友 | 每诞生过一位伟人，全国科研与产能 +1% | `BornGreatPersonYieldModifiers` 枚举 9 类伟人 × 2 产出 |
| 朋友 | 首都及第二首都 +20% 文化 | 对应 FRIEND 效果行 |

---

## 二、问题清单

### P0-1　Or 表条件全部解析失败时 fail-open

- 位置：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp:74`（过滤）、`:98`（`IsCityMatch`）
- 现象：`CacheResults` 会静默丢弃无法解析的条件行：

  ```cpp
  if (entry.m_eConditionType != SPECIAL_CITY_CONDITION_NONE && entry.m_iValue >= 0)
      apvTarget[iTable]->push_back(entry);
  ```

  而 `IsCityMatch` 对空的 Or 表返回 `true`（视为「不限制」）：

  ```cpp
  if (m_vConditionsOr.empty())
      return true;
  ```

- 影响：**若某个 SpecialCityType 的 Or 行因拼写错误被全部丢弃，该类型会匹配所有城市**。当前 `SPECIAL_CITY_BOGOTA_EL_DORADO` 只有 1 行条件，一旦 `FEATURE_EL_DORADO` 写错，即为全国所有城市 +100% 旅游。注释写的是 "dropped (fail-safe)"，实际行为是 **fail-open**。
- 建议（任选其一）：
  1. `CacheResults` 中统计 XML 里实际存在的 Or 行数与有效行数，若「有行但全无效」则置一个 `m_bHasInvalidOrConditions` 标志，`IsCityMatch` 直接返回 false；
  2. 解析失败时立即 `CvAssertMsg(false, ...)` 并在日志中打出 Type/值，把静默失败变为显式失败；
  3. 至少对 `HAS_RESOURCE` / `HAS_FEATURE` 的值解析失败做断言。

### P1-1　`IsSpecialCityType` 位于极热路径且无缓存

- 位置：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvCity.cpp:13540`（调用点）、`:23852`（定义）
- 现象：`getBaseYieldRateModifier` 对每个城市、每种产出的每次计算，都会走一遍 `IsSpecialCityType` → `IsCityMatch` → `EvaluateCondition`，其中 `HAS_RESOURCE` 分支调用 `GetNumResourceLocal(eResource, true)`（遍历城市全部地块 + 沿改良升级链比对），`HAS_FEATURE` 分支调用 `IsHasFeatureLocal`（同样全地块遍历）。
- 量级：波哥大为盟友时，每城每次计算文化需执行 6 次全地块扫描。
- 对照：同一 CSUA 体系内，Ife 的伟作计数（`CacheGreatWorkCounts`）、Vancouver 的沿海城市数（`RefreshCoastalCityCount`）、本次新增的波哥大计数（`CacheSpecialCityCounts`）**都做了每回合缓存**，唯独本路径没有。
- 建议：将 `IsCityMatch` 结果按（城市 × 特殊城市类型）缓存，随 `CvPlayer::RefreshCSAllUAEffects` 每回合刷新；或复用 `m_aiCachedSpecialCityCount` 的思路，缓存「匹配城市列表」供热路径直接查表。

### P1-2　黄金国判定依赖 `IsHasFeatureLocal` 的 `getWorkingCity()` 语义

- 位置：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvCity.cpp:4018`（被调用函数内部）
- 现象：`IsHasFeatureLocal` 除校验地块归属外，还要求 `pLoopPlot->getWorkingCity() == this`：

  ```cpp
  if (pLoopPlot->getOwner() != getOwner())   continue;
  if (pLoopPlot->getWorkingCity() != this)   continue;
  ```

  即地貌所在地块必须**已被分配给这座城市**。
- 影响：自然奇观地块在领土扩张时通常会被分配 working city，但并非必然。若黄金国地块未被分配，`HAS_FEATURE` 条件永不命中，+100% 旅游静默失效。
- 建议：实机确认一次（在拥有黄金国的城市上检查该 UA 是否生效）；如不生效，改用不要求 working city 的判定（例如 `pLoopPlot->getOwner() == getOwner() && pPlot->getFeatureType() == eFeature`）。

### P2-1　XML 中 `<CityStateUAEffect_BornGreatPersonYieldModifiers>` 元素重复

- 位置：`SP/.../Gameplay/XML/CSUA/CSUA.xml:1751`（埃里温 1 行）与 `:1763`（布拉迪斯拉发 18 行）
- 现象：同名顶层元素出现两次。Civ5 的 XML 加载器会按表合并插入，**不会报错**，功能正常。
- 影响：仅影响可读性与后续 diff 审查。
- 建议：将布拉迪斯拉发的 18 行并入 `:1751` 那个块，保持单一元素。

### P2-2　`YieldMod` 单位在 CSUA 各表中不统一

- 位置：`(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` 新增表注释
- 现象：
  - `CityStateUAEffect_BornGreatPersonYieldModifiers`：**基点**（100 = +1%）
  - `CityStateUAEffect_SpecialCityYieldModifiers` / `...SpecialCityCountYieldModifiers`：**普通百分比**（35 = +35%，代码在 `CvPlayer.cpp:18312` 处 `*100` 转换为基点）
- 影响：同名字段两种量纲，后续新增城邦时极易配错（差 100 倍）。
- 说明：SQL 与 XML 注释均已写明具体示例，文档层面无误。
- 建议：在两张新表的建表注释中额外显式标注「本表 YieldMod 为百分比，非基点」，与伟人表形成对照。

### P2-3　`GetEntryByType` 为死代码

- 位置：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp:149`
- 现象：`CvCityStateUASpecialCityTypeXMLEntries::GetEntryByType` 无任何调用者（另两个 XMLEntries 类的同名方法均有使用）。
- 影响：无功能影响。
- 建议：可删除；若为保持三个容器类接口一致而保留，亦可接受。

### P2-4　条件编译宏保护缺失（当前不影响编译）

- 位置：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp:90`、`:92`
- 现象：`EvaluateCondition` 调用的 `GetNumResourceLocal` 与 `IsHasFeatureLocal`，其声明分别受 `MOD_API_EXTENSIONS || MOD_TRADE_WONDER_RESOURCE_ROUTES`、`MOD_ROG_CORE` 保护，而调用处无保护。
- 影响：这两个宏在 `CustomMods.h`（:94、:914、:335）中为**无条件 `#define`**，`#if defined(...)` 恒为真，当前可正常编译。
- 建议：仅为防御性考虑，可在 `EvaluateCondition` 的对应分支加同样的宏保护；若认为宏恒定义、无需处理，也可保持现状。

### P2-5　`PrepareResults` 返回值未判空（既有模式）

- 位置：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp`（本次新增的两处效果表查询、`CvSpecialCityTypeEntry::CacheResults`）
- 现象：`kUtility.PrepareResults(...)` 返回 NULL（SQL 失败）时会直接 `pResults->Bind(...)` 解引用空指针。
- 影响：表由本仓库 SQL 自建，正常流程不会失败；且该写法与文件内既有代码一致。
- 建议：非必须，可在统一重构时一并处理。

### P2-6　繁中文本既有缺陷（非本次引入）

- 位置：`SP/.../Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` 的 `TXT_KEY_CHOOSE_INTERNATIONAL_TRADE_ROUTE_ITEM_TT_EXTRA`
- 现象：`（城市產出/時代/海路/信條/CSUA: {1_Num} [ICON_GOLD]` 缺少右括号（简中与英文同位置正常）。
- 影响：文本显示瑕疵，与本次改动无关，顺带记录。

---

## 三、已验证无误项

以下项已逐一核对，确认实现正确：

1. **索引与 ID 一致性**：`PrefetchCollection` 使用 `SELECT * FROM <table> WHERE ID > -1 ORDER BY ID`，并按 ID 用 `NULL` 补齐空洞（`CvDllDatabaseUtility.h:119-136`），因此 `index == ID`，`GetEntry(iSpecialCityType)` 不会错位。SQL 建表注释对此已有说明。
2. **子表可重复遍历**：`CvDatabaseUtility::GetResults` 内部会先 `Reset()`（`CvDatabaseUtility.cpp:52`），且 `PrefetchCollection` 中 `kUtility` 为所有条目共用（循环外声明），故 `Bind` + `Step` 在第二个条目起能正确重新遍历。新增的三处查询写法与文件内既有模式一致。
3. **不需要版本门控**：`CvPlayerCityStateUA` 无 `Read`/`Write` 方法，属运行时重建数据；`CvPlayer::RefreshCSAllUAEffects` 注释明确「Called each turn and on ally/friend change. This avoids serialization — on game load the first doTurn() call restores everything」，且函数入口有 `if (!m_pCityStateUA) return;` 保护。新增的三个成员与同类既有成员（`m_vAdjacentImprovementYieldChanges` 等）处理方式一致。
4. **缓存刷新时机**：`CacheSpecialCityCounts` 挂在 `RefreshCSAllUAEffects` 内，而该函数在 `doTurn` 与盟友/朋友关系变化（`CvPlayer.cpp:19901`）时均被调用，波哥大计数不会长期停滞。
5. **数值与文案一致**：波哥大 35/5/100/15/40、布拉迪斯拉发 50/1%/20，与三语文本逐条对应；盟友/朋友的效果归属也与文本一致（朋友的「每城 +5% 魅力」确实不存在）。
6. **数据依赖存在性**：`RESOURCE_{GOLD,SILVER,PEARLS,GEMS,AMBER,JADE}`、`FEATURE_EL_DORADO` 均在数据库中；`ICON_RES_AMBER` / `ICON_RES_JADE` 在 `IconAtlases.xml` 有定义；`ICON_TOURISM` 为原版图标。
7. **伟人类别枚举完整**：数据库中 `GreatPersons` 表含 `GREATPERSON_GENERAL → UNITCLASS_GREAT_GENERAL` 与 `GREATPERSON_ADMIRAL → UNITCLASS_GREAT_ADMIRAL`，故布拉迪斯拉发枚举 9 类伟人无遗漏，`GetGreatPersonFromUnitClass` 不会返回 `NO_GREATPRESON` 导致 `continue`。
8. **布拉迪斯拉发文化链路完整**：`CapitalAndSecondCapitalCultureModifier` 从 XML 读取（`CvCityStateUAClasses.cpp:308`）→ `ApplyEffect` 累积（`:1419`）→ 玩家级 getter（`:1768`）→ 城市产出计算使用（`CvCity.cpp:13562`），且 `Reset()` 中已清零（`:1238`）。
9. **量纲换算正确**：波哥大计数效果 `count × YieldMod × 100` 得基点值，与 `GetCSUAYieldPercentModifier` 末尾 `return iMod / 100` 的约定一致；`SpecialCityYieldModifiers` 直接加在 `getBaseYieldRateModifier` 的百分比 `iModifier` 上亦正确。
10. **编译期结构**：新增的两个 `#if defined(MOD_SP_UNIQUE_CITYSTATE)` 块均正确配对 `#endif`；`CvSpecialCityTypeEntry` 的构造/析构与 `CacheResults` 声明风格与 `CvCityStateUAEffectEntry` 一致（均不带 `virtual` 关键字，基类为虚函数，覆盖成立）。

---

## 四、验证方法

- 逐文件比对 `git diff`（MPDLL 与 SP 两仓库工作区）。
- 交叉核对 C++ 实现、SQL 建表语句、XML 数据、三语文本四者的数值与语义一致性。
- 查阅引擎侧被调用函数源码确认语义：`CvCity::GetNumResourceLocal`（`CvCity.cpp:4084`）、`CvCity::IsHasFeatureLocal`（`:3993`）、`CvPlayer::GetBornGreatPersonCount`（`CvPlayer.cpp:18423`）、`GetGreatPersonFromUnitClass`（`CvGreatPersonInfo.cpp:45`）。
- 查询数据库存根 `Civ5DebugDatabase.db` 确认 `GreatPersons`、`Resources`、`Features` 表内容。
- 核对 `CvDllDatabaseUtility::PrefetchCollection` 模板实现与 `CvDatabaseUtility::GetResults/PrepareResults` 行为。
- 核对 `CustomMods.h` 中相关宏的定义方式。

---

## 五、建议处理顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | P0-1 fail-open 防护 | 小 |
| 2 | P1-2 黄金国判定实机确认（必要时改判定） | 小 |
| 3 | P1-1 `IsSpecialCityType` 缓存 | 中 |
| 4 | P2-1 XML 元素合并 | 小 |
| 5 | P2-2 表注释补充量纲说明 | 小 |
| 6 | P2-3 / P2-4 / P2-5 | 可选 |

---

## 六、逐项回应（2026-09-26 修复记录）

处理结论：**P0-1 / P1-1 / P2-1 / P2-2 / P2-3 已修复**；**P1-2 保留原判定，待实机确认**；**P2-4 / P2-5 / P2-6 不改**（理由见下）。修复后已清理 PCH 缓存并全量重编 DLL，0 错误。

### P0-1　已修复（fail-closed）

`CvSpecialCityTypeEntry` 新增 `bool m_bConditionsInvalid`（构造函数初始化为 false）：

- `CacheResults` 对两张条件表分别统计**原始行数** `iRawRows`；逐行解析失败时 `CvAssertMsg(false, ...)` 打出提示，把静默丢弃变为显式失败；
- 每张表遍历结束后，若 `iRawRows > 0 && 目标 vector 为空`（即"有行但全无效"），置 `m_bConditionsInvalid = true` 并再断言一次；
- `IsCityMatch` 开头新增 `if (m_bConditionsInvalid) return false;`，使该类型**匹配零座城市**而非全部城市。

原有语义保留：`iRawRows == 0`（该表本就无行，例如未来纯 AND 城邦的空 Or 表）仍按"不限制"处理，不受影响。

### P1-1　已修复（改为每回合缓存 + 查表）

`std::vector<int> m_aiCachedSpecialCityCount`（按类型存计数）升级为 `std::vector< std::vector<int> > m_avCachedSpecialCityIDs`（按类型存**匹配城市 ID 列表**），接口相应调整：

| 原 | 现 |
| --- | --- |
| `CacheSpecialCityCounts()` | `CacheSpecialCityMatches()` |
| `GetCachedSpecialCityCount(iType)` | 不变（返回 `m_avCachedSpecialCityIDs[iType].size()`） |
| —— | 新增 `IsCachedSpecialCityTypeMatch(iCityID, iType)` |

**重构的必要伴随改动**（措辞已按复审 7.4(1) 订正）：原 `CacheSpecialCityCounts` 只扫描 `m_vSpecialCityCountYieldModifiers` 引用的类型。原实现下这**并非缺陷**——EL_DORADO 的 +100% 旅游走 `CvCity::IsSpecialCityType` 实时判定、不读缓存，而 `GetCachedSpecialCityCount` 仅被 Count 效果消费（Count 表只引用 LUXURY），故三项效果均正常。

但改用「按类型存匹配城市 ID 列表」后，热路径改为**查缓存**，缓存的类型集合就必须同时覆盖两张效果表，否则仅被 `m_vSpecialCityYieldModifiers` 引用的 `SPECIAL_CITY_BOGOTA_EL_DORADO` 会取不到数据。新实现据此同时收集两张效果表引用的类型。

消费点 `CvCity::GetBaseYieldRateModifier` 由 `IsSpecialCityType(...)` 改为 `pCityStateUA->IsCachedSpecialCityTypeMatch(GetID(), ...)`；`CvCity::IsSpecialCityType` 保留为**原始未缓存判定**，仅供缓存构建器调用（避免递归）。刷新点仍挂在 `CvPlayer::RefreshCSAllUAEffects`。

代价：效果随缓存每回合刷新，回合中途新开发的资源要到下回合生效——与 Ife / Vancouver / 原波哥大计数缓存的既有取舍一致。

### P1-2　保留原判定，待实机确认

已核实 `CvCity::IsHasFeatureLocal`（`CvCity.cpp:3993`）与 `CvCity::GetNumResourceLocal`（`:4084`）均以 `pLoopPlot->getWorkingCity() == this` 表达"地块归属本城"，这正是计划中"城市疆域内"的定义，故**不改判定**。

待验证：在拥有黄金国的城市上确认旅游 +100% 是否生效。若不生效，说明自然奇观地块未被分配给该城，届时改用 `pLoopPlot->getOwner() == getOwner() && pPlot->getFeatureType() == eFeature`。

### P2-1　已修复

布拉迪斯拉发 18 行已并入埃里温所在的 `<CityStateUAEffect_BornGreatPersonYieldModifiers>` 块，现为**单一元素共 19 行**（1 埃里温 + 18 布拉迪斯拉发）。两条注释上移到元素之前；埃里温"相邻改良由 SQL 生成"的说明保留原位。已用 `xml.etree` 校验：顶层元素 1 个、行数 19。

### P2-2　已修复

两张新表建表注释补充量纲说明：

- `CityStateUAEffect_SpecialCityYieldModifiers`：标注 "YieldMod here is a PLAIN PERCENT (35 means +35%), NOT basis points"，并与 `BornGreatPersonYieldModifiers`（100 = +1%）显式对照；
- `CityStateUAEffect_SpecialCityCountYieldModifiers`：同样标注百分比，并说明 `CvPlayer::GetCSUAYieldPercentModifier` 中的 `×100` 是该函数内部基点归一所需，**不要预先换算存储值**。

### P2-3　已修复

删除 `CvCityStateUASpecialCityTypeXMLEntries::GetEntryByType` 的声明与实现（已确认全仓库无调用者；同名方法在另两个容器类中仍有使用，未触碰）。

### P2-4　不改

`GetNumResourceLocal` / `IsHasFeatureLocal` 的宏保护属防御性考虑；相关宏在 `CustomMods.h` 中为无条件定义，加保护只增噪声，且与文件内既有调用写法保持一致。

### P2-5　不改

`PrepareResults` 返回值未判空是文件内既有的统一写法；表由本仓库 SQL 自建，正常流程不会失败。留待将来统一重构时一并处理。

### P2-6　不改（非本次引入）

`TXT_KEY_CHOOSE_INTERNATIONAL_TRADE_ROUTE_ITEM_TT_EXTRA` 繁中缺右括号属既有缺陷，与本次改动无关，仅记录在案。

### 修复后状态

- MPDLL 工作区：9 文件 **+536 行**；SP 工作区：5 文件 **+387 / −2**（git 显示删除的 2 行为 P2-1 合并时上移的两条注释）
- 行尾格式保持：LF 文件 CR=0；`CvCity.cpp`（CRLF）CR 数 = LF 数
- DLL 全量重编（先删 `BuildTemp/VS2022_CvGameCore_Expansion2ReleaseWin32` 清 PCH）：**0 错误**，产物已复制至 `(1) CIV5MPDLL/DLL`
- 三语文本 6 个 Tag 各出现 1 次，BOM 状态保持（en_US / zh_CN 无 BOM，zh_Hant 有 BOM）
- 尚未构建模组；尚未覆盖 `Documents\My Games\Sid Meier's Civilization 5\` 根目录 DLL

---

## 七、复审结论（2026-09-26 复审）

复审方式：不采信第六节修复记录的文字描述，逐项回读 MPDLL / SP 工作区**实际代码与数据**，核对改动是否落实、语义是否正确、有无新引入问题。

**总体结论：修复记录属实，5 项声称已修复的改动均已落实且实现正确，DLL 已重编；3 项决定不改的理由成立。**

### 7.1 逐项验证

| 项 | 记录声称 | 复审结果 | 关键证据 |
| --- | --- | --- | --- |
| P0-1 | fail-closed | 属实且正确 | 见 7.2 |
| P1-1 | 每回合缓存 + 查表 | 属实且正确 | 见 7.3 |
| P1-2 | 保留原判定待实机 | 论证成立 | `IsHasFeatureLocal` / `GetNumResourceLocal` 同以 `getWorkingCity() == this` 表达归属，语义自洽 |
| P2-1 | 合并为单一元素 19 行 | 属实 | `xml.etree` 解析：顶层元素 1 个、行数 19 |
| P2-2 | 补量纲注释 | 属实 | SQL 两处 `PLAIN PERCENT ... NOT basis points` |
| P2-3 | 删除死代码 | 属实 | 全仓库已无 `CvCityStateUASpecialCityTypeXMLEntries::GetEntryByType`；另两个容器类同名方法保留未动 |
| P2-4 / P2-5 / P2-6 | 不改 | 理由成立 | — |

### 7.2 P0-1 实现核对

`CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp`：

- 成员 `m_bConditionsInvalid` 在构造函数初始化列表置 false（:26），`CacheResults` 入口再次重置（:41）；
- 两张条件表各自统计原始行数 `iRawRows`（:62、:66）；解析失败行触发 `CvAssertMsg`（:85）后丢弃；
- 遍历结束若 `iRawRows > 0 && 目标 vector 为空`，置 `m_bConditionsInvalid = true` 并再次断言（:91-95）；
- `IsCityMatch` 入口新增 `if (m_bConditionsInvalid) return false;`（:123-124）。

语义保留正确：`iRawRows == 0`（该表本就无行）不置位，故未来纯 AND 城邦的空 Or 表仍按「不限制」处理，未被本次修复波及。

### 7.3 P1-1 实现核对

- 缓存容器改为 `std::vector< std::vector<int> > m_avCachedSpecialCityIDs`（按类型存匹配城市 ID 列表）；
- `CacheSpecialCityMatches`（:2153）先由**两张效果表**共同求 `iMaxType`（:2161-2170），再合并标记 `abReferenced`（:2175-2186），最后逐城逐类型调用 `IsSpecialCityType` 收集 ID（:2189-2200）；
- 消费点 `CvCity.cpp:13550` 改为 `pCityStateUA->IsCachedSpecialCityTypeMatch(GetID(), ...)`；`CvPlayer.cpp` 刷新点改为 `CacheSpecialCityMatches()`；`Reset()` 清空缓存（:1408）；
- `CvCity::IsSpecialCityType` 保留为原始判定，全仓库**仅剩缓存构建器一个调用点**（:2197），无递归风险；
- 缓存未构建（刷新前）时 `IsCachedSpecialCityTypeMatch` 返回 false，属 fail-closed，安全。

### 7.4 复审新发现

**（1）修复记录 P1-1 的措辞需订正**

记录称「原 `CacheSpecialCityCounts` 只扫描 `m_vSpecialCityCountYieldModifiers` 引用的类型，会漏掉仅被 `m_vSpecialCityYieldModifiers` 引用的类型——波哥大的 `SPECIAL_CITY_BOGOTA_EL_DORADO` 正是如此，导致其缓存恒为空」。

经核对，**原实现下这并非缺陷**：EL_DORADO 的 +100% 旅游原本走 `CvCity::IsSpecialCityType` 实时判定，不读缓存；而 `GetCachedSpecialCityCount` 仅被 Count 效果消费，Count 表只引用 LUXURY。故原代码三项效果均正常工作。

准确表述应为：**改用 ID 列表缓存方案后，缓存的类型集合必须同时覆盖两张效果表**——属重构的必要伴随改动，而非修复既有 bug。改动本身必要且正确，仅措辞会误导后来读者。

**（2）P1-2 的补充验证手段**

黄金国判定可通过**城市产出明细 tooltip 直接观察**，无需读存档：命中时代码会执行 `BuildProdModHelpText(toolTipSink, "TXT_KEY_PRODMOD_YIELD", 100)`，在拥有黄金国的城市打开产出明细即可看到 +100% 条目，较间接验证更快。

**（3）可选优化（非阻塞）**

`IsCachedSpecialCityTypeMatch` 为线性查找，复杂度 O(匹配城市数)。当前规模（数十城）足够；若将来出现「匹配大量城市」的类型（如按全国城市数加成的城邦），可改 `std::set` / 排序二分 / 位图。

**（4）可选加固（非阻塞）**

`CacheResults` 中若 `PrepareResults` 返回 NULL，:63 `pResults->Bind(...)` 将解引用空指针（即 P2-5 所记）。当前解析失败路径已有断言，而 `PrepareResults` 失败路径没有——补一句 `CvAssertMsg(pResults != NULL, ...)` 成本极低，可按需处理。

### 7.5 复审结论

- P0-1 / P1-1 / P2-1 / P2-2 / P2-3 修复**确认有效**，可进入下一步；
- P1-2 建议按 7.4(2) 的方法实机验证一次黄金国旅游加成；
- 7.4(1) 的措辞订正建议一并修正，以免后续误读；
- 7.4(3)(4) 属可选优化，不影响本次功能正确性。

---

## 八、对复审的回应（2026-09-26）

复审 7.1 确认 5 项修复属实且正确，此处只处理复审提出的 4 条新发现。

### 8.1　7.4(1) 措辞订正 — 已采纳

复审意见成立。原实现下 EL_DORADO 走实时判定、不读缓存，Count 表又只引用 LUXURY，故**原代码无缺陷**；我的"顺带修正一处缺陷"表述有误。

已改写第六节 P1-1 的对应段落：改为说明这是**改用 ID 列表缓存方案后的必要伴随改动**——热路径从实时判定变为查缓存后，缓存类型集合必须覆盖两张效果表。代码本身无需改动。

### 8.2　7.4(2) 黄金国验证手段 — 已记录

采纳。tooltip 路径确实更快：命中时代码执行 `BuildProdModHelpText(toolTipSink, "TXT_KEY_PRODMOD_YIELD", 100)`，在拥有黄金国的城市打开产出明细即可看到 +100% 条目。实机验证按此执行。

### 8.3　7.4(4) `PrepareResults` 返回 NULL — 已加固（并升级为 fail-closed）

复审指出该路径只缺断言。核对后确认问题比断言更重：`PrepareResults` 返回 NULL 时条件表**两表皆空**，`IsCityMatch` 会走「Or 表为空 → 不限制」分支**匹配所有城市**——与 P0-1 同一类 fail-open，且比 P0-1 更隐蔽（连行都没有，`iRawRows` 恒为 0，原统计逻辑无法察觉）。

故不只加断言，而是按 P0-1 的同一处理原则**直接 fail-closed**。`CvSpecialCityTypeEntry::CacheResults` 新增：

```cpp
if (pResults == NULL)
{
    m_bConditionsInvalid = true;
    CvAssertMsg(false, "CvSpecialCityTypeEntry: failed to prepare the condition query; this special city type will match no city");
    continue;
}
```

注意：因 `iRawRows == 0` 是合法的"纯 AND 空 Or 表"语义，不能用行数判断，只能在此处直接置位——这也是它与 P0-1 判定条件不同的原因。

### 8.4　7.4(3) 线性查找优化 — 暂不处理

**（理由已按三审 9.3 订正）** `IsCachedSpecialCityTypeMatch` 确实位于**热路径** `CvCity::getBaseYieldRateModifier`（`CvCity.cpp:13550`），每城每产出每次计算都会调用；每回合一次的只是缓存**构建**（`CacheSpecialCityMatches`，其中调用的是 `IsSpecialCityType`）。我原先写的"只在缓存构建时发生一次/回合"指的是后者，张冠李戴。

正确的暂不优化理由：查表是 O(匹配城市数) 的 int 线性比较（数十个元素），远轻于被它替换掉的实时判定（全地块扫描 × 6 种资源），因此收益已足够。待将来出现"匹配大量城市"的类型时再改 `std::set` / 位图。

### 8.5　处理结果

- 改动：`CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` 新增 6 行 NULL 防护；报告第六节 P1-1 措辞订正
- DLL 全量重编（清 PCH）：**0 错误**，产物已更新至 `(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll`（22:49）
- 行尾格式保持（LF，CR=0）
- 仍未构建模组、未覆盖根目录 DLL

---

## 九、三审结论（2026-09-26 三审）

三审方式：核对第八节 4 条回应，重点验证其中唯一涉及代码改动的 8.3，并重新系统梳理 `IsCityMatch` 的全部返回路径。

**总体结论：第八节 4 条中 3 条落实无误、1 条（8.4）结论合理但理由表述有误；另发现 1 处残留的 fail-open 场景。**

### 9.1 逐条核对

| 项 | 回应内容 | 三审结果 |
| --- | --- | --- |
| 8.1 | 措辞订正 | 属实。第六节 P1-1 已改写为「重构的必要伴随改动」，并明确写出原实现并非缺陷 |
| 8.2 | 验证手段记录 | 属实，无代码影响 |
| 8.3 | `PrepareResults` NULL 加固 | 属实且正确，见 9.2 |
| 8.4 | 线性查找暂不处理 | 结论成立，**理由表述有误**，见 9.3 |

### 9.2 8.3 代码改动核对

实际代码（`CvCityStateUAClasses.cpp:61-68`）与记录一致。三点确认：

1. **`continue` 语义正确**：跳至下一个表，且 `m_bConditionsInvalid` 已置位；该标志的重置只在函数入口（:41），循环结束后不再被改写，故 fail-closed 必然生效；
2. **「不能用 `iRawRows` 判断」的论证成立**：`iRawRows == 0` 是「纯 AND 空 Or 表」的合法语义，无法与「表不存在」区分，只能在此处直接置位；
3. **上游旁路已排除**：`CvBaseInfo::CacheResults` 恒返回 `true`（`CvInfos.cpp:75`），故函数开头的 `if (!CvBaseInfo::CacheResults(...)) return false;` 永不触发，不存在「提前返回导致 invalid 未置位」的路径。

### 9.3 8.4 理由表述有误（结论不变）

「该调用只在缓存构建时按类型发生一次/回合」不准确：`IsCachedSpecialCityTypeMatch` 恰恰在**热路径** `CvCity::getBaseYieldRateModifier` 中被调用（`CvCity.cpp:13550`），每城每产出每次计算都会执行；每回合一次的只有缓存**构建**（`CacheSpecialCityMatches`，其中调用的是 `IsSpecialCityType`）。

正确表述应为：查表为 O(匹配城市数) 线性比较（数十个 int），缓存构建才是每回合一次的全地块扫描；因前者远轻于被它替换掉的实时判定，故暂不优化。**结论（暂不处理）不受影响，仅理由需订正。**

### 9.4 三审新发现：仍有一处 fail-open 未被覆盖

系统梳理 `IsCityMatch` 所有返回 true 的路径后确认：

| 场景 | 现状 |
| --- | --- |
| Or 表有行但全解析失败 | 已封堵（P0-1） |
| Or 表 `PrepareResults` 失败 | 已封堵（8.3） |
| **Or 表与 And 表都没有任何行** | **仍返回 true，匹配所有城市** |
| 未知 condition type | `EvaluateCondition` 返回 false，安全 |
| `pEntry == NULL`（ID 空洞占位） | `IsSpecialCityType` 返回 false，安全 |

第三种情形下两表 `iRawRows` 皆为 0，P0-1 与 8.3 的判定条件均不触发。设计上「空 Or 表 = 不限制」是有意保留的（为未来纯 AND 城邦留空间），但**两表皆空**实际上只可能来自配置遗漏——纯 AND 城邦必有 And 行。此时该类型会静默匹配所有城市，后果与 P0-1 同级，且更隐蔽（无任何断言触发）。

建议在 `CacheResults` 两表处理完成后追加低成本防护，只加断言、不改运行行为，既保留「无限制」语义的灵活性，又能在新增城邦漏写条件时立即暴露：

```cpp
if (m_vConditionsOr.empty() && m_vConditionsAnd.empty())
    CvAssertMsg(false, "CvSpecialCityTypeEntry: special city type has no condition rows; it will match every city");
```

### 9.5 旁证

- DLL 时间戳 22:49 晚于源文件 22:48，重编属实；
- `CvCityStateUAClasses.cpp` 为 LF 文件，CR=0 保持未破坏；`git diff --stat` 显示该文件 +318（纯新增，无整文件重写）。

### 9.6 三审结论

- 8.1 / 8.2 / 8.3 落实无误，**8.3 的 fail-closed 加固正确且覆盖完整**；
- 8.4 建议订正理由表述（结论保留）；
- 9.4 的残留 fail-open 建议补一行断言，属可选加固，不影响当前功能正确性（现有 XML 数据中两个类型均已定义条件行）；
- 至此 P0-1 / P1-1 / P2-1 / P2-2 / P2-3 修复链完整，P1-2 待实机验证，其余为可选优化。

---

## 十、对三审的回应（2026-09-26）

### 10.1　9.3 8.4 理由订正 — 已采纳

三审意见成立，我的表述确实张冠李戴：`IsCachedSpecialCityTypeMatch` 在热路径被调用，每回合一次的只是缓存**构建**。已改写第八节 8.4，正确理由为"查表是数十个 int 的线性比较，远轻于它替换掉的实时全地块扫描"。结论（暂不优化）不变。

### 10.2　9.4 残留 fail-open — 已封堵，但**未采纳"只加断言"的建议**

三审识别的问题成立：Or 表与 And 表**都没有任何行**时，两表 `iRawRows` 皆为 0，P0-1 与 8.3 的判定条件均不触发，`IsCityMatch` 走「Or 表为空 → 不限制」分支匹配所有城市。

**处理方式与三审建议不同**：三审建议只加断言、保留运行行为不变，以维持「无限制」语义的灵活性。我改为**同时置位 fail-closed**：

```cpp
if (m_vConditionsOr.empty() && m_vConditionsAnd.empty())
{
    m_bConditionsInvalid = true;
    CvAssertMsg(false, "CvSpecialCityTypeEntry: special city type has no condition rows; it would match every city");
}
```

**偏离理由（供斟酌）**：

1. **一致性**：P0-1（有行但全解析失败）与 8.3（查询失败）都已 fail-closed；同为"条件集为空导致 fail-open"的第三种情形却只加断言，三条路径处置不一致，后来读者难以判断哪条是刻意为之。
2. **断言在 Release 下不生效**：断言编译掉之后，Release 版会静默给全国所有城市挂上 +100% 旅游——后果与 P0-1 同级（P0-1 也正是因此被定为 P0）。两种失败方向对比：fail-open 表现为"凭空多出一个强力加成"，酷似正常功能；fail-closed 表现为"效果不生效"，一眼可辨且不会破坏平衡。
3. **实际不损失灵活性**：三审担心的"未来需要『任意城市』类型"场景，用类型抽象本身就是多余——不引用类型的效果天然作用于所有城市。「空 Or 表 = 不限制」的语义是为**纯 AND 城邦**（And 有行、Or 为空）保留的，该情形不受本次改动影响（`m_vConditionsAnd` 非空，新判定不触发）。

若认为应严格保留「无限制」语义，把 `m_bConditionsInvalid = true;` 一行删掉即可退化为三审建议的纯断言方案。

### 10.3　处理结果

- 改动：`CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` 新增 6 行（两表皆空 → fail-closed + 断言）；报告 8.4 措辞订正
- DLL 全量重编（清 PCH）：**0 错误**，产物已更新至 `(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll`（22:56）
- 行尾格式保持（LF，CR=0）
- 仍未构建模组、未覆盖根目录 DLL
- 待办：P1-2 黄金国旅游加成实机验证（按 7.4(2) 的 tooltip 方法）
