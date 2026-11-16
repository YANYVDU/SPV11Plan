# MPDLL × SP 11.08–11.16 提交复审报告 · 三审（修复实施结果）

- 三审日期：2026-11-17
- 三审对象：按一审问题清单 + 作者裁决实施的**修复改动本身**，而非区间内的原始提交
- 基线：`CIV5MPDLL` 分支 `V11dev`，修复系列基于 `8d694f3`（即原 HEAD `8ea2ddc` 之后的既有提交），共 **16 个提交**
- 编译状态：`Release|Win32` **通过**（`BUILD_EXIT=0`，已先删 `BuildTemp`；最后一次编译在**全部 16 个提交落盘后的干净工作树**上执行）
- 说明：本报告**不重复**一审/二审已列、且作者已明确裁定的条目（版本号 168、P2-1 双份奖励、P2-2 贸易协定不撤销、P2-5 停战文案、P3-13/14/17/25/26/31/32、P3-3 无主城市），只记录本轮实际改了什么、复审裁决如何、以及仍留待处理的部分。

---

## 〇、结论摘要

| 项目 | 结果 |
|---|---|
| 实施修复项 | 22 项（对应一审的 2×P1、12×P2、25×P3 中的可执行部分） |
| 编译 | 通过（全量 Release\|Win32） |
| 修复代码复审 | **21 项通过 / 1 项需修改 / 0 阻断** |
| 需修改项的处置 | 已修（F13 死分支），并连带修掉复审提出的 6 条观察 |
| 提交拆分 | 16 个提交，按「修复组」拆分；每组可独立 revert |
| 遗留 | 4 条不影响发布（见第五节） |

**发布前必须完成的事：无。** 唯一的发布前置仍是作者已裁定接受的内测期版本号策略（不升 168）。

---

## 一、修复提交清单（16 个）

> 拆分原则：按「一审问题项」一组一提交。少数项因改动的 hunk 在同一函数内交错（例如任务前提、单次抽签、越界检查都在 `CvMinorCivAI::DoStartQuest`/`IsValidQuestForPlayer` 同一段），单独拆分会产出无法编译的中间提交，因此合为一组，组名即覆盖的问题项。

| # | 提交 | 覆盖问题项 | 主要改动 |
|---|---|---|---|
| 1 | `6c2b527` Fix: return const yield arrays from the info accessors | P3-2 | `CvImprovementEntry` 13 个、`CvBuildingEntry` 44 个 `Get...Array()` 改返回 `const int*`；`CvCity::doBuildingInstantYield` 参数同步改 `const int*`（防止向共享只读零块写入） |
| 2 | `3c2f84d` Fix: keep the shared 2D array refcount honest | P3-19 | `ReleaseShared2DArray` 删掉不可达分支，改为显式 `CvAssertMsg(false, ...)` |
| 3 | `d2f86ac` Cleanup: move the misplaced Reset doc comment | P3-21 | 把 `/// Reset status arrays to all false` 从 `GetOwnedBuildings` 移回 `Reset` |
| 4 | `ae26c11` Fix: count real and free copies and gate every class-based effect | P2-6 / P2-7 / P2-8 / P3-1 | 重建改 `GetNumRealBuilding + GetNumFreeBuilding`；`GetNumBuildingClassActive`/`ChangeNumBuildingClassActive` 加边界检查；CSUA 三处加 `SP_BUILDING_CLASS_COUNT_ALL_TYPES` 门控；政策建筑类快乐改为按类取 active 计数并跳过过时建筑 |
| 5 | `172c00b` Fix: keep specialists when the citizen plan runs with auto-assign off | P2-9 / P2-10 / Q4 / P3-20 / P3-22 / P3-6 | `noAuto` 时保留现有专家只分配余量；专家偏置按 `SP_SPECIALIST_AI_BY_TYPE` 分支（新增 `GetMaxSpecialistSlotsInBuildingsForType`）；新增 `SP_CITIZEN_REALLOC_AUDIT` 审计开关；删除未用计数与死门控；修正估值注释 |
| 6 | `2cf47aa` Fix: harden the research-agreement city-state quest | P1-2 / P3-8 / P3-9 / P2-11 | 抽 `CanPairForResearchAgreementQuest`（含「至少一方解锁 RA 科技」「双方都没研完科技树」「目标未持有同类任务」）；`HasResearchAgreementTargetForQuest` / `HasTradeRouteToCityTargetForQuest` 改为零随机数存在性判断；抽样点收敛到 `DoStartQuest` 一处；`DoStartQuest`/`IsComplete` 补目标范围检查；Lua 入口加范围 + 有效性校验 |
| 7 | `0b83f34` Fix: let the whole team's allied city-states follow a ceasefire | P2-12 | 新增 `IsMinorAllyOfTeam`，按队伍而非按玩家收集盟友城邦 |
| 8 | `6aa7ffa` Fix: make the AidPointActions table the only source of aid-point prices | P2-3 / P3-24 / P3-30 | 表为唯一权威（缺行即禁用、价格只取 `DefaultCost`、不再读 `CostOption`）；`CvAidPointActions.h` 精简为 Type→enum；新增 `CvGame::ResetAidPointActions()` 并在 `CvGame::init` 调用；删掉 5 个已无读取方的 `SP_AID_POINT_COST_*` 选项；DDL 注释标注 `CostOption` 废弃 |
| 9 | `d5b596c` Feat: let the AI buy city-state denouncements on its own turn | P2-4 / P3-10 / Q1 | 删除「AI 谴责后立刻让城邦跟」；`DoAidPointDenounceSpend` 改为在 `DoCityStateAidPointAI` 里独立选目标（已谴责/敌意，或目标临近外交胜利 `IsPlayerNearDiploVictory`）、30% 概率门槛、走 `abPoolUsed` + 吞并保证金；新增 `m_aiTurnLastAidPointDenounce`（168 门控）+ Define `SP_AID_POINT_DENOUNCE_COOLDOWN=20`，AI 与人类共用冷却；新增 `InvalidateResearchAgreementQuestCache` 并在任务新增/完成/取消/重掷/清空处失效 |
| 10 | `3e250da` Fix: report permanent aid-point votes under their own source | P3-11 / P3-12 | 永久票从「奇观票」拆出单独票源行（新三语 Tag）；议会开会期间禁止购买永久票 |
| 11 | `5c58f29` Fix: read the trade-agreement route bonus from a define | P3-18 | 新增 Define `TRADE_AGREEMENT_ROUTE_GOLD_PERCENT=20` 与 `CvGlobals` getter、`CvGame::GetTradeAgreementRouteGoldPercent`、Lua `Game.GetTradeAgreementRouteGoldPercent`；DLL 两处与 SP 的 `TradeRouteHelpers.lua` 都改为读它 |
| 12 | `b2409d9` Perf: cache the per-policy happiness and aid-point sums | P3-28 / P3-29 / P3-23 | `GetLocalHappinessFromFaithPercent` 与援助点政策求和改为非序列化缓存，在 `processPolicies` 入口与 `uninit` 失效；修正误导性注释 |
| 13 | `e056949` Fix: push an empty string for a NULL aid-point action tag | P3-16 | `TextTag`/`HelpTag` 为 NULL 时压空串而不是 nil |
| 14 | `f373c96` Fix: drop the unused clear path of the permanent vote mask | P3-27 | `SetAidPointPermanentVote` 去掉永远为 false 的 `bValue` 参数 |
| 15 | `8b024eb` Fix: reject dead players in the hasten-congress aid-point entry | P3-4 / P3-5 | 四个 `Do*WithAidPoints` 入口 + 第五个 `DoHastenCongressWithAidPointsFromMajor` 补 `isAlive()` |
| 16 | `5b6f561` Cleanup: swap the two aid-point entry comments back into place | — | 拆提交时工具把两条注释互换，改回 |

副作用（有意为之，需知悉）：
- 删除 5 个 `SP_AID_POINT_COST_*` 选项后，SP 的 `DLL_Options.xml` 里对它们的 `<Update>` 已一并删除，`CSUA.sql` 的 `CostOption` 列已置 `NULL`；价格仍与改动前完全一致（20/50/10/20/50）。
- `CvCityStateUAClasses.cpp` 的建筑类大科点只在开关开启时按 active 计数，关闭时回到原版口径。

---

## 二、修复代码复审（子代理）裁决

22 项逐条复审结果：**21 通过 / 1 需修改 / 0 阻断**。

### 2.1 唯一需修改项（已修）

**F13「临近外交胜利 100% 买谴责」是死分支。**
`DoAidPointDenounceSpend` 允许对「未被本方谴责但临近外交胜利」的目标直接购买，但 `CvGame::DoMinorCivDenounceWithAidPoints` 的第一道业务校验是「付款方必须已谴责目标」，因此该分支永远失败。

处置：给成交函数加第四参数 `bRequirePayerDenounce`（默认 `true`，人类/Lua 路径保持原规则），AI 路径传 `false`——AI 为阻止对手外交胜利可以先买谴责，再自行决定是否公开谴责。同时修正了 `IsPlayerNearDiploVictory` 在「首个特殊会议之前」会触发 Debug 断言的调用。

### 2.2 复审提出、本轮一并修掉的观察（6 条）

| 观察 | 处置 |
|---|---|
| `DoHastenCongressWithAidPointsFromMajor` 漏 `isAlive()`（第五个 Lua 入口） | 已补（提交 15） |
| 科研协定任务缓存在 reroll / `EndAllActiveQuestsForPlayer` 两条清除路径未失效 | 已补（提交 9） |
| `processPolicies` 的 one-shot 早退会跳过缓存失效 | 失效语句移到函数入口（提交 12） |
| 第三方谴责通知仍会泄露「未相遇目标」的真名 | `{1}{2}` 都按 `TXT_KEY_UNMET_PLAYER` 掩码（提交 9） |
| 内容模组残留已死的 `CostOption` 配置（`DLL_Options.xml` 5 条 `<Update>`、`CSUA.sql` 值） | 已清理（提交 8 的配套改动） |
| `NewTableChanges.sql` 有一行 CRLF 被改成 LF，产生无意义 diff | 已恢复该行 CRLF，diff 只剩 5 行新增 |

---

## 三、修复项的自查结论（按六类问题）

1. **空值与越界**：新增的 5 个 Lua 入口全部有索引区间 + 存活校验；`DoStartQuest`/`IsComplete` 的 `NO_PLAYER` 路径改为提前返回；`GetNumBuildingClassActive` 加边界（Lua 可传任意索引）；`IsAidPointDenounceOnCooldown`/`SetTurnLastAidPointDenounce` 自带索引检查。
2. **联机不同步**：新增的随机数调用只出现在 `DoAidPointDenounceSpend`，其全部输入（谴责状态、approach、联盟票数、永久票掩码）都是同步状态，且 `DoCityStateAidPointAI` 有回合防重入；未新增 GameEvent 回调内的广播；序列化新增只有 `m_aiTurnLastAidPointDenounce`，读用 `MOD_SERIALIZE_READ_ARRAY(168, …)`、写用数组 `<<`，读写对称。
3. **效果与文本**：新增文本 `TXT_KEY_LEAGUE_OVERVIEW_MEMBER_DETAILS_PERMANENT_VOTE` 简中/繁中/英文各一条，占位符 `{1_Num}` 与 C++ push 顺序一致；贸易协定加成与 Tooltip 现在同源。
4. **原版接口**：没有删除或改名任何原版 Lua/C++ 接口。`DoMinorCivDenounceWithAidPoints` 增加默认参数，Lua 绑定仍按 3 参数调用；`SetAidPointPermanentVote` 去掉参数——该方法从未暴露给 Lua，无外部调用方。
5. **注释**：本轮新增注释全部英文（复审已全量 CJK 扫描）；修掉 3 处与实现不符的注释（估值缓存、`Cached-local-happiness`、`Aid point costs`），1 处错位文档注释归位，1 处落在错误函数上的旧文档注释删除。
6. **残余**：删掉 `iNumPlannedPlots`/`iNumPlannedSpecialists`、`GetSpecialistProviderBuilding` 的死门控、`ReleaseShared2DArray` 的不可达分支、5 个无人读取的成本选项、6 处 `CostOption` 配置；新增的 `SP_CITIZEN_REALLOC_AUDIT` 四处注册齐全、默认 0。

---

## 四、验证建议（实机）

1. **死任务（修复项 6）**：影响力 31、双方有 Education、**未互设使馆** → 不应再发布该任务；末期「双方都研完科技树」同理。
2. **任务奖励口径**：正常链路下双方各领一份奖励、城邦合计 120 影响力（作者已裁定该口径），确认与设计文档一致。
3. **建筑类计数（修复项 4）**：造一座同类过时建筑，开关开/关对比 Ragusa 快乐、Prague/Yerevan 产出、建筑大科点；再存读档确认计数不再跳变。
4. **公民分配（修复项 5）**：开 `SP_CITIZEN_REALLOC_PLANNED`，观察 `noAuto` 回合 AI 大城的专家不再被清空；把 `SP_CITIZEN_REALLOC_AUDIT` 置 1，检查 `CUSTOMLOG` 有无「left N unassigned citizens」告警。
5. **援助点价格（修复项 8）**：从 `CSUA.sql` 删掉「求和平」一行，确认 UI 不显示且 AI 不再购买（这才是「删行即禁用」）；价格仍应等于 40。
6. **城邦谴责（修复项 9）**：AI 是否改为「过回合时偶尔买」而不是「谴责当回合立刻买」；同一目标同一城邦 20 回合内无法二次购买（换另一个文明买也被挡）；让某文明票数逼近门槛，观察 AI 是否会为阻止其胜利而买谴责。
7. **联机双人**：永久票/应急提案/谴责/调停各点一次，确认两端状态一致、通知只出一条；同一城市存读档后对比快乐/产出（OOS 面）。
8. **编译**：按仓库规则先删 `BuildTemp\VS2022_CvGameCore_Expansion2ReleaseWin32`；用 `dumpbin /imports` 复核只导入 `MSVCP90/MSVCR90`。

---

## 五、遗留与建议（不阻塞发布）

1. ~~**谴责冷却没有暴露给 UI**：冷却中点击「买谴责」会静默失败。~~ **已修（`5655a43`）**：新增只读判定 `CvGame::CanMinorCivDenounceWithAidPoints` / `CanBuyPermanentVoteWithAidPoints` 并暴露为 `Game.CanMinorCivDenounceWithAidPoints(eMajor, eMinor, eTarget)` / `Game.CanBuyPermanentVoteWithAidPoints(eMajor, eMinor)`（不含点数与价格，只看规则）；`Do*` 改为先走 `Can*` 再扣费。UI 侧：谴责目标列表与消耗行都按 `Can*` 过滤（全部目标在冷却时整行消失），永久票行在议会会期内直接隐藏。
2. ~~**冷却粒度是「目标 × 城邦」**：同一文明换一个城邦可以再买一次对同一目标的谴责（理论上可叠加多次 -5%）。若要限制，可再加「每付款方每回合一次」的总闸。~~ **设计意图，不限制（`22a9a67`）**：作者确认这是「短期高成本施压、快速压制对手胜利」的核心玩法，并进一步要求 AI 也能一回合在多个城邦同时谴责同一目标。已实现：AI 在选定目标后可继续向其它城邦下单（每池仍只能花一次、并存保证金照旧），新增 Define `SP_AID_POINT_DENOUNCE_MAX_POOLS_PER_TURN`（默认 0 = 不设上限）供日后调平衡；人类侧本来就是手动逐城邦购买，未加总闸。
3. ~~**`DoStartQuest` 失败时仍会 push 任务**~~ **已修（`6a18ca6`）**：`CvMinorCivQuest::DoStartQuest` 改为返回 `bool`，在 15 处「目标解析不出来」的 `FAssertMsg` 之后补了 `if(目标 == NO_*/NULL) return false;`，`AddQuestForPlayer` 不再 push 失败的任务。顺带把原来「断言后直接解引用 `NO_RESOURCE`/`NO_BUILDING`/`NO_UNIT`/`NO_TECH`/`NULL` plot」的崩溃路径一并堵掉（这些在 Release 下断言不生效，原本会空指针）。`DoStartQuestUsingExistingData` 的两处调用忽略返回值（全局竞赛任务无目标数据，不受影响）。
4. **`GetMaxSpecialistSlotsInBuildingsForType` 未过滤「已满建筑」**：与经典搜索的 `IsCanAddSpecialistToBuilding` 有细微差别（不会多分配，仅排序可能不同）。属精度问题。
5. **`Fixed` 系列的中间提交可编译性**：16 个提交按依赖顺序排列，各组独立可 revert；但第 9 组（谴责重做）与第 8 组（价格）都改 `CvGame.cpp`，若单独 revert 第 8 组需手工处理同一文件的相邻 hunk。

---

*三审基于修复后的真实代码与两次独立复审结论整理；一审/二审报告保持原样不再改动。*
