# CSUA 审查报告：姆班扎刚果（Mbanza Kongo）

- 审查日期：2026-10-01
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 2 文件 **+62 / −0**；SP 5 文件 **+95 / −0**
- 结论摘要：三条盟友效果与一条朋友效果**逐条对得上设计稿**，**未发现功能性缺陷**。实现方式为**复用框架提交 `68d732c` 已建好的 3 个 `CityStateUAEffects` 标量列与 getter**，本次只在 3 个热路径挂钩点消费它们：`CvPlayer::getProductionModifier(eUnit)`（组建速度）、`CvPlayer::getNumResourceTotal`（人力）、`CvUnit::GetGenericMaxStrengthModifier`（战斗力），并在 SP 侧写入 2 个效果条目 + 城邦绑定 + 三语文本。有 **0 项应修正**、**3 项待拍板**、**3 项提示**。

---

## 一、改动清单

### MPDLL（本次工作区改动）

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +32 / −0 | ① `getProductionModifier(UnitTypes, CvString*)` 军事生产分支新增组建速度块（`:10012-10029`）；② `getNumResourceTotal` 战略资源分支新增人力块（`:24667-24680`） |
| `CvGameCoreDLL_Expansion2/CvUnit.cpp` | +30 / −0 | `GetGenericMaxStrengthModifier` 末尾新增科技差战斗力块（`:15741-15770`） |

> **框架前置说明（非本次改动）**：本次消费的 3 个数据库列 `UnitProductionModifierPerCity` / `ManpowerPerCity` / `CombatBonusPerTechDifference`（`(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql:92-95`）、`CvCityStateUAEffectEntry` / `CvPlayerCityStateUA` 的解析、getter 与 `ApplyEffect` 聚合（`CvCityStateUAClasses.cpp:290-292 / 442-444 / 1103-1105 / 1471-1473 / 1596-1598 / 1819-1821 / 2267-2269`，头文件 `:294-296 / 504-506 / 764-766 / 1034-1036`）**均由更早的提交 `68d732c "feat: Unique CS UA framework"` 引入**，本次工作区 `git status` 显示这两个类文件为干净状态。因此本次改动是纯「消费钩子」，不新增任何序列化成员。

### SP（本次工作区改动）

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 / −0 | 城邦绑定 `MINOR_CIV_MBANZA_KONGO` → `CSUA_MBANZA_KONGO`（`:65`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +19 / −0 | 2 个效果（`:497-508`）、1 个 UA 条目（`:1807-1813`） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +25 / −0 | 3 个文本 Tag（`:20479` 起，追加于文件末尾） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +25 / −0 | 3 个文本 Tag（`:18948` 起，追加于文件末尾） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +25 / −0 | 3 个文本 Tag（`:18754` 起，追加于文件末尾） |

### 效果设计对照（设计稿 `1.城邦UA/军事型.txt:29-33`）

| 对象 | 设计文本 | 实现 | 判定 |
| --- | --- | --- | --- |
| 盟友① | 盟友每有一座城市，全国军事单位组建速度+10% | `EFFECT_CSUA_MBANZA_KONGO_ALLY.UnitProductionModifierPerCity=10`（`CSUA.xml:499`），经 `CvPlayer::getProductionModifier(eUnit)` 以 `10 × getNumCities()` 平百分数累加（`CvPlayer.cpp:10012-10029`） | **符合设计** |
| 盟友② | 盟友每座城市额外提供4人力 | `EFFECT_CSUA_MBANZA_KONGO_ALLY.ManpowerPerCity=4`（`CSUA.xml:500`），经 `CvPlayer::getNumResourceTotal` 以 `4 × getNumCities()` 累加（`CvPlayer.cpp:24667-24680`） | **符合设计** |
| 盟友③ | 盟友在对抗科技数量更多的文明时每个科技数量差距+10%战斗力 | `EFFECT_CSUA_MBANZA_KONGO_ALLY.CombatBonusPerTechDifference=10`（`CSUA.xml:501`），经 `CvUnit::GetGenericMaxStrengthModifier` 以 `(敌队科技 − 我队科技) × 10` 单向累加（`CvUnit.cpp:15741-15770`） | **符合设计** |
| 朋友① | 朋友每有一座城市，全国军事单位组建速度+4% | `EFFECT_CSUA_MBANZA_KONGO_FRIEND.UnitProductionModifierPerCity=4`（`CSUA.xml:506`），同一组建速度钩子，仅朋友档生效 | **符合设计** |

> 朋友档**只**含 `UnitProductionModifierPerCity=4`，未设置 `ManpowerPerCity` / `CombatBonusPerTechDifference`（列默认 0），故盟友②③**不会**误施于朋友。设计稿朋友档仅一条，实现一一对应。

---

## 二、问题清单

### 应修正

无。本次改动未发现功能性缺陷。

### 待拍板（需确认，非缺陷）

#### Q-1　效果③战斗力加成不设上限

- 位置：`CvUnit.cpp:15763-15765`（`iDiff = iEnemyTechs - iMyTechs; if (iDiff > 0) iModifier += iDiff * iPerTech;`）。
- 证据：`iPerTech = 10`，`iDiff` 无任何截断。`GetGenericMaxStrengthModifier` 的返回最终在 `GetMaxAttackStrength`（`CvUnit.cpp:16153`）以 `GetBaseCombatStrength() × (iModifier + 100)` 合成，即 `iModifier` 为百分数；`iModifier` 全函数仅在下限有截断（`if(iModifier < -90) iModifier = -90;`，`:16151`），**无上限**。
- 影响评估：当盟友落后某文明 30 个科技时，该盟友对其全部单位获得 +300% 战斗力。设计稿原文「每个科技数量差距+10%战斗力」未提上限，三语帮助文本亦未提上限（`TextInfos_en_US.xml:20486`「+10% Combat Strength per technology of difference」），**实现与帮助文本一致**。
- 需确认：是否接受「无上限」这一口径（科技落后越多，反打越强）。若需设上限，应同步改帮助文本。

#### Q-2　效果③仅覆盖近战攻防，不含远程攻击强度

- 位置：`CvUnit.cpp:15741-15770`（挂在 `GetGenericMaxStrengthModifier`）。
- 证据：该函数仅被 `GetMaxAttackStrength`（`:15793`）与 `GetMaxDefenseStrength`（`:16178`）调用；远程攻击强度走 `GetMaxRangedCombatStrength`，**不经过**此函数。故：近战单位攻击 ✅、任意单位防御 ✅、远程单位的远程攻击 ❌（但其防御强度仍享受加成）。
- 影响评估：Civ5 术语中「Combat Strength（战斗力）」与「Ranged Combat Strength（远程战斗力）」是两套数值，帮助文本写的是「Combat Strength」，**措辞与实现一致**。
- 需确认：设计稿「+10%战斗力」是否也意图覆盖远程攻击；若意图覆盖，需另挂 `GetMaxRangedCombatStrength`。

#### Q-3　效果②的 4 人力会被 AI 难度修正放大

- 位置：`CvPlayer.cpp:24667-24680`（人力块）与紧邻其后的 `:24681-24685`（`GetStrategicResourceMod()` 乘法）、`:24686-24692`（AI 难度 `iHanHandicapMod` 乘法）。
- 证据：人力块被有意置于两处乘法**之前**（注释称 D8），故 `getNumCities() × 4` 会随后续乘法一起缩放。经查：
  - 人类玩家的 `m_iStrategicResourceMod` 由政策 `GetStrategicResourceMod()` 决定，SP 中唯一相关设置为 `Policies.xml:639 <Set StrategicResourceMod="0"/>`，即人类通常为 0、不缩放；
  - 但 AI 难度块 `iHanHandicapMod`（`AIBonus.xml:103/121/140/154` 等，最高 110 + 每时代增量）对 AI 玩家生效，故**AI 盟友每城实际获得超过 4 人力**。
- 影响评估：与既有「政策授予人力」路径口径一致（`iCityResourceFromPolicy` 同样在 `:24665`、乘法之前），属全局一致行为，**不是 bug**；但设计稿字面「+4人力」未提缩放。
- 需确认：是否接受 AI 盟友被难度修正放大（多数全局战略资源加成皆如此），还是要求 4 人力为不受修正的绝对值。

### 提示（非缺陷）

#### P-1　代码注释引用了内部计划文档的决策编号

- 位置：`CvUnit.cpp:15744-15745`（「D7: melee only」「D4: no hard cap, per design rule 15」）、`CvPlayer.cpp:24669`（「D8」）。
- 说明：`D4/D5/D7/D8`、「design rule 15」等编号源自实现前的设计讨论文档，代码内无法自解释。后续维护者读到时需反查外部文档才能理解约束来源。
- 建议（可选）：把编号替换为自包含描述（例如「no cap, matches help text」「placed before GetStrategicResourceMod to match building/policy manpower path」），或保留编号同时补一句释义。

#### P-2　效果②热路径每次调用都做一次字符串→类型查找

- 位置：`CvPlayer.cpp:24672`（`eIndex == (ResourceTypes)GC.getInfoTypeForString("RESOURCE_MANPOWER", true)`）。
- 说明：`getNumResourceTotal` 是极热函数，本行对**每个玩家、每次战略资源总量查询**都执行一次字符串哈希查找。经查 `GC.getInfoTypeForString` 使用 `stdext::hash_map`（`CvGlobals.h:187`）做 O(1) 查找，开销很小；且整块被 `MOD_SP_UNIQUE_CITYSTATE` 与 `RESOURCEUSAGE_STRATEGIC` 双重收窄。
- 建议（可选）：如需极致优化，可把 `ResourceTypes` 缓存为静态量或 `CvGlobals` 成员，避免每次字符串哈希；非必须。

#### P-3　效果②③无 tooltip 归因（仅记录）

- 位置：`CvPlayer.cpp:24667-24680`、`CvUnit.cpp:15741-15770`。
- 说明：效果①经 `BuildProdModHelpText(toolTipSink, "TXT_KEY_PRODMOD_CITYSTATE_UA", ...)`（`CvPlayer.cpp:10025`）在城市产出明细显示「来自城邦修正: N%」，与既有 CSUA 惯例一致；效果②（人力）显示于资源面板、效果③（战斗力）显示于战斗预览，二者**均无既有归因位**，不显示来源。非缺陷，与设计稿/帮助文本无冲突，仅记录。

---

## 三、已验证无误项

1. **逐条效果与数值完全对应**：盟友①+10%/城、盟友②+4人力/城、盟友③+10%/科技差、朋友①+4%/城，SP 数据（`CSUA.xml:498-508`）与设计稿（`军事型.txt:30-33`）、三语文本四方一致。
2. **盟友/朋友档位互斥且归属正确**：`RefreshCSAllUAEffects`（`CvPlayer.cpp:20152-20159`）以 `IsAllies` 优先、`else if IsFriends` 择一 `ApplyEffect`；盟友只取盟友效果、朋友只取朋友效果，无叠加。朋友档未设人力/战斗力字段，不会误得盟友专属效果。
3. **效果①挂钩点正确**：位于 `CvPlayer::getProductionModifier(UnitTypes, CvString*)` 的 `if(pUnitEntry->IsMilitaryProduction())` 分支内（`CvPlayer.cpp:10006-10029`），**只作用于军事单位**，不误伤民用/非军事单位；以 `iPerCity * getNumCities()` 为乘数（`:10023`），语义即「每城+10%，全国」。
4. **效果①为平百分数、未套错公式**：`iMultiplier` 直接累加 `iPerCity * getNumCities()`（`:10024`），未乘 100；与消费方 `getBaseYieldRateModifier`（`CvCity.cpp:13421`）以百分数使用、以及既有 `getMilitaryProductionModifier()` 同单位口径一致。代码注释明确「no basis-point scaling here, because the consumer is getProductionModifier」。
5. **效果①触达每城生产路径**：`CvCity::getProductionModifier(UnitTypes,...)`（`CvCity.cpp:6661`）在 `:6676` 调用 `thisPlayer.getProductionModifier(eUnit, toolTipSink)`，且被 `CvCity::getProductionModifier(CvString*)`（`:6614`）转发，故该玩家**所有城市**生产军事单位均生效一次，无重复计数。
6. **效果②挂钩点与资源类型正确**：`RESOURCE_MANPOWER` 在 SP 中定义 `<ResourceUsage>1</ResourceUsage>`（`NewResources_Define.xml:21`）= `RESOURCEUSAGE_STRATEGIC`，故人力块所在 `if(pkResource->getResourceUsage() == RESOURCEUSAGE_STRATEGIC)` 分支（`CvPlayer.cpp:24639`）**必然命中**。
7. **效果②为「每城」乘数且只对盟友本人**：`iTotalNumResource += getNumCities() * iPerCity`（`:24677`）；`GetManpowerPerCity()` 仅盟友效果置 4、朋友为 0，且 CSUA 缓存挂在「与城邦结盟的那个玩家」身上，**不会误发给朋友或无关玩家**。
8. **效果②放置位置与既有政策/建筑人力口径一致**：人力块置于 `GetStrategicResourceMod()` 乘法（`:24681`）之前，与政策授予人力 `iCityResourceFromPolicy`（`:24665`）、建筑授予人力（经 `Building_ResourceQuantity` 进入基础量）同一处理层级，注释所述「follows the same path as building/policy manpower」经核实成立（`BuildingsEffects.xml:690/695/705/...` 为建筑授予行）。
9. **效果③与河内块共存无冲突**：河内块（`CvUnit.cpp:15583-15605`）位于 `pBattlePlot` 守卫作用域内、按地块归属施加「敌军减益」；姆班扎块（`:15741-15770`）位于函数末尾、`pOtherUnit` 守卫之外、按敌方队伍科技差施加「我方增益」。二者作用对象（减益 vs 增益）、判据（地块归属 vs 队伍科技）、作用域均不同，**互不覆盖、互不重复**，均为纯加法累加。
10. **效果③为 Team 级取数**：`GET_TEAM(getTeam()).GetTeamTechs()->GetNumTechsKnown()` 与 `GET_TEAM(GET_PLAYER(eEnemy).getTeam())...`（`:15761-15762`），科技为团队共享，取数口径正确；`GetNumTechsKnown()` 为 `CvTeamTechs` 的成员读值（`CvTechClasses.cpp:2128`）。
11. **效果③为单向**：仅 `iDiff > 0`（敌方科技多于我方）时加成（`:15764`），差距 = 敌 − 我，符合设计「对抗科技数量更多的文明时」。
12. **效果③敌方判定正确且安全**：`pOtherUnit != NULL` 时取 `pOtherUnit->getOwner()`（对抗敌方单位）；`pOtherUnit == NULL` 且 `pBattlePlot->isCity()` 时取城市拥有者（攻打空城）；再经 `eEnemy != NO_PLAYER && eEnemy != getOwner() && GET_PLAYER(eEnemy).isAlive()`（`:15759`）三重守卫，**空指针/同玩家/已死玩家均被排除**；同队友单位因 `iDiff == 0` 天然不生效。
13. **效果③覆盖近战攻防、语义与帮助文本一致**：经 `GetGenericMaxStrengthModifier` 同时进入 `GetMaxAttackStrength`（`:15793`）与 `GetMaxDefenseStrength`（`:16178`），近战攻击与一切防御均生效；`iModifier` 为百分数（`:16153` 合成、`:15422` 亦以 `getExtraCombatPercent()` 同单位累加），故 +10/科技 = +10% 战斗力。
14. **三处字段均无重复引用**：全仓库检索 `GetUnitProductionModifierPerCity` / `GetManpowerPerCity` / `GetCombatBonusPerTechDifference`，除类定义文件外**各仅一处**消费点（`CvPlayer.cpp:10020 / 24675`、`CvUnit.cpp:15750`）；`GetCSUAYieldPercentModifier` **未**引用这三个字段，无「平百分数 + 基点」双重应用。
15. **热路径开销可忽略**：三处钩子均先做「值是否为 0」短路（`:10021 / 24676 / 15751`），未持有姆班扎效果的玩家近乎零开销；仅盟友执行常数级计算（`getNumCities()` 为 `m_cities.GetCount()`，`CvPlayer.cpp:26915`，无递归/无重扫）。
16. **无空指针/越界/除零**：`GetPlayerCityStateUA()` 均先判 NULL（`:10020 / 24675 / 15750`）；`getNumResourceTotal` 起始已判 `pkResource == NULL` 返回 0（`:24632`）；无除法。
17. **城邦绑定与描述 Tag 正确**：`CSUA.sql:65` 绑定 `MINOR_CIV_MBANZA_KONGO` → `CSUA_MBANZA_KONGO`，与 `CSUA.xml:1807-1813` 一致。描述 Tag `TXT_KEY_CITYSTATE_MBANZA_KONGO`（`CSUA.xml:1809`）经核实与游戏本体一致——`Assets/DLC/Expansion2/Gameplay/XML/Civilizations/CIV5MinorCivilizations.xml:682-683` 的 `Description`/`ShortDescription` 正是 `TXT_KEY_CITYSTATE_MBANZA_KONGO`（**无 `_CITY` 后缀**，且全盘检索 `TXT_KEY_CITYSTATE_MBANZA_KONGO_CITY` 零命中），与魁北克那类「漏/多后缀」孤例相反，此处正确。
18. **模组开关已启用**：`MOD_SP_UNIQUE_CITYSTATE` 在 `CustomMods.h:983` 定义为运行期选项，SP 的 `DLL_Options.xml:401-403` 将其 `<Set Value="1"/>`，功能可生效。
19. **三语文本齐全、语义与数值一致、追加于末尾**：`TXT_KEY_CSUA_MBANZA_KONGO_HELP`、`TXT_KEY_EFFECT_CSUA_MBANZA_KONGO_ALLY_HELP`、`TXT_KEY_EFFECT_CSUA_MBANZA_KONGO_FRIEND_HELP` 在中/繁/英三文件均存在，均插入各文件 `</Language_xx>` 之前（末尾），未打乱既有分组；三语数值 10 / 4 / 10 / 4 与设计稿、XML 一致。
20. **图标合法**：`[ICON_PRODUCTION]` / `[ICON_RES_MANPOWER]` / `[ICON_STRENGTH]` 均在 SP 既有文本中大量使用（如 `TextInfos_en_US.xml:1520/1892`），映射有效。
21. **注释全英文**：MPDLL diff 中文行数为 0；SP diff 的中文行仅出现在本地化文本内容（译文），代码注释无中文，符合规范。
22. **行尾格式保持**：MPDLL 两文件与 SP 五文件抽样均为 LF（CR 计数为 0），`git diff --numstat` 全为小改动（+32/−0、+30/−0、+1/−0、+19/−0、+25×3），无整文件重写。
23. **无序列化改动**：本次未新增任何 `CvPlayer`/`CvCity`/`CvUnit` 成员，`CvPlayerCityStateUA` 为每回合 `Reset` + 全量重建的运行期缓存（`RefreshCSAllUAEffects`，`CvPlayer.cpp:20120`），不触发版本门控要求。
24. **无重复定义、无误改无关代码**：`CSUA_MBANZA_KONGO` / `EFFECT_CSUA_MBANZA_KONGO_ALLY` / `EFFECT_CSUA_MBANZA_KONGO_FRIEND` 各仅一处；MPDLL/SP 未跟踪文件为空，改动均落在相关函数与数据内。
25. **构建产物晚于全部源文件**：`BuildOutput/VS2022_ReleaseWin32/CvGameCore_Expansion2.dll` 与 `(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll` 均为 2026-10-01 04:31（5339648 字节），晚于最晚源文件 `CvPlayer.cpp`/`CvUnit.cpp`（04:25）；二进制内可检索到 `RESOURCE_MANPOWER` 与 `UnitProductionModifierPerCity` 相关字符串，产物含本次改动。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff` / `git diff --numstat` / `git status --short`，核对改动规模、行尾与提交状态（无未跟踪文件）。
- 交叉核对 C++ 实现、XML 数据、三语文本、设计稿（`军事型.txt:29-33`）四者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvPlayer::getProductionModifier`（`CvPlayer.cpp:9981/9996`）、`CvCity::getProductionModifier(UnitTypes,...)`（`CvCity.cpp:6661-6676`）、`getBaseYieldRateModifier`（`CvCity.cpp:13421`）、`CvPlayer::getNumResourceTotal`（`CvPlayer.cpp:24625-24712`）、`GetStrategicResourceMod`（`:24929`）、`CvUnit::GetGenericMaxStrengthModifier`（`CvUnit.cpp:15414-15772`）及其两个调用方 `GetMaxAttackStrength`（`:15776`）/`GetMaxDefenseStrength`（`:16178`）、`CvTeamTechs::GetNumTechsKnown`（`CvTechClasses.cpp:2128`）。
- 回读河内既有块（`CvUnit.cpp:15583-15605`）确认共存；回读 `RefreshCSAllUAEffects`（`CvPlayer.cpp:20120-20160`）确认盟友/朋友互斥。
- 全仓库检索三个新字段的消费点（各仅一处）与 `GetCSUAYieldPercentModifier` 是否引用它们（未引用），排除双重应用。
- 以 `grep -w` 在文明 5 安装目录核实 `TXT_KEY_CITYSTATE_MBANZA_KONGO`（无 `_CITY`）与 `MINOR_CIV_MBANZA_KONGO`；核实 `RESOURCE_MANPOWER` 的 `ResourceUsage=1`（战略）与建筑/政策/改良的人力授予路径。
- 以 `grep -a` 在 DLL 二进制中检索关键字符串确认产物包含改动；比对 DLL 与源文件时间戳。
- 以 Python 扫描 diff 检测中文注释（MPDLL 0 行；SP 仅译文），抽样检测行尾 CR 计数。

---

## 五、结论

- 姆班扎刚果 4 条效果（盟友 3 + 朋友 1）**逐条实现、数值正确、档位正确**，未发现功能性缺陷。
- 架构上，本次改动是**纯消费钩子**：3 个新列与 getter 由框架提交 `68d732c` 预先建好，本次仅把它们接到 3 个既有热路径（`getProductionModifier` / `getNumResourceTotal` / `GetGenericMaxStrengthModifier`），并补齐 SP 数据与三语文本；设计干净、无重复应用、无序列化负担。
- 需用户拍板 3 项口径（**Q-1 战斗力无上限、Q-2 是否覆盖远程攻击、Q-3 人力是否应受 AI 难度修正缩放**），均为设计确认而非缺陷。
- 提示 3 项（**P-1 注释引用内部决策编号、P-2 热路径字符串查找可缓存、P-3 效果②③无 tooltip 归因**），均可选。

### 建议处理顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | Q-1 / Q-2 / Q-3 口径拍板（如需调整则改代码 + 帮助文本） | 无 / 小 |
| 2 | （可选）P-1 注释去编号化 | 极小 |
| 3 | （可选）P-2 缓存 ResourceTypes | 极小 |
| 4 | 构建模组并按下方步骤实机验证 | 小 |

### 实机验证步骤

1. **盟友①**：与姆班扎刚果结盟后，城市生产任一**军事**单位，产出明细应出现「来自城邦修正: N%」，N = 10 × 该盟友城市数；生产非军事单位（如工人/开拓者）应**不**出现该加成。对照：断盟后消失。
2. **盟友②**：结盟后，战略资源面板的**人力**总量应比断盟时多 `4 × 城市数`（可对照 `getNumResourceAvailable(RESOURCE_MANPOWER)` 数值）；每新建一城，人力应于**下一回合**增加 4。对照：朋友档无此加成。
3. **盟友③**：结盟后，对**科技多于我方**的文明作战，我方近战单位攻击与任意单位防御的战斗力应有 +10%/科技差的加成（可在战斗预览对照数值）；对**科技落后**的文明作战应无加成；远程单位的**远程攻击**强度应无加成（仅其防御有）。
4. **朋友档**：与姆班扎刚果仅为朋友（非盟友）时，仅获得 +4%/城的组建速度，**无**人力、**无**战斗力加成。
5. **档位切换/断交负例**：盟友↔朋友↔无关系切换后，上述效果应于关系变化当回合立即重建（验证 `RefreshCSAllUAEffects` 的 `Reset`+全量重建路径）。
6. **文本回归**：城邦外交界面 / 开局城邦选择列表 / 百科城邦页的 UA 说明应完整显示三段盟友效果 + 一段朋友效果，且 `[ICON_PRODUCTION]` / `[ICON_RES_MANPOWER]` / `[ICON_STRENGTH]` 图标正常渲染。
