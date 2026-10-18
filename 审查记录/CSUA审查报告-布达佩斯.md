# CSUA 审查报告：布达佩斯（Budapest）

- 审查日期：2026-10-01
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order\Super Power - Remaking of World Order (v 7)`（分支 `EconomicAid`）
- 改动规模：MPDLL 6 文件 **+92 / −1**；SP 5 文件 **+101 / −0**
- 结论摘要：三条盟友效果与一条朋友效果**逐条对得上设计稿**，**未发现功能性缺陷**。实现方式为 **`CityStateUAEffects` 扩展 2 列（`UnitMaintenancePerCavalry` / `WoundedFixedDamage`）+ 三处引擎挂钩**（`CvTreasury::CalculateUnitCost` 维护费扣减、`CvUnit::isRiverCrossingNoPenalty` 渡河免疫、`CvUnitCombat` 新增固定伤害 intervene）。有 **0 处应修正**、**2 项待拍板（设计口径确认）**、**4 项非缺陷提示**。

---

## 一、改动清单

### MPDLL

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +4 / −0 | `CityStateUAEffects` 新增 2 列：`UnitMaintenancePerCavalry`（`:85`）、`WoundedFixedDamage`（`:87`），均 `integer DEFAULT 0` |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +8 / −0 | `CvCityStateUAEffectEntry` / `CvPlayerCityStateUA` 两类的 getter 声明（`:287-288` / `:757-758`）与成员声明（`:497-498` / `:1029-1030`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +16 / −0 | 两类构造函数初始化（`:285-286` / `:1466-1467`）、`CacheResults` 解析（`:435-436`）、`Reset` 归零（`:1591-1592`）、`ApplyEffect` 聚合（`:1812-1813`）、getter 实现（`:1096-1097` / `:2262-2263`） |
| `CvGameCoreDLL_Expansion2/CvTreasury.cpp` | +18 / −0 | ① `#include "CvCityStateUAClasses.h"`（`:12`）；② `CalculateUnitCost` 内新增维护费扣减块（`:647-661`） |
| `CvGameCoreDLL_Expansion2/CvUnit.cpp` | +16 / −1 | `isRiverCrossingNoPenalty()` 扩展：既有 `count>0` 之外，盟友陆军（`DOMAIN_LAND`）亦返回 true（`:23039-23057`） |
| `CvGameCoreDLL_Expansion2/CvUnitCombat.cpp` | +30 / −0 | ① `#include "CvCityStateUAClasses.h"`（`:17`）；② 新增 `BudapestWoundedFixedDamageIntervene`（`:4858-4884`）；③ 分发器 `InterveneInflictDamage` 增一行调用（`:4978`） |

> 说明：`CvUnit.cpp` 未在本次 diff 新增 include，但其 `:40` **早已** `#include "CvCityStateUAClasses.h"`（该文件另有 3 处既有 `CvPlayerCityStateUA` 使用），故无缺头文件问题。

### SP

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 / −0 | 城邦绑定 `MINOR_CIV_BUDAPEST` → `CSUA_BUDAPEST`（`:63`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +19 / −0 | 2 个效果行 `EFFECT_CSUA_BUDAPEST_ALLY`（`:473-479`）、`EFFECT_CSUA_BUDAPEST_FRIEND`（`:480-484`）；1 个 UA 条目 `CSUA_BUDAPEST`（`:1769-1775`） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +27 / −0 | 3 个文本 Tag（`TXT_KEY_CSUA_BUDAPEST_HELP` / `TXT_KEY_EFFECT_CSUA_BUDAPEST_ALLY_HELP` / `TXT_KEY_EFFECT_CSUA_BUDAPEST_FRIEND_HELP`） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +27 / −0 | 同上 3 个 Tag（简中） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +27 / −0 | 同上 3 个 Tag（繁中） |

---

## 二、效果设计对照表

设计稿来源：`1.城邦UA/军事型.txt:17-22`。城邦绑定 `MinorCivilizations.Type = MINOR_CIV_BUDAPEST`、`CSUA Type = CSUA_BUDAPEST`（无命名错位）。

| # | 对象 | 设计原文 | 实现 | 判定 |
| --- | --- | --- | --- | --- |
| A | 盟友 | 盟友每有一个轻重骑兵，单位维护费-4，至多降低为0 | `CvTreasury.cpp:647-661`：`dFinalCost -= GetUnitMaintenancePerCavalry() * GetNumUnitsWithUnitCombat(UNITCOMBAT_MOUNTED)`，置于 `return std::max(0, int(dFinalCost))`（`:663`）**之前** | 符合 |
| B | 盟友 | 盟友的单位对受伤单位造成的伤害固定+4（攻防都+4） | `CvUnitCombat.cpp:4858-4884`：目标（承受方）`getDamage()>0` 时，对 `piAttackInflictDamage`（我方为攻）与 `piDefenseInflictDamage`（我方为守）各 `+= 4`，限单位对单位 | 符合 |
| C | 盟友 | 盟友的陆军免疫渡河作战惩罚 | `CvUnit.cpp:23039-23057`：`getDomainType()==DOMAIN_LAND` 且单位所属玩家持有该效果时，`isRiverCrossingNoPenalty()` 返回 true | 符合（影响面见 Q-2） |
| D | 朋友 | 朋友每有一个轻重骑兵，单位维护费-2，至多降低为0 | `EFFECT_CSUA_BUDAPEST_FRIEND`：`UnitMaintenancePerCavalry = 2`（未设 `WoundedFixedDamage` / `LandUnitsImmuneRiverCrossing`，取默认 0/false） | 符合 |

盟友/朋友数值比：4 : 2 = **2 倍**，符合设计全局规则第 2 条（朋友为盟友的 2-3 倍，取边界值）。

### 效果 A 的 UnitCombat 映射（本次审查重点核对）

- 设计术语「轻重骑兵」并非游戏内字面类型，需映射到 `UnitCombatTypes`。实现取 **`UNITCOMBAT_MOUNTED`**。
- 独立取证（未依赖任何实现说明文档）：
  - 缓存数据库 `Civ5DebugDatabase.db` 中 `UNITCOMBAT_MOUNTED` 含 `UNIT_HORSEMAN` / `UNIT_KNIGHT` / `UNIT_LANCER` / `UNIT_CAVALRY` 及各文明骑兵 UU（Companion Cavalry、Cataphract、Conquistador、Winged Hussar、Sipahi、Mamluk、Teutonic Knight、Elite Rider 等），即 **轻骑兵（Horseman/Lancer/Cavalry）+ 重骑兵（Knight）** 同属此类。
  - `UNITCOMBAT_ARMOR` 全部为坦克系（WWI Tank、Tank、Panzer、T-34、MBT、Modern Armor、Land Ironclad、Super Tank、Mech），**非骑兵**。
  - `UNITCOMBAT_HELICOPTER` 中文名为「陆军游猎单位」，承载 SP 的「打了就跑」单位（战车弓手/中世纪战车等），**非轻重骑兵**。
  - `UNITCOMBAT_RECON` 为侦察系（含侦察骑兵），**非轻重骑兵**。
  - 旁证：SP 特性 `TRAIT_TERROR` 文本「所有重骑兵-装甲单位和骑射-直升机单位+1移动」（`TextInfos_zh_CN.xml:6016`），其实现 `Trait_MovesChangeUnitCombats`（`Traits.xml:424-447`）恰好配 `MOUNTED` / `ARMOR` / `HELICOPTER` —— 证明 SP 语境下「重骑兵」= `MOUNTED`，「装甲」= `ARMOR`，二者分列。
- 结论：`UNITCOMBAT_MOUNTED` 恰好等于「轻重骑兵」的并集，映射**干净且自洽**；排除项（装甲/坦克、游猎/骑射、侦察）与设计「骑兵」语义一致。该判定为设计口径确认项，列 Q-1。

---

## 三、问题清单

### 应修正

**无。** 逐条回读被改函数后，未发现功能性缺陷、数值错误、挂钩位置错误或数据/文本不一致。

### 待拍板（需确认，非缺陷）

#### Q-1　「轻重骑兵」映射为 `UNITCOMBAT_MOUNTED` 的口径确认

- 位置：`CvTreasury.cpp:655`（`GC.getInfoTypeForString("UNITCOMBAT_MOUNTED", true)`）。
- 现状：计数仅取 `UNITCOMBAT_MOUNTED`；`UNITCOMBAT_ARMOR`（坦克）、`UNITCOMBAT_HELICOPTER`（战车/游猎）、`UNITCOMBAT_RECON`（侦察骑兵）均**不计**。
- 证据：见「二、效果 A 的 UnitCombat 映射」，`MOUNTED` 恰为轻/重骑兵并集，排除项与「骑兵」语义相符。
- 需确认：**是否接受「仅 `MOUNTED`」的口径**。若设计意图把「重骑兵」理解为含装甲/坦克，或把 SP 的战车/游猎单位视为骑兵，则需改用白名单（按 `UnitClass` 精确枚举）——但据 SP 既有分类，`MOUNTED` 是更自然的映射。
- 建议：维持 `UNITCOMBAT_MOUNTED`；若确认，可视为已闭合。

#### Q-2　渡河免疫的实际影响面略宽于设计字面

- 位置：`CvUnit.cpp:23039-23057`（`isRiverCrossingNoPenalty`）；消费点 `CvUnit.cpp:16007`（战斗）、`CvAStar.cpp:1198-1203 / 1894-1899`（寻路成本）。
- 设计字面：「盟友的陆军免疫渡河**作战**惩罚」——仅战斗。
- 实现实际：① 移除战斗攻击惩罚 `RIVER_ATTACK_MODIFIER`（`CvUnit.cpp:16007`，**符合设计**）；② 使 `CvAStar` 寻路不再为渡河加惩罚权重（AI/自动寻路更倾向渡河，**设计未提及**）。
- 需澄清：**是否接受「盟友 AI 寻路不再规避渡河」这一附带效果**。属正向但超出字面的语义扩展。
- 备注：真正的「移动力成本」（`CvUnitMovement.cpp:55` 的 `RIVER_EXTRA_MOVEMENT`）**未**被豁免——该处直接用 `isRiverCrossing` 判定，不经 `isRiverCrossingNoPenalty`，故「渡河免费」并未发生（见 P-1）。

### 提示（非缺陷）

#### P-1　C++ 注释 `movement and combat` 与实现不符

- 位置：`CvUnit.cpp:23047` 注释 `// Budapest UA: the ally's land units are immune to river-crossing penalties (movement and combat).`
- 说明：实现只覆盖「战斗惩罚 + 寻路成本估计」，**移动力成本未被豁免**（`CvUnitMovement.cpp:55` 用 `isRiverCrossing` 直判，不受本函数影响）。注释中的 `movement` 易误导后续维护者。
- 建议（可选）：改为 `// immune to the river-crossing combat penalty (and the AI pathing penalty); the extra movement cost still applies`。

#### P-2　帮助文本用 `[ICON_MOVES]` / `[ICON_STRENGTH]` 可能引起歧义

- 位置：三语 `TXT_KEY_CSUA_BUDAPEST_HELP` 中「免疫渡河惩罚`[ICON_MOVES]`」与「固定`[ICON_STRENGTH]`+4」。
- 说明：`[ICON_MOVES]` 可能让玩家以为渡河移动免费（实际不免费，见 P-1）；`[ICON_STRENGTH]`（战斗力）用于表示固定 HP 伤害，与设计原文「伤害固定+4」的语义（固定 HP 伤害，非 +4 战斗力）存在轻微错位。SP 既有同类文本（如 `TXT_KEY_TRAIT_TERROR` 的固定伤害描述）多不配图标。
- 建议（可选）：`[ICON_MOVES]` 可删或改述为「渡河作战惩罚」；`[ICON_STRENGTH]` 可去除。属纯文案。

#### P-3　固定伤害与既有晋升/政策固定伤害线性叠加

- 位置：`CvUnitCombat.cpp:4862-4884`（`*ctx->piAttackInflictDamage += ...`），与 `FixAddDamageIntervene`（`:4855` 调用）写同一指针。
- 说明：布达佩斯的 +4 与「胡服骑射」政策、固定伤害晋升等**线性相加**（都走 `+=`）。设计全局规则对加成类不设硬上限，属预期行为，但一次战斗内可能存在多个固定伤害来源叠加。
- 建议：无需改动，仅记录。

#### P-4　`isRiverCrossingNoPenalty` 在寻路热路径新增玩家查询

- 位置：`CvUnit.cpp:23052-23054` 在 `CvAStar` 每次边扩展时执行 `GET_PLAYER(...).GetPlayerCityStateUA()` 判空查询。
- 说明：对大军团寻路为 O(边数) 次查询，实测开销应可忽略（`GetPlayerCityStateUA` 为 O(1)），但与既有「仅查 `count>0`」相比新增了分支。
- 建议：无需改动，仅在性能回归时关注。

---

## 四、已验证无误项

1. **城邦绑定与 Type 正确**：`CSUA.sql:63` 为 `UPDATE MinorCivilizations SET UAType = 'CSUA_BUDAPEST' WHERE Type = 'MINOR_CIV_BUDAPEST'`，与 `CSUA.xml:1769-1775` 的 `CityStateUAs` 条目、基游戏 `MINOR_CIV_BUDAPEST`（`CIV5MinorCivilizations.xml:44`）一致，无命名错位。
2. **维护费扣减位置正确**：`CvTreasury.cpp:647-661` 的 `dFinalCost -= ...` 位于所有既有修正（`GetUnitGoldMaintenanceMod`、人类/AI handicap）**之后**、`return std::max(0, int(dFinalCost))`（`:663`）**之前**，保证「至多降低为0」。
3. **扣减量为总额语义**：`perCav × 骑兵数`，即每骑兵 -4 金的**总额**（非单单位），与设计「每有一个…单位维护费-4」一致。
4. **计数口径为存活单位**：`CvPlayer::GetNumUnitsWithUnitCombat`（`CvPlayer.cpp:5035-5053`）以 `firstUnit/nextUnit` 遍历，仅计存活单位；不含生产中单位。
5. **仅盟友/朋友生效、互斥、可归零**：`CvPlayer.cpp:20122-20128` 以 `IsAllies` 优先、`else if IsFriends` 择一 `ApplyEffect`；`RefreshCSAllUAEffects` 每回合先 `Reset()`（`:20103`）再全量重建，失去关系当回合即归零；盟友得 4、朋友得 2，无 4+2 叠加。
6. **固定伤害 intervene 覆盖攻防两侧**：`CvUnitCombat.cpp:4864-4874`（攻方）、`:4876-4884`（守方）分别以**承受方** `getDamage()>0` 判定，语义与「对受伤单位…（攻防都+4）」精确对应；判定用战斗前 HP，符合「对已受伤目标」。
7. **固定伤害只对单位、不对城市**：两分支均要求 `pAttackerUnit != nullptr && pDefenderUnit != nullptr`；单位攻城市（`pDefenderUnit==nullptr`）、城市攻单位（`pAttackerUnit==nullptr`）均不触发（对照 `CvUnitCombat.cpp:120-145` 城防路径 `ctx.pDefenderUnit` 未设）。
8. **固定伤害不重复施加**：单次战斗 `InterveneInflictDamage` 仅调用一次（各调用点各一次），攻/守两个分支写入**不同指针**（`piAttackInflictDamage` vs `piDefenseInflictDamage`），无双计。
9. **渡河免疫限陆军且仅盟友单位**：`CvUnit.cpp:23049-23055` 先判 `getDomainType()==DOMAIN_LAND`，再取**单位所属玩家**的 CSUA，符合「盟友的**陆军**」。
10. **新列全链路补齐**：解析（`CvCityStateUAClasses.cpp:435-436`）、聚合（`:1812-1813`）、`Reset`（`:1591-1592`）、构造初始化（`:285-286` / `:1466-1467`）、getter（`:1096-1097` / `:2262-2263`）、声明（`.h:287-288/497-498`、`:757-758/1029-1030`）**七环无缺**。
11. **无新增序列化成员**：`CvPlayerCityStateUA` 为纯运行时缓存（无 `Read`/`Write`，每回合 `Reset`+全量重建）；本次未触碰任何 `FAutoVariable`/存档成员，不触发版本门控要求。
12. **编译守卫充分**：`MOD_SP_UNIQUE_CITYSTATE` 已定义（`CustomMods.h:983` → `gCustomMods.isSP_UNIQUE_CITYSTATE()`，选项 `SP_UNIQUE_CITYSTATE` 见 SP `DLL_Options.xml:402`）；`InterveneInflictDamage` 所在块由 `#ifdef MOD_NEW_BATTLE_EFFECTS`（`CvUnitCombat.cpp:4695`，宏恒定义于 `CustomMods.h:960`）包裹，新函数在块内（`:4858`）且在分发器（`:4969`）内被调用，不会被编译剔除。
13. **三语文本齐全且一致**：三个 Tag 在英/简/繁三语**各恰一处**；数值 4 / 4 / 2 与设计、XML 三方一致；均追加于各语言文件**末尾**（`</Language_...>` 之前），未打乱既有分组。
14. **`TXT_KEY_CITYSTATE_BUDAPEST` 真实存在**：基游戏 `CIV5MinorCivilizations.xml` 及三语 `CIV5GameTextInfos_CityStates.xml` 均定义，CSUA 的 `<Description>` 引用有效。
15. **无重复主键**：`CSUA_BUDAPEST` / `EFFECT_CSUA_BUDAPEST_ALLY` / `EFFECT_CSUA_BUDAPEST_FRIEND` 在 SP 全库各仅一处；新增 2 列名在 SQL 中不重复。
16. **注释为英文**：新增 C++ / SQL 注释均为英文，符合 [[sp-english-comments-only]]。
17. **行尾格式保持**：MPDLL 侧 `CvTreasury.cpp` 维持 CRLF（改动行 `:647/653/658` 均以 `\r\n` 结尾），`CvUnit.cpp` / `CvUnitCombat.cpp` / `CvCityStateUAClasses.cpp/.h` / `UNIQUE_CITYSTATES.sql` 维持 LF；SP 五文件维持 LF。`git diff --numstat` 均为小改动，无整文件重写。
18. **DLL 已重编且含本次改动**：`BuildOutput/VS2022_ReleaseWin32/CvGameCore_Expansion2.dll` 与 `(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll` 均为 5338112 字节、时间 2026-10-01 03:56，晚于全部源文件（最晚 `CvUnit.cpp` 03:50）；二进制内 `UnitMaintenancePerCavalry` / `WoundedFixedDamage` / `UNITCOMBAT_MOUNTED` 均可检索到。

---

## 五、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff` / `git diff --stat` / `git diff --numstat`，核对改动规模、行尾与提交状态。
- 交叉核对 C++ 实现、XML 数据、三语文本、设计稿四者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvTreasury::CalculateUnitCost`（`CvTreasury.cpp:580-664`）、`CvPlayer::GetNumUnitsWithUnitCombat`（`CvPlayer.cpp:5035-5053`）、`CvUnit::isRiverCrossingNoPenalty`（`CvUnit.cpp:23039-23057`）及其消费点（`CvUnit.cpp:16007`、`CvAStar.cpp:1198-1203/1894-1899`、`CvUnitMovement.cpp:21/55`）、`CvUnitCombat::InterveneInflictDamage` 全分发链（`CvUnitCombat.cpp:4969-4999`）及 `InflictDamageContext` 结构体（`CvUnitCombat.h:16-33`）。
- 回读框架归属：`CvPlayer::RefreshCSAllUAEffects`（`CvPlayer.cpp:20099-20130`）确认 `IsAllies` 优先、`else if IsFriends`、每回合 `Reset`+全量重建。
- 独立取证 UnitCombat 映射：查询 `Civ5DebugDatabase.db`（`Units.CombatClass`）列出 `MOUNTED`/`ARMOR`/`HELICOPTER` 成员；查询 `Localization-Merged.db` 取 `TXT_KEY_UNITCOMBAT_*` 中文名；交叉 `TRAIT_TERROR` 文本与其 `Trait_MovesChangeUnitCombats` 实现（`Traits.xml:424-447`）。
- 以 `grep -a -o` 在 DLL 二进制中检索新列名 / 类型名，确认产物包含本次改动。
- 全盘检索 `TXT_KEY_CITYSTATE_BUDAPEST`（基游戏安装目录 + SP 仓库）与 `MINOR_CIV_BUDAPEST`，验证绑定与描述引用有效。
- 逐文件检查行尾（`tr -dc '\r'` 计数）与改动行首尾字节，确认 CRLF/LF 未被破坏。

---

## 六、当前状态与建议处理顺序

### 状态

- MPDLL 工作区：6 文件 **+92 / −1**（未 commit）；DLL 已重编（03:56），产物在 `BuildOutput/VS2022_ReleaseWin32/` 与 `(1) CIV5MPDLL/DLL/`。
- SP 工作区：5 文件 **+101 / −0**（未 commit）。
- 游戏根目录 DLL 与 MODS 目录**未更新**（未构建）。
- 文档滞后：若 `未完成/未完成清单.md` 仍列布达佩斯，需在完成后刷新。

### 建议顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | Q-1 拍板（确认「轻重骑兵 = `UNITCOMBAT_MOUNTED`」，排除装甲/游猎/侦察） | 无 |
| 2 | Q-2 拍板（是否接受「AI 寻路不再规避渡河」的附带效果） | 无 |
| 3 | （可选）P-1 修正 `CvUnit.cpp:23047` 注释、P-2 调整帮助文本图标 | 极小 |
| 4 | 覆盖根目录 DLL 或构建模组，按下述步骤实机验证 | 小 |
| 5 | 刷新 `未完成/未完成清单.md`（布达佩斯 → 已完成） | 小 |

### 实机验证步骤

1. **盟友效果 A**：与布达佩斯结盟后，造 N 个轻重骑兵（如 Horseman / Knight / Cavalry），观察「经济概览」单位维护费下降 `4N` 金；造到维护费被减至 0 时不再为负；改造坦克/战车/侦察兵，维护费**不应**再降。断盟后维护费回弹。
2. **盟友效果 B**：以盟友单位攻击一个**已受伤**敌单位，伤害应比攻击满血单位时多 4 点（固定 HP）；令盟友单位**防守**并反击一个受伤来敌，其反击伤害同样 +4；攻击**城市**不应有此 +4。
3. **盟友效果 C**：盟友陆军从河流一侧攻击对岸目标，应无 `RIVER_ATTACK_MODIFIER` 惩罚（战斗力预估无 -25% 类衰减）；对照**海军/空军**及**非盟友**单位仍受惩罚。渡河**移动力**仍应被正常消耗。
4. **朋友效果 D**：与布达佩斯为朋友（非盟友），其维护费扣减应为每骑兵 2 金，且**无**固定伤害 +4、**无**渡河免疫。
5. **断交负例**：与布达佩斯断交后，上述全部效果应于关系变化当回合消失（验证 `RefreshCSAllUAEffects` 重建路径）。
6. **文本回归**：城邦外交界面 / 开局城邦选择列表 / 百科城邦页的 UA 说明应完整显示三段盟友效果 + 一段朋友效果（验证 `Help` 链）。

---

## 修订（2026-10-01）：效果 A/D 计数口径与实现方式变更

本报告上述内容基于**旧实现**（单列 `CityStateUAEffects.UnitMaintenancePerCavalry` + `UNITCOMBAT_MOUNTED` 计数），该实现**已废弃**。

### 变更要点

- **口径修正**：旧报告 Q-1 判定「轻重骑兵 = `UNITCOMBAT_MOUNTED`」**不成立**。SP 把轻骑兵/骑射系归入 `UNITCOMBAT_HELICOPTER`，`UNITCOMBAT_MOUNTED` 仅含重骑兵，会漏计轻骑兵。**新口径按根晋升计数**：轻骑兵 `PROMOTION_HITANDRUN`、重骑兵 `PROMOTION_KNIGHT_COMBAT`；排除坦克（`PROMOTION_TANK_COMBAT`）、直升机（`PROMOTION_HELI_ATTACK`）。
- **实现方式**：由硬编码单列改为 **DB 子表 `CityStateUAEffect_UnitMaintenanceByPromotion`** 驱动，设计者可在 XML 自由配置「晋升 → 每单位维护费变化量」，支持任意数量、任意晋升、任意正负数值。
- **列名语义**：`MaintenanceChange`（负 = 降低，正 = 增加），替代原 `UnitMaintenancePerCavalry`（仅能降低）。
- **消费点**：`CvTreasury::CalculateUnitCost` 尾部按子表条目求和，复用 `CvPlayer::getUnitCountFromHasPromotion(PromotionTypes)`；`std::max(0, int(dFinalCost))` 兜底不变。

### 对旧报告结论的影响

| 旧编号 | 旧结论 | 现状 |
| --- | --- | --- |
| Q-1 | 「轻重骑兵 = `UNITCOMBAT_MOUNTED`」，建议维持 | **推翻**：口径改为按根晋升，`UNITCOMBAT_MOUNTED` 会漏轻骑兵 |
| A / D 行 | `dFinalCost -= GetUnitMaintenancePerCavalry() * GetNumUnitsWithUnitCombat(UNITCOMBAT_MOUNTED)` | **改写**：按子表 `(晋升, 变化量)` 求和 |
| 其余（B 固定伤害、C 渡河免疫、文本、编译） | 无变化 | **不受影响** |

### 编译与验证

- MSBuild Release/Win32，exit 0，0 error；已清 PCH 重建；行尾未翻转；DLL 版本号维持 164。
- 实机（新开存档）：盟友 1 轻骑兵 + 1 重骑兵 → 维护费 -8；朋友 → -4；坦克/直升机不计入。
- DB 校验：`SELECT * FROM CityStateUAEffect_UnitMaintenanceByPromotion;` 期望 4 行、`MaintenanceChange` 均为负。
