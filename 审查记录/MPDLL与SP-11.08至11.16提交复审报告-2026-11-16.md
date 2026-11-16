# MPDLL × SP 11.08–11.16 提交复审报告

- 审查日期：2026-11-16
- 审查对象：
  - `CIV5MPDLL`（分支 `V11dev`）2026-11-08 至 2026-11-16 的 **25 个提交**，基线 `8ea2ddc`，工作树干净。
  - `SP V11`（分支 `main`）同区间的 **3 个提交**（`3f296bf`、`4a9baaa`、`504fed0`，均为文档/更新说明）。
- 改动规模：MPDLL 53 个文件，+3039 / −264；SP V11 2 个文件，+33 / −6。
- 关联仓库（仅作交叉核对，未纳入提交范围）：`V11/Super-Power-Remaking-of-World-Order`（SP 内容模组工作树）、`Civ5-MPDLL-API-INSTRUCTION`（API 说明库）。
- 审查重点（按用户指定）：空值/越界、联机不同步、效果与文本不符、删除原版接口、无用多余注释与中文注释、残余文本/变量未清理。
- 方法：按主题分 7 批独立复审（建筑类计数、公民分配性能、交易与政策、城邦任务与贸易协定、援助点代价接口、援助点杂项小修、世界议会与城邦外交），每批以 HEAD 真实代码逐行核对；P1 级结论由主线二次复核。

> **修订记录（2026-11-16）**：本报告已交子代理二审，二审裁决见同目录 `MPDLL与SP-11.08至11.16提交复审报告-二审报告-2026-11-16.md`。二审判定 P2-2、P2-7、P2-10 应降为 P3（理由见各条下的「二审意见」），本报告保留原编号以维持两份文档的可对照性。二审对 P2-1 的「数字全错」裁决经主线复核后**不成立**（二审误读了 `AIStrategiesTweak.xml` 相邻行的归属），本报告 P2-1 维持原值，详见二审报告末尾的主线复核补注。P2-4 已按二审意见收窄范围。

---

## 〇、结论摘要

**必须先修的两条 P1**：

1. **新增序列化字段复用了已发布的 DLL 版本号 168**（`788f66a`）——新 DLL 读 11-04 之后任何 168 存档都会整体错位，属坏档/联机崩溃级。
2. **城邦「科研协定任务」仍缺 RA 硬前提**（`9d38b6b` 触及同一函数但未修，旧审查报告已列为 P1）——缺使馆/缺 RA 科技/科技树走完时必产生 30 回合死任务，且阈值从 60 降到 30 后更常见。

**次高优先（P2）集中在四处**：

- **效果与文本不符**：贸易协定在 DoF 破裂后不撤销、城邦"调停停战"文案宣称非正式和约但实现写了正式和约、永久票显示为"奇观票"、SP 更新说明宣称"建筑类效果统计整合"但政策本地快乐仍统计过时建筑。
- **平衡/数值错误**：科研协定任务镜像后双方各领一份奖励（一次 RA 给城邦合计 120 影响力）；CSUA 三处 active 计数绕过新开关；公民计划分配在 `noAuto` 回合把非强制专家全降为闲人。
- **数据/逻辑双源**：援助点行动"存在性"由 DB 与 C++ 回退表两个来源决定，内容模组删行后 UI 消失但 AI 照常扣点；AI 谴责花费绕开"每池每回合一次"与吞并保证金。
- **潜在联机不一致**：建筑类 active 计数的"增量维护"与"读档重建"口径不同，读档后计数会跳变，两端重建时机不同即可产生快乐/产出 OOS。

**未发现**：中文注释违规、删除/改名原版 Lua 与 C++ 接口、枚举值插队导致既有值偏移、在 GameEvent 回调里重复广播、新增未门控的写状态不同步入口。SP V11 仓库的三个文档提交本身无代码风险，但更新说明与实现存在 3 处可定位的不符（见第七节）。

---

## 一、审查范围明细

### 1.1 CIV5MPDLL（25 个提交，按主题归组）

| 组 | 提交 | 主题 |
|---|---|---|
| A | `541e63d`、`707baea`、`98a13b0`、`36c63e0` | 建筑类计数（active counts）、空 2D 信息表共享只读零块 |
| B | `89be399`、`d03eb52` | 公民分配性能剖析与重写（含两个新 ModOption） |
| C | `308a825`、`25fa9dc`、`8db447b`、`f020fc4`、`81ad1e9`、`5c7b6da`、`cc71d69` | 互不侵犯估值、信仰幸福政策、联盟摘要文本、一次加-删往返、注释 |
| D | `bd699f0`、`9d38b6b`、`d7ff192` | 商路任务、科研协定任务流程、贸易协定 |
| E | `a9c427d` | 援助点通用代价接口（14 文件，+405） |
| F | `4cab1c9`、`7d2cc26`、`8ea2ddc`、`30bffd0`、`372a3d0`、`ed1e33a` | 援助点独特单位、行动数据搬迁、盟邦停火、强制 DoF、空运起点、待定交易图标 |
| G | `788f66a`、`ef3bdc2` | 援助点→世界议会永久票/紧急议案、城邦谴责与调停 |

> `f020fc4` + `81ad1e9` 是一次「新增后删除」的往返。已用 `git diff f020fc4^ 81ad1e9` 验证净改动为零、六处无残留，因此不计为问题（仅建议后续避免同类往返提交）。

### 1.2 SP V11（3 个提交）

| 提交 | 内容 |
|---|---|
| `3f296bf` | `1.城邦UA/海洋型.txt` 魁北克 UA 默默无闻加成 4% → 3% |
| `4a9baaa`、`504fed0` | `更新记录/SP11.0更新说明.txt` 改名为 `SP11.0更新说明.txt` 并大批补充条目 |

---

## 二、P1 问题（2 条）

### [P1-1] 新增序列化字段复用了已发布的 `MOD_DLL_VERSION_NUMBER = 168`，会读坏旧档

- 位置：
  - `CvGameCoreDLL_Expansion2/CustomMods.h:36`（`#define MOD_DLL_VERSION_NUMBER ((uint) 168)`）
  - `CvGameCoreDLL_Expansion2/CvPlayer.cpp:30953`（`MOD_SERIALIZE_READ(168, kStream, m_uiAidPointPermanentVoteMask, 0)`）、`CvPlayer.cpp:31932`（对应写）
  - `CvGameCoreDLL_Expansion2/CvVotingClasses.cpp:7629`（`MOD_SERIALIZE_READ(168, loadFrom, writeTo.m_eEmergencyProposalPlayer, NO_PLAYER)`）、`CvVotingClasses.cpp:7702`（对应写）
- 事实链：
  - 版本号 168 是 `3c24b09 "V68"`（2026-11-04）设定并打包发布过的；`git log -S"((uint) 168)" -- CustomMods.h` 只有这一处改动，之后直到 HEAD 未再升。
  - `git log 3c24b09..HEAD -- CustomMods.h` 只有 `541e63d`、`d03eb52` 两个提交改过该文件，均为新增 ModOption，**没有升版本号**。
  - 而 `788f66a`（11-16）新增了 `CvPlayer::m_uiAidPointPermanentVoteMask`（8 字节）与 `CvLeague::m_eEmergencyProposalPlayer`（4 字节），门控写的是 168。
  - 工作区内确有该期间的发布包：`backup-DLC/MP_MODSPACK_20261114_131353`（11-14 打包，晚于 `d03eb52`），其 DLL 版本号同为 168，但不含上述两个字段。
- 后果：
  - `MOD_SERIALIZE_READ(v, ...)` 的语义是「存档版本 ≥ v 就必须读」。新 DLL 读任何 11-04 之后、`788f66a` 之前构建（版本同为 168、无这两字段）的存档时，`CvPlayer::Read` 会从这里开始整体错位 8 字节，`CvLeague` 流会在末尾多读 4 字节吃掉后续对象的数据。
  - 表现为数值错乱、读档校验失败或联机中途崩溃；两边分别用改动前/后的 168 DLL 时，版本号相同会被判为兼容，联机存档交换同样会坏。
- 建议：

  ```cpp
  // CustomMods.h
  #define MOD_DLL_VERSION_NUMBER ((uint) 169)
  // CvPlayer.cpp / CvVotingClasses.cpp
  MOD_SERIALIZE_READ(169, ...)  // 两处读、两处写
  ```

  本仓库既有习惯是「升版本号 + 加字段」写在同一个提交里（见 `3c24b09`），本次应补齐。**这一条必须在发布任何 DLL 之前修掉。**

### [P1-2] 城邦「科研协定任务」仍无 RA 硬前提，必然产出死任务

- 位置：`CvGameCoreDLL_Expansion2/CvMinorCivAI.cpp:7723-7801`（`GetBestResearchAgreementTargetForQuest` 候选循环）、`CvMinorCivAI.cpp:5969-5978`（`IsValidQuestForPlayer` 的 RA 分支）
- 对照实现：`CvGameCoreDLL_Expansion2/CvDealClasses.cpp:581-605` 的 `TRADE_ITEM_RESEARCH_AGREEMENT` 硬条件（已亲自复核）：

  ```
  IsResearchAgreementTradingAllowed()（至少一方）
  HasEmbassyAtTeam()（双向）
  IsDoFAccepted()（双向）
  !IsHasResearchAgreement()
  双方都未 HasResearchedAllTechs()
  ```

- 问题：`9d38b6b` 加了「影响力 > 30、双方个人任务槽未满、排除同队、排除交战/未建交/互相谴责/UNFORGIVABLE/ENEMY/WAR/HOSTILE、排除已有 RA」，但**使馆、RA 科技、科技树走完这三条一条都没进发布条件**。DoF 由强制路径兜底、金币可靠期限内攒钱，这三条没有任何兜底。
- 后果：
  - 发布给「缺双向使馆」或「双方都没解锁 RA 科技」的组合时，AI 每 10 回合调用一次 `IsMakeOfferForResearchAgreementForced`，每次都在 `IsPossibleToTradeItem` 处失败并 `ClearItems`，任务到 30 回合期限结束都无法完成。
  - 后期「任一方已研究完所有科技」时任务永远无法满足。
  - 白占双方各一个个人任务槽 30 回合，城邦影响力/奖励落空，直接违反设计文档「可完成性优先」。
  - 阈值从 60 降到 30 后这类组合比旧版更常见。
- 建议（在候选循环 `veValidPlayers.push_back` 之前补）：

  ```cpp
  CvTeam& kPlayerTeam = GET_TEAM(GET_PLAYER(ePlayer).getTeam());
  CvTeam& kLoopTeam   = GET_TEAM(pLoopPlayer->getTeam());

  if(!kPlayerTeam.HasEmbassyAtTeam(kLoopTeam.GetID()) ||
     !kLoopTeam.HasEmbassyAtTeam(kPlayerTeam.GetID()))
      continue;
  if(!kPlayerTeam.IsResearchAgreementTradingAllowed() &&
     !kLoopTeam.IsResearchAgreementTradingAllowed())
      continue;
  if(kPlayerTeam.GetTeamTechs()->HasResearchedAllTechs() ||
     kLoopTeam.GetTeamTechs()->HasResearchedAllTechs())
      continue;
  ```

  该条在 `SP城邦任务-科研协定任务-审查报告-2026-11-14.md` 已列为 P1，本次 `9d38b6b` 触及同一函数但未处理，属**复发项**。

---

## 三、P2 问题（12 条）

### [P2-1] 科研协定任务镜像后双方各领一份奖励

- 位置：镜像 `CvMinorCivAI.cpp:1920-1927`；影响力结算 `CvMinorCivAI.cpp:2117`；额外奖励 `CvMinorCivAI.cpp:2121-2139`
- 问题：一次 RA 后 origin 与 target 各自的镜像任务都 `IsComplete`，各自 `ChangeFriendshipWithMajor(GetInfluenceReward())` 并各自领 `RewardGold/RewardCulture`。SP 配置为 `Friendship=60 RewardCulture=50`（`AIStrategiesTweak.xml:1177-1180`）。
- 后果：一次 RA 给该城邦带来**合计 120 影响力**，并给双方各发文化；若参与方带「完成任务影响力 +X%」类效果会再各乘一次。
- 建议：先确认设计口径。若沿用「单方任务」，给镜像任务打标记（如 `m_iData2` 置 1），在 `DoFinishQuest` 只发通知不发奖励；同时把镜像与双份奖励写进设计文档。

### [P2-2] 贸易协定在 DoF 破裂/谴责后不失效

- 位置：签订条件 `CvDealClasses.cpp:618-623`；效果只读旗标 `CvTradeClasses.cpp:2726-2731`、`2883-2888`；清除只在到期/`DoEndTradedItem`（`CvDealClasses.cpp:3954-3956`）
- 问题：TA 签订要求双方 DoF，但没有任何路径在 DoF 失效或谴责时撤销 `m_abTradeAgreement`；+20% 只看旗标。
- 后果：谴责甚至翻脸后双方商路仍吃「贸易协定」+20% 直到 30 回合自然到期，与「只有友谊国之间才有贸易协定」的设定与文本不符；AI 也会在已谴责对象身上继续吃加成。
- 建议：在 `SetDoFAccepted(false)` / `DoDenounceStatement` 路径里结束该 TA 交易项并 `SetHasTradeAgreement(otherTeam, false)`；不建议在 `GetTradeConnectionValueTimes100` 里每回合复核 DoF（高频）。
- **二审意见（拟降为 P3）**：11.0 更新说明并未承诺「DoF 破裂即失效」，原版所有交易项也都跑满期限；作为改进项保留，不阻塞发布。

### [P2-3] 援助点行动的「存在性」有两个真相来源

- 位置：`CvGame.cpp:12124-12195`（C++ 回退造价表 + `LoadAidPointActions`）与 `Lua/CvLuaGame.cpp:2369-2420`（UI 列表完全按 DB 行生成）
- 问题：`LoadAidPointActions` 先用 `GetAidPointActionDefaults` 播种再被 DB 覆盖，只要查询成功（哪怕 0 行）就置 `s_bAidPointActionsLoaded=true`，造价接口永远可用；而 `GetAidPointActions` 只返回 DB 里真实存在的行。
- 后果：内容模组少写一行（或想删掉某行动来禁用）时，UI 里没有它，但 AI 的 `DoAidPointRerollSpend` / `DoAidPointGiftUnitSpend` / `DoAidPointPeaceSpend` 仍能拿到回退造价并照常扣点。**内容模组无法真正禁用行动**；未装/未更新内容模组时玩家看到空列表，AI 却在用同一套点数。
- 建议：让「表里没有该 Type」成为唯一权威——`GetAidPointBaseCost` 在已加载且 Type 不在表中时返回 0，各 Spend 在 `iCost <= 0` 时跳过；或让 `GetAidPointActions` 在表为空时回退到默认表。

### [P2-4] AI 援助点花费绕过「每池每回合一次」与吞并保证金

- 位置：
  - `CvDiplomacyAI.cpp:22400-22401`（`DoAidPointDenounceSpend(ePlayer, NULL)`）与 `CvDiplomacyAI.cpp:26901-26923`（自建循环直接判 `GetEconomicAidPoints`）
  - 对照 `CvDiplomacyAI.cpp:26311-26318`、`26334-26367`（`GetAidPointPaymentMinor` 过滤 `pabPoolUsed` 并扣 `GetAidPointAnnexReserve`）
  - 永久票/应急提案：`CvDiplomacyAI.cpp:27033-27034` 已正确传入 `abPoolUsed`，但同样直接用 `GetEconomicAidPoints < iCost` 判定（`DoAidPointPermanentVoteSpend` 起始于 `:26927`）
- 问题（经二审修正后的准确范围）：
  1. **同池一回合花两次——仅谴责这一条**。`DoAidPointDenounceSpend` 被 `DoDenouncePlayer` 从外交陈述路径调用（与 `DoCityStateAidPointAI` 的 `DoTurn` 路径分离），传 `NULL` 自建循环，看不见 `DoTurn` 内的 `abPoolUsed` 局部数组，因此同一城邦的池可以在同一回合被「谴责 + 其它购买」各花一次，违反 `DoCityStateAidPointAI` 顶部注释声明的「一个池每回合最多参与一次购买」。永久票/应急提案已在 `DoCityStateAidPointAI` 内传入 `abPoolUsed`，不受此影响。
  2. **吞并保证金——三个新函数都绕过**。谴责/永久票/应急提案都直接用 `GetEconomicAidPoints(eMajor) < iCost` 判断而不走 `GetAidPointPaymentMinor`，因此都不扣 `GetAidPointAnnexReserve`（`CvDiplomacyAI.cpp:26345-26350` 的「吞并优先于其它一切购买」对它们不生效），AI 会把已攒到吞并门槛的池花掉，`CanMajorBuyout` 永远攒不够。
- 后果：可复现的平衡与逻辑错误（对联合国大战略 + 奥地利式吞并的 AI 尤其明显）。
- 建议：谴责花费并入同一套 `abPoolUsed`（或记录「本回合想谴责的目标」在援助花费阶段统一执行）；三个新函数改走 `GetAidPointPaymentMinor(..., /*bHonorReservation*/ true)` 以保留吞并保证金。

### [P2-5] 「只是协议停战、不等同于正式和平条约」的文案与实现不符

- 位置：实现 `CvGame.cpp:11922`（`GET_TEAM(eMajorTeam).makePeace(eTargetTeam, true, false, eMajor)`）、`CvTeam.cpp:1724-1727`（`SetTurnMadePeaceTreatyWithTeam`）、`CvTeam.cpp:1729-1745`（计入 `NumWarPeacesCompleted`，Hanoi UA 用）；文案 `V11/.../TextInfos_en_US.xml:20902`、`TextInfos_zh_CN.xml:19372`、`TextInfos_zh_Hant_HK.xml:19178`
- 问题：三语 tooltip 明确写「这只是协议停战，不等同于正式和平条约」，但实现走的是原版 `makePeace`，会写入 `TurnMadePeaceTreatyWithTeam` 并触发「完成一次和平条约」统计。
- 后果：玩家买到的是正式和约——立刻再宣战会被判为撕毁和约（`CvTeam.cpp:1370-1381` 置 `HasBrokenPeaceTreaty`，附带外交惩罚），还会给 Hanoi 玩家刷「和约完成数」。
- 建议：二选一——改文案承认这是正式和约（说明 10 回合条约与撕约惩罚），或实现一条不写 `TurnMadePeaceTreatyWithTeam` 的停战路径（需同时处理 `DoNowAtWarOrPeace`、盟邦跟随等副作用）。

### [P2-6] 建筑类 active 计数的「增量维护」与「读档重建」口径不一致

- 位置：增量 `CvCity.cpp:8710-8713`（`processBuilding` 的 `iChange` 直接累加）；重建 `CvCity.cpp:23813`（用 `GetCityBuildings()->GetNumBuilding`）；口径差异来源 `CvBuildingClasses.cpp:5134-5137`（`CITY_MAX_NUM_BUILDINGS() <= 1` 时 `GetNumBuilding = max(real, free)`）；两条写入路径 `CvBuildingClasses.cpp:5479`、`5717`
- 问题：真实副本与免费副本各调用一次 `processBuilding`，增量计数把两份都加上；重建走 `max(real, free)` 只算一份。同一种建筑同时存在免费与真实副本时，两条路径相差 1。
- 可达路径：`acquireCity` 先发免费建筑（`CvPlayer.cpp:3372`、`3394`）再转移真实建筑（`CvPlayer.cpp:3449`）；`GLOBAL_CITY_SCALES` 下 `UpdateScaleBuildings` 也会按目标值重设免费数量（`CvCity.cpp:25416`）。
- 后果：计数**会在读档后从 2 跳回 1**；直接消费方（Ragusa 快乐、Prague/Yerevan 产出修正、建筑大科点，开关开启时还有政策/信条产出、快乐、旅游）随存读档变化。联机下「第一次触发重建」的时机依赖本端调用史，若一端已重建、另一端未重建，同一城市在两端算出不同快乐/产出，属**潜在 OOS**。
- 建议：重建改为累加 `GetNumRealBuilding + GetNumFreeBuilding`，或增量路径只在 `GetNumBuilding()` 真变化时按差值计数；也可在 `CvCity::read` 末尾显式 `m_bActiveBuildingClassCountsValid = false`，从设计上消除对加载顺序的依赖。

### [P2-7] CSUA 三处 active 计数绕过本批自己新增的开关

- 位置：`CvCity.cpp:12997`（Ragusa 建筑类快乐）、`CvCity.cpp:13757`（Prague/Yerevan 建筑类产出修正）、`CvCityStateUAClasses.cpp:2826`（建筑类大科点）
- 问题：`98a13b0` 把这三处的 `GetNumBuildingClass` 换成 `GetNumBuildingClassActive`，外层只有恒真的 `#if defined(MOD_SP_UNIQUE_CITYSTATE)` 与 NULL 判定，**没有 `MOD_SP_BUILDING_CLASS_COUNT_ALL_TYPES` 门控**；而同批的 `707baea` 对完全同类的语义变化（政策/信条/旅游「过时建筑是否计入」）全部用新开关门控且默认关闭。
- 后果：同一语义改动一半默认生效、一半默认不生效。只要启用 CSUA（SP 内容模组的默认状态），即使 `SP_BUILDING_CLASS_COUNT_ALL_TYPES=0`，城市拥有同类过时建筑时这三项数值也会变小——无提示的平衡改动。
- 建议：给三处加同一开关门控（`MOD_SP_BUILDING_CLASS_COUNT_ALL_TYPES ? GetNumBuildingClassActive : GetNumBuildingClass`）；若确实要「无条件排除过时建筑」，则应把 `707baea` 的 5 处也改成无条件，并在提交说明与 SP 更新说明里明确。
- **二审意见（拟降为 P3）**：SP 内容模组 `Gameplay/XML/DLL_Options.xml:413-414` 已把 `SP_BUILDING_CLASS_COUNT_ALL_TYPES` 置 1，发布配置下三处 CSUA 与开关开启路径一致，**不产生可见后果**；保留为代码一致性/可维护性问题。注意：若玩家或整合包把该开关关掉，不对称立刻暴露。

### [P2-8] 开关开启时，「政策建筑类快乐」仍统计过时建筑

- 位置：`CvCity.cpp:12897-12902`（`aBuildingsHere` 取自 `GetOwnedBuildings()`，后者只判 `GetNumBuilding > 0`，不过滤过时）、`CvCity.cpp:12938-12947`（开关只用于取消「必须是本文明该类建筑」）、`12956`（按实例数累加）；对照同函数信条路径 `CvCity.cpp:12855`
- 问题：开关名与注释都声明「count every **non-obsolete** building of the class」，信条/旅游/`CvPlayer::processPolicies` 都按非过时计数，唯独这段遍历全部拥有建筑。
- 后果：同一条政策的建筑类快乐会比信条路径多算过时建筑；**且这与 SP 更新说明「三.5 建筑类效果统计整合：政策、信条、城邦UA 现在会统计该类下所有未过期的建筑」直接矛盾**（见第七节 S-1）。
- 建议：在循环里跳过 `GET_TEAM(getTeam()).isObsoleteBuilding(eBuilding)`，并把实例数改为按类取 active 计数（避免按多类型重复求和）。

### [P2-9] 公民计划分配：`noAuto` 回合会把非强制专家全降为闲人

- 位置：`CvCityCitizens.cpp:1893`、`1987`（专家候选集整体放在 `!IsNoAutoAssignSpecialists()` 之下）；经典回退分支 `CvCityCitizens.cpp:1530`（AI 城市仍补专家）；`DoTurn` 周期性置 `noAuto` 于 `CvCityCitizens.cpp:327`、`419`
- 问题：经典路径在 `noAuto` 时仍会为 AI 城市补专家（只是不降级），计划路径直接跳过专家分配。
- 后果：地格已满的大城在 `noAuto` 回合把全部非强制专家降为闲人，GPP 与专家产出间歇丢失；与经典路径行为不一致。
- 建议：计划路径按经典语义处理 `noAuto`（只增不减），并补一条双路径对照断言。
- **优先级提示（按二审意见上调）**：SP `DLL_Options.xml:414/418` 把 `SP_CITIZEN_REALLOC_PLANNED` 与 `SP_BUILDING_CLASS_COUNT_ALL_TYPES` 都置 1，本条是**线上默认行为**而非可选项；`DoTurn` 周期约 8 回合触发一次，建议排在 P2 修复的前列。

### [P2-10] 公民计划分配：专家排序不等价于经典路径，且与 `SP_SPECIALIST_AI_BY_TYPE` 耦合

- 位置：`CvCityCitizens.cpp:1909-1914`（计划路径无条件套用「按类型 + 城市槽位总量」偏置）、`1195-1200`（新偏置）、`1202`（按专家类型索引破平）；对照经典 `1144-1153`（按单个建筑槽数加偏置）、`1149`（按建筑索引破平）
- 问题：计划路径固定用 `GetAIBestSpecialist()` 的 `((iSlots-1)*iValue*10)/100`，`iSlots` 是全城该类型槽位总和；经典路径按每个建筑自己的 `GetSpecialistCount()` 加偏置。于是只开 `SP_CITIZEN_REALLOC_PLANNED`、`SP_SPECIALIST_AI_BY_TYPE=0` 时排序也会从「逐建筑」切到「逐类型」。
- 后果：多建筑/多槽位场景排序结果改变（例：同类型分散在 3 个 1 槽建筑，经典偏置 0、新公式 +20%），与提交说明「keeping the old slot bias and tie-break」「same assignment as DoReallocateCitizens()」不符；两个选项无法独立对照测试。
- 建议：计划路径按 `MOD_SP_SPECIALIST_AI_BY_TYPE` 分支选择估值，关闭时复刻经典排序；至少修正提交说明与该处注释。
- **二审意见（拟降为 P3）**：SP `DLL_Options.xml:417-418` 把 `SP_SPECIALIST_AI_BY_TYPE` 与 `SP_CITIZEN_REALLOC_PLANNED` 同时置 1，发布配置下计划路径的估值口径正是 `GetAIBestSpecialist` 那一套，两开关「耦合」不产生可见差异；保留为开关独立性问题。

### [P2-11] Lua 强制发布任务时，RA 任务会在 `NO_PLAYER` 上越界

- 位置：入口 `Lua/CvLuaPlayer.cpp:7740` → `CvMinorCivAI.cpp:4941-4967`（`AddQuestForPlayer` 不校验任务有效性）；越界点 `CvMinorCivAI.cpp:1905-1913`（`DoStartQuest`）、`CvMinorCivAI.cpp:920-928`（`IsComplete`）
- 问题：Lua 公开 API 直接调 `AddQuestForPlayer`；若玩家槽位已满或选不出 RA 目标，`GetBestResearchAgreementTargetForQuest` 返回 `NO_PLAYER`，`DoStartQuest` 仅 `FAssertMsg` 便执行 `GET_PLAYER(eTarget).getCivilizationShortDescriptionKey()`；`IsComplete` 对 `m_iData1` 同样直接 `GET_PLAYER`。Release 下 `FAssert` 不中断。
- 后果：模组/脚本或异常存档可触发 `GET_PLAYER(-1)` 越界读（崩溃或读到错乱对象）。旧报告已提过，本次未修。
- 建议：`DoStartQuest` / `IsComplete` 的 RA 分支开头加 `if(eTarget < 0 || eTarget >= MAX_MAJOR_CIVS) return;`；`AddQuestForPlayer` 对 `eType` 补一次 `IsValidQuestForPlayer`。

### [P2-12] 调停停火只处理「双方玩家本人」的盟友城邦，队友的盟友城邦仍在打

- 位置：`CvGame.cpp:11947`、`CvGame.cpp:11953`、`CvGame.cpp:11961-11970`
- 问题：停火循环判断的是 `pAllyAI->IsAllies(eMajor)` / `IsAllies(eTarget)`，只认这两个具体玩家。若 eMajor 与队友 T 同队，T 的盟友城邦同样因同盟对 eTargetTeam 宣战，但其 `m_eAlly` 是 T 不在收集集合中；eTarget 一侧同理，第二段「盟友城邦两两停战」也漏掉这些城邦对。
- 后果：组队联机/任何 team 局里，主停火生效后仍会出现「本方队友的盟友城邦继续和对方及对方盟友城邦交战」，与提交说明「both sides' allied city-states」不符。
- 建议：按「队」而非按「玩家」收集盟友城邦（遍历同队成员，判断 `IsAllies(eMember)`）。

---

## 四、P3 问题

### 4.1 空值与越界

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| P3-1 | `CvCity.cpp:23794`、`Lua/CvLuaCity.cpp:2404-2416` | 新 Lua API `City:GetNumBuildingClassActive` 只拦 `NO_BUILDINGCLASS`，不拦 `< -1` 或 `>= 类别数`，直接越界读 vector（旧 `GetNumBuildingClass` 同病，但本次新增了新对外接口） | getter 内加 `[0, size())` 检查，Lua 侧同样校验 |
| P3-2 | `CvDatabaseUtility.cpp:186` + `CvImprovementClasses.h:226/228/230/232/236`、`CvBuildingClasses.h:284/287/562/564/571/583/586` | 表已指向 `PAGE_READONLY` 共享块，访问器仍返回非 const `int*`；下游模组一旦写入会 access violation，崩点远离写入点（本仓库内已确认运行期只读） | 被共享的访问器改返回 `const int*`，并在 `CvDatabaseUtility.h` 写明契约 |
| P3-3 | `CvUnit.cpp:8733-8735` | `eCityOwner == NO_PLAYER` 被判为「友好空运起点」，默认值方向反了；后一个 `eCityOwner == eUnitOwner` 分支与前一句基本冗余。**二审判为误报**：`CvCity` 在整个生命周期内恒有 owner，该分支不可达（降为代码整洁问题） | `NO_PLAYER` 直接 `return false` |
| P3-4 | `CvGame.cpp:11985-11987`、`12026-12028`、`11785-11791`、`11913-11921` | 四个 `DoMinorCiv*WithAidPoints` 入参只校验 ID 区间，缺 `GET_PLAYER(eMinor).isAlive()`；Lua 公开 API（`CvLuaGame.cpp:97-100`）可对已灭亡城邦买票/买提案位/谴责/调停 | 四入口加存活校验（AI 侧 `CvDiplomacyAI.cpp:26907` 等处已有） |
| P3-5 | `CvGame.cpp:11893-11904` | 调停入口只校验 eMajor 索引范围，未校验存活；未使用玩家槽的 `getTeam()` 可能为 `NO_TEAM`，随后 `GET_TEAM(NO_TEAM)` 有越界风险 | 补 `isAlive()`；这是该 Lua 入口既有问题，本次新增循环同样依赖该团队 ID |

### 4.2 联机与确定性

- **P3-6** `CvCityCitizens.cpp:1839-1840` 注释声称「per-turn static yield cache」，但 `GetPlotValue`（`:522`）/`GetSpecialistValue`（`:1263`）读的是实时食物率，`SetWorkingPlot`（`:2184`/`2233`）会改变它；计划路径在分配前一次性估值，与经典逐公民动态估值不等价。结果确定（不 desync），但与注释及提交说明不符。
- **P3-7** `CvGame.cpp:11842-11847`、`11876-11879`：城邦谴责的第三方通知只判断「见过城邦或见过目标」之一，且直接用城邦真名；原版 `DoDenouncePlayer`（`CvDiplomacyAI.cpp:22344-22358`）会把未相遇一方替换成 `TXT_KEY_UNMET_PLAYER`。当前实现向只见目标、未见过该城邦的玩家泄露城邦名字。
- **P3-8** `CvMinorCivAI.cpp:5975`+`1907`（RA）、`5737`+`5745`+`1694-1697`（商路任务）：校验与发布各抽一次目标选择随机数，新商路任务的水库抽样是「每候选城市抽一次」（`7856-7858`），一次校验可能消耗几十次同步随机数。各端消耗一致所以不 desync，但浪费随机数、日志目标与校验目标可能不一致。
- **P3-9** `CvMinorCivAI.cpp:1924-1926`：镜像唯一跳过条件是「目标已持有该城邦的 RA 任务」，此时目标不被要求也不领奖、AI 也不再被推动，但发布校验仍认为合法（旧报告 P3 未修）。
- **P3-10** `CvDiplomacyAI.cpp:21874-21905`：`IsResearchAgreementQuestWithPlayer` 的每回合缓存若在同一回合内任务完成/新发布，会返回旧值；当前只影响「已完成任务还能多弹一次强制 DoF/RA」，未见 desync 风险，但若将来用于改状态的路径需按事件失效。

### 4.3 效果与文本不符

| # | 位置 | 问题 |
|---|---|---|
| P3-11 | `CvVotingClasses.cpp:4008`、`4065-4071`；`CvGame.cpp:12007-12009` | 永久票实现为 `m_iExtraLeagueVotes +1`，议会总览把它整体记到「世界奇观票」票源下；通知却写「your United Nations vote is permanently +1」，而该票在联合国成立前（世界议会阶段）就能买。建议拆独立票源行或改中性文案 |
| P3-12 | `CvGame.cpp:11978-12015` | 永久票可在议会**开会期间**购买，但 `Member::iVotes` 已在 `StartSession` 分配完毕（`CvVotingClasses.cpp:6220-6225`），本会期不生效，通知却说「permanently +1」。建议开会期间禁用或改文案为「从下次会期起 +1」 |
| P3-13 | `AllText_zh_CN.xml:474-476`、`AllText_zh_Hant_HK.xml:476-478` | 中文世界银行摘要写「所有文明获得结息」，实现是 `!isMinorCiv() && !isBarbarian()`（`CvPlayer.cpp:5477`）；英文文本并未这么写，属中文翻译扩大范围 |
| P3-14 | `AllText_en_US.xml:483-485`（及 zh_CN:483-485、zh_Hant_HK:485-487）；实现 `CvUnit.cpp:9820-9821` | IMO 禁掠文案写「ocean 海洋国际商路」，代码用 `isWater()`（含海岸/湖泊）。文案改「水上」或代码改 `isOcean()` |
| P3-15 | `CvVotingClasses.cpp:5929-5934` | WHO 摘要的两段文案被 `if (iWHOFoodConsumptionModifier != 0)` 一起控制；若某决议只设 `WHOSanitationFoodKeptPercent`，sanitation 效果会静默不显示。当前数据（-10/10）不触发 |
| P3-16 | `Lua/CvLuaGame.cpp:2390-2396` | `TextTag`/`HelpTag` 为 SQL NULL 时向 Lua 压 nil，而 SP 的 `GetAidSpendRow`（`CityStateDiploPopup.lua:909-910`）直接参与字符串拼接会抛 Lua 错、整块刷新中断。表结构允许 NULL（`DDL_Policies.sql:10-11` 未加 NOT NULL） |
| P3-17 | `CvGame.cpp:11801-11822` | 城邦谴责扣费在 `:11799`，但影响力扣除只对 `iInfluence > 0` 的城邦生效；目标对所有已相遇城邦影响力都 ≤ 0 时什么都改、20 点照扣。建议先累计 `iTotalLoss`，为 0 时退款并返回 false |
| P3-18 | `CvTradeClasses.cpp:2730`、`2887`；SP `TradeRouteHelpers.lua:25-29` | 贸易协定的 +20% 在 DLL 两处、Lua 一处各硬编码一次，缺 DB/define 定义，调平衡要改三处，容易 UI 与实际不一致 |
| P3-31 | `CvCity.cpp:12737`、`13009`；缓存写入点 `CvCity.cpp:2654-2663` | 「信仰→本地快乐」的换算率取 `GetFaithPerTurn(true)`（静态信仰缓存），而 `doAdoptPolicy()` 末尾只调 `updateYield()`（`CvPlayer.cpp:6218-6234`）不刷新城市静态信仰，所以采用政策/信条后到下次城市产出重算前反馈项用旧值（通常 0~2 点）。不建议直接改 `GetFaithPerTurn(false)`（会经 `UpdateCityYieldFromYield` 回到 `GetLocalHappiness` 形成环）；可在政策/信条变化后显式重算相关城市的 `UpdateCityYields(YIELD_FAITH)` |
| P3-32 | `CvCity.cpp:12781-12793`（公式）、`13011-13036`（上限裁剪） | 反馈抵消的定点公式假定「信条把 R% 的 `GetLocalHappiness()` 转成信仰」，但 `UpdateCityYieldFromYield()`（`CvCity.cpp:8985`）实际用的是**裁剪后**的本地快乐；接近本地快乐人口上限的城市会多扣 `R × 被裁掉的部分`（通常 0~2 点）。公式里改用 `min(H0 + 项, cap)` 参与反馈项即可 |

### 4.4 注释与残留

| # | 位置 | 问题 |
|---|---|---|
| P3-19 | `CvDatabaseUtility.cpp:213-215` | `ReleaseShared2DArray` 的 `if(kShared.iRefs == 0) return true;` 分支不可达（归零时条目已移除），是误导性死代码；同提交说明还宣称「harden the refcount」。建议删除或改成 `CvAssertMsg(false, ...)` |
| P3-20 | `CvCityCitizens.cpp:1922-1923` | `iNumPlannedPlots`、`iNumPlannedSpecialists` 只增不减地写入（`1985`、`1980`/`1992`）从未读取，属无用变量 |
| P3-21 | `CvBuildingClasses.cpp:4953-4955` | 新增 `GetOwnedBuildings` 插在 `Uninit()` 与 `Reset()` 之间时，把 `Reset()` 的文档注释「Reset status arrays to all false」留在了它头上；真正的 `Reset()`（`:5001`）反而没注释 |
| P3-22 | `CvCityCitizens.cpp:3033-3041` | `GetSpecialistProviderBuilding` 新增的 `MOD_SP_SPECIALIST_AI_BY_TYPE` 条件是死条件（`iFreeSlots > iBestFreeSlots` 已排除已满建筑），注释却暗示两分支有差异 |
| P3-23 | `CvPlayer.cpp:37429` | 注释写「Cached-local-happiness percent」，但函数每次实时遍历全部政策求和、没有缓存，与紧邻真正缓存的 `GetGlobalHappinessFromFaithPercent` 形成误导 |
| P3-24 | `CvGame.h:629-631` | 旧的 `// Aid point costs for the spending actions above (0 = disabled)` 紧接新注释且已不准确（这些方法现在只返回基础价），属注释残留 |
| P3-25 | `CvGameCoreDLLPCH.h:87` + `CvCityCitizens.cpp:479/495/1733/1742/1773` | `AI_PERF_FORMAT_NESTED` 只让 `cvStopWatch` 变 inert，`CvString::Format(...)` 与 `getCivilizationShortDescription()` 仍无条件执行；提交说明「timers stay inert」不准确，在性能提交里给联机回合加了常驻小开销 |
| P3-26 | `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql:175-179` | `5c7b6da` 提交标题「text change」无信息量；实际只删除了一句重复注释。建议写明改了什么 |
| P3-27 | `CvPlayer.cpp:15644-15653` | `SetAidPointPermanentVote(..., false)` 的清除分支无任何调用点、也未暴露给 Lua，属未接线的半成品 API |

### 4.5 性能（影响联机回合时间）

- **P3-28** `CvPlayer.cpp:37430-37447`（调用点 `CvCity.cpp:12731`）：`GetLocalHappinessFromFaithPercent()` 每城每次全量遍历 `GC.getNumPolicyInfos()`（SP 下数百条），而它位于 `GetLocalHappiness()` 热路径内。建议照 `GlobalHappinessFromFaithPercent` 的做法在 `processPolicies` 里增量维护。
- **P3-29** `CvPlayer.cpp:15656-15674`、`15700-15733`：`GetAidPointCostModifier/QuestReward/ContestReward` 每次询价全量扫描政策表；`DoCityStateAidPointAI` 每回合对每个城邦多次询价，SP 政策数百条 × 41 城邦是数万级查表。建议按回合缓存或在政策变更时增量维护。
- **P3-30** `CvMinorCivAI.cpp:7835-7858`：`GetBestTradeRouteToCityTargetForQuest` 对「每个玩家 × 每个目标城市 × 己方每个城市」做含完整寻路的 `CanCreateTradeRoute`，而它被候选枚举、镜像校验、任务重掷多处调用。建议先按距离/已有商路粗筛，或按回合缓存「可到达城市集合」。

### 4.6 口径与设计存疑（不进问题清单，需策划确认）

1. `308a825` 的净额估值：`GetNonAggressionPactValue` 返回 `bFromMe ? net : -net`，而 `GetDealValue` 对「我方给出」的项再乘 -1，最终 NAP 对成交易值的贡献恒为 `-net`、与谁给出无关；`iValueImOffering`/`iValueTheyreOffering` 已不再表示「我方付出/对方付出」，恰好与「咨询外交官」面板写反的标签互相抵消。建议补注释明确约定。
2. `25fa9dc` 新增本地快乐进入 `GetLocalHappiness()` 后也会被 `GetCorruptionScoreFromLocalHappiness()`（`CvCity.cpp:25623-25626`）计入腐败分数；若同时存在「腐败分数→信仰」与「本地快乐→信仰」两条信条，会形成定点公式未覆盖的弱反馈环（量级 ~1e-4）。
3. `ef3bdc2` 的城邦「谴责」只是全城邦 -5% 影响力 + 通知，引擎里城邦没有持久「被谴责」状态；若设计要求真实影响交易/边境，则功能未实现。
4. AI 抢到应急提案位后若提不出议案，可能让世界议会一直不开会（`CheckStartSession` 只要有人 `CanPropose` 就不开会，`CvVotingClasses.cpp:6200-6216`）。
5. 人类可被第三方花 40 点强制停战且毫不知情（`DoMinorCivPeaceWithAidPoints`）。建议确认是否应给被强制方通知/拒绝判定。

---

## 五、六类专项核查结论

### 1. 空值/越界
**结论：新增的 Lua↔C++ 入口在参数校验上整体做得不错，但 getter 与遗留分支仍有 5 处越界面（P2-11、P3-1~P3-5）。**
- 已确认安全：`GetBestTradeRouteToCityTargetForQuest` 只返回合法指针或 NULL；`HasTradeRouteToCity`、`IsComplete`、`IsObsolete`、`DoFinishQuest` 对 plot/城市全判空，且 `GC.getMap().plot(-1)` 返回 NULL；`4cab1c9` 的 `GC.getUnitInfo`/`GC.getUnitClassInfo` 先判 NULL、`eUnit` 先做范围校验；四个 `DoMinorCiv*WithAidPoints` 都做了三段 ID 区间校验；`CvLeague::CanClaimEmergencyProposal` 自行复核成员/权限；`25fa9dc` 的定点公式分母在 `p>0、R>0` 保证下恒 > 0，无除零。
- 风险集中在：Lua 单端可传任意索引的 getter（`GetNumBuildingClassActive`）、无主城市被当成合法空运起点、四个援助点入口缺存活校验、以及 `NO_PLAYER` 只 `FAssert` 后继续 `GET_PLAYER(-1)` 的遗留路径。

### 2. 联机不同步
**结论：未发现新增的确定性破坏，但存在 1 处潜在 OOS 与 3 处确定性冗余（P2-6、P3-8~P3-10）。**
- 已确认安全：
  - 所有会写全局状态的人类入口（永久票 `CityStateDiploPopup.lua:1101`、应急提案 `:1111`、谴责/和平 `:1980`/`:1982`、送兵 `:1976`）都走 `SendAndExecuteLuaFunction`，实参只用显式玩家/城邦/单位 ID，不依赖 `getActivePlayer()` 或 UI 端计算值。
  - 本区间**没有新增 GameEvent 回调**，不存在「回调内再广播 → 双倍叠加」。
  - `ed1e33a` 只是本机置 `GameData_DIRTY_BIT`（`CvDealClasses.cpp:2337-2345`、`2493-2498`），UI 为单端本地行为，不需要也不能广播；`CvDeal*` 先拷贝再 `erase`，无迭代器失效。
  - 新增的非序列化缓存（`IsResearchAgreementQuestWithPlayer` 的回合缓存 `CvDiplomacyAI.h:1499-1503`、`m_bActiveBuildingClassCountsValid`）都不进存档，不改变两端流结构。
  - 随机数：任务抽签全部走 `getJonRandNum` 且只存在于确定性 AI 路径；镜像由同一随机序列驱动、带 `eForcedTarget` 防二次镜像。
  - `308a825` 全整数运算、无新增随机数调用；AI 援助点花费只依赖存档态。
- 需重点关注：P2-6 的 active 计数「重建时机依赖本端调用史」是本次唯一的真实 OOS 面。

### 3. 效果与文本不符
**结论：文本体系（三语齐全、占位符与 C++ push 顺序匹配）做得扎实，问题集中在「文案承诺 ≠ 实现行为」共 6 条（P2-2、P2-5、P2-8、P3-11~P3-15）。**
- 已核对匹配：新商路任务的 `{1}`=城市名、`{2}`=城邦名（`DoStartQuest` push 顺序，SP `TextInfos_zh_CN.xml:20133-20157`）；`TXT_KEY_NOTIFICATION_CITY_STATE_DENOUNCED*` 系列、World Bank `{1_Rate}{2_RouteRate}{3_Turns}`、WHO `{1_Food}{2_Kept}`、IMO 各占位符个数与顺序全部吻合；`25fa9dc` 的 5% 全局 / 每 10 点信仰 +1 本地快乐与数据侧 `Policies.xml:251-252`、三语帮助文本一致；`Quests.xml` 5 个新图标 + 1 个新行图标在 SP `IconAtlases.xml:1856-1886` 全部存在；MPDLL 行 `<Enabled>false</Enabled>` 靠 SP `AIStrategiesTweak.xml:1201-1204` 的 `Update Enabled="1" Friendship="25" RewardGold="50"` 生效，与 C++ 奖励口径一致。
- 不符要点：贸易协定 DoF 失效不撤销、调停停战实为正式和约、政策建筑类快乐含过时建筑、永久票显示与通知错源、中文世界银行「所有文明」、IMO「海洋」vs `isWater()`。

### 4. 删除原版接口
**结论：未发现删除/改名任何原版 C++ 或 Lua 接口，也未发现枚举值插队导致既有值偏移。**
- `CvLuaGame`/`CvLuaPlayer`/`CvLuaCity`/`CvLuaDeal` 全部只新增方法，没有删除或改名既有暴露项。
- 新增枚举一律追加在原版枚举末尾、`NUM_*` 之前：`MINOR_CIV_QUEST_TRADE_ROUTE_TO_CITY` = 37（`CvMinorCivAI.h:97`，与 `Quests.xml:570` 的 `<ID>37</ID>` 一致）、`DIPLO_STATEMENT_TRADE_AGREEMENT_OFFER`（`CvEnums.h:135`）、`DIPLO_MESSAGE_TRADE_AGREEMENT_OFFER`（`CvEnums.h:420`）、`AID_POINT_ACTION_*`。`TRADE_ITEM_TRADE_AGREEMENT` 早已存在于枚举中（`CvDealClasses.h:30`），本次只是启用。
- 唯一「默认改变原版行为且未加开关」的是 `372a3d0`：允许从盟友城邦城市空运，只要加载本 DLL 就生效，其他基于 MPDLL 的内容模组无法关闭。建议加 `SP_ALLIED_CS_AIRLIFT` 之类开关并双层注册；其注释声称的「开放边境」条件实际未校验（见 P3-3）。

### 5. 中文注释 / 无用注释
**结论：25 个提交的 `+` 行全部为 ASCII/英文，未发现中文注释违规（MPDLL 约定：注释一律英文，VC9 按 GBK 解析会误报）。**
- 无被注释掉的旧代码块、无调试 `printf`/`OutputDebugString`。
- 但发现 7 处注释与实现不符或为死代码：P3-6、P3-19、P3-21、P3-22、P3-23、P3-24、P3-25。

### 6. 残余文本 / 变量未清理
**结论：新功能的主链路都已接线，无孤儿文本 Tag；但存在 2 处「加了没接线」与 1 处死开关。**
- `7d2cc26` 搬迁后 DLL 仍保留 `AidPointActions` 建表与 `Policy_AidPointCostModifiers`，只删了 9 条 INSERT，无孤儿表；DLL 不含 SP 侧 `TXT_KEY_POP_CSTATE_AID_*`，文本全在 SP 三语文件，符合「MPDLL 提供功能、SP 提供内容」的分工。
- 新增 ModOption `SP_BUILDING_CLASS_COUNT_ALL_TYPES`、`SP_SPECIALIST_AI_BY_TYPE`、`SP_CITIZEN_REALLOC_PLANNED` 均四处齐全（`CustomModOptions.xml` + `CustomMods.h` 宏/声明 + `CustomMods.cpp` 缓存），默认值 0。
- 残留问题：`iNumPlannedPlots`/`iNumPlannedSpecialists` 未使用（P3-20）；`SetAidPointPermanentVote(..., false)` 无调用点（P3-27）；`GetSpecialistProviderBuilding` 的死门控（P3-22）；`ReleaseShared2DArray` 的不可达分支（P3-19）。
- `f020fc4` + `81ad1e9` 往返已完全回滚：六个文件与 `25fa9dc` 版本逐字节一致，全仓库/API 说明库/DLC 构建产物均无 `MinorFriendshipGrowthMod` 残留。

---

## 六、已核对无误（择要）

- **序列化（除 P1-1 的版本号取值外）**：`m_uiAidPointPermanentVoteMask` 在构造（`CvPlayer.cpp:207`）、`uninit()`（`:1067`）、`Read()` 默认值（`:30953`）全部初始化；`CvLeague` 新字段在 `ClearProposalPrivileges` 复位；两处读写均用 `MOD_SERIALIZE_READ/WRITE`，读写顺序对称。位掩码 `1ULL << eMinor` 在 `MAX_CIV_PLAYERS=63` 下不越界，`UINT64` 有 8 字节流重载。
- **读档兼容（建筑类计数）**：`CvCity::read` 开头调 `reset()`（`CvCity.cpp:21115`），后者把 `m_bActiveBuildingClassCountsValid` 置 false（`:1725`），读档后首次使用必重建；新计数不写进 `write()`，未新增序列化成员。
- **共享零块（`36c63e0`）无二次释放/越界**：共享块大小与 `Initialize2DArray` 分配大小逐项一致；行数用 `ppArray[0] - ppArray` 回读真实值，零值扫描长度即真实长度；`iCount2 != NUM_YIELD_TYPES` 及行指针连续性双重校验保证形状识别正确；77 个共享成员在各自析构里都有对应 `SafeDelete2DArray`（脚本核对无遗漏）；全仓扫描确认这批表**运行期无写入**；登记表按形状去重后约 15 种，远小于 `MAX_SHARED_2D_ARRAYS=64`。
- **`CvTechEntry::m_ppiTechYieldChanges`** 的构造初始化与析构释放（`CvTechClasses.cpp:83/98`）修的是一个真缺陷（此前分配但从未释放）。
- **贸易协定时长与条件**：`AddTradeAgreement` 的 `m_iDuration` 由 `CvDealAI.cpp:4173-4175` 传 `GC.getGame().GetDealDuration()`，在 `FinalizeDealValidAndAccepted`（`CvDealClasses.cpp:2525-2536`）被折算成 `gameTurn + duration`，标准速度 30 回合，与更新说明一致；`+20%` 在陆/海两条国际商路分支（`CvTradeClasses.cpp:2726-2731`、`2883-2888`）都已接线。
- **互不侵犯协定 10/15 回合**：`GetNonAggressionPactLength()`=10、`GetNonAggressionPactCooldown()`=15（`CvDealClasses.cpp:4026-4036`）；生效期阻止宣战由 `CvTeam.cpp:1088` 实现，与更新说明一致。
- **城邦任务总数 38**：逐项数过 `MinorCivQuestTypes`（`CvMinorCivAI.h:75-99`）为 38 个，与更新说明「全部 38 个城邦任务」一致；`Quests.xml` ID 与枚举值一一对应。
- **城邦影响力自然衰减 1%/0.5%**：`CvMinorCivAI.cpp:8311-8331`，`max(100, influence) * 100/100`（最低 1 点），未达盟友门槛时基数减半，与更新说明一致。
- **`4cab1c9` 的白名单闭合**：独特单位候选与下发校验用的是同一个 `pMinorAI`，不存在「拿 A 城邦的独特单位给 B 城邦花钱」；旧单参 Lua 调用 `GetMinorGiftUnitChoices(iActivePlayer)` 只是拿不到新增独特单位，不会崩。
- **`8db447b` 的数值与实现一致**：数据 300/25/10、WHO -10/10、IMO 20/1 与 `CvPlayer.cpp:5477-5509`（利息）、`CvCity.cpp:9459-9464`（食物消耗）、`CvTradeClasses.cpp:2713-2717`、`CvUnit.cpp:9817-9843` 实现相符。
- **`cc71d69` 的注释指向真实开关**：`config.ini:224` 的 `AIPerfLog = 1` 确实存在，`Logs` 下已生成 `AI-perf.csv`/`CSUA-perf.csv`。
- **API 文档同步**：`policy.sql:189`（`LocalHappinessFromFaithPercent`）与 `policy.sql:915-935`（`AidPointActions` 新列与「动态造价行动返回 ID=-1、Cost=0」）均已更新。

---

## 七、SP V11 仓库（3 个文档提交）复审

### 7.1 与实现核对一致的部分

| 更新说明条目 | 核对结果 |
|---|---|
| 城邦UA 魁北克「默默无闻 4%→3%」 | ✅ 与内容模组三语文本一致：`TextInfos_zh_CN.xml:19006-19013`、`TextInfos_en_US.xml:20536`、`TextInfos_zh_Hant_HK.xml:18812` 三处均为 3%，上限 +40% 未变 |
| 三.5「建筑类效果统计整合」的开关与默认值 | ✅ `SP_BUILDING_CLASS_COUNT_ALL_TYPES` 四处注册齐全、默认 0 |
| 六.8「贸易协定：签订后 30 回合、商路金钱 +20%」 | ✅ 时长与数值与 C++ 一致 |
| 六.7「互不侵犯协定：10 回合内不能宣战、再次签订间隔 15 回合」 | ✅ 与 `GetNonAggressionPactLength/Cooldown` 一致（该交易项在 11-08 前已存在，本区间只改估值，属 11.0 累积说明） |
| 一.2「城邦影响力自然衰减 1%/回合、未达盟友门槛减半」 | ✅ 与 `CvMinorCivAI.cpp:8322-8331` 一致 |
| 四.5「城邦任务图鉴列出全部 38 个任务」 | ✅ 枚举确为 38 个 |
| f.(14) 科研协定任务「影响力均大于 30 且双方个人任务均未满」 | ✅ 与 `CvMinorCivAI.cpp:7726/7730/7782/7786` 一致（阈值确为 30，槽位检查确有） |
| f.(15) 新商路任务「只由商业城邦发布」 | ✅ `IsEnabledQuest`/`IsValidQuestForPlayer` 均校验 `MINOR_CIV_TRAIT_MERCANTILE` |
| 七.6「修复联盟持续效果列表不显示世界银行/WHO/IMO」 | ✅ 对应 `8db447b` |

### 7.2 文档与实现不符（3 条）

**[S-1｜P2] 三.5「建筑类效果统计整合」的表述过宽。**
更新说明写「政策、信条、城邦UA 中按建筑类统计的效果，现在会统计该类下**所有未过期的**建筑」，但「政策建筑类本地快乐」这条路径仍统计过时建筑（`CvCity.cpp:12897-12902`，见 P2-8），且 CSUA 三处（见 P2-7）不受开关控制。建议改为「政策产出/快乐修正、信条、旅游、城邦UA 的建筑类统计已统一为非过时计数；政策本地快乐的建筑类快乐仍按拥有建筑计算」，或直接修好实现后再保持现文案。

**[S-2｜P3] 六.8「贸易协定」的签订条件漏写科技前提。**
更新说明写「签订条件：双方未交战、互设大使馆、双方宣友」，但 `CvDealClasses.cpp:613-637` 还要求 `IsTradeAgreementTradingAllowed()`（至少一方解锁该交易项科技）。建议补一句「且至少一方已解锁相应科技」。

**[S-3｜P3] f.(15) 商路任务的奖励描述不全。**
更新说明只写「奖励吃游戏速度修正的金钱」，实际为 **25 影响力 + 50 金钱**（`Quests.xml` 的 `<Friendship>25</Friendship>`/`<RewardGold>50</RewardGold>`，SP `AIStrategiesTweak.xml:1201-1204` 相同）。Pedia 文本（`TXT_KEY_PEDIA_EXTRA_QUEST_TRADE_ROUTE_TO_CITY_HELP`）已正确写「影响力 +25，金钱 +50」，建议更新说明同步。

**[S-4｜P3] 可追溯性建议。** 七.bug修复 5–12 条（世界议会投票结果通知、读档后视野/城邦缓存、耶路撒冷 UA、国库负数军事力量 NaN、UI 按钮错位等）在 11-08～11-16 的 MPDLL 提交里找不到对应 C++ 改动，应属 SP 内容模组一侧或更早期提交。更新说明覆盖整个 11.0 发布可以理解，但建议每条附上版本号或提交短哈希，便于日后 bisect 与二审核对。

---

## 八、验证建议

**优先顺序：先修 P1-1（版本号）→ P1-2（死任务）→ P2-1/2/3/4，再进实机。**

1. **存档兼容（P1-1）**：升到 169 后，用 `backup-DLC/MP_MODSPACK_20261114_131353` 版本的 DLL 存一档，再用新 DLL 读；修复前应能观察到数值错乱/读档异常，修复后正常。同时在联机下用两端不同版本号 DLL 互传存档验证被拒。
2. **死任务复现（P1-2）**：影响力 31、双方有 Education、但未互设使馆 → 观察是否发布该任务；修复后应不再发布。再测「双方都已研究完所有科技」的末期场景。
3. **单机 — 任务全链路**：影响力 > 30、双向使馆、至少一方有 Education、双方各有 RA 成本金币 → 发布后 AI 主动 DoF + RA；核对**双份**影响力/文化是否符合确认后的口径（P2-1）。
4. **单机 — 新商路任务**：商业城邦、至少一城可通往目标 → UI 图标/文本/奖励（25 影响力 + 50 金）正确；目标城市被摧毁后任务应自动 obsolete 而不是报错。
5. **单机 — 贸易协定**：签订后 +20% 生效；让 DoF 破裂/互相谴责，确认 P2-2 修复后加成应撤销。
6. **单机 — 建筑类计数**：造一座同类的过时建筑，分别开关 `SP_BUILDING_CLASS_COUNT_ALL_TYPES`，对比 Ragusa 快乐 / Prague-Yerevan 产出 / 建筑大科点是否随开关变化（当前 P2-7 是「不随」）；再存读档对比政策建筑类快乐是否跳变（P2-6）。
7. **单机 — 公民分配**：开 `SP_CITIZEN_REALLOC_PLANNED`，观察 `noAuto` 回合大城专家是否被降为闲人（P2-9）；与关闭状态逐城对比专家分布（P2-10）。
8. **联机双人（必做）**：
   - 在「同一城市存读档后」对比两端快乐/产出是否一致（P2-6 的 OOS 面）；
   - 永久票/应急提案/谴责/调停四个按钮各点一次，确认两端状态一致、通知只出现一次；
   - 确认援建点消费不出现「一回合同一池被花两次」（P2-4）。
9. **编译**：按仓库规则先删 `BuildTemp\VS2022_CvGameCore_Expansion2ReleaseWin32` 再编译（PCH 陈旧会报大量「成员不存在」假错误）；用 `dumpbin /imports` 确认只导入 `MSVCP90/MSVCR90`。

---

## 九、结论

11.08–11.16 这批提交的主体设计是合理的：援助点体系把「行为—代价」数据化并迁到内容模组，城邦任务补了两条新任务并修好了旧报告里的冷却/缓存/槽位问题，性能侧把公民分配从「每公民×每地块」降到「每地块一次」。三语文本、枚举追加、ModOption 双层注册、Lua 广播路径这些容易出错的规约**基本都守住了**，没有发现中文注释违规、原版接口删除或枚举值偏移。

但有两条必须在发布前处理：

- **P1-1 的版本号复用是硬伤**——它不会在开发机上暴露，只会在「用旧包存档的人升级后读档」时爆发，正好是最难在测试里覆盖、后果最重的场景。
- **P1-2 的死任务是旧报告的复发项**——同一个函数在同一周内被再次修改却没补上这三条前提，说明修复时缺少「按 RA 交易硬条件逐条对照」的检查动作。

P2 层的 12 条里，我认为最值得先动手的是 **P2-3（援助点行动双数据源）** 和 **P2-6（建筑类计数口径不一致）**：前者是数据搬迁引入的新结构性不一致，会让内容模组失去「删行即禁用」的能力；后者是本次唯一的潜在联机 OOS 面，且修复成本很低（重建改用 `GetNumRealBuilding + GetNumFreeBuilding` 或读档时显式置无效）。

SP V11 仓库的三个文档提交本身没有代码风险，但更新说明里的「建筑类效果统计整合」表述过宽（S-1），建议要么修实现、要么改文案，避免发布后玩家按说明去核对却对不上。

---

*本报告由主线汇总 7 个批次复审结果并复核 P1 级结论与跨仓库文本一致性后定稿。*
