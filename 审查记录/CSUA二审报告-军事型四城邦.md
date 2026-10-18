# CSUA 二审报告：军事型四城邦（贝尔格莱德 / 布达佩斯 / 河内 / 姆班扎刚果）

> **2026-10-01 后续变更**：河内 `EnemyFixedDamageModifierInBorders` 已由「禁用百分比正数（100/50）」改为负数语义（-100/-50），消费端与 UI 相应调整。本报告下述 100/50 数值为变更前的旧语义。

- 二审日期：2026-10-01
- 审查对象：四个城邦**修复后已提交版本**（工作区干净，`git status` 无改动）
- 涉及仓库与提交：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`），基线 `cd54104`（魁北克）
    - `e7ffedf` 贝尔格莱德 → `fa6a5ed` 布达佩斯 → `e6b3bed` 河内 → `a73c20a` 姆班扎刚果（HEAD）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`），基线 `3df2b1b`（魁北克）
    - `c8161fc` 贝尔格莱德 → `9c1b1fb` 布达佩斯 → `8af4a90` 河内 → `814377c` 姆班扎刚果（HEAD）
- 合计改动规模：MPDLL `git diff cd54104..HEAD` = **13 文件，+500 / −61**；SP `git diff 3df2b1b..HEAD` = **5 文件，+386 / −0**（与任务描述一致）
- 一审报告：贝尔格莱德（0 应修正 / 3 提示）、布达佩斯（0 应修正 / 2 待拍板 / 4 提示）、河内（0 应修正 / 4 待拍板 / 3 提示）、姆班扎刚果（0 应修正 / 3 待拍板 / 3 提示）
- **结论摘要**：
  - 四条盟友/朋友效果**逐条对得上设计稿**，数值、档位、方向全部正确。
  - 一审的**「应修正」为 0**，全部一审「建议类提示」中可落地的（贝尔格莱德 P-1/P-3、布达佩斯 P-1/P-2、河内 Q-1 注释/P-1、姆班扎 P-1）**均已修复**，逐条有证据（见第二节）。
  - **跨城邦交互审查未发现新缺陷**：河内对固定伤害的缩放**正确覆盖**布达佩斯的 +4 贡献（有意为之），无重复缩放，攻/守归属正确；河内与姆班扎在 `GetGenericMaxStrengthModifier` 内**共存无冲突**；ZOC 重写、维护费、计数器落点均不干扰既有机制。
  - 二审新发现：**应修正 0 项**；待拍板 0 项（沿用一审 9 项）；提示 3 项（D9 残留、布达佩斯帮助文本多一行城邦名、序列化版本不升导致的同版本存档不互通风险）。

---

## 一、四城邦总览表

| 城邦 | 效果条数 | MPDLL 提交 | SP 提交 | 一审结论 | 二审结论 |
| --- | --- | --- | --- | --- | --- |
| 贝尔格莱德 Belgrade | 盟友 3 + 朋友 1 | `e7ffedf` | `c8161fc` | 0 应修正 / 3 提示 | 通过（P-1、P-3 已修；P-2 保留） |
| 布达佩斯 Budapest | 盟友 3 + 朋友 1 | `fa6a5ed` | `9c1b1fb` | 0 应修正 / 2 待拍板 / 4 提示 | 通过（P-1、P-2 已修；Q-1、Q-2 待拍板） |
| 河内 Hanoi | 盟友 3 + 朋友 1 | `e6b3bed` | `8af4a90` | 0 应修正 / 4 待拍板 / 3 提示 | 通过（Q-1 注释、Q-2 帮助文本、P-1 已修；Q-3、Q-4 待拍板） |
| 姆班扎刚果 Mbanza Kongo | 盟友 3 + 朋友 1 | `a73c20a` | `814377c` | 0 应修正 / 3 待拍板 / 3 提示 | 通过（P-1 已修；Q-1~Q-3 待拍板） |

数值与档位核对（XML ↔ 设计稿 ↔ 三语文本，四方一致）：

| 城邦 | 盟友 | 朋友 | 盟友/朋友比值 | 规则 2 判定 |
| --- | --- | --- | --- | --- |
| 贝尔格莱德 | XP 30 / ZOC +1 / 驻军城防 +200% | XP 15 | 2.0 | 合规 |
| 布达佩斯 | 维护费 −4/骑兵 / 对受伤 +4 / 陆军渡河免疫 | 维护费 −2/骑兵 | 2.0 | 合规 |
| 河内 | 境内敌固定伤害失效(100) / 和谈 +5% 文化 / 被宣战 −10% 敌军战斗力 | 境内敌固定伤害 50% | 2.0 | 合规 |
| 姆班扎刚果 | 组建 +10%/城 / 人力 +4/城 / 科技差 +10% 战斗力 | 组建 +4%/城 | 2.5 | 合规 |

绑定与文本核对（全部通过）：

| 城邦 | MinorCivilizations | CSUA Type | Description Tag | 基游戏 Tag 核实 |
| --- | --- | --- | --- | --- |
| 贝尔格莱德 | `MINOR_CIV_BELGRADE` | `CSUA_BELGRADE` | `TXT_KEY_CITYSTATE_BELGRADE` | 存在（Expansion2 `CIV5MinorCivilizations.xml:161-164`，无 `_CITY`） |
| 布达佩斯 | `MINOR_CIV_BUDAPEST` | `CSUA_BUDAPEST` | `TXT_KEY_CITYSTATE_BUDAPEST` | 存在（`:44-47`，无 `_CITY`） |
| 河内 | `MINOR_CIV_HANOI` | `CSUA_HANOI` | `TXT_KEY_CITYSTATE_HANOI` | 存在（`:213-216`，无 `_CITY`） |
| 姆班扎刚果 | `MINOR_CIV_MBANZA_KONGO` | `CSUA_MBANZA_KONGO` | `TXT_KEY_CITYSTATE_MBANZA_KONGO` | 存在（`:681-684`，无 `_CITY`） |

SP 侧文本三语齐备：12 个 Tag（4 城邦 × `_HELP`/`_ALLY_HELP`/`_FRIEND_HELP`）在 en_US / zh_CN / zh_Hant_HK **各恰一处**（脚本核对 en=cn=hant=1），均追加在各语言文件末尾（`</Language_*>` 之前），XML 经解析器验证 well-formed。

---

## 二、一审修复验证（逐城邦逐条，附证据）

### 2.1 贝尔格莱德（一审：0 应修正 / 0 待拍板 / 3 提示）

| 一审项 | 一审建议 | 最终代码状态 | 是否修复 | 证据 |
| --- | --- | --- | --- | --- |
| **P-1** 每回合无条件重算全城城防 | 收窄 `UpdateCityStrength()` 到关系变化路径，或仅在持有 `GarrisonCityDefenseModifier != 0` 时调用 | **已修复**：`RefreshCSAllUAEffects` 开头捕获旧值 `iOldGarrisonCityDefenseModifier`，末尾仅当「旧值 ≠ 0 或新值 ≠ 0」时才 `UpdateCityStrength()` | ✅ | `CvPlayer.cpp:20129`（捕获）、`:20222-20225`（条件调用） |
| **P-2** `static` 缓存不随新开游戏/读档重置 | （可选）在 `CvGame::init`/读档处置 `-1`，或改存「本回合最大 ZOC 半径」 | **未修复**：`static int s_iCachedTurn = -1; static bool s_bCached = false;` 仍在，进程级持久 | ⚠️ 保留（可选） | `CvUnitMovement.cpp:328-329` |
| **P-3** 注释「O(1)」「无加成时不受影响」表述偏乐观 | 注释改为「每回合 O(1) 缓存判定；无加成时 3×3，有加成时全局 5×5」 | **已修复**：注释已改为「The lookup is cached per game turn... Note this only picks the scan window size: the scan is 3x3 while no bonus exists and expands globally to 5x5 while any bonus is active.」 | ✅ | `CvUnitMovement.cpp:322-326` |

**P-1 修复的安全性复核**：收窄条件只影响「城防重算」这一用途。经全仓 grep，CSUA 侧影响城市强度的输入**只有** `GetGarrisonCityDefenseModifier`（`CvCity.cpp:17021` 是唯一消费点）；`CvCity.cpp` 其余 CSUA 引用（`:2294` 瓦莱塔免疗、`:12767` 改良快乐、`:13512` 建筑类产出等）均不进入 `updateStrengthValue`。故「仅当驻军修正变化时重算」不会漏掉任何其他 CSUA 的同回合生效需求。

### 2.2 布达佩斯（一审：0 应修正 / 2 待拍板 / 4 提示）

| 一审项 | 一审建议 | 最终代码状态 | 是否修复 | 证据 |
| --- | --- | --- | --- | --- |
| **Q-1** 「轻重骑兵」映射为 `UNITCOMBAT_MOUNTED` | 确认口径 | **未决**：仍仅取 `UNITCOMBAT_MOUNTED`，排除 `ARMOR`/`HELICOPTER`/`RECON` | 待拍板 | `CvTreasury.cpp:655` |
| **Q-2** 渡河免疫影响面含 AI 寻路 | 确认是否接受 | **未决**：`isRiverCrossingNoPenalty` 仍被 `CvAStar.cpp:1200/1894` 消费 | 待拍板 | `CvUnit.cpp:23100-23114` |
| **P-1** 注释 `movement and combat` 与实现不符 | 改为「combat penalty（+AI pathing）；extra movement cost still applies」 | **已修复**：注释已改为 `immune to the river-crossing combat penalty (and the AI pathing penalty); the extra movement cost still applies.` | ✅ | `CvUnit.cpp:23103` |
| **P-2** 帮助文本 `[ICON_MOVES]`/`[ICON_STRENGTH]` 歧义 | 删/改图标 | **已修复**：三语帮助文本中「渡河」与「+4 伤害」两行**均不再带图标**（保留的 `[ICON_GOLD]` 用于维护费，语义正确） | ✅ | `TextInfos_en_US.xml:20434-20436`、`zh_CN:18903-18905`、`zh_Hant_HK:18709-18711` |
| **P-3** 固定伤害线性叠加 | 仅记录 | 无改动（预期行为） | — | `CvUnitCombat.cpp:4903-4926` |
| **P-4** 寻路热路径新增玩家查询 | 仅关注 | 无改动 | — | `CvUnit.cpp:23107-23111` |

### 2.3 河内（一审：0 应修正 / 4 待拍板 / 3 提示）

| 一审项 | 一审建议 | 最终代码状态 | 是否修复 | 证据 |
| --- | --- | --- | --- | --- |
| **Q-1** 判定基准是「战斗地块归属」而非「敌方单位位置」 | 确认口径 (b)；建议在 `GetCSUAFixedDamageScale` 注释写清 battle plot 与 unit location 的区别 | **口径未决，但注释已补**：注释新增 `NOTE: the criterion is BATTLE PLOT OWNERSHIP, not the unit's own location...` | ✅（注释部分）/ 口径待拍板 | `CvUnitCombat.cpp:4702-4705` |
| **Q-2** 效果③ −50% 上限为实现自选 | 确认是否保留；若保留，同步进设计稿/帮助文本 | **已同步三语帮助文本**：en `(up to 50%)`、简中 `（最多-50%）`、繁中 `（最多-50%）`，语义一致 | ✅（帮助文本）/ 是否保留待拍板 | `TextInfos_en_US.xml:20461`、`zh_CN:18930`、`zh_Hant_HK:18736` |
| **Q-3** 效果③不作用于远程攻击强度 | 确认「战斗力」是否应含远程 | **未决**：仍只挂 `GetGenericMaxStrengthModifier`（近战攻防） | 待拍板 | `CvUnit.cpp:15583-15605` |
| **Q-4** 计数器终身累计；和谈计数排除城邦 | 确认起点与口径 | **未决**：仍终身累计、和谈要求双方均主要文明 | 待拍板 | `CvPlayer.cpp:32879-32902`、`CvTeam.cpp:1725` |
| **P-1** 城市固定伤害有意不缩放、缺注释 | 补一行英文注释 | **已修复**：新增 `cities are the territory itself, never scaled...` | ✅ | `CvUnitCombat.cpp:4758-4759` |
| **P-2** 热路径新增判定 | 仅记录 | 无改动 | — | `CvUnit.cpp:15588-15604` |
| **P-3** 新成员未进构造函数初始化列表 | 可选补入 | **未修复**：仍仅由 `uninit()` 归零（`reset()` 调 `uninit()`，实际安全） | ⚠️ 保留（可选） | `CvPlayer.cpp:1280-1281` |

### 2.4 姆班扎刚果（一审：0 应修正 / 3 待拍板 / 3 提示）

| 一审项 | 一审建议 | 最终代码状态 | 是否修复 | 证据 |
| --- | --- | --- | --- | --- |
| **Q-1** 战斗力加成不设上限 | 确认无上限口径 | **未决**：`iDiff * iPerTech` 无截断，帮助文本亦未提上限 | 待拍板 | `CvUnit.cpp:15765-15767` |
| **Q-2** 仅覆盖近战攻防，不含远程攻击 | 确认是否应含远程 | **未决** | 待拍板 | `CvUnit.cpp:15741-15771` |
| **Q-3** 4 人力会被 AI 难度修正放大 | 确认是否接受 | **未决**：人力块仍在 `GetStrategicResourceMod()`/AI 难度乘法之前 | 待拍板 | `CvPlayer.cpp:24668-24680` |
| **P-1** 注释引用内部决策编号（`D4`/`D5`/`D7`/`D8`/`design rule 15`） | 去编号化 | **已修复（针对姆班扎代码）**：`CvUnit.cpp` 与 `CvPlayer.cpp` 的姆班扎块注释已无 `D4/D5/D7/D8/design rule` 字样 | ✅ | `CvUnit.cpp:15742-15748`、`CvPlayer.cpp:24668-24671`（残留见第四节 提示 N-1） |
| **P-2** 热路径字符串→类型查找 | 可选缓存 | **未修复**：`GC.getInfoTypeForString("RESOURCE_MANPOWER", true)` 仍在热路径 | ⚠️ 保留（可选） | `CvPlayer.cpp:24672` |
| **P-3** 效果②③无 tooltip 归因 | 仅记录 | 无改动 | — | — |

**P-1 残留核查（grep 证据）**：全仓 `grep -rn "D4:\|D5:\|D7:\|D8:\|design rule"` 在 MPDLL 的 `CvGameCoreDLL_Expansion2/` 内**零命中**；唯一命中的是 `CvUnit.cpp:15587` 的 `D9:`，属**河内**块（非姆班扎），详见第四节提示 N-1。

---

## 三、跨城邦交互审查（二审核心）

### B.1 `CvUnitCombat.cpp` 固定伤害链路：河内缩放 × 布达佩斯 +4

**结论：河内的缩放正确覆盖布达佩斯的贡献，属有意为之；无重复缩放；攻/守归属正确。**

- 缩放门 `GetCSUAFixedDamageScale(pUnit, pBattlePlot)`（`CvUnitCombat.cpp:4708-4729`）在 `InterveneInflictDamage` 顶部按**战斗地块归属方**一次性预算出攻/守两侧的 scale（`:5024-5028`），写入 `ctx->iAttackerFixedDamageScale` / `iDefenderFixedDamageScale`（默认 100）。
- 布达佩斯新函数 `BudapestWoundedFixedDamageIntervene`（`:4903-4926`）**显式**乘以所属单位的 scale：
  - 攻方分支：`*piAttackInflictDamage += GetWoundedFixedDamage() * iAttackerFixedDamageScale / 100;`（`:4914`）
  - 守方分支：`*piDefenseInflictDamage += GetWoundedFixedDamage() * iDefenderFixedDamageScale / 100;`（`:4924`）
  - 函数头注释明示：`Hanoi CS UA: this is also fixed damage, so it is scaled by the owning unit's fixed-damage scale.`（`:4905`）→ **有意覆盖，非遗漏**。
- **无重复缩放**：scale 每场战斗对每个单位只预算一次（`:5027-5028`），布达佩斯对自身贡献只乘一次；其余固定伤害接触点各自乘一次，彼此不重复。
- **叠加数值正确**（同玩家兼为布达佩斯盟友与河内盟友）：
  - 该玩家在**自己领土**内战斗 → `GetCSUAFixedDamageScale` 命中 `eOwner == pUnit->getOwner()` 短路返回 100（`:4712`）→ 布达佩斯 +4 全额生效；河内只削「敌方」固定伤害，己方不受影响。
  - 该玩家在**河内盟友的敌国领土**内进攻 → 敌方非河内盟友，scale = 100 → +4 全额；河内战斗惩罚作用于对方。
  - 对方为河内盟友、我方进攻其领土 → 我方单位 scale = 0 → 布达佩斯 +4 亦被归零，符合「敌人在盟友境内时其固定伤害失效」的设计（河内保护领土不受**任何**敌方固定伤害，含布达佩斯）。
- **攻/守方向归属正确**：`UnitDamageChangeIntervene`（`:4751-4755`）、`UnitAttackInflictDamageIntervene`（`:4800`）、`UnitDefenseInflictDamageIntervene`（`:4821`）、`FixReduceDamageIntervene`（`:4835`）、`FixAddDamageIntervene`（`:4872`）、`SiegeInflictDamageIntervene`（`:4928`）、`DamageInterveneFromTraitReligion`（`:4945`）、`SiegeDamageInterveneIfSameReligion`（`:4976`）、`OutsideFriendlyLandsDamageIntervene`（`:4992`）——每一处贡献一律使用「其归属单位」的 scale（攻方贡献用 attacker scale，守方贡献用 defender scale）。`UnitDamageChangeInterveneNoCondition` 的 `pAttackerUnit→piDefenseInflictDamage` 映射为**改动前既有映射**，本次仅补 scale 参数，方向未变。
- 覆盖面核对：全仓 grep 确认所有固定伤害 getter（`GetAttackInflictDamageChange`、`GetFixReducePerPromotionTotal`、`GetSiege*`、`GetOutsideFriendlyLands*`、`GetOriginalCapital*`、`GetWoundedFixedDamage` 等）在 `CvUnitCombat.cpp` 之外**无其他战斗消费点**，无遗漏。

### B.2 `CvUnit.cpp` 的 `GetGenericMaxStrengthModifier`：河内块 × 姆班扎块

**结论：两块共存无冲突、无互相覆盖、无重复应用；作用对象区分正确。**

- 河内块（`CvUnit.cpp:15583-15605`）：位于 `if(pBattlePlot != NULL)`（`:15520`）作用域内，按**战斗地块归属方**对**本方单位**施加「敌军战斗力惩罚」（`iModifier += iHanoiPenalty`，负值），封顶 −50%。
- 姆班扎块（`CvUnit.cpp:15741-15771`）：位于函数末尾、`pBattlePlot` 守卫**之外**，按**敌方队伍科技差**对**本方单位**施加「己方战斗力加成」（`iModifier += iDiff * iPerTech`，正值）。
- 二者作用对象（减益 vs 增益）、判据（地块归属 vs 队伍科技）、作用域（守卫内 vs 函数尾）均不同，均为纯加法累加，**互不覆盖、互不重复**。极端情形（我方为姆班扎盟友、与河内盟友交战于河内领土）下两块同时命中同一 `iModifier`，属两种效果真实叠加，数值正确。
- 对象区分：河内块以 `eHanoiPlotOwner != getOwner()` 排除自身（`:15591`），故河内盟友在本国领土防御时**不被**自罚；姆班扎块以 `eEnemy != getOwner()`（`:15761`）排除自身，单向加成。
- 空安全：两块均先判 `pHanoiUA/pCSUA != NULL`；姆班扎块以 `GET_PLAYER(eEnemy).isAlive()` 三重守卫。

### B.3 `CvUnitMovement.cpp` ZOC 重写（贝尔格莱德）

**结论：不影响其他城邦与既有机制。**

- `AnyPlayerHasZOCRangeBonus()`（`:320-357`）只在有玩家持有 `ZOCRangeBonus > 0` 时把扫描窗扩为 5×5；`ZOCRangeBonus` 全库**仅贝尔格莱德**盟友行配置（`CSUA.xml:464`），其他城邦不触发。
- 逐源半径 `iSrcRange` 读**每个源单位持有者**的 CSUA（`:487-497`），非盟友单位恒为 1；城市分支以 `iFromDist == 1` 严格限定，城市恒为半径 1。
- 半径=1 回归等价性：3×3 盒 + `plotDistance ∈ (0,1]` 过滤，经 `plotDistance`（`CvGameCoreUtils.h:137-158`，含 `dxWrap`/`dyWrap`）在存储坐标下枚举出的邻居集合与 `plotDirection` 的 6 方向一致；`IsSlowedByZOC` 仅此一处实现，被 `CvAStar.cpp:1004/1607`、`CvUnitMovement.cpp:186` 复用，无第二套 ZOC 逻辑。
- 距离=2 覆盖性：5×5 盒经 `plotDistance ≤ 2` 过滤可覆盖全部六边形距离 2 的格子（2 步方向的存储偏移恒在 ±2 内）。

### B.4 `CvPlayer.cpp` 的 `GetCSUAYieldPercentModifier` / `RefreshCSAllUAEffects`

**结论：河内（文化）与姆班扎（组建速度）落点互不干扰。**

- 河内文化块（`:18463-18472`）：在 `GetCSUAYieldPercentModifier` 末尾、`return iMod/100` 之前，以**基点**累加 `GetNumWarPeacesCompleted() * iPerPeace * 100`，仅 `YIELD_CULTURE` 且 `iPerPeace != 0`（仅盟友档）生效。函数起始 `if (!m_pCityStateUA) return 0;`（`:18264`）保证空安全。
- 姆班扎**不**使用 `GetCSUAYieldPercentModifier`：组建速度走 `CvPlayer::getProductionModifier`（`:10011-10029`，平百分数、无基点换算，与消费方 `getProductionModifier` 口径一致），人力走 `getNumResourceTotal`（`:24668-24680`）。三者物理隔离，无双重应用（全仓 grep 确认 `GetUnitProductionModifierPerCity`/`GetManpowerPerCity`/`GetCombatBonusPerTechDifference` 各仅一处消费点，且 `GetCSUAYieldPercentModifier` 未引用它们）。
- 贝尔格莱德城防刷新收窄（`:20222-20225`）不影响其他城邦（见 2.1 安全性复核）。

### B.5 `CvTreasury.cpp`（布达佩斯维护费）、`CvTeam.cpp`/`CvDiplomacyAI.cpp`（河内计数器）

**结论：不影响既有逻辑。**

- 布达佩斯维护费（`CvTreasury.cpp:647-662`）：`dFinalCost -= perCav * GetNumUnitsWithUnitCombat(UNITCOMBAT_MOUNTED)` 位于所有既有修正之后、`return std::max(0, int(dFinalCost))`（`:664`）之前，实现「至多降低为 0」。`GetNumUnitsWithUnitCombat`（`CvPlayer.cpp:5037-5054`）以 `firstUnit/nextUnit` 遍历存活单位，口径正确。该函数是维护费唯一扣减点，无其他 CSUA 在同一函数内改动。
- 河内和谈计数（`CvTeam.cpp:1720-1736`）：位于 `DoMakePeace` 的 `if(isAtWar(eTeam))` 块内；公共入口 `makePeace` 每事件仅调用一次 `DoMakePeace`（`:1650-1660`），且块首 `setAtWar(false)` 使重复调用短路，**不重复计数**；递归调用（`:1818-1820`）恒为城邦侧、被 `!isMinorCiv()` 排除。
- 河内被宣战计数（`CvDiplomacyAI.cpp:5996-6003`）：`DoSomeoneDeclaredWarOnMe` 仅由 `CvTeam.cpp:1358` 对**防守方队伍**玩家各调用一次；侵略方不计；barbarian 宣战被 `if(!isBarbarian())`（`:1352`）排除。
- 序列化合规：两成员 `MOD_SERIALIZE_READ/WRITE` 门控 164，与 `MOD_DLL_VERSION_NUMBER`（`CustomMods.h:36`）一致，声明/`uninit`/读/写四处宏守卫（`MOD_ROG_CORE` + `MOD_SP_UNIQUE_CITYSTATE`）一致。

---

## 四、二审新发现的问题

### 应修正

**无。** 逐文件回读被改函数、逐条核对设计与三方数据后，**未发现功能性缺陷、数值错误、挂钩位置错误、方向错误或数据/文本不一致**。二审特别针对跨城邦热点函数（`CvUnitCombat.cpp` 固定伤害链、`CvUnit.cpp` 通用强度修正、`CvUnitMovement.cpp` ZOC、`CvPlayer.cpp` 产出/刷新、`CvTreasury.cpp`/`CvTeam.cpp`/`CvDiplomacyAI.cpp`）做了共存性检查，均通过。

### 待拍板

**二审未新增待拍板项**，沿用一审 9 项（见第五节）。

### 提示（非缺陷，二审新发现 3 项）

#### N-1　河内块仍保留外部文档决策编号 `D9`

- 位置：`CvUnit.cpp:15587` — `// D9: the penalty is capped at -50% (the only implementation-chosen cap for this UA).`
- 说明：姆班扎一审 P-1 要求「注释去决策编号」，姆班扎自身的 `D4/D5/D7/D8` 与 `design rule 15` 已彻底清除（grep 零命中），但**同一批次的河内块**仍留 `D9` 这一外部讨论文档编号，属同类残留、且与本批清理口径不一致。功能无影响。
- 建议（可选）：改为自包含描述，如 `// The penalty is capped at -50% to avoid a zero-output enemy; the cap is mirrored in the help text.`

#### N-2　布达佩斯 `TXT_KEY_CSUA_BUDAPEST_HELP` 多出一行城邦名标题

- 位置：`TextInfos_en_US.xml:20428-20430`（`[ICON_CITY_STATE]Budapest`）、`zh_CN:18897-18899`（`[ICON_CITY_STATE]布达佩斯`）、`zh_Hant_HK:18703-18705`（`[ICON_CITY_STATE]布達佩斯`）。
- 说明：该字段被 `SelectCityStates.lua:128-131` 用作开局城邦选择界面的勾选提示。经全库比对，**其余全部 CSUA 的 `_HELP`（含魁北克、蒙巴萨、摩加迪沙及本批另三城邦）均以「盟友效果：」直接开头**，唯布达佩斯多一行城邦名标题。功能无影响，仅界面风格不一致（且城邦名在界面他处已显示）。
- 建议（可选）：删除该三语标题行以对齐其余城邦；若确实希望显示城邦名，则应给全部城邦统一补上（本次不建议扩大改动面）。

#### N-3　河内两个新序列化成员与上一 164 构建存档不互通（项目级约定风险）

- 位置：`CvPlayer.cpp:30412-30413`（Read）、`:31295-31296`（Write）、`CvPlayer.h:3284-3285`（声明）。
- 说明：本次仅河内新增 2 个序列化成员（`m_iNumWarPeacesCompleted` / `m_iNumTimesDeclaredWarOn`），门控版本 164 = 当前 `MOD_DLL_VERSION_NUMBER`。按 [[dev-build-version-control]]「内测期不升版本号」的既定约定，这**符合规范**；但需知悉：`MOD_SERIALIZE_READ(164, ...)` 的判据是 `uiDllSaveVersion >= 164`，因此**由上一个 164 构建（尚未含这两个成员）写入的存档，其版本号同样是 164**，用新 DLL 载入会多读 2 个 int 而**流错位**。
- 影响面：仅影响「跨内测构建」的存档（正式发布升版本号后即恢复兼容）。属既定约定下的已知取舍，非本次代码缺陷。
- 建议：实机验证四个城邦时**使用新开存档**；发布前按流程升级 `MOD_DLL_VERSION_NUMBER`。

---

## 五、用户复审清单（汇总全部待拍板项）

| # | 城邦 | 问题 | 一审判断 | 二审独立判断 | 影响面 |
| --- | --- | --- | --- | --- | --- |
| 1 | 布达佩斯 | Q-1「轻重骑兵」映射为 `UNITCOMBAT_MOUNTED`（排除装甲/游猎/侦察） | 建议维持 | **建议保留**：`MOUNTED` 恰为轻/重骑兵并集，与 SP 既有 `TRAIT_TERROR` 文本口径一致 | 维护费扣减口径 |
| 2 | 布达佩斯 | Q-2 渡河免疫附带「AI 寻路不再规避渡河」 | 需澄清 | **建议接受**：正向附带效果，战斗惩罚已正确移除；移动力成本未豁免（`CvUnitMovement.cpp:21` 用 `isRiverCrossing` 直判） | 战斗 + AI 寻路 |
| 3 | 河内 | Q-1 判定基准为「战斗地块归属」而非「单位位置」 | 建议确认 (b) | **建议保留 (b)**：更贴合「守土」手感，与效果③战场语义自洽；注释已写清 | 固定伤害失效判定 |
| 4 | 河内 | Q-2 效果③ −50% 上限（设计稿未提） | 建议确认；若保留同步帮助文本 | **建议保留**：−100% 会导致敌军零输出；帮助文本三语已同步（`（最多-50%）`/`(up to 50%)`）。**建议同时把上限补写进设计稿** | 长局战斗力平衡 |
| 5 | 河内 | Q-3「战斗力」不含远程攻击强度 | 建议确认 | **建议保留现状**：Civ5 中战斗力与远程战斗力分列，通用强度修正历来不含远程，帮助文本措辞一致 | 远程/空军入境效果 |
| 6 | 河内 | Q-4 计数器终身累计；和谈计数排除城邦和谈；被宣战计数含城邦宣战 | 建议确认起点与口径 | **建议保留**：符合「累计过」字面；但需知悉新结盟当回合会一次性吃到历史累计 | 文化加成 / 敌军惩罚强度 |
| 7 | 姆班扎刚果 | Q-1 效果③战斗力加成不设上限 | 建议确认 | **建议保留无上限**：帮助文本未提上限，与规则 15「加成类不设硬上限」一致；但 30 科技差 = +300% 需关注 | 科技落后方反打强度 |
| 8 | 姆班扎刚果 | Q-2 效果③仅近战攻防、不含远程攻击 | 建议确认 | **建议保留现状**：帮助文本写「Combat Strength」，措辞与实现一致 | 远程单位输出 |
| 9 | 姆班扎刚果 | Q-3 效果② 4 人力会被 AI 难度修正放大 | 建议确认 | **建议保留现状**：与既有政策/建筑授予人力口径一致（同在 `GetStrategicResourceMod` 乘法前），非 bug | AI 盟友人力收益 |

未采纳的提示项汇总（保留不改，均为可选优化）：贝尔格莱德 P-2（static 缓存不重置）、河内 P-3（新成员未进构造函数初始化列表）、姆班扎 P-2（热路径字符串查找）、姆班扎 P-3（效果②③无 tooltip 归因）。

---

## 六、结论与建议

### 结论

1. 四个城邦的**盟友 3 条 + 朋友 1 条**效果**逐条对得上设计稿**，数值（30/15、4/2、100/50、10/4）、档位、方向全部正确；盟友/朋友互斥（`RefreshCSAllUAEffects` 以 `IsAllies` 优先、`else if IsFriends`），朋友档未误得盟友专属字段。
2. **一审「应修正」为 0**；一审「建议类提示」中可落地的部分**已全部修复**（贝尔格莱德 P-1/P-3、布达佩斯 P-1/P-2、河内 Q-1 注释/Q-2 帮助文本/P-1、姆班扎 P-1），证据见第二节。
3. **跨城邦交互无新缺陷**：河内对固定伤害的缩放**正确且有意**地覆盖布达佩斯 +4，无重复缩放、攻/守归属正确；河内与姆班扎在 `GetGenericMaxStrengthModifier` 内共存无冲突；ZOC 重写、维护费、计数器均不干扰既有机制。
4. 工程规范达标：注释全英文、行尾保持（每文件纯 CRLF 或纯 LF，无混行）、SP 三语文本齐备且追加末尾、XML well-formed、序列化门控 164、无重复主键；DLL（`BuildOutput/VS2022_ReleaseWin32/` 与 `(1) CIV5MPDLL/DLL/`，04:39）含全部 7 个新列名串。
5. **二审新发现：应修正 0 项，待拍板 0 项，提示 3 项（N-1 D9 残留、N-2 布达佩斯标题行、N-3 同版本存档不互通风险）**，均非缺陷。

### 是否建议构建实机验证

**建议构建实机验证。** 静态审查已覆盖全部逻辑与跨城邦交互，但以下依赖运行期状态的行为需实机确认：

| 优先级 | 场景 | 重点观察 |
| --- | --- | --- |
| 1 | **河内 × 布达佩斯交叉**：玩家同时结盟两城邦，攻击第三方的受伤单位 | 布达佩斯 +4 是否全额（第三方非河内盟友）；若第三方为河内盟友，其领土内我方 +4 是否归零 |
| 2 | **河内效果①**：敌方单位从境外进攻盟友境内目标 | 按「战斗地块归属」判定，敌方固定伤害是否失效（含远程？确认远程攻击强度不受效果③影响） |
| 3 | **河内效果③**：盟友累计被宣战 5 次以上 | 境内敌军战斗力是否封顶 −50%，帮助文本「最多-50%」是否与实际一致 |
| 4 | **贝尔格莱德**：结盟后建造单位（30 XP）vs 购买（无效）；驻军城防 ×3；ZOC 半径 2 生效；**关系变化当回合**立即生效（验证 `RefreshCSAllUAEffects → 条件 UpdateCityStrength` 路径） | 断盟当回合城防回弹 |
| 5 | **布达佩斯**：每骑兵 −4 维护费、至多降为 0；对受伤单位攻防各 +4（打城市不加）；陆军渡河无战斗惩罚但**移动力仍消耗** | 坦克/战车/侦察兵不计入骑兵数 |
| 6 | **姆班扎刚果**：军事单位组建 +10%/城（非军事单位无）、人力 +4/城、对科技更多文明 +10%/科技差（单向、无上限）；远程攻击强度无加成 | AI 盟友人力是否被难度修正放大 |
| 7 | **四城邦朋友档**：仅得缩水效果，无盟友专属效果；断交当回合全部消失 | 文本回归（外交界面 / 开局选择界面 / 百科） |

实机验证请**使用新开存档**（见 N-3）。

### 建议处理顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | 用户拍板第五节 9 项待拍板（其中 #4 建议同时把 −50% 上限补进设计稿） | 无 |
| 2 | （可选）N-1 去 `D9`、N-2 删布达佩斯标题行 | 极小 |
| 3 | 构建 SP V11 + MPDLL 模组，按上表实机验证（新档） | 小 |
| 4 | （可选）一审保留的 4 项提示（static 缓存、构造函数列表、热路径字符串、tooltip 归因） | 极小 |
| 5 | 发布前升级 `MOD_DLL_VERSION_NUMBER` 并刷新 API 说明库 | 小 |

---

## 附：审查方法

- 逐仓库比对 `git log` / `git diff --stat` / `git diff --numstat`（`cd54104..HEAD`、`3df2b1b..HEAD`），确认工作区干净、改动规模与任务描述一致。
- 逐文件回读被改函数确认语义与挂钩：`CvUnitCombat::InterveneInflictDamage` 全分发链（`CvUnitCombat.cpp:4708/4903/5018-5045`）与 `InflictDamageContext`（`CvUnitCombat.h:33-40`）；`CvUnit::GetGenericMaxStrengthModifier`（`CvUnit.cpp:15414-15774`）及其两个调用方；`CvUnit::isRiverCrossingNoPenalty`（`CvUnit.cpp:23095-23114`）及其消费点（`CvUnit.cpp:16063`、`CvAStar.cpp:1200/1894`、`CvUnitMovement.cpp:21`）；`CvUnitMovement::IsSlowedByZOC`（`:361-519`）与 `AnyPlayerHasZOCRangeBonus`（`:320-357`）；`CvPlayer::getProductionModifier`（`:10011-10029`）、`GetCSUAYieldPercentModifier`（`:18262-18473`）、`RefreshCSAllUAEffects`（`:20120-20226`）、`getNumResourceTotal`（`:24668-24680`）；`CvTreasury::CalculateUnitCost`（`:584-665`）；`CvTeam::DoMakePeace`（`:1650-1736`）；`CvDiplomacyAI::DoSomeoneDeclaredWarOnMe`（`:5996-6003`）；`CvCity::updateStrengthValue`（`:17012-17029`）。
- 交叉核对 C++ 实现、SP XML 数据（`CSUA.xml`）、三语文本、设计稿（`军事型.txt:10-33`）四者数值与语义；以 `SelectCityStates.lua`/`CivilopediaScreen.lua`/`CityStateStatusHelper.lua` 确认 `_HELP` 与 `_EFFECT_HELP` 的实际消费方。
- 以 Python `xml.dom.minidom` 验证 4 个 SP 文件 well-formed；以脚本统计 12 个 Tag × 3 语言的定义数（各为 1）。
- 以 `tr -dc '\r' | wc -c` 逐文件核对行尾（每文件 CR 与 LF 计数相等或 CR=0，无混行）。
- 以 `grep` 全盘检索 `D4/D5/D7/D8/design rule`（仅 `D9` 命中，属河内块）、固定伤害 getter 的其他消费点（无遗漏）、`GetGarrisonCityDefenseModifier`/`UpdateCityStrength` 消费点（收窄安全）、`GetUnitProductionModifierPerCity`/`GetManpowerPerCity`/`GetCombatBonusPerTechDifference` 消费点（各一处）。
- 以 `grep -a` 在 DLL 二进制中检索 7 个新列名串，确认产物包含全部改动；核对 DLL 时间戳（04:39）晚于全部源文件。
- 以基游戏安装目录（`D:\steam\steamapps\common\Sid Meier's Civilization V`）核实 4 个 `TXT_KEY_CITYSTATE_*` 与 `MINOR_CIV_*` 的真实存在与后缀。
