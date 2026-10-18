# CSUA 审查报告：布加勒斯特（Bucharest）

- 审查日期：2026-09-27
- 审查对象：工作区未提交改动（审查时尚未 commit；审查通过后提交）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 7 文件 +272；SP 6 文件 +220
- 提交：MPDLL `87d6b00`、SP `19be703`
- 结论摘要：机制全部复用既有 CSUA 挂点，**一审无严重问题**。一审提出 1 项一般问题（移民速率 tooltip 明细缺少布加勒斯特归因），已修复并复审通过。另有多项可选建议，见「二、问题清单」。

> 审查方式：由独立子代理完成（上下文与实现过程完全隔离，只拿到设计文本、方案文档路径与 `git diff`）。

---

## 一、改动清单

### MPDLL `87d6b00`

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +21 | 新建两张子表（`:377` WorldWonder / `:387` DiplomatAbroad） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +46 | 两个结构体 + 两个 vector getter/成员 + 两个缓存 int |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +107 | 构造函数初始化（`:1313-1314`）、`CacheResults` 解析（`:778-795` / `:798-815`）、`ApplyEffect` 累加（`:1748-1766`）、`Reset` 清零（`:1441-1444`）、`CacheWorldWonderCount()` / `CacheDiplomatAbroadCount()`（`:2304-2312`） |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +72 | `GetCSUAYieldPercentModifier` 两段（`:18342-18365`）、`GetCSUAImmigrationRateModifier()` / `GetCSUAEmigrationRateModifier()`、`GetImmigrationRate` 接线（`:19492-19493`）、`RefreshCSAllUAEffects` 两处缓存调用（`:20073-20074`） |
| `CvGameCoreDLL_Expansion2/CvPlayer.h` | +4 | 两个速率 getter 声明 |
| `CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.cpp` | +20 | Lua 导出两个 getter（`Method()` 注册 `:448-449`，实现 `:3629-3645`） |
| `CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.h` | +2 | 两个 `static int lXxx(lua_State*)` 声明（`:335-336`） |

### SP `19be703`

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 | 布加勒斯特 `UAType` 绑定（`MINOR_CIV_BUCHAREST` → `CSUA_BUCHAREST`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +64 | 2 个效果（`:400-412`）、世界奇观表 4 行（`:2091-2113`）、外交官表 2 行、1 个 UA 行 |
| `Gameplay/XML/Localization/TextInfos_{en_US,zh_CN,zh_Hant_HK}.xml` | 各 +45 | 3 个 CSUA Tag + 4 个移民 tooltip Tag × 3 语言，追加于各文件末尾 |
| `UI/InGame/Popups/CultureOverview.lua` | +20 | 移民速率 tooltip 新增 4 个 CSUA 明细分支（`:2183-2201`） |

### 效果设计（已核对与三语文本、XML 三方一致）

| 对象 | 设计文本 | 实现 |
| --- | --- | --- |
| 盟友 | 每世界奇观 全国魅力 + 文化 +4% | `WorldWonderYieldModifiers` × {CULTURE, TOURISM} × 4，`Cap=0`（无上限） |
| 盟友 | 每接收一个移民 迁入速率 +5%（上限 +100%）；每离开一个移民 迁出速率 -5%（上限 -90%） | 主表列 `ImmigrationRatePerImmigrant=5 / ImmigrationRateMax=100`、`EmigrationRatePerImmigrant=5 / EmigrationRateMax=90` |
| 盟友 | 每有一个在他国的外交官 全国产能 + 科研 +5% | `DiplomatAbroadYieldModifiers` × {PRODUCTION, SCIENCE} × 5，`CacheDiplomatAbroadCount` 用 `isMinorCiv()` **排除派驻城邦** |
| 朋友 | 每世界奇观 全国魅力 + 文化 +2% | `WorldWonderYieldModifiers` × {CULTURE, TOURISM} × 2 |

> 「魅力」映射为 `YIELD_TOURISM`（旅游），符合 SP 设计术语约定。

---

## 二、问题清单

### P2-1　移民速率 tooltip 明细缺少布加勒斯特归因 —— **已修复**

- 位置：`SP/.../UI/InGame/Popups/CultureOverview.lua:2110-2200`
- 现象：该 tooltip 逐条列出每一项速率修正（开边 / 谴责 / 友谊 / 宗教 / 快乐 / 政策 / `TRAIT_RIVER_EXPANSION`）。布加勒斯特是**第一个**进入 `CvPlayer::GetImmigrationRate` 的城邦修正，但明细里没有对应条目。显示的「Actual Rate」本身正确（直接调 `GetImmigrationRate`），但明细与实际速率对不上，玩家无法归因。
- 处理：新增 4 个 Lua 分支 + 4 个三语言 Tag（`TXT_KEY_CO_SP_MOVE_{IN,OUT}_CSUA_{YOU,THEM}`），经新导出的 `GetCSUAImmigrationRateModifier()` / `GetCSUAEmigrationRateModifier()` 读取。
- 复审确认：Lua 导出三处齐全（`Method()` 注册在**实例方法区**，故 Lua 侧冒号语法正确）；正负号无误——CSUA getter 返回正数，迁入直显、迁出用正数表达「减少」，与既有 POLICY 行的处理在显示效果上等价（POLICY 行因存储值为负才在 Lua 侧取负），无双重取负；4 个 Tag 与 Lua 引用逐一精确匹配。

### P3-1　tooltip 明细未按实际方向过滤（**非本次引入，保留**）

- 位置：`CultureOverview.lua:2183-2201`（既有 POLICY 行为 `:2164-2175`）
- 现象：公式里实际只用到「MoveIn 方的迁入修正」与「MoveOut 方的迁出修正」两项，但代码把双方共 4 项只要有值就全部列出。例如 activePlayer 为迁出方时，仍会绿色显示「Increase X% Move-in Rate for you」，而该项在此配对上并未参与 `iMoveOutCounterMod`。
- 判断：**不是本次增量引入**——既有 POLICY 四行是同一结构、同一问题，本次只是照抄既有模式。单独修正会破坏同族一致性，建议留到后续 tooltip 统一重构时连同 POLICY 行一起处理。

### P3-2　tooltip 文案未点名布加勒斯特（保留）

- 位置：三语言各 4 个 `TXT_KEY_CO_SP_MOVE_*_CSUA_*`
- 现象：文本写作「你的城邦盟友能力」而非具名。目前只有布加勒斯特提供该效果，语义正确；但若将来再有城邦 UA 接入移民速率修正，这些 Tag 会被复用而指向错误的城邦。
- 建议：接入第二个城邦前留意，或改为具名。

### P3-3　「-90%」上限只约束本项贡献，叠加后可能超过 -90%（保留）

- 位置：`CvPlayer.cpp`（本项封顶 90 个百分点）+ 框架既有钳位 `if (iMoveOutCounterMod < 0) iMoveOutCounterMod = 0;`
- 现象：当同时存在谴责（-50）等其他负修正时，合成值可被钳到 0，即迁出被完全停止（实际降幅 > 90%）。
- 判断：与框架内其他修正的叠加方式一致，若视为符合预期可不动；若设计意图是「最终速率不低于基线的 10%」，需在钳 0 之前另设下限。

### P3-4　`CacheDiplomatAbroadCount` 遍历包含已死亡间谍（保留）

- 位置：`CvCityStateUAClasses.cpp:2304-2312`
- 现象：用 `GetNumSpies()`（= `m_aSpyList.size()`，含 DEAD/TERMINATED）作上界，靠坐标 -1 过滤。
- 判断：逻辑正确、开销极小（仅在该玩家持有布加勒斯特效果时才进入）。所有死亡路径都会先把坐标重置为 -1，故死亡/未派驻间谍不会被计入。如需更省可改用 `GetNumAliveSpies()`，但会偏离本文件既有惯例，非必要。

### P3-5　（既有代码，顺带发现）Lua 导出名缺一个 U

- 位置：`CvLuaPlayer.cpp:3625`
- 现象：实际成员是 `GetCSACityAttackIgnoreBuildingDefensePercent`（`CvPlayer.h:1838`），而 Lua 导出名是 `lGetCSUACityAttackIgnoreBuildingDefensePercent`。内部自洽、可正常编译，仅命名不统一。

---

## 三、已验证无误项

- **数值与盟友/朋友区分**：世界奇观 4%/2%、移民 5%/上限 100% 与 -5%/上限 90%、外交官 5%，朋友段**仅**世界奇观两行（无移民/外交官行）。
- **两套百分比口径**：两张子表 `YieldMod` 为**普通百分比**，代码 `iMod += iTotal * 100`（`:18342-18365`），末尾 `return iMod / 100;`，与 Bogota / Manila 完全一致；`Cap > 0` 才生效。
- **移民速率方向与对称性**：`iMoveOutCounterMod += kMoveInPlayer->GetCSUAImmigrationRateModifier();` / `-= kMoveOutPlayer->GetCSUAEmigrationRateModifier();`。`kMoveInPlayer` / `kMoveOutPlayer` 由 `iMoveOutCounterBase` 符号推导，故 `A.GetImmigrationRate(B)` 与 `B.GetImmigrationRate(A)` 得到同一乘数。单位一致（`iMoveOutCounterMod` 起始 100，普通百分比）。下限钳 0 与「-90%」兼容（基线 100 − 90 = 10 > 0，保留涓流）。
- **边界与安全**：`m_pCityStateUA` / `GetEspionage()` / `pCity` 均判空；无除法；间谍遍历索引与 `IsDiplomat` / `GetCityWithSpy` 的 `uiSpyIndex` 语义一致（均按列表下标）。
- **六处完整性**：构造函数初始化列表（顺序与声明一致）、`CacheResults` 解析、`ApplyEffect` 累加（`*= iChange` 后 push_back，与 Ife 写法一致）、`Reset` 清零、缓存刷新调用点（`RefreshCSAllUAEffects`，经 `doTurn` → `RefreshCSAlliesFriends` 对所有非城邦/非蛮族玩家每回合执行）、tooltip 文本。
- **热路径性能**：`GetCSUAYieldPercentModifier` 只读 flat int，两处入口均有 `Has*()` 早退；缓存方法本身有「无效果早退」（`:2283`）。
- **数据完整性**：SQL 列 `(EffectType, YieldType, YieldMod, Cap)` ↔ C++ `select Yields.ID, YieldMod, Cap` ↔ XML 三方一致；外键目标存在；主表标量列 `ImmigrationRate*` / `EmigrationRate*` 早已存在于 `UNIQUE_CITYSTATES.sql:66-69`（**本次未新增列，故无需版本门控**）。`Civ5DebugDatabase.db` 中 `MINOR_CIV_BUCHAREST` 存在；`Localization-Merged.db` 中 `TXT_KEY_CITYSTATE_BUCHAREST` 存在。
- **规范**：MPDLL 新增注释全英文；两个仓库 diff 纯新增零删除；SP 文件 CR=0（LF 保持），无行尾破坏；版本号未动。

---

## 四、验证方法

由独立子代理执行，未运行 MSBuild（编译由主流程单独完成）：

1. 两仓库 `git diff` 通读
2. 阅读改动所在函数的完整上下文，比对 Ife / Manila / Bogota 模板
3. 查 `Civ5DebugDatabase.db` / `Localization-Merged.db` 核对本体数据
4. 四个改动 XML 经 `ElementTree` 解析校验 well-formed
5. 三语言 Tag 与 Lua 引用程序化比对（missing / extra 均为空）

编译验证：清 PCH 全量重建，`exit=0`，`error C` / `error LNK` 计数为 0。

---

## 五、当前状态与建议处理顺序

### 状态

- 已提交：MPDLL `87d6b00`、SP `19be703`（均未 push）
- 已构建模组到 MODS 目录
- 一审无严重问题；1 项一般问题已修复并复审通过
- **未做实机验证**（实现期间用户不在）

### 建议顺序

1. 先做第 7 节交接文档中的实机验证（重点：移民速率 tooltip 明细、外交官是否排除城邦）
2. 再决定 P3-1 / P3-2 是否需要处理
3. P3-5 属既有代码，可择机统一命名
