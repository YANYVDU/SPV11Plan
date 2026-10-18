# CSUA 审查报告：贝尔格莱德（Belgrade）

- 审查日期：2026-10-01
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 6 文件 **+132 / −28**；SP 5 文件 **+95 / −0**
- 结论摘要：三条盟友效果与一条朋友效果**逐条对得上设计稿**，**未发现功能性缺陷**。实现方式为**主表 `CityStateUAEffects` 扩展 1 列 `ZOCRangeBonus` + `CvUnitMovement::IsSlowedByZOC` 重写为「范围扫描」 + `CvCity::updateStrengthValue` 驻军贡献乘算 + 复用既有 `MilitaryUnitProductionXP` 列**。经逐分支论证，`IsSlowedByZOC` 在**半径=1 时与原逻辑完全等价**（回归安全）。有 **0 处应修正**、**0 项待拍板**、**3 项非缺陷提示**（均与性能/缓存陈旧度有关）。

---

## 一、改动清单

### MPDLL

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +3 / −0 | `CityStateUAEffects` 新增列 `ZOCRangeBonus`（普通整数，`DEFAULT 0`，`:79-81`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +4 / −0 | `GetZOCRangeBonus()` 声明与成员（`CvCityStateUAEffectEntry` `:284`/`:492`；`CvPlayerCityStateUA` `:750`/`:1021`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +9 / −0 | 读列（`:429`）、`CvCityStateUAEffectEntry` 构造初始化（`:283`）、`CvPlayerCityStateUA` 构造初始化（`:1457`）、`Reset` 归零（`:1580`）、`ApplyEffect` 聚合（`:1797`）、两个 getter（`:1088`、`:2246`） |
| `CvGameCoreDLL_Expansion2/CvCity.cpp` | +14 / −0 | `updateStrengthValue` 中对**驻军贡献** `iStrengthFromUnits` 乘 `(100 + GarrisonCityDefenseModifier) / 100`（`:17015-17027`） |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +5 / −0 | `RefreshCSAllUAEffects` 末尾调用 `UpdateCityStrength()`（`:20182-20185`） |
| `CvGameCoreDLL_Expansion2/CvUnitMovement.cpp` | +97 / −28 | `#include "CvCityStateUAClasses.h"`（`:8`）；新增 `AnyPlayerHasZOCRangeBonus()`（`:320-356`）；`IsSlowedByZOC` 重写为「盒式范围扫描 + 逐源半径」（`:381-515`） |

> **既有机制复用说明**：`MilitaryUnitProductionXP` 列（XP 效果）与 `GarrisonCityDefenseModifier` 列**并非本次新增**，其列定义与 **XP 的消费点** `CvCity::CreateUnit`（`CvCity.cpp:19068-19082`，判断 `!bIsGold && !bIsFaith`）均已在本分支更早的提交中落地。本次贝尔格莱德改动**只新增 `ZOCRangeBonus` 一列**，并首次把 `GarrisonCityDefenseModifier` 接入 `updateStrengthValue`，同时补齐 SP 侧数据与文本。

### SP

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 / −0 | 城邦绑定 `MINOR_CIV_BELGRADE` → `CSUA_BELGRADE`（`:62`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +19 / −0 | 2 个效果行 `EFFECT_CSUA_BELGRADE_ALLY` / `_FRIEND`（`:461-472`）、1 个 UA 条目 `CSUA_BELGRADE`（`:1750-1756`） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +25 / −0 | 3 个文本 Tag（`:20402-20429`） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +25 / −0 | 3 个文本 Tag（`:18871-18898`） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +25 / −0 | 3 个文本 Tag（`:18677-18704`） |

### 效果设计（已核对与三语文本、XML 三方一致）

| 对象 | 设计文本（`1.城邦UA/军事型.txt:10-16`） | 实现 |
| --- | --- | --- |
| 盟友① | 盟友的城市建造的单位获得额外 30 经验（购买无效） | `EFFECT_CSUA_BELGRADE_ALLY.MilitaryUnitProductionXP = 30`，经 `CvCity::CreateUnit` 在 `!bIsGold && !bIsFaith` 时对战斗单位 `changeExperience(30)` |
| 盟友② | 盟友的单位 ZOC 范围 +1 | `EFFECT_CSUA_BELGRADE_ALLY.ZOCRangeBonus = 1`，`IsSlowedByZOC` 中该持有者（盟友）的单位 `iSrcRange = 1 + 1 = 2` |
| 盟友③ | 盟友单位为城市提供的城防 +200% | `EFFECT_CSUA_BELGRADE_ALLY.GarrisonCityDefenseModifier = 200`，`updateStrengthValue` 中驻军贡献 `×(100+200)/100 = ×3` |
| 朋友① | 朋友的城市建造的单位获得额外 15 经验（购买无效）（原文「盟友的」为笔误） | `EFFECT_CSUA_BELGRADE_FRIEND.MilitaryUnitProductionXP = 15`，同上路径 |

城邦绑定：`MinorCivilizations.Type = MINOR_CIV_BELGRADE`（vanilla `Assets/DLC/Expansion/Gameplay/XML/Civilizations/CIV5MinorCivilizations.xml:162-164`），CSUA Type = `CSUA_BELGRADE`，无命名错位。

---

## 二、问题清单

> 经逐文件回读与三方对照，**未发现应修正项，也未发现需要用户拍板的设计歧义**。以下 3 条均为非缺陷的提示，涉及性能与缓存陈旧度，可按需处理。

### 应修正

（无）

### 待拍板（需确认，非缺陷）

（无）

### 提示（非缺陷）

#### P-1　`RefreshCSAllUAEffects` 每回合无条件重算全城城防，与 `CvCity::doTurn` 重复

- 位置：`CvPlayer.cpp:20185`（新增 `UpdateCityStrength()`）、对照 `CvCity.cpp:2439`（`CvCity::doTurn` 内已有 `updateStrengthValue()`）。
- 证据：`CvCity::doTurn()` 每回合对每座城调用一次 `updateStrengthValue()`；`RefreshCSAllUAEffects` 由 `CvPlayer::doTurn`（`CvPlayer.cpp:5420`）对**所有主要文明**每回合调用，末尾又对**该玩家全部城市**再跑一遍 `UpdateCityStrength()`。两次调用读取同一份 CSUA 状态，结果相同。
- 影响评估：**仅性能**，无正确性问题。对回合流程而言，这次调用在「常规每回合」路径上是冗余的（真正的价值在「关系变化当回合立即生效」路径）。
- 建议（可选）：把 `UpdateCityStrength()` 收窄到关系变化刷新路径，或仅当玩家实际持有 `GarrisonCityDefenseModifier != 0` 时才调用；若追求最简，保留现状亦可（成本为每回合每玩家一次 O(城市数) 的强度重算）。

#### P-2　`AnyPlayerHasZOCRangeBonus()` 的 `static` 缓存不随新开游戏 / 读档重置

- 位置：`CvUnitMovement.cpp:328-329`（`static int s_iCachedTurn` / `static bool s_bCached`）。
- 证据：缓存以 `GC.getGame().getGameTurn()` 为键，但两个 `static` 变量是进程级、跨局持久。读档 / 新开一局时，若当前回合号**恰好等于**上一局缓存的回合号，会返回上一局的陈旧布尔。
- 影响评估：**几乎无害**。该缓存只决定 `iScanRange`（扫描窗口大小），真正的 ZOC 判定由**逐源** `iSrcRange`（读实时 CSUA 状态）二次把关：陈旧 `true` 只会让一次 ZOC 判定多扫 5×5（不影响结果）；陈旧 `false` 会让盟友的半径 2 ZOC 漏判一个回合——但仅在回合号巧合相同时发生。属边缘情形。
- 建议（可选）：如需彻底消除，可在 `CvGame::init`/读档处把该缓存置 `-1`；或在缓存里直接存「本回合最大 ZOC 半径」而非布尔（语义更清晰，扫描窗口不变）。

#### P-3　注释「A* 热路径 O(1)」与「无加成时不受影响」表述偏乐观

- 位置：`CvUnitMovement.cpp:322-325`（注释）、`:394-395`（注释）、`:396-398`（盒式双层循环）。
- 证据：无加成时 `iScanRange = 1`，循环为 **3×3 = 9 次** `GC.getMap().plot()` + `plotDistance()`，而原实现为 **6 次** `plotDirection()`；此外，只要**任意**一名玩家持有 ZOC 加成，`iScanRange` 即为 2，**全地图所有单位**的 ZOC 判定都扩为 **5×5 = 25 次**。`AnyPlayerHasZOCRangeBonus()` 本身确实是 O(1)（每回合首次 O(玩家数)，之后命中缓存）。
- 影响评估：**仅性能**。量级与原实现同阶，且扫描窗口的放大是「正确性所需」（否则找不到半径 2 的源）。不构成缺陷。
- 建议（可选）：把注释改为「每回合 O(1) 缓存判定；无加成时扫描窗口为 3×3，有加成时全局扩为 5×5」，避免后续维护者误以为无加成时循环次数与原实现一致。

---

## 三、已验证无误项

1. **城邦绑定与 Type 正确**：`CSUA.sql:62` 为 `UPDATE MinorCivilizations SET UAType = 'CSUA_BELGRADE' WHERE Type = 'MINOR_CIV_BELGRADE'`，与 `CSUA.xml:1750-1756` 的 `CityStateUAs` 条目、`MINOR_CIV_BELGRADE` 一致，无命名错位。
2. **`Description` 引用的 Tag 真实存在**：`CSUA.xml:1752` `<Description>TXT_KEY_CITYSTATE_BELGRADE</Description>`。经全盘检索文明 5 安装目录（实际路径 `D:\steam\steamapps\common\Sid Meier's Civilization V`，注意非 `5`），`TXT_KEY_CITYSTATE_BELGRADE` 定义于 vanilla `Assets/Gameplay/XML/Civilizations/CIV5MinorCivilizations.xml:214-217` 与 `Assets/DLC/Expansion/Gameplay/XML/Civilizations/CIV5MinorCivilizations.xml:162-164`（`Description`/`ShortDescription`），并有 EN/zh_CN/zh_Hant 三语文本。与魁北克漏 `_CITY` 的孤例不同，贝尔格莱德**不带** `_CITY` 后缀即为正确 tag。
3. **数值三方一致**：XML（30 / 15 / 200 / 1）＝ 设计稿（30 / 15 / +200% / +1）＝ 三语文本（30 / 15 / 200% / +1），逐项对齐。
4. **`IsSlowedByZOC` 在半径=1 时与原逻辑完全等价（回归安全）**：
   - 外层邻居枚举：原 `plotDirection` 的 6 个六边形邻居，等价于新代码「以起点为中心的 3×3 盒 + `plotDistance ∈ (0,1]` 过滤」——`plotDistance` 内部经 `dxWrap`/`dyWrap` 处理地图 X 环绕，与 `plotDirection`（内部 `xToHexspaceX`/`hexspaceXToX` + `CvMap::plot` 的 `coordRange` 环绕）产出的邻居集合一致；且盒范围 `|dX|≤1,|dY|≤1` 覆盖全部 6 个邻居（六边形邻居的存储坐标偏移恒在 ±1 内）。
   - 城市分支：原「枚举敌城邻居并与目的坐标精确比对」等价于新「`plotDistance(to, city) == 1`」（均表示目的格是敌城的邻居），且新代码以 `iFromDist == 1` 限定城市半径恒为 1，与「城市始终半径 1」的设计一致。
   - 单位分支：原「源单位位于起点邻居，且目的格是该源单位的邻居」等价于新「`iFromDist ≤ iSrcRange` 且 `0 < iToDist ≤ iSrcRange`」（半径=1 时即两者皆为 1）；`iToDist > 0` 排除目的格＝源格。
   - 早退顺序不同（原按方向序、新按盒序），但 `IsSlowedByZOC` 是纯谓词、一旦命中即 `return true`，结果与顺序无关。
5. **性能闸门真实生效**：无任何玩家持加成时 `iScanRange` 恒为 1，退化为 3×3；`MOD_SP_UNIQUE_CITYSTATE` 关闭时走 `#else` 分支（`iScanRange = 1`、`iSrcRange = 1`），行为与原实现完全一致。
6. **城防 +200% 只乘「驻军单位贡献」**：`CvCity.cpp:17018` 的 `if (iStrengthFromUnits > 0)` 保证仅在存在驻军时生效，`iStrengthFromUnits` 是 `GetGarrisonedUnit()` 的贡献（`:17012`），**不**触及城市基础城防与建筑城防（`iBuildingDefense` 在 `:16982-16987` 独立累加，位于乘算之前）。乘算后立即在 `:17029` 汇入 `iStrengthValue`，无其他副作用。
7. **经验 30/15 只在「建造」给予、购买无效**：`CvCity::CreateUnit`（`CvCity.cpp:19068-19082`）以 `!bIsGold && !bIsFaith` 为闸门。生产完成路径 `CvCity.cpp:18468` 传 `CreateUnit(eTrainUnit, false, false, ...)`；金币购买 `:19977` 传 `(eUnitType, true, false)`；信仰购买 `:20097` 传 `(eUnitType, false, true)`；AI 行动购买（`CvMilitaryAI.cpp:874/918`）亦传 gold/faith。四类路径判定与设计「建造给经验、购买不给」精确一致。
8. **经验只发给「该城所属玩家（盟友本人）」**：`CreateUnit` 以 `GET_PLAYER(getOwner())` 取城的主人，读取其 `GetMilitaryUnitProductionXP()`，不会误发给其他玩家。仅对战斗单位（`Combat > 0 || RangedCombat > 0`）生效——设计语境下「建造的单位」即军事单位，合理。
9. **新列 `ZOCRangeBonus` 全链路完整**：解析 `CacheResults`（`CvCityStateUAClasses.cpp:429`）、聚合 `ApplyEffect`（`:1797`）、`Reset`（`:1580`）、`CvCityStateUAEffectEntry` 构造（`:283`）、`CvPlayerCityStateUA` 构造（`:1457`）、getter（`:1088`、`:2246`）、两处声明（`.h:284/492/750/1021`）——七项齐全，无缺环。
10. **无新增序列化成员，无需版本门控**：`m_iZOCRangeBonus` 属 `CvPlayerCityStateUA`，该类为**纯运行时缓存**（`RefreshCSAllUAEffects` 每回合 `Reset` + 全量 `ApplyEffect` 重建，全类无 `Read`/`Write`，`m_pCityStateUA` 由 `CvPlayer` 构造分配 `:629`、析构释放 `:688`）。`ZOCRangeBonus` 未出现在任何 `CvPlayer`/`CvGameCoreDLLPCH` 的序列化路径中。不触发 CLAUDE.md 的版本门控要求。
11. **盟友 / 朋友互斥且归属正确**：`RefreshCSAllUAEffects`（`CvPlayer.cpp:20116-20123`）以 `IsAllies` 优先、`else if IsFriends` 择一应用。盟友独得 30 XP + ZOC + 城防；朋友只得 15 XP，**无** ZOC、**无**城防加成（朋友行未配这两列）。数值比 30 / 15 = 2.0，符合设计全局规则第 2 条（盟友数值为朋友的 2-3 倍；与魁北克 50/20=2.5 同一口径）。
12. **ZOC 加成按「源」判定、不误伤普通单位**：`iScanRange` 只放宽搜索窗口，真正生效的半径 `iSrcRange` 由**每个源单位**的持有者 CSUA 状态决定（`CvUnitMovement.cpp:484-494`）。非盟友的普通单位 `iSrcRange` 恒为 1，即使被 5×5 窗口扫到也不会施加半径 2 的 ZOC。
13. **城市不获得 ZOC 半径加成**：设计为「盟友的**单位** ZOC 范围 +1」，实现中城市分支被 `iFromDist == 1` 严格限定，城市恒为半径 1，与设计一致。
14. **ZOC 判定入口唯一**：`IsSlowedByZOC` 仅此一处实现，被 `CvAStar.cpp:1004`、`:1607` 与 `CvUnitMovement.cpp:186` 复用，无第二套 ZOC 逻辑需要同步修改。
15. **三语文本齐备且追加于末尾**：`TXT_KEY_CSUA_BELGRADE_HELP`、`TXT_KEY_EFFECT_CSUA_BELGRADE_ALLY_HELP`、`TXT_KEY_EFFECT_CSUA_BELGRADE_FRIEND_HELP` 在中、繁、英三语均存在，数值 30 / 15 / 200% / +1 一致，且均插入在各语言文件的**最后一行 Row 之后、`</Language_*>` 之前**，未打乱既有分组；使用 `[ICON_BULLET]` / `[ICON_STRENGTH]` 提升可读性。
16. **注释为英文**：MPDLL 与 SP 本次新增的全部 C++ / SQL 注释均为英文，符合 [[sp-english-comments-only]] / VC9 GBK 工具链要求。
17. **无数据重复主键**：`CSUA_BELGRADE` / `EFFECT_CSUA_BELGRADE_ALLY` / `EFFECT_CSUA_BELGRADE_FRIEND` 在 SP 各仅一处定义；`ZOCRangeBonus` 仅 Belgrade 盟友行配置。
18. **行尾格式保持**：MPDLL 侧 `CvUnitMovement.cpp`、`CvCity.cpp` 维持 CRLF（工作区 CR 计数 = 增改后的 LF 计数，逐文件吻合），`CvCityStateUAClasses.cpp/.h`、`CvPlayer.cpp`、`UNIQUE_CITYSTATES.sql` 维持 LF；SP 五文件维持 LF。`git diff --numstat` 均为小改动（+3、+4、+9、+14、+5、+97/−28、+1、+19、+25×3），无整文件重写。
19. **DLL 已重编且包含本次改动**：`BuildOutput/VS2022_ReleaseWin32/CvGameCore_Expansion2.dll` 与 `(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll` 均 5337600 字节、时间 2026-10-01 03:32，晚于最新源码（`CvUnitMovement.cpp` 03:30）；二进制中可检索到字符串 `ZOCRangeBonus`（新列名），确认产物含本次改动。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff` / `git diff --numstat`，核对改动规模、行尾与提交状态。
- 交叉核对 C++ 实现、XML 数据、三语文本、设计稿（`1.城邦UA/军事型.txt:10-16`）四者数值与语义。
- 回读引擎侧被调用函数确认语义与挂钩：
  - `CvUnitMovement::IsSlowedByZOC`（`CvUnitMovement.cpp:359-518`）与新增 `AnyPlayerHasZOCRangeBonus`（`:320-356`），逐分支对照改前版本（`git diff` 保留的 `−` 行），并以 `plotDistance`（`CvGameCoreUtils.h:137-158`，含 `dxWrap`/`dyWrap`）、`plotDirection`（同文件 `:178-194`）、`CvMap::plot`（`CvMap.h:221-230`，含 `coordRange` 环绕）三者的坐标语义论证半径=1 等价性。
  - `CvCity::updateStrengthValue`（`CvCity.cpp:16971-17029`），确认乘算只作用于 `iStrengthFromUnits`（驻军贡献）。
  - `CvCity::CreateUnit`（`CvCity.cpp:19049-19091`）及其全部调用点（`CvCity.cpp:18468` 建造、`:19977` 金币购买、`:20097` 信仰购买、`CvMilitaryAI.cpp:874/918`），确认 XP 只在建造路径给予。
  - `CvPlayer::RefreshCSAllUAEffects`（`CvPlayer.cpp:20090-20186`）、`RefreshCSAlliesFriends`（`:20046-20083`）及其调用点（`CvPlayer::doTurn` `:5420`、`CvMinorCivAI.cpp:6716/6720/7025`），确认刷新时机与盟友/朋友互斥。
  - `CvPlayer::UpdateCityStrength`（`:6141-6147`）与 `CvCity::doTurn`（`CvCity.cpp:2439`）的重复性对照（支撑 P-1）。
  - `CvPlayer::GetPlayerCityStateUA`（`CvPlayer.cpp:15451-15456`）确认对野蛮人/城邦返回 NULL，`AnyPlayerHasZOCRangeBonus` 的空指针判断安全。
- 以 `grep -rn` 全盘检索 SP 仓库与 MPDLL 仓库，核对 `CSUA_BELGRADE` / `EFFECT_CSUA_BELGRADE_*` / `ZOCRangeBonus` / `MINOR_CIV_BELGRADE` 的定义唯一性与绑定。
- 以 `grep -rn` 全盘检索文明 5 安装目录（`D:\steam\steamapps\common\Sid Meier's Civilization V`）核实 `TXT_KEY_CITYSTATE_BELGRADE` 与 `MINOR_CIV_BELGRADE` 的真实存在。
- 逐文件以 `tr -dc '\r' | wc -c` 对比 HEAD 与工作区 CR 计数，核对行尾未被破坏。
- 以 `grep -a` 在 DLL 二进制中检索新列名字符串，确认产物包含本次改动。

---

## 五、当前状态与建议处理顺序

### 状态

- MPDLL 工作区：6 文件 **+132 / −28**（未 commit）；DLL 已重编（03:32），产物在 `BuildOutput/VS2022_ReleaseWin32/` 与 `(1) CIV5MPDLL/DLL/`。
- SP 工作区：5 文件 **+95 / −0**（未 commit）。
- 游戏根目录 DLL（`Documents\My Games\Sid Meier's Civilization 5\CvGameCore_Expansion2.dll`）与 MODS 目录**未更新**（未构建）。
- 文档：本次仅新增**列**（非新表），按 [[api-instruction-lib-unreliable]] 的既定约定（CSUA 全部完成前不更新 API 说明库），无需即时同步。

### 建议顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | （可选）P-1 收窄 `UpdateCityStrength()` 调用范围 | 小 |
| 2 | （可选）P-3 修正 `CvUnitMovement.cpp` 两处注释表述 | 极小 |
| 3 | （可选）P-2 在 `CvGame::init`/读档处重置 `s_iCachedTurn` | 极小 |
| 4 | 覆盖根目录 DLL 或构建模组，按下述步骤实机验证 | 小 |

### 实机验证步骤

1. **盟友经验**：与贝尔格莱德结盟后，在盟友城市**建造**任意军事单位，出生即应带 30 经验；**金币/信仰购买**同一单位**不应**带经验。对照：朋友关系时建造给 15 经验。
2. **盟友 ZOC +1**：结盟后，令敌方单位处于盟友单位**两格**（原为不受影响的距离）处，盟友单位移动/敌方单位穿越其附近时，ZOC 应于半径 2 生效（移动被截停）；断盟后应退回半径 1。建议同时验证非盟友玩家的单位仍为半径 1。
3. **盟友城防 +200%**：结盟后，在有驻军的盟友城市查看城防数值，驻军贡献应约为断盟时的 3 倍；**撤走驻军**后加成立即消失；城市基础城防与建筑城防不受影响。关系变化当回合即应生效（验证 `RefreshCSAllUAEffects → UpdateCityStrength` 路径）。
4. **朋友效果**：与贝尔格莱德为朋友（非盟友），建造单位给 15 经验，且**无** ZOC 加成、**无**城防加成。
5. **断交负例**：断交后全部效果应于关系变化当回合消失（验证每回合全量重建路径）。
6. **文本回归**：城邦外交界面 / 开局城邦选择列表 / 百科城邦页的 UA 说明应完整显示三段盟友效果 + 一段朋友效果（验证 `Help` 链）；`Description` 引用的 `TXT_KEY_CITYSTATE_BELGRADE` 已确认真实存在，无需修复。
7. **ZOC 回归**：在**无任何玩家与贝尔格莱德结盟**的普通对局中，单位在敌城/敌军相邻处的 ZOC 截停行为应与改动前一致（验证半径=1 等价性）。
