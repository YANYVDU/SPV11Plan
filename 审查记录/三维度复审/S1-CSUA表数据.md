# S1 SP 的 CSUA 数据库表数据 三维度复审报告

- 审查范围：`git diff a7c2416..HEAD -- "Super Power - Remaking of World Order (v 7)/Gameplay/XML/CSUA/CSUA.xml" ".../CSUA.sql"`（CSUA.xml 2981 行 / 38 提交；CSUA.sql 132 行 / 34 提交）
- 审查日期：2026-10-02
- 结论：应修正 0 项 / 提示 4 项 / 确认无误 12 项

---

## 一、应修正（会导致实际缺陷）

无。

说明：本域数据层未发现会导致运行期缺陷的问题。第 2 项任务重点——子表数值单位不一致（`GreatWorkYieldModifiers` 等为 basis points、多数其它表为 plain percent）——已逐表对照 C++ 消费端的乘除口径，本窗口新增/改动的数值全部与消费端约定一致，未出现"100 倍"或"1/100 倍"错配。第 5 项任务发现的 4 处"设计稿 vs 实现数值"矛盾不构成运行期缺陷（三语言本地化与实现自洽，仅设计稿不符），列于第二节供裁定。

---

## 二、提示（不构成缺陷，供决策）

本节 4 项均为"设计稿（`d:\Git\CIV5\dyy\SP V11\1.城邦UA\*.txt`）与实现（CSUA.xml + 三语言本地化）不一致"。共性：**三语言本地化与实现数值/语义一致，设计稿与之不符**。若认定实现为准，需回写设计稿；若认定设计稿为准，需改数据与本地化。请用户裁定归属。

### [P-1] 【中】西顿 SIDON 无视城防比例：实现 30%/15%，设计稿 50%/20%

- **文件**：`Super Power - Remaking of World Order (v 7)/Gameplay/XML/CSUA/CSUA.xml:207`（盟友 `<CityAttackIgnoreBuildingDefensePercent>30</...>`）、`:214`（朋友 `15`）
- **维度**：A（数值口径，正数无翻转风险）
- **证据**：设计稿 `d:\Git\CIV5\dyy\SP V11\1.城邦UA\军事型.txt:36-38`：
  ```
  盟友效果：盟友的海军进攻城市时无视城市50%来自建筑的城防
  朋友效果：朋友的海军进攻城市时无视城市20%来自建筑的城防
  ```
  实现为 30/15；三语言本地化文件（`Gameplay/XML/Localization/TextInfos_zh_CN.xml`、`TextInfos_en_US.xml`、`TextInfos_zh_Hant_HK.xml`）的 `TXT_KEY_EFFECT_CSUA_SIDON_ALLY_HELP` / `_FRIEND_HELP` 均写 30%/15%，且文案为"你的单位"，未限定"海军"。
- **建议**：确认以哪一方为准——实现为准则回写 `军事型.txt`；设计稿为准则改 `CSUA.xml:207/214` 及三语言。

### [P-2] 【低】布加勒斯特 BUCHAREST 世界奇观产出：实现盟友 +4%，设计稿 +5%

- **文件**：`.../CSUA.xml:2648-2659`（`<CityStateUAEffect_WorldWonderYieldModifiers>` 内 `EFFECT_CSUA_BUCHAREST_ALLY`，`YIELD_CULTURE` 与 `YIELD_TOURISM` 各 `<YieldMod>4</YieldMod>`，`<Cap>0</Cap>`）
- **维度**：A（plain percent，正值无翻转风险）
- **证据**：设计稿 `d:\Git\CIV5\dyy\SP V11\1.城邦UA\文化型.txt:20`（该文件 mtime 2026-10-02）："盟友每拥有一个世界奇观，全国魅力和文化产出+5%"；实现为 4，三语言本地化为 4。朋友档（`YieldMod=2`）与设计稿"朋友…+2%"一致。
- **建议**：同 P-1。

### [P-3] 【低】阿拉木图 ALMATY 朋友骑射加成：实现 12%，设计稿 8%

- **文件**：`.../CSUA.xml:855`（`<CityStateUAEffect_KillMaxHpByPromotion>` 内 `EFFECT_CSUA_ALMATY_FRIEND`，骑射 `Percent=12`）
- **维度**：A（plain percent，正值无翻转风险）
- **证据**：设计稿 `d:\Git\CIV5\dyy\SP V11\1.城邦UA\军事型.txt:7`："朋友效果：朋友的骑射单位获得其击杀数x盟友多余马匹数量x8%的额外血量"；实现为 12，三语言本地化为 12。盟友档（20%）与设计稿一致。
- **建议**：同 P-1。

### [P-4] 【低】拉古萨 RAGUSA 第三盟友效果与设计语义不一致

- **文件**：`.../CSUA.xml:509`（effect 行 `<LocalHappinessCapModifier>50</LocalHappinessCapModifier>`）
- **维度**：A（plain percent；消费点 `CvCity.cpp:12802-12822` 以 `× (100+mod)/100` 应用于本地快乐上限，正值无翻转风险）
- **证据**：设计稿 `d:\Git\CIV5\dyy\SP V11\1.城邦UA\海洋型.txt:48`（该文件 mtime 2026-10-02）："盟友城市每点本地快乐+1%本地文化加成"；实现为"城市可获得的本地快乐上限+50%"，三语言本地化同为"城市的本地快乐上限+50%"。
- **说明**：二者是不同机制——前者为随本地快乐缩放的文化产出加成，后者为快乐容量上限提升——非单纯数值偏差。
- **建议**：确认最终设计；若为"每点本地快乐+1%文化"，需新增产出型效果并替换该字段。

---

## 三、已核查确认无误项

1. **CHORE 提交 43ac092（剥离中文注释）未删除任何真实内容**：对父提交与本提交版本分别用正则 `<!--.*?-->` 剥离 XML 注释后比对，两者均为 2276 行 / 70488 字节，逐字节相同；剥离后 XML 仍可解析。仅删注释，未动任何条件/元素/字符串。
2. **主表 `<CityStateUAs>` 记录完整性**：58 条记录均具备 `Type` / `Description` / `AllyEffectType` / `FriendEffectType`；每个 `EFFECT_*` 在主 `<CityStateUAEffects>` 中都有对应块，且 `CSUA_xxx ↔ EFFECT_CSUA_xxx_ALLY/FRIEND` 程序化配对无缺项、无悬空。
3. **子表 `<CityStateUAEffect_*>` 引用完整**：全部 `EffectType` 均指向已声明效果；无悬挂引用（dangling）；无孤儿效果（声明了效果却零数据行）。
4. **枚举/条件值合法性**：所有子表成员的元素名均能在 DB 存根 `Civ5DebugDatabase.db` 的类型表中解析（UnitClassType/BuildingClassType/YieldType/GreatWorkClass/ImprovementType/SpecialistType/PromotionType/ResourceType/TechType 等拼写正确）；8 种 `SpecialCityType` 条件与 C++ 枚举一一对应；空 `Or`/`And` 条件表未产生"匹配全部"隐患。
5. **本地化键齐全**：CSUA.xml 引用的 234 个 `TXT_KEY_*` 全部存在于 `Localization-Merged.db`。
6. **CSUA.sql 目标合法**：58 条 `UPDATE MinorCivilizations SET UAType=... WHERE Type=...` 的目标城邦在 DB 中均存在；霍尔木兹的 `BUILDINGCLASS_CSUA_HORMUZ` / `BUILDING_CSUA_HORMUZ` 建表正常。
7. **SQL 动态生成表可展开**：耶烈万 `CityStateUAEffect_AdjacentImprovementYieldChanges`（源 `Improvements WHERE ...`）与乌尔 `CityStateUAEffect_BuildingClassYieldModifiers`（源 `BuildingClasses WHERE MaxPlayerInstances>0`）的源集非空，且各自带有 `AFTER INSERT` 触发器以保证后续新增行同源。
8. **数值单位与消费端一致（第 2 项重点）**：逐表核对 C++ 乘除口径——basis points 表（`GreatWorkYieldModifiers`、`BornGreatPersonYieldModifiers`、`LiteracyYieldModifiers`、`LeagueVoteYieldModifiers`、`CoastalCityHappiness`、`WorldWonderHappiness`、`HolySiteHappiness`、`HappinessYieldModifiers`、`LuxuryHappinessYieldModifiers`、`ImmigrantYieldModifiers`、`TradeRouteGoldPerSurplusResource` 等）与 plain percent 表（`GoldenAgeYieldModifiers`、`SpecialCityYieldModifiers`、`BuildingClassGlobalYieldModifiers`、`WorldWonderYieldModifiers`、`DiplomatAbroadYieldModifiers`、`UnknownInfluenceYieldModifiers`、`LocalHappinessCapModifier` 等）取值均与设计意图吻合，无 100 倍量级错配。例：温哥华 `CoastalCityHappiness=300`→+3 快乐；乌尔 `WorldWonderHappiness=200`→+2；伊费 `GoldenAgeYieldModifier=25`→+25%；耶烈万 `BornGreatPersonYieldModifiers=500`→+5%、布拉迪斯拉发 `=100`→+1%。
9. **负值均有界、语义正确、消费端有钳制（第 2 项"翻转"风险）**：全部负值均为折扣或哨兵语义，且消费端 clamp——河内 `EnemyCombatModifierInBordersPerBeenDoW`（-10，`CvUnit.cpp:19822-19823` 钳至 -50）、河内 `EnemyFixedDamageModifierInBorders`（-100/-50，`CvUnit.cpp:19892-19900` 缩放钳 0..100）、布达佩斯 `MaintenanceChange`（-4/-2，`CvTreasury.cpp` 末 `std::max(0,...)` 兜底）、伊费 `CostRiseModifier`（-30/-10，`CvCity.cpp:6257-6260` / `6313` 上限 -90%）、克孜勒 `FaithPurchaseGreatPeopleCostRiseModifier`（-50，上限 -90%）、基辅 `GoldenAgeBuildingMaintenanceMod`（-50）、安塔那那利佛 `CoastalCityGrowthThresholdModifier`（-20/-10，`CvCity.cpp:9518` 为 `×(100+mod)/100` 乘性）、维尔纽斯 `GoldenAgeThresholdPerPopulation`（-100，`CvPlayer.cpp:16129` 为每人口 -1 的加性项）。均无"加成变惩罚"的意外翻转。
10. **无除零/取模零/数组越界隐患**：CSUA 数值中无被用作除数或数组长度的字段；`Cap=0` 表示"无上限"而非除零。
11. **无重复数据行（本窗口）**：对每个子表按整行键做重复检测，唯一一处重复（`PurchasedBuildingXP` / VALLETTA）经 `git show a7c2416` 核对为**基线存量**，不计入本窗口、不上报。
12. **三语言本地化数值与实现一致**：抽查 `TXT_KEY_EFFECT_CSUA_SIDON_*`、`_BUCHAREST_*`、`_ALMATY_*`、`_RAGUSA_*`，简中/繁中/英三份文件与 CSUA.xml 实现数值一致（差异仅存在于设计稿侧，见第二节）。
