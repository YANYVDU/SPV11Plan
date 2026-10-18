# CSUA 审查报告：新加坡（Singapore）

- 审查日期：2026-09-28
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`，本地领先 origin 4 个提交、未 push）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 6 文件 +266 / −1（**含新加坡与推罗两个城邦**，新加坡占 5 文件）；SP 5 文件 +139 / −0（全部为新加坡）
- 结论摘要：实现路径清晰、消费点齐全、数值三方一致，**未发现功能性缺陷**。发现 1 项**需用户确认的语义问题**（"大型城市"按累加口径计数、"一级城市"按互斥口径计数，同一条 UA 内两套计数语义不同），1 项**可测性阻塞**（DLL 构建时间早于本次多个源码文件，需重编），以及数值强度、归因明细等提示项。另：工作区同时混有**推罗（Tyre）**的完整 MPDLL 改动，本报告不覆盖，但提交时需一并处理。

> 术语：设计中的「魅力」= `YIELD_TOURISM`（旅游）。本 UA 未涉及。

---

## 一、改动清单

### MPDLL（新加坡部分）

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +23 | 新建两张表（`:248-264`），含列语义与「仅可用于每城唯一的假建筑类」的口径警告 |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +30 | 两个结构体（`:168-180`）；`CvCityStateUAEffectEntry` 的两个 getter 与成员（`:419-422`、`:588-590`）；`CvPlayerCityStateUA` 的 getter/Has 声明与成员（`:872-878`、`:1099-1101`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +70 | `CacheResults` 两段解析（`:923-984`）；`Reset` 清空（`:1651-1653`）；`ApplyEffect` 两段累加（`:2071-2090`）；两个 `Has*` 实现（`:2645-2653`） |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +13 | `GetCSUAYieldPercentModifier` 产出段（`:18324-18336`） |
| `CvGameCoreDLL_Expansion2/CvTechClasses.cpp` | +19 | `GetResearchCost` 科研阈值折扣段（`:1640-1657`） |

新增接口名：

- 表 `CityStateUAEffect_BuildingClassGlobalYieldModifiers (EffectType, BuildingClassType, YieldType, YieldMod)` —— YieldMod 为**普通百分比**（10 = 每座 +10%）
- 表 `CityStateUAEffect_BuildingClassTechCostModifiers (EffectType, BuildingClassType, TechCostMod)` —— TechCostMod 为**普通百分比**（2 = 每座 −2%）
- 结构体 `BuildingClassGlobalYieldModifierEntry` / `BuildingClassTechCostModifierEntry`
- `CvPlayerCityStateUA::HasBuildingClassGlobalYieldModifiers()` / `HasBuildingClassTechCostModifiers()`
- 消费点复用：`CvPlayer::GetCSUAYieldPercentModifier`（`CvCity.cpp:13605` 调用）、`CvPlayerTechs::GetResearchCost`

### SP

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 | `MINOR_CIV_SINGAPORE` → `CSUA_SINGAPORE` 绑定（`:56`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +63 | 1 个 UA（`:1682-1688`）、2 个效果（`:441-452`）、5 行产出修正 + 1 行科研修正（`:2228-2271`） |
| `Gameplay/XML/Localization/TextInfos_{en_US,zh_CN,zh_Hant_HK}.xml` | 各 +25 | 3 个文本 Tag × 3 语言，追加于各文件末尾 |

---

## 二、效果设计与 XML 三方对照

术语映射已逐一核对（依据游戏内文本 `TXT_KEY_BUILDING_CITY_SIZE_*` 与 `TXT_KEY_BUILDING_CITY_HALL_LV1`）：

| 设计用词 | 假建筑类 | 人口/分数门槛 |
| --- | --- | --- |
| 大型城市 | `BUILDINGCLASS_CITY_SIZE_LARGE` | 26 人口 |
| 特大城市 | `BUILDINGCLASS_CITY_SIZE_XL` | 40 人口 |
| 一级城市 | `BUILDINGCLASS_CITY_HALL_LV1` | 腐败分数 > 0 |

| 对象 | 设计文本 | 实现 | 状态 |
| --- | --- | --- | --- |
| 盟友 | 每座大型城市 → 全国 +10% 金钱 | `LARGE` × `YIELD_GOLD` × 10 | 一致 |
| 盟友 | 每座大型城市 → 全国 +10% 科研 | `LARGE` × `YIELD_SCIENCE` × 10 | 一致 |
| 盟友 | 每座特大城市 → 全国 +20% 产能 | `XL` × `YIELD_PRODUCTION` × 20 | 一致 |
| 盟友 | 每座一级城市 → 科研阈值 −2% | `CITY_HALL_LV1` × `TechCostMod` 2 | 一致 |
| 朋友 | 每座大型城市 → 全国 +4% 金钱与科研 | `LARGE` × {`GOLD`,`SCIENCE`} × 4 | 一致 |

三语言文本数值与语义逐条一致；英文用 `Large City` / `XL City` / `Lv1 City`，与游戏内显示名对齐。

---

## 三、问题清单

### P2-1　「大型城市」与「一级城市」的计数语义不同（需确认设计意图）

同一张表、同一套代码路径（`getBuildingClassCount`）读取两类假建筑，但两类假建筑的**授予方式不同**，导致计数语义不一致：

- **城市规模假建筑：累加保留。** `CvCity::UpdateScaleBuildings`（`CvCity.cpp:24542-24600`）在规模变化时先清空全部规模建筑、再按**当前规模的完整授予列表**重新授予；而 `SP_CityScales.sql:22-23` 中 `BUILDINGCLASS_CITY_SIZE_LARGE` 的授予条件是 `ID >= 4`，即 XL / XXL / GLOBAL 规模的授予列表里**同样包含** `CITY_SIZE_LARGE`。
  → `getBuildingClassCount(CITY_SIZE_LARGE)` = **所有 ≥26 人口的城市数**（特大城市、巨型城市、大都会一并计入）。
  → 一座 40 人口城市同时贡献 +10% 金钱科研（`LARGE`）与 +20% 产能（`XL`）。
- **腐败市政厅假建筑：替换式。** `CvCity.cpp:24677-24696` 在等级切换时先 `SetNumRealBuilding(old, 0)`、再 `SetNumRealBuilding(new, 1)`，每城恒定只持有当前等级的一个市政厅。
  → `getBuildingClassCount(CITY_HALL_LV1)` = **恰好处于腐败 LV1 档的城市数**（不含 LV2 及以上）。

**影响**：若设计者读「每座大型城市」时理解为「26~39 人口的城市」，实际收益会高于预期；而「每座一级城市」按字面就是「恰好一级腐败」，两者并非同一种计数口径。

**建议**：确认设计意图。

- 若「大型城市」本意即「达到大型及以上」→ 现状正确，建议在 `CSUA.xml` 注释中显式写明「累加口径，特大城市亦计入」。
- 若「一级城市」本意是「至少一级腐败」→ 需要改计数口径（现有假建筑体系无法直接表达，因为市政厅是互斥替换的）。

### P2-2　DLL 构建产物早于本次多个源码文件（需重编）

| 文件 | 修改时间 |
| --- | --- |
| `(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll` | **2026-09-28 22:20** |
| `CvPlayer.cpp` | 22:13 |
| `CvTechClasses.cpp` | 22:13 |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | 22:34 |
| `CvCityStateUAClasses.h` | 22:35 |
| `CvCityStateUAClasses.cpp` | 22:36 |
| `CvCity.cpp` | 22:36 |

`CvCityStateUAClasses.{h,cpp}`、`CvCity.cpp`、建表 SQL 均晚于 DLL。若这几次改动包含新加坡的 `CacheResults` / `Reset` / `ApplyEffect` / `Has*` 实现，则**这些内容不在当前 DLL 中**，实机验证会得到「效果完全不生效」的假象。

**建议**：编译前按项目规则清理 PCH 缓存目录 `BuildTemp/VS2022_CvGameCore_Expansion2ReleaseWin32`（本次改了被 PCH 包含的 `CvCityStateUAClasses.h`），再全量重编，确认产物时间戳晚于全部源码。

### P3-1　数值强度提示（非缺陷，供平衡参考）

- **产出加成无上限**：`YieldMod` 无 `Cap` 列，实现亦不做钳制。规模假建筑是累加口径，后期一个 20~30 座大型城市的帝国将获得 +200%~+300% 金钱与科研。设计文本未设上限，故属设计内行为。
- **科研阈值折扣极易触顶**：腐败 LV1 是「分数刚大于 0」的最低档，绝大多数非首都城市长期处于该档，故「每座一级城市」≈「每座城市」。50 座城市即达 `iPercent = 100` 的钳制上限，城市数科研惩罚完全归零。若这不是预期强度，需调低单座值（2）或改档位。

### P3-2　产出加成无归因明细

产出加成经 `GetCSUAYieldPercentModifier` 汇入城市产出修正，tooltip 显示为统一的 `TXT_KEY_PRODMOD_CITYSTATE_UA`（「来自城邦修正: N%」），不区分「每座大型城市 +10%」的构成。这与绝大多数既有 CSUA 一致（仅布加勒斯特因单列明细需求做了专属 tooltip），非本次引入的问题，仅记录。

### P3-3　科研折扣段的两个静默分支

`CvTechClasses.cpp:1652-1654`：

```cpp
if (iPercent > 100) iPercent = 100;
if (iPercent > 0)
    iMod = iMod * (100 - iPercent) / 100;
```

- `TechCostMod` 若被误写为负数，`iPercent` 为负时被 `iPercent > 0` 静默跳过（不会反向放大惩罚）——是合理的防护，但静默。
- `iMod` 理论上可为负（`iModPerCity × GetMaxEffectiveCities(true)`，后者含 `− iNumNoResearchCostWLKDCity` 项）。此时乘 `(100−iPercent)/100` 会让负值绝对值变小，即「折扣」表现为「减少优惠」。正常数据下 `iMod ≥ 40 > 0`，实际不可达；记录以备将来数据变动。

---

## 四、已验证无误项

1. **术语映射正确**：`TXT_KEY_BUILDING_CITY_SIZE_LARGE` = 「大型城市」、`TXT_KEY_BUILDING_CITY_SIZE_XL` = 「特大城市」、`TXT_KEY_BUILDING_CITY_HALL_LV1` = 「市政厅（一级）」（`TextInfos_zh_CN.xml:2826-2836`、`:2862-2864`），与 XML 用的三个假建筑类一一对应。
2. **假建筑类均存在**：`BUILDINGCLASS_CITY_SIZE_LARGE` / `BUILDINGCLASS_CITY_SIZE_XL` / `BUILDINGCLASS_CITY_HALL_LV1` 在 `Civ5DebugDatabase.db` 中均可查到。
3. **城邦绑定可解析**：`MINOR_CIV_SINGAPORE` 存在于基础游戏；`TXT_KEY_CITYSTATE_SINGAPORE` 由基础游戏提供（`Localization-Merged.db` 的 `Language_zh_CN` 中已定义，SP 无需自建），与 `CSUA.xml:1684` 的 `Description` 匹配。
4. **百分比口径正确**：产出表 `YieldMod` 为普通百分比，消费端 `* vBC[i].m_iYieldMod * 100` 转成 basis points（因 `GetCSUAYieldPercentModifier` 末尾 `return iMod / 100`）；科研表 `TechCostMod` 为普通百分比，消费端直接 `(100 - iPercent) / 100`。两处均无「乘 100 / 不乘 100」抄错。
5. **两处消费点齐全**：产出走 `CvPlayer::GetCSUAYieldPercentModifier`（`CvCity.cpp:13605` 调用并计入 `iModifier`）；科研阈值走 `CvPlayerTechs::GetResearchCost`（`CvTechClasses.cpp:1640-1657`）。两个效果均有实际生效路径，无「只建表不接线」。
6. **科研折扣位置正确**：位于吉隆坡傀儡折扣之后、黄金时代缩放之前（注释亦已说明必须 ahead of golden-age line），与既有折扣的串联顺序合理。
7. **盟友 / 朋友互斥且归属正确**：`RefreshCSAllUAEffects`（`CvPlayer.cpp:20080-20087`）以 `IsAllies` 优先、`else if IsFriends` 择一 `ApplyEffect`，故新加坡盟友与朋友效果不会叠加；效果存于**盟友玩家**的 `m_pCityStateUA`，加成落在盟友城市而非城邦自身。
8. **实时读取无缓存滞后**：`getBuildingClassCount`（`CvPlayer.cpp:25500-25505`）直接读 `m_paiBuildingClassCount`，由建筑系统实时维护，故本 UA 不依赖 `RefreshCSAllUAEffects` 中的每回合缓存——城市建成 / 规模变化立即反映，优于基辅、吉隆坡的「最多滞后 1 回合」。
9. **`getBuildingClassCount` 语义匹配**：返回**已建成**的建筑类数（非 `...PlusMaking`），而规模 / 腐败假建筑均为即时授予、不经过建造队列，口径吻合。
10. **腐败市政厅每城唯一**：`CvCity.cpp:24677-24696` 的替换式授予保证 `CITY_HALL_LV1` 计数即「恰好一级腐败的城市数」；傀儡城市走 `CORRUPTION_PUPPET`（`BUILDINGCLASS_PUPPET_GOVERNEMENT`）、首都走 `CORRUPTION_CAPITAL`（无市政厅），均不贡献 LV1 计数。
11. **SQL ↔ C++ 列序对齐**：`BuildingClassGlobalYieldModifiers` 的 select 列序 `(BuildingClassID, YieldID, YieldMod)` 与 `entry.m_iBuildingClass / m_iYieldType / m_iYieldMod` 一一对应；`BuildingClassTechCostModifiers` 的 `(BuildingClassID, TechCostMod)` 同理。
12. **三语言文本齐备且一致**：`TXT_KEY_CSUA_SINGAPORE_HELP`、`TXT_KEY_EFFECT_CSUA_SINGAPORE_ALLY_HELP`、`TXT_KEY_EFFECT_CSUA_SINGAPORE_FRIEND_HELP` 在 `en_US` / `zh_CN` / `zh_Hant_HK` 各 1 条，数值（10 / 20 / 2 / 4）与盟友/朋友划分完全一致，均追加于各文件末尾。
13. **图标有效**：`ICON_CITYBANNER_CITY_LV1` 定义于 `IconAtlases.xml:1801`，且已被既有文本（宫殿）使用，非新造图标；`ICON_GOLD` / `ICON_RESEARCH` / `ICON_PRODUCTION` 均为标准图标。
14. **无需版本门控**：`CvPlayerCityStateUA` 无 `Read` / `Write`，效果在 `RefreshCSAllUAEffects` 中 `Reset()` 后全量重建；本次新增成员为运行时状态，不涉及存档序列化，无需 `MOD_SERIALIZE` 门控。
15. **行尾格式保持**：SP 的 `CSUA.xml` / `CSUA.sql` / 三个 `TextInfos` 均为 LF（CR=0）；MPDLL 的 `CvCityStateUAClasses.{h,cpp}` / `CvPlayer.cpp` / `UNIQUE_CITYSTATES.sql` 为 LF，`CvTechClasses.cpp` 保持其原有的 CRLF，无整篇翻转。
16. **产出明细文本存在**：`TXT_KEY_PRODMOD_CITYSTATE_UA` 在三种语言中均已定义（如 `zh_CN:17922`），加成可在城市产出明细中显示。

---

## 五、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff`（注意 `git diff` 输出较长，需导出后分段读取，避免截断误判）。
- 交叉核对设计文本（`未完成\商业型-未完成.txt:1-5`）、SP XML 数据、三语文本三者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvPlayer::getBuildingClassCount`（`CvPlayer.cpp:25500`）、`CvPlayer::GetCSUAYieldPercentModifier`（`:18235`）、`CvPlayerTechs::GetResearchCost`（`CvTechClasses.cpp:1599`）、`CvCity::UpdateScaleBuildings`（`CvCity.cpp:24542`）、`CvCity::SetScale`（`:24517`）、腐败等级切换（`CvCity.cpp:24655-24704`）、`CvPlayer::RefreshCSAllUAEffects`（`CvPlayer.cpp:20054`）。
- 核对数据来源：`SP_CityScales.sql:4-32`（规模门槛与累加授予条件）、`SPCorruptions.sql:1-9`（腐败档位与市政厅建筑类）。
- 查询 `Civ5DebugDatabase.db` 确认 `MINOR_CIV_SINGAPORE` 与三个建筑类存在；查询 `Localization-Merged.db` 确认 `TXT_KEY_CITYSTATE_SINGAPORE` 由基础游戏提供。
- 核对 `IconAtlases.xml:1801` 确认 `ICON_CITYBANNER_CITY_LV1` 定义。
- 逐文件统计 CR 字符数确认行尾未被翻转。

---

## 六、当前状态与建议处理顺序

### 状态

- MPDLL 工作区：6 文件 +266 / −1（未 commit），**含新加坡与推罗两个城邦**
- SP 工作区：5 文件 +139 / −0（未 commit），仅新加坡
- DLL 产物（`(1) CIV5MPDLL/DLL/` 与 `BuildOutput/VS2022_ReleaseWin32/`）时间戳均为 2026-09-28 22:20，**早于** `CvCityStateUAClasses.{h,cpp}`、`CvCity.cpp`、建表 SQL
- 尚未构建模组
- 缓存数据库 `Civ5DebugDatabase.db` 中 `CSUA_SINGAPORE` 相关数据为空，属「尚未加载新模组」的正常状态

### 建议顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | 确认 P2-1 两套计数口径是否符合设计意图（累加 vs 互斥） | 决策 |
| 2 | 清理 PCH 缓存后全量重编 DLL，消除 P2-2 的可测性阻塞 | 小 |
| 3 | 实机验证（见下） | 小 |
| 4 | P3-1 平衡评估 | 可选 |

### 实机验证步骤（建议）

1. 用世界编辑器放置新加坡并结为盟友，**新开存档**（本次含建表 SQL）。
2. **大型城市加成**：使一座城市人口达到 26 → 全国金钱、科研各 +10%；达到 40 → 额外 +20% 产能，且金钱科研仍保持 +10%（验证累加口径，见 P2-1）。
3. **科研阈值**：观察新科技成本随城市数上升的幅度是否被压低（每座一级腐败城市 −2%，50 座后完全归零）。
4. **朋友档**：降为朋友关系 → 应只剩 +4% 金钱科研，无产能、无科研阈值折扣。
5. **负例**：与新加坡无关系 → 城市产出明细不应出现「来自城邦修正」条目。
6. 数据库校验：`SELECT * FROM CityStateUAEffect_BuildingClassGlobalYieldModifiers;` 与 `..._BuildingClassTechCostModifiers;` 应各有 5 行 / 1 行。

### 需注意的连带事项

- **工作区混有推罗（Tyre）的完整 MPDLL 实现**（枚举 `IS_OTHER_CONTINENT` 及其解析/判定、`SpecialCityDamageReductionEntry` 结构体、建表 `CityStateUAEffect_SpecialCityDamageReduction`、`CvCity::changeDamage` 消费点）。SP 侧尚无推罗数据与文本。若按城邦拆分提交，需从 `CvCityStateUAClasses.{h,cpp}`、`CvCity.cpp`、`UNIQUE_CITYSTATES.sql` 中分离两城邦的 hunk。
- **API 说明库未同步**：按既有约定（CSUA 全部完成前不更新），本次未更新 `d:\Git\CIV5\dyy\Civ5-MPDLL-API说明`；待 CSUA 全部完成后统一重写。
