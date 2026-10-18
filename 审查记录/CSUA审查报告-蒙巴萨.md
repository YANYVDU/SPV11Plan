# CSUA 审查报告：蒙巴萨（Mombasa）

- 审查日期：2026-10-01
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 2 文件 **+24 / −1**；SP 5 文件 **+143 / −3**
- 结论摘要：三条效果与设计稿逐条一致，**未发现功能性缺陷**。实现方式为**零新表复用**——沿用既有 `SpecialCityYieldModifiers`（逐城加成）与 `SpecialCityCountYieldModifiers`（全国按城市数加成），仅新增一个布尔特殊城市条件 `HAS_LAND_AND_SEA_INTERNATIONAL_TR`，并把推罗的 `SPECIAL_CITY_TYRE_COASTAL` 通用化为 `SPECIAL_CITY_COASTAL` 供两城邦共用。有 **1 个口径缺陷（低危）**、**1 个需拍板的强度点**，另有 5 项非缺陷提示。

---

## 一、改动清单

### MPDLL

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +1 | `SpecialCityConditionTypes` 新增枚举 `SPECIAL_CITY_CONDITION_HAS_LAND_AND_SEA_INTERNATIONAL_TR`（`:127`，插在 `IS_OTHER_CONTINENT` 之后、`NUM_` 之前） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +23 / −1 | `ParseSpecialCityCondition` 新增字符串解析（`:25`）、`IsBooleanSpecialCityCondition` 纳入新枚举（`:35`）、`EvaluateCondition` 新增 case 实现（`:165-184`） |

**未改动任何表结构、任何消费点**——`SpecialCityYieldModifiers` / `SpecialCityCountYieldModifiers` 的读取、聚合、缓存、消费链路（`CvCityStateUAClasses.cpp:888-923` / `:2064-2079` / `:2604-2668`、`CvCity.cpp:13549-13564`、`CvPlayer.cpp:18322-18330`）在本次改动前即已存在，蒙巴萨直接复用。

### SP

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 | 蒙巴萨 `UAType` 绑定（`:59`，`MINOR_CIV_MOMBASA` → `CSUA_MOMBASA`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +73 / −3 | 2 个效果（`:434-441`）、1 个 UA 条目（`:1662-1668`）、1 个特殊城市类型 `SPECIAL_CITY_MOMBASA_LAND_SEA_TR`（`:2007-2009`）与其 And 条件（`:2073-2075`）、6 行逐城产出修正（`:2151-2185`）、2 行全国计数产出修正（`:2201-2212`）；**并含对推罗的 3 处重命名**（见 P-4） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +23 | 3 个文本 Tag（`:20326-20348`） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +23 | 3 个文本 Tag（`:18795-18817`） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +23 | 3 个文本 Tag（`:18601-18623`） |

### 效果设计（已核对与三语文本、XML 三方一致）

| 对象 | 设计文本 | 实现 |
| --- | --- | --- |
| 盟友① | 盟友同时发出陆路与海路国际商路的城市，金钱、文化、食物 +15% | `SpecialCityYieldModifiers` × `SPECIAL_CITY_MOMBASA_LAND_SEA_TR`：GOLD/CULTURE/FOOD 各 15（逐城） |
| 盟友② | 盟友每座沿海城市提高全国 5% 食物和产能 | `SpecialCityCountYieldModifiers` × `SPECIAL_CITY_COASTAL`：FOOD/PRODUCTION 各 5（全国，按沿海城市数） |
| 朋友① | 朋友同时发出陆路与海路国际商路的城市，金钱、文化、食物 +6% | `SpecialCityYieldModifiers` × 同上，各 6（逐城）；**无**计数行 |

设计稿来源：`1.城邦UA/海洋型.txt:23-26`（与 `未完成/海洋型-未完成.txt:7-10` 一致）。蒙巴萨在 `1.城邦UA/城邦类型.txt` 归类为海洋型，`MinorCivilizations.Type = MINOR_CIV_MOMBASA`、`CSUA Type = CSUA_MOMBASA`（见 [[citystate-name-type-mapping]]，该城邦无命名错位）。

---

## 二、问题清单

### 决策点（需拍板，非缺陷）

#### D-1　效果②的强度与上限

- 位置：`CSUA.xml:2201-2212`（`EFFECT_CSUA_MOMBASA_ALLY` × `SPECIAL_CITY_COASTAL` × FOOD/PRODUCTION × 5）；消费点 `CvPlayer.cpp:18328`（`GetCachedSpecialCityCount(...) * 5 * 100`，并入 `GetCSUAYieldPercentModifier`）。
- 现象：全国食物与产能各 **+5% × 沿海城市数**，**无上限**。
- 规模测算：中后期单玩家常见 8~15 座城市，沿海占 5~10 座 → **全国食物与产能 +25%~50%**；群岛/大陆边缘开局可轻松 15+ 沿海城市 → **+75% 以上**。
- 对照：同表 Bogota 为 `SPECIAL_CITY_BOGOTA_LUXURY` × YIELD_TOURISM × 5（`CSUA.xml:2189-2194`），即 **+5% 旅游 / 座**。数值口径与蒙巴萨一致，属仓库既有惯例；但蒙巴萨作用于**食物 + 产能双产出**，且产能是更稀缺的资源，实际强度高于 Bogota 的单产出旅游。
- 影响：食物百分比直接进人口增长路径（与神庙等既有修正同路），产能进建造路径，两者均为高价值乘数。设计规则 15 要求加成类"达到 100% 以上几乎不可能"——15 座沿海城市即触 75%，已接近该目标边界。
- 建议：三选一——① 加全国上限（如 +50%），与温哥华 / 马尼拉的 cap 风格一致；② 降为 +3%/座；③ 维持现状并在设计稿标注"无上限、预期 +25%~75%"作为已知强度。**注意**：cap 类字段当前在聚合层用加法而非取最大值（马尼拉报告 D2-2 遗留），若新增 cap 需一并处理。

#### D-2　效果①的"国际"判定用玩家级而非队伍级（口径缺陷，低危）

- 位置：`CvCityStateUAClasses.cpp:178`，条件为 `pConnection->m_eDestOwner == pConnection->m_eOriginOwner` 即视为国内并跳过。
- 分歧：仓库既有口径 `CvGameTrade::IsConnectionInternational`（`CvTradeClasses.cpp:542-558`）以**所属队伍**比较（`GET_PLAYER(...).getTeam()`），**同队不同玩家 = 非国际**。本实现以**玩家 ID** 比较，会把同队两玩家之间的商路误判为国际，从而错误点亮效果①。
- 影响面：仅在**组队（Team）**场景触发——单机常规对局（每人一队）下 `owner` 与 `team` 判定等价，**无影响**；联机固定队伍 / 单机自定队伍时可能高估。城邦商路场景不受影响（城邦 owner 与玩家必然不同）。
- 建议：改用 `pTrade->IsConnectionInternational(*pConnection)`，与马尼拉等既有城邦口径统一。改动极小（1 行）。

### 提示（非缺陷）

#### P-1　效果①的条件较为苛刻，属"路径"型高门槛高回报

- 需该城市**同时**为至少一条国际陆路与至少一条国际海路的**起点**。内陆城市天然不满足；沿海城市需同时保有指向两个不同目标（或陆海皆可通达）的国际商路。门槛高，但一旦满足即 GOLD/CULTURE/FOOD 各 +15%，回报显著，符合设计"路径选择"原则。仅记录，无建议。

#### P-2　缓存导致 1 回合延迟

- `HAS_LAND_AND_SEA_INTERNATIONAL_TR` 经 `CacheSpecialCityMatches`（`CvCityStateUAClasses.cpp:2604`）每回合在 `RefreshCSAllUAEffects` 中缓存一次；商路建立 / 取消 / 改道后，效果在**下一回合**才反映。
- 评价：1 回合瞬态、不崩溃，与 [[csua-cache-lag-tolerance]] 既定容忍口径一致。仅记录。

#### P-3　性能：每回合每城遍历全部商路

- `EvaluateCondition` 新 case 对每个待评估城市扫描 `m_aTradeConnections` 全表（全玩家商路，约 30~60 条）。单玩家每回合约 `城市数 × 商路数` ≈ 数百~千次迭代，且仅在**持有蒙巴萨效果**的玩家上运行（`m_vSpecialCity*` 非空才进缓存循环）。开销可忽略。仅记录。

#### P-4　重命名推罗数据（对已提交城邦的重构）

- 改动：`SPECIAL_CITY_TYRE_COASTAL` → `SPECIAL_CITY_COASTAL`，共 3 处（`CSUA.xml:2002` 定义、`:2066` And 条件、`:2280` 推罗 DamageReduction 引用）。
- 核实：全 SP 仓库已无 `SPECIAL_CITY_TYRE_COASTAL` 残留（`grep` 命中 0）；MPDLL 侧无该字符串；`SPECIAL_CITY_COASTAL` 仅此一处定义，无重复主键。逻辑等价（定义与全部引用同步改名），推罗功能不受影响。
- 评价：通用化合理——`IS_COASTAL` 本就是通用条件，推罗的伤害减免与蒙巴萨的沿海计数共用同一类型名，避免 `TYRE_` 前缀污染。**但这是对已提交推罗（见 `审查记录/CSUA审查报告-推罗.md`）的改动**，提交时需在 SP 提交信息中一并说明。
- 附带：`SPECIAL_CITY_TYRE_OTHER_CONTINENT`（`:2005`）仍保留 `TYRE_` 前缀，命名不统一但无害。

#### P-5　文本 ICON 位置

- `en_US`：`a [ICON_INTERNATIONAL_TRADE]land and a sea international trade route`——图标落在 "land" 前，视觉上近似 "a 🚢land"。中文（`[ICON_INTERNATIONAL_TRADE]陆路与海路国际商路`）因图标统领整个短语，可读性尚可。
- 建议（可选）：将 `[ICON_INTERNATIONAL_TRADE]` 移至 "international trade route" 前，如 `both a land and a sea [ICON_INTERNATIONAL_TRADE]international trade route`，更符合 [[sp-design-charm-means-tourism]] 同类的图标用法惯例。三语需同步。

---

## 三、已验证无误项

1. **城邦绑定与 Type 正确**：`MINOR_CIV_MOMBASA` → `CSUA_MOMBASA`（`CSUA.sql:59`），与 `CSUA.xml:1662-1668` 的 `CityStateUAs` 条目、`Description = TXT_KEY_CITYSTATE_MOMBASA` 一致；无命名错位。
2. **三语文本齐全且语义一致**：`TXT_KEY_CSUA_MOMBASA_HELP`（盟友 + 朋友两段）、`TXT_KEY_EFFECT_CSUA_MOMBASA_ALLY_HELP`、`TXT_KEY_EFFECT_CSUA_MOMBASA_FRIEND_HELP` 三语均存在，数值 15/5/6 与设计稿、XML 三方一致；均追加于各语言文件**末尾**，未打乱既有分组。
3. **数值三方一致**：设计稿（`海洋型.txt:23-26`）= XML = 三语文本，逐条对应；盟友①为朋友①的 2.5 倍，符合设计规则 2 的 2~3 倍要求。
4. **零新表复用正确**：`SpecialCityYieldModifiers` 走逐城路径（`CvCity.cpp:13549-13564`，`iModifier += YieldMod`，平百分数直接相加）；`SpecialCityCountYieldModifiers` 走全国路径（`CvPlayer.cpp:18322-18330`，`城市数 × YieldMod × 100` 并入 `GetCSUAYieldPercentModifier` 的 basis points，末尾 /100）。语义与设计"该城市 +15%"、"全国每座沿海 +5%" 精确对应。
5. **Tooltip 归属符合既定口径**：效果①为本地逐城型，用通用 `TXT_KEY_PRODMOD_YIELD`（`CvCity.cpp:13560`）；效果②为全局聚合型，经 `GetCSUAYieldPercentModifier` 由 `CvCity.cpp` 以 `TXT_KEY_PRODMOD_CITYSTATE_UA`（「来自城邦修正」）输出。与 [[csua-yield-tooltip-attribution]] 口径一致。
6. **新条件解析链路完整**：`ParseSpecialCityCondition` 新增字符串（`CvCityStateUAClasses.cpp:25`）→ `IsBooleanSpecialCityCondition` 纳入（`:35`，使其免于 `m_iValue >= 0` 校验而被丢弃，见 `:102-106`）→ `EvaluateCondition` case（`:165-184`）。布尔型无需 Value，正确。
7. **引擎 API 用法正确**：`m_aTradeConnections` 遍历以 `IsTradeRouteIndexEmpty` 过滤空槽（`CvTradeClasses.cpp:838-841`，判定 origin/dest 坐标均为 −1），与马尼拉计数写法同构；`m_eDomain` 为 `DomainTypes`，建路时由 `eDomain` 参数赋值（`:338`），陆路 / 海路分别由 `InternationalTradeRouteLandFinder` / `SeaFinder` 生成（`:302-306`），判定可靠；`m_iOriginX/Y` 与 `pCity->getX()/getY()` 比较定位起点城市，正确。
8. **枚举插入位置安全**：新枚举插在 `IS_OTHER_CONTINENT` 之后、`NUM_` 之前，既有枚举值（`IS_RIVER`…`IS_OTHER_CONTINENT`）数值不变；该枚举为 XML 运行时解析、不入存档序列化，无兼容性影响。
9. **特殊城市类型定义完备**：`SPECIAL_CITY_MOMBASA_LAND_SEA_TR`（`CSUA.xml:2008`）仅含一个 And 条件 `HAS_LAND_AND_SEA_INTERNATIONAL_TR`（`:2074`），满足"有行即有效"要求（空 Or 表会被读作"匹配一切"，见 `CvCityStateUAClasses.cpp:113-129` 的 fail-closed 保护）。
10. **无重复主键**：`SPECIAL_CITY_COASTAL` 全 SP 仅 `CSUA.xml:2002` 一处定义；`SPECIAL_CITY_MOMBASA_LAND_SEA_TR` 唯一；MPDLL 侧 SQL 未预置同名 `SPECIAL_CITY_*` 行（`UNIQUE_CITYSTATES.sql` 仅注释提及示例）。
11. **盟友 / 朋友互斥且归属正确**：效果存于**盟友玩家**的 `m_pCityStateUA`，`RefreshCSAllUAEffects` 以 `IsAllies` 优先、`else if IsFriends` 择一应用；朋友行未填效果②，故朋友只得 6% 逐城加成，与设计一致。
12. **每回合重建、无需版本门控**：本次未新增任何序列化成员（仅新增枚举与 XML 行），效果随 `RefreshCSAllUAEffects` 全量重建，符合 CLAUDE.md 版本门控的适用条件（无新增 `Read`/`Write` 成员）。
13. **DLL 已含本次改动**：`BuildOutput/VS2022_ReleaseWin32/CvGameCore_Expansion2.dll`（2026-10-01 00:15）与 `(1) CIV5MPDLL/DLL/` 同名产物均 5332480 字节；二进制内 `HAS_LAND_AND_SEA_INTERNATIONAL_TR` 命中 1 次，旧串 `SPECIAL_CITY_TYRE_COASTAL` 命中 0 次。产物时间晚于源文件（`.cpp` 00:13、`.h` 00:12）。
14. **行尾格式保持**：MPDLL 两文件、SP 的 `CSUA.xml` / `CSUA.sql` / 三语文本均 CR=0（LF），无混合、无破坏；`git diff --stat` 无整文件重写（SP 最大为 `CSUA.xml` +73/−3，属正常行级增删）。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff`，核对改动规模与行尾。
- 交叉核对 C++ 实现、XML 数据、三语文本、设计稿四者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvCityStateUAClasses.cpp` 的 `ParseSpecialCityCondition` / `IsBooleanSpecialCityCondition` / `EvaluateCondition`（`:134-188`）、`CacheSpecialCityMatches`（`:2604-2668`）、`GetCachedSpecialCityCount`（`:2585-2590`）；`CvCity::getBaseYieldRateModifier` 的 SpecialCityYieldModifiers 落点（`CvCity.cpp:13549-13564`）；`CvPlayer::GetCSUAYieldPercentModifier` 的 SpecialCityCountYieldModifiers 落点（`CvPlayer.cpp:18322-18330`）。
- 回读引擎侧商路 API：`CvGameTrade::IsConnectionInternational`（`CvTradeClasses.cpp:542-558`）、`IsTradeRouteIndexEmpty`（`:838-841`）、建路时 `m_eDomain` 赋值（`:302-338`）。
- 以 `grep -a -o` 在 DLL 二进制中检索新 / 旧条件字符串，确认产物包含本次改动且无旧名残留。
- 与既有同类实现横向对照：Bogota（`SpecialCityCountYieldModifiers` × 5 旅游/座，`CSUA.xml:2189-2194`）、推罗（`SPECIAL_CITY_COASTAL` DamageReduction 40%、`SPECIAL_CITY_TYRE_OTHER_CONTINENT` × 5 金/座）作为写法与强度基准。

---

## 五、当前状态与建议处理顺序

### 状态

- MPDLL 工作区：2 文件 **+24 / −1**（未 commit）；DLL 已重编，产物在 `BuildOutput/VS2022_ReleaseWin32/` 与 `(1) CIV5MPDLL/DLL/`（00:15）。
- SP 工作区：5 文件 **+143 / −3**（未 commit，含推罗重命名 3 行）。
- 游戏根目录 DLL（`Documents\My Games\Sid Meier's Civilization 5\CvGameCore_Expansion2.dll`）与 MODS 目录**未更新**（未构建）。
- 文档滞后：`未完成/未完成清单.md` 海洋型仍列蒙巴萨；完成后海洋型未完成应剩 **3 项**（摩加迪沙、魁北克、拉古萨）。

### 建议顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | D-2 改用 `IsConnectionInternational` 统一国际口径（组队场景） | 极小（1 行） |
| 2 | D-1 效果②强度拍板（加上限 / 降数值 / 维持并标注） | 小 |
| 3 | P-5 文本 ICON 位置（可选） | 小 |
| 4 | 清理 `BuildTemp/VS2022_CvGameCore_Expansion2ReleaseWin32` 后全量重编一次（消除时序疑点，成本极小） | 小 |
| 5 | 覆盖根目录 DLL 或构建模组，按下述步骤实机验证 | 小 |
| 6 | 刷新 `未完成/未完成清单.md`（蒙巴萨 → 已完成） | 小 |

### 实机验证步骤

1. **盟友效果①**：与蒙巴萨结盟，令某城同时保有 1 条国际陆路与 1 条国际海路，城市产出明细中 GOLD/CULTURE/FOOD 各应 +15%；仅有一条或全为国内商路时**无**此加成。
2. **盟友效果②**：城市产出明细（或悬停食物 / 产能）应出现「来自城邦修正: X%」条目，X = 5 × 沿海城市数；新建 / 失去一座沿海城市后，该值应于**下一回合**更新（缓存刷新时机）。
3. **朋友效果**：与蒙巴萨为朋友（非盟友），仅见 +6% 逐城三产出，**无**效果②的全国食物 / 产能加成。
4. **组队负例（验证 D-2）**：若 D-2 已修，组队（同队不同玩家）之间的商路**不应**点亮效果①；若未修，可复现误判。
5. **断交负例**：与蒙巴萨断交后，上述条目应全部消失（验证 `RefreshCSAllUAEffects` 重建路径）。
6. **推罗回归**：与推罗结盟后，其沿海城市伤害减免 40%（`SPECIAL_CITY_COASTAL`）与跨大陆城市 +5% 金应仍正常（验证 P-4 重命名无副作用）。
