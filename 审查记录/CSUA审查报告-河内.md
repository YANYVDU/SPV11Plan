# CSUA 审查报告：河内（Hanoi）

> **2026-10-01 后续变更**：`EnemyFixedDamageModifierInBorders` 已由「禁用百分比正数（100/50）」改为负数语义（-100/-50），消费端 `GetCSUAFixedDamageScale` 相应改为 `scale = 100 + value`；效果③的境内战力修正抽为 `CvUnit::GetCSUACombatModifierInBorders`，并接入 `EnemyUnitPanel` 的「战争领域修正」行。本报告下述数值描述（如 `100-100=0`、`100-50=50`）为变更前的旧语义。

- 审查日期：2026-10-01
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 7 文件 **+193 / −34**；SP 5 文件 **+95 / −0**
- 结论摘要：四条效果（盟友 3 条 + 朋友 1 条）**逐条对得上设计稿**，数值、盟友/朋友档位、方向（失效 vs 50% 生效）均正确，**未发现必须修复的功能性缺陷（应修正 0 项）**。实现方式为：复用既有 `CityStateUAEffects` 三个标量列（`EnemyFixedDamageModifierInBorders` / `CulturePerWarPeace` / `EnemyCombatModifierInBordersPerBeenDoW`）+ 在 `CvUnitCombat` 固定伤害链路上做统一缩放 + 两个 `CvPlayer` 序列化计数器。有 **4 项待拍板的设计口径**（战斗地块语义、-50% 上限、远程攻击不生效、计数为终身累计）与 **3 项非缺陷提示**。

---

## 一、改动清单

### MPDLL

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `CvGameCoreDLL_Expansion2/CvUnitCombat.h` | +8 / −0 | `InflictDamageContext` 新增 `iAttackerFixedDamageScale` / `iDefenderFixedDamageScale`（默认 100），`:34-40` |
| `CvGameCoreDLL_Expansion2/CvUnitCombat.cpp` | +85 / −34 | 新增静态门 `GetCSUAFixedDamageScale`（`:4703-4717`）；在 `InterveneInflictDamage` 顶部预算攻/守双方缩放（`:5013-5022`）；对全部固定伤害接触点逐一乘 `iScale`（详见下） |
| `CvGameCoreDLL_Expansion2/CvPlayer.h` | +10 / −0 | 新增 getter/setter 声明（`:1190-1196`）与序列化成员（`:3284-3285`） |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +40 / −0 | `uninit()` 归零（`:1280-1281`）；`GetCSUAYieldPercentModifier` 文化落点（`:18445-18454`）；`Read`/`Write` 门控 164（`:30383-30384` / `:31263-31264`）；计数器实现（`:32844-32869`） |
| `CvGameCoreDLL_Expansion2/CvTeam.cpp` | +18 / −0 | `DoMakePeace` 内对和谈双方全部主要文明玩家 `ChangeNumWarPeacesCompleted(1)`（`:1720-1735`） |
| `CvGameCoreDLL_Expansion2/CvDiplomacyAI.cpp` | +8 / −0 | `DoSomeoneDeclaredWarOnMe` 内 `ChangeNumTimesDeclaredWarOn(1)`（`:5998-6004`） |
| `CvGameCoreDLL_Expansion2/CvUnit.cpp` | +24 / −0 | `GetGenericMaxStrengthModifier` 内按战斗地块归属施加境内敌军战斗力惩罚（`:15583-15605`） |

> **既有基础设施复用说明**：三个 DB 列（`(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql:88-91`，注释 `-- Hanoi: ...`）、`CvCityStateUAClasses` 的解析/聚合/getter（`CvCityStateUAClasses.cpp:287-289 / 438-440 / 1815-1817 / 2264-2266`）**并非本次新增**，已在先前提交落地；本次为纯逻辑实现。

### SP

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 / −0 | 城邦绑定 `MINOR_CIV_HANOI` → `CSUA_HANOI`（`:64`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +19 / −0 | 2 个效果（`:485-496`）+ 1 个 UA 条目（`:1788-1794`） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +25 / −0 | 3 个文本 Tag（`:20454-20478`） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +25 / −0 | 3 个文本 Tag（`:18923-18947`） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +25 / −0 | 3 个文本 Tag（`:18729-18753`） |

### 效果设计对照表

| 对象 | 设计文本（`1.城邦UA/军事型.txt:23-27`） | 实现 | 判定 |
| --- | --- | --- | --- |
| 盟友① | 敌人在盟友境内时固定免伤和固定造成伤害失效 | `EnemyFixedDamageModifierInBorders = 100` → `GetCSUAFixedDamageScale` 返回 `100-100=0`，对战场地块归属方为盟友、且与之交战的单位，把其全部固定伤害/固定免伤贡献乘以 0 | **符合设计** |
| 盟友② | 盟友每完成过一次战争和谈，全国文化产出+5% | `CulturePerWarPeace = 5`；`DoMakePeace` 每次和谈双方主要文明玩家 `+1`；`GetCSUAYieldPercentModifier(YIELD_CULTURE)` 累加 `计数 × 5 × 100` 基点 → `/100` 得 `+5%×计数`，作用于每城 `getBaseYieldRateModifier` | **符合设计** |
| 盟友③ | 盟友每被宣战过一次，全国境内敌军降低10%战斗力 | `EnemyCombatModifierInBordersPerBeenDoW = -10`；`DoSomeoneDeclaredWarOnMe` 每次被宣战 `+1`；`GetGenericMaxStrengthModifier` 对「战斗地块属于持有者、且与之交战的敌方单位」`iModifier += -10×计数` | **部分符合**（见 Q-2、Q-3） |
| 朋友① | 敌人在朋友境内时固定免伤和固定造成伤害只能生效50% | `EFFECT_CSUA_HANOI_FRIEND` 仅设 `EnemyFixedDamageModifierInBorders = 50` → scale `= 50`，各贡献 `×50/100` | **符合设计** |

设计稿来源：`d:\Git\CIV5\dyy\SP V11\1.城邦UA\军事型.txt:23-27`。绑定 `MINOR_CIV_HANOI`、`CSUA_HANOI` 与 `CityStateUAs` 条目一致，无命名错位。

---

## 二、问题清单

### 应修正

**无。** 逐条核对未发现明确缺陷。四条效果的设计语义、数值、档位与方向均正确落地；序列化、注释语言、行尾、三语文本、图标、空指针/除零/越界均无问题（详见第三节「已验证无误项」）。

### 待拍板（需确认，非缺陷）

#### Q-1　效果①的判定基准是「战斗地块归属」而非「敌方单位实际位置」

- 位置：`CvUnitCombat.cpp:4703-4717`（`GetCSUAFixedDamageScale`）、`:5013-5022`（取 `ctx->pCombatInfo->getPlot()`）。
- 现象：门函数的判据是 `pBattlePlot->getOwner()`。对近战而言，战斗地块是**防守方所在格**；对远程/空袭而言是**目标格**。因此当敌方单位**从境外进攻境内目标**时（敌方本身不在盟友境内），其固定伤害同样被失效；反之，友方单位在盟友境内进攻境外敌人时不受影响。
- 分析：字面「敌人在盟友境内时」可作两种解读——(a) 敌方单位所在位置在境内；(b) 战斗发生在境内（战场地块归属）。实现取 (b)。取 (b) 更贴近「守土」的手感（敌方跨入边境发起的一切战斗其固定伤害皆无效），也与「境内敌军降战斗力」的战场语义一致；取 (a) 则需改为按 `pUnit->plot()` 判定。
- 建议：确认采用战场地块口径 (b)。若采纳，建议在 `GetCSUAFixedDamageScale` 注释中把「battle plot」与「unit location」的区别写清楚，避免后续维护者误改。

#### Q-2　效果③的 −50% 上限为实现自选，设计稿未提及

- 位置：`CvUnit.cpp:15600` `if (iHanoiPenalty < -50) iHanoiPenalty = -50;`（注释自称 `D9: the only implementation-chosen cap`）。
- 现象：设计「每被宣战过一次…降低10%战斗力」为线性累加、无上限；实现把累计惩罚封顶在 −50%（即第 5 次被宣战后不再增加）。
- 分析：长局中主要文明被宣战 5 次以上很常见，封顶会显著改变后期表现。加封顶是合理的安全阀（避免 −100% 造成敌方零输出），但属对设计数值的实质削减。
- 建议：确认是否保留 −50% 上限。若保留，建议同时同步进设计稿/帮助文本，避免口径不一致。

#### Q-3　效果③的「战斗力」不作用于远程攻击强度

- 位置：`CvUnit.cpp:15583-15605`（位于 `GetGenericMaxStrengthModifier` 内）。
- 证据：`GetGenericMaxStrengthModifier` 仅被 `GetMaxAttackStrength`（`:15763`，近战攻击强度）与 `GetMaxDefenseStrength`（`:16148`，防御强度）调用；`GetMaxRangedCombatStrength`（`:16524`）与空袭伤害路径**均不经过**该函数。故境内敌军的**近战攻击**与**防御**受罚，但**远程攻击强度不受影响**（远程单位在境内轰炸仍满额）。
- 分析：Civ5 中「战斗力（Combat Strength）」与「远程战斗力（Ranged Combat Strength）」是两项独立数值，通用强度修正历来不作用于远程攻击，故实现与引擎惯例自洽；但若设计意图是「削弱一切入境敌军」，则远程/空军攻击的豁免是缺口。
- 建议：确认「战斗力」是否应含远程攻击。若要覆盖远程，需另在 `GetMaxRangedCombatStrength`（及空袭路径）挂同一修正。

#### Q-4　两个计数器为「终身累计」，且和谈计数排除城邦和谈、被宣战计数包含城邦宣战

- 位置：`CvTeam.cpp:1720-1735`、`CvDiplomacyAI.cpp:5998-6004`。
- 现象：
  - 计数为**终身累计**（serialized、永不衰减），包含**结盟之前**发生的和谈/被宣战；即新结盟当回合即可能一次性吃到历史累计的全部加成/惩罚。
  - 和谈计数**要求双方均为主要文明**（`:1727` `!isMinorCiv() && !GET_TEAM(eTeam).isMinorCiv()`），故「主要文明↔城邦」的和谈不计入。
  - 被宣战计数**不区分**宣战者身份（注释明示「city-states included」），且防御条约链中由第三方加入导致的宣战也会给**侵略方**记一次（`CvTeam.cpp:1244-1246` 递归 `DoDeclareWar` → `:1358` 对 `eTeam` 侧玩家调用 `DoSomeoneDeclaredWarOnMe`）。
- 分析：均非崩溃/坏档类问题，属设计口径选择。终身累计符合「累计过」的字面，但与「结盟期间累计」的直觉不同。
- 建议：确认「累计」的起点（终身 vs 结盟期间）与「战争和谈」是否应含城邦和谈。

### 提示（非缺陷）

#### P-1　城市固定伤害未纳入缩放（有意为之，建议补注释）

- 位置：`CvUnitCombat.cpp:4753-4759`（`CityDamageChangeInterveneNoCondition`）、`:4786-4790`（`CityDamageChangeIntervene` 未传 scale）。
- 说明：城市（`pAttackerCity` / `pDefenderCity`）的强制/变更伤害不受 Hanoi 缩放影响。这是**正确**的——城市本身即「领土」，不存在「城在盟友境内却是敌军」的情形；当敌方单位攻打盟友城市时，被缩放的只是**敌方单位**（`pAttackerUnit`）的固定伤害，盟友城市的反击伤害不受影响。逻辑自洽，但代码中未加说明，建议补一行英文注释点明「cities are the territory itself, never scaled」。

#### P-2　热路径新增判定（性能影响可忽略，记录备查）

- 位置：`CvUnit.cpp:15588-15604`。
- 说明：`GetGenericMaxStrengthModifier` 在 AI 规划与 UI 显示中被高频调用，本块每次都要 `GET_PLAYER` + `GetPlayerCityStateUA()` + `atWar()`。由于非 Hanoi 局中 `GetEnemyCombatModifierInBordersPerBeenDoW()` 恒为 0（短路返回 100），且 `pBattlePlot == NULL` / 同属一方亦提前退出，实测开销可忽略，无需改动；仅记录该热路径的新增分支。

#### P-3　新增成员未进构造函数初始化列表，依赖 `uninit()`

- 位置：`CvPlayer.h:3284-3285`（声明）、`CvPlayer.cpp:1280-1281`（`uninit()` 归零）、`:417-419`（构造函数列表仅含更早的三个成员）。
- 说明：`m_iNumWarPeacesCompleted` / `m_iNumTimesDeclaredWarOn` 仅由 `uninit()` 归零（`reset()` 会调用 `uninit()`，故实际安全），与既有 `m_iCityStateUASpyKillProgress` 的处理方式一致。为增强健壮性与一致性，可考虑补入构造函数初始化列表，非必需。

---

## 三、已验证无误项

1. **效果①覆盖全部固定伤害接触点，无遗漏、无重复缩放**。逐点核对（均在 `CvUnitCombat.cpp`）：`UnitDamageChangeInterveneNoCondition`（强制/变更，`:4733-4750`）、`UnitAttackInflictDamageIntervene`（`:4792-4811`）、`UnitDefenseInflictDamageIntervene`（`:4813-4825`）、`FixReduceDamageIntervene`（`:4827-4862`）、`FixAddDamageIntervene`（`:4864-4890`）、`BudapestWoundedFixedDamageIntervene`（`:4895-4918`）、`SiegeInflictDamageIntervene`（`:4920-4934`）、`DamageInterveneFromTraitReligion`（`:4937-4965`）、`SiegeDamageInterveneIfSameReligion`（`:4968-4980`）、`OutsideFriendlyLandsDamageIntervene`（`:4984-5008`）。以全仓 grep 验证：所有固定伤害 getter（`GetAttackInflictDamageChange`、`GetFixReducePerPromotionTotal`、`GetPerKill*`、`GetSiege*`、`GetOutsideFriendlyLands*`、`GetOriginalCapital*`、`getForcedDamageValue`、`GetWoundedFixedDamage` 等）**除 `CvUnitCombat.cpp` 的上述函数外无其他战斗消费点**，故无遗漏。
2. **`/100` 与 `/10000` 无混用错误**。原式含 `/100`（百分比型：`*MaxHPPercent`、`*PerPromotionTotal`、`*SiegeDamagePercentIfSameReligion`）者统一改为 `/10000`；原式为平值者统一 `/100`。`iScale == 100` 时 `x*100/100` 与原值严格相等，非 Hanoi 局零影响。
3. **攻/守归属正确、无交叉串味**。每个贡献一律使用**其归属单位**的 scale：攻击方贡献用 `iAttackerFixedDamageScale`，防守方贡献用 `iDefenderFixedDamageScale`。`FixReduceDamageIntervene` 中「攻方减伤→`piDefenseInflictDamage`（攻方承伤）」与「守方减伤→`piAttackInflictDamage`（守方承伤）」的映射与原代码一致，scale 归属亦正确。
4. **效果①朋友档「只生效 50%」正确**。`scale = 100 - 50 = 50`，各贡献减半；盟友档 `100-100=0` 完全失效。两者语义与设计「失效 / 只能生效50%」精确对应，且朋友档不是「完全失效」也非「完全生效」。
5. **`GetCSUAFixedDamageScale` 空安全**。入口对 `pUnit == nullptr || pBattlePlot == nullptr` 返回 100（`:4705`）；`pCombatInfo` 以三元判空（`:5018`）。全部 6 处 `InterveneInflictDamage` 调用点（`:145 / 258 / 804 / 879 / 996 / 1862 / 1959`）均已设置 `pCombatInfo`，`InflictDamageContext` 逐次栈上构造、默认 scale 100，无脏值。
6. **效果②数值换算正确**。`CvPlayer.cpp:18453` `iMod += GetNumWarPeacesCompleted() * iPerPeace * 100;`（`iPerPeace = 5`），末尾 `return iMod / 100;` → 每次和谈 +5%，符合「普通百分比列须 ×100」约定；仅在 `YIELD_CULTURE` 且 `iPerPeace != 0`（仅盟友档）时生效。
7. **效果③数值方向正确**。DB 存 `-10`，`CvUnit.cpp:15598-15601` 直接以百分比累加进 `iModifier`（不经基点换算，正确），1 次被宣战即 −10%。
8. **盟友/朋友互斥且档位正确**。`RefreshCSAllUAEffects`（`CvPlayer.cpp:20117-20124`）`IsAllies` 优先、`else if IsFriends` 择一 `ApplyEffect`；盟友档三效果全生效，朋友档仅效果①的 50%，无叠加、无档位颠倒。
9. **效果②只在盟友档生效**：`EFFECT_CSUA_HANOI_FRIEND` 未设 `CulturePerWarPeace`（默认 0）与 `EnemyCombatModifierInBordersPerBeenDoW`（默认 0），故朋友无文化加成、无战斗力惩罚。
10. **和谈计数器无重复计数**。`CvTeam::DoMakePeace` 单实现（`MOD_EVENTS_WAR_AND_PEACE` 只切换签名），公共 `makePeace` 每个和谈事件仅调用一次；递归调用（`:1818-1820`）恒为「己方城邦盟友 ↔ 城邦」且被 `!isMinorCiv()` 排除；计数位于 `if(isAtWar(eTeam))` 块内，仅战争→和平时触发。
11. **被宣战计数器归属正确**。`DoSomeoneDeclaredWarOnMe` 仅对**防守方**队伍玩家调用（`CvTeam.cpp:1356-1359`），侵略方不计；barbarian 宣战被 `if(!isBarbarian())` 排除。
12. **序列化合规**。两成员 `MOD_SERIALIZE_READ(164, ...)` / `MOD_SERIALIZE_WRITE(...)`，门控版本 164 = 当前 `MOD_DLL_VERSION_NUMBER`（`CustomMods.h:36`），符合「内测期不递增、新成员用 164」约定；读/写/`uninit()`/声明四处宏守卫（`MOD_ROG_CORE` + `MOD_SP_UNIQUE_CITYSTATE`）一致；旧档（<164）读默认 0，向后兼容。
13. **`m_pCityStateUA` 空守卫完备**。`GetCSUAYieldPercentModifier` 起始 `if (!m_pCityStateUA) return 0;`（`CvPlayer.cpp:18246`）；`GetCSUAFixedDamageScale` 与 `CvUnit.cpp` 惩罚块均判 `pUA != NULL`。
14. **注释全英文**。以脚本扫描 MPDLL 全部新增行，CJK 计数 **0**；SP 新增的 `.sql` / `.xml`（数据文件）无注释。符合 [[sp-english-comments-only]]。
15. **行尾格式保持**。逐文件比对 HEAD 与工作区：`CvPlayer.cpp` / `CvUnit.cpp` / `CvUnitCombat.cpp` 维持 LF，`CvPlayer.h` / `CvUnitCombat.h` / `CvTeam.cpp` / `CvDiplomacyAI.cpp` 维持 CRLF；SP 五文件维持 LF。`git diff --numstat` 均为小改动，无整篇重写。
16. **三语文本齐全、末尾插入、图标有效**。`TXT_KEY_CSUA_HANOI_HELP` / `TXT_KEY_EFFECT_CSUA_HANOI_ALLY_HELP` / `TXT_KEY_EFFECT_CSUA_HANOI_FRIEND_HELP` 在英/简/繁三文件均存在，数值与语义与设计稿一致，均追加于各文件 `</Language_*>` 之前（末尾），未打乱既有分组；使用 `[ICON_WAR]`（基座 `CIV5IconFontMapping.xml:248` 已定义，SP 内已用 72 处）、`[ICON_CULTURE]`、`[ICON_STRENGTH]`、`[ICON_BULLET]`。
17. **城邦名文本 Tag 正确**。`CSUA.xml:1790` `<Description>TXT_KEY_CITYSTATE_HANOI</Description>`——经比对基座 `Assets/DLC/Expansion2/Gameplay/XML/Civilizations/CIV5MinorCivilizations.xml:214-216`，Hanoi 的官方 tag **无** `_CITY` 后缀（与魁北克相反），此处正确、非魁北克式 D-1 缺陷。
18. **无重复主键**。`CSUA_HANOI` / `EFFECT_CSUA_HANOI_ALLY` / `EFFECT_CSUA_HANOI_FRIEND` / 三个文本 Tag 全 SP 各仅一处定义。
19. **无越界/除零**。缩放除数均为常量 100 / 10000；`ChangeNumWarPeacesCompleted` / `ChangeNumTimesDeclaredWarOn` 以 `max(0, ...)` 防负；计数器循环限 `MAX_MAJOR_CIVS`。
20. **未误改无关代码**。diff 全部集中于河内功能；`UnitDamageChangeInterveneNoCondition` 新增的第三参数仅本文件两处调用，无外部调用者，签名变更安全。
21. **构建产物包含本次改动**。`BuildOutput/VS2022_ReleaseWin32/CvGameCore_Expansion2.dll` 与 `(1) CIV5MPDLL/DLL/` 均为 2026-10-01 04:14:54，晚于全部源文件；对应 `.obj`（CvDiplomacyAI/CvTeam/CvUnitCombat/CvPlayer/CvUnit）均在各自源文件改动之后重建。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff` / `git diff --numstat` / `git status --short`，核对改动规模、行尾与提交状态。
- 交叉核对 C++ 实现、XML 数据、三语文本、设计稿四者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvUnitCombat::InterveneInflictDamage`（`:5010-5049`）及其全部固定伤害子函数；`CvUnit::GetGenericMaxStrengthModifier`（`:15414`）及两处调用点 `GetMaxAttackStrength`（`:15744`）/ `GetMaxDefenseStrength`（`:16131`）；确认 `GetMaxRangedCombatStrength`（`:16524`）不经该函数。
- 追踪计数递增点：`CvTeam::DoMakePeace`（`CvTeam.cpp:1717-1735`）与 `DoDeclareWar`→`DoSomeoneDeclaredWarOnMe` 调用链（`CvTeam.cpp:1356-1359`），验证递归与侵略方/防守方归属。
- 核对 `GetCSUAYieldPercentModifier`（`CvPlayer.cpp:18244-18456`）的基点约定与落点，及其唯一消费点 `CvCity::getBaseYieldRateModifier`（`CvCity.cpp:13621-13629`）。
- 以脚本扫描新增行 CJK 字符；以 Python 逐文件比对 HEAD 与工作区的行尾类型。
- 以全盘 grep 检索基座 `CIV5MinorCivilizations.xml` 确认 Hanoi 的官方文本 tag；检索 `CIV5IconFontMapping.xml` 确认 `ICON_WAR` 有效。
- 核对构建产物时间戳与 `.obj` 重建时间，确认 DLL 晚于全部源文件。

---

## 五、结论

河内（Hanoi）CSUA 的四条效果（盟友 3 条 + 朋友 1 条）**逐条对得上设计稿，数值与档位均正确，未发现必须修复的功能性缺陷（应修正 0 项）**。实现质量良好：固定伤害缩放对十余个接触点逐一覆盖且攻/守归属无串味、`/100` 与 `/10000` 换算无误、盟友/朋友档位互斥、序列化门控合规、注释/行尾/三语文本/图标均达标、无空指针/越界/除零、DLL 已含本次改动。

需要用户拍板的是 4 项**设计口径**（非缺陷）：效果①以「战场地块归属」而非「敌方单位实际位置」为判据（Q-1）；效果③的 −50% 上限为设计稿外自选（Q-2）；效果③的「战斗力」不作用于远程攻击强度（Q-3）；两计数器为终身累计、和谈计数排除城邦和谈（Q-4）。另有 3 项提示（城市固定伤害有意不缩放、热路径新增分支、成员未进构造函数列表）。

建议处理顺序：先拍板 Q-2/Q-3（直接影响强度平衡），再确认 Q-1/Q-4 口径；P-1 可顺带补注释。之后按 [[build-project-paths]] 构建 SP V11 与 MPDLL 实机验证（重点：境内敌军的固定伤害是否归零/减半、远程攻击是否仍满额、被宣战计数与战斗力惩罚的累计与上限、和谈文化加成是否仅盟友档生效）。
