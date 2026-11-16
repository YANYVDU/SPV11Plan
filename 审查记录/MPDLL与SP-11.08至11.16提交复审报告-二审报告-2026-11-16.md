# MPDLL × SP 11.08–11.16 提交复审报告 · 二审

- **二审日期**：2026-11-16
- **二审对象**：`SP V11\审查记录\MPDLL与SP-11.08至11.16提交复审报告-2026-11-16.md`（下称"一审报告"）
- **基线**：`CIV5MPDLL` 分支 `V11dev`，HEAD = `8ea2ddc`，工作树干净；区间 `541e63d^..8ea2ddc` 实测 **25 个提交 / 53 文件 / +3039 −264**（与一审报告统计完全一致，已用 `git diff --shortstat 89c0a67..HEAD` 复核）
- **交叉核对**：`SP V11` HEAD = `504fed0`；SP 内容模组工作树 `V11\Super-Power-Remaking-of-World-Order\...`；游戏实测数据库 `cache\Civ5DebugDatabase.db`（只读）
- **二审方法**：逐条打开 HEAD 真实代码复核行号与结论；对否定结论做反向抽样（非 ASCII 扫描、Lua 注册表删行扫描、枚举/XML ID 对齐、三语 Tag 全量比对、DB 生效值查询）；另查一审未覆盖的 SP 侧 `DLL_Options.xml` 开关实际取值

---

## 〇、二审结论摘要

**一句话**：一审的**主干结论站得住**——两条 P1 都是真的、行号基本精确，P2 里最有价值的几条（P2-3/6/8/9/11/12）实测完全成立；但有 **1 条误报、3 条严重级别判断错误**（都源于没有核对 SP 内容模组的实际开关取值），另有 **1 条的关键数字错得离谱**，以及 **2 条一审漏掉的缺陷**。

**抽验统计**（共复核 26 条）：

| 裁决 | 条数 | 编号 |
|---|---|---|
| 成立 | **20** | P1-1、P1-2、P2-3、P2-5、P2-6、P2-8、P2-9、P2-11、P2-12、P3-1、P3-2、P3-4、P3-7、P3-11、P3-12、P3-17、P3-19、P3-20、P3-21、P3-27 |
| 部分成立 | **2** | P2-1（数字全错）、P2-4（"永久票/应急提案"一节不成立） |
| 误报 | **1** | P3-3 |
| 级别有误 | **3** | P2-2（P2→P3）、P2-7（P2→P3）、P2-10（P2→P3） |
| 一审遗漏缺陷 | **2** | L-1、L-2（见第三节） |
| 一审覆盖缺口 | **3** | 未核 SP 开关取值、否定结论措辞错误（见第三、四节） |

### 发布前必须修（二审最终清单）

1. **P1-1** 升 `MOD_DLL_VERSION_NUMBER` 到 169（`CustomMods.h:36` + 四处门控）——**硬伤，成立**。
2. **P1-2** RA 任务补「双向使馆 / RA 科技 / 未走完科技树」三条前提——**成立，且已确认强制报价路径必然失败**。
3. **P2-9** `noAuto` 回合同步清空 AI 全部非强制专家——**成立，比一审描述更严重：AI 每 8 回合触发一次**。
4. **P2-6** 建筑类 active 计数的增量/重建口径不一致——**成立，唯一真实 OOS 面**。
5. **P2-11** `GET_PLAYER(NO_PLAYER)` 遗留路径——**成立**。
6. **P2-3 / P2-4（仅 denounce 分支）** 援助点双真相源与"每池每回合一次"漏网——**成立**。
7. **L-1** 援建点造价"三源"（DB `DefaultCost` 对 5 个行动**完全无效**）——一审漏掉。

**可从必修列表降级的**：P2-7、P2-10（SP 发布配置已把开关置 1，代码不一致不产生可见后果）、P2-2（引擎语义，无文本承诺）、P3-3（不可达）。

---

## 一、逐条裁决表

| 一审编号 | 标题 | 裁决 | 实测位置（HEAD） | 说明 |
|---|---|---|---|---|
| P1-1 | 序列化字段复用版本号 168 | **成立** | `CustomMods.h:36`、`CvPlayer.cpp:30953/31932`、`CvVotingClasses.cpp:7629/7702` | 四处行号全对；168 确由 `3c24b09 "V68"` 设定后再未升；读写顺序对称，问题只在版本号 |
| P1-2 | RA 任务缺 RA 硬前提 | **成立** | `CvMinorCivAI.cpp:7723-7801`（实为 7726/7782 阈值，7747-7791 过滤）、`CvDealClasses.cpp:581-610`、`CvDealAI.cpp:4147-4159` | 三条前提确实一条都没进候选条件；强制报价路径复用 `IsPossibleToTradeItem`，必然 false→`ClearItems` |
| P2-1 | 镜像任务双份奖励 | **部分成立** | 镜像 `CvMinorCivAI.cpp:1920-1927`、影响力 `:2117`、奖励 `:2121-2139` | 双份结构成立；但一审给的 `Friendship=60 RewardCulture=50` **完全错误**：实测 SP 为 `Friendship="50" RewardGold="100"`，合计 **100** 影响力 + **2×100 金**（非文化） |
| P2-2 | 贸易协定 DoF 破裂不撤销 | **级别有误（P2→P3）** | 签订 `CvDealClasses.cpp:613-637`；效果 `CvTradeClasses.cpp:2727-2728`、`2884-2885`；唯一清除 `CvDealClasses.cpp:3956` | 代码事实成立（只有 `DoEndTradedItem` 清旗标）；但"与文本不符"的前提不成立：更新说明只写"签订后 30 回合内 +20%"，未承诺撤销，且原版所有 deal 都跑满期限 |
| P2-3 | 援助点行动双真相源 | **成立** | `CvGame.cpp:12122-12186`（一审写 12124-12195，差 2 行）；`CvLuaGame.cpp:2369-2420` | `s_aiAidPointDefaultCost` 播种后永不清除，DB 删行后 `GetAidPointBaseCost` 仍返回回退值 |
| P2-4 | AI 谴责花费绕开池去重/保证金 | **部分成立** | `CvDiplomacyAI.cpp:22401`（传 NULL）、`:26889-26924`、`:26271-26332`、`:27027-27044` | denounce 分支（传 `NULL`、忽略 `GetAidPointAnnexReserve`）成立；但**永久票/应急提案在 `:27033-27034` 已传入 `abPoolUsed`**，"同一池花两次"对它们不成立 |
| P2-5 | "协议停战"实为正式和约 | **成立** | `CvGame.cpp:11922`；`CvTeam.cpp:1726-1727`、`:1734-1744`、`:1373-1381`；文本 `TextInfos_zh_CN.xml:19372`、`zh_Hant:19178`、`en_US:20902` | 三语文案与实现直接矛盾；`makePeace` 写和平条约回合，10 回合内再宣战触发 `SetHasBrokenPeaceTreaty` |
| P2-6 | active 计数增量/重建口径不一致 | **成立** | `CvCity.cpp:8710-8713`、`:23805-23837`（重建用 `:23813`）；`CvBuildingClasses.cpp:5134-5141`、`:5479`、`:5717`；`CvCity.cpp:1094/1725/21115` | 前提已验证：`cache\Civ5DebugDatabase.db` 的 `Defines.CITY_MAX_NUM_BUILDINGS = 1` → `GetNumBuilding = max(real,free)`；读档 `reset()` 置无效→首次使用重建为 1，而存前增量是 2 |
| P2-7 | CSUA 三处绕过新开关 | **级别有误（P2→P3）** | `CvCity.cpp:12997`、`:13757`、`CvCityStateUAClasses.cpp:2826` 确无门控；对照 `CvCity.cpp:9045-9053`、`:12851-12866` 有门控 | 代码不对称成立；但 SP `DLL_Options.xml:414` 已把 `SP_BUILDING_CLASS_COUNT_ALL_TYPES` 置 **1**，发布配置下两边都走 active 计数，**无可见后果** |
| P2-8 | 开关开启时政策建筑类快乐统计过时建筑 | **成立** | `CvCity.cpp:12897-12902`、`:12938-12947`、`:12956` | 行号全对；`aBuildingsHere` 来自 `GetOwnedBuildings()`，不过滤 obsolete；与更新说明第 137 行原文直接冲突 |
| P2-9 | `noAuto` 回合清空非强制专家 | **成立（应升级描述）** | 计划路径 `CvCityCitizens.cpp:1893-1917`、`:2021-2061`、`:480-483`；经典 `:1530`；触发 `:324-327` | 计划路径 `iTarget = forced + 0` 后全量移除；且 `:324` 是"AI 每 8 回合置 noAuto"，不是偶发场景 |
| P2-10 | 专家排序不等价 + 与开关耦合 | **级别有误（P2→P3）** | `CvCityCitizens.cpp:1909-1914`、`:1195-1207`、`:1202`；经典 `:1144-1153`、`:1149` | 行为差异成立，但 SP `DLL_Options.xml:418` 同时置 `SP_SPECIALIST_AI_BY_TYPE=1`，此时计划路径正是复刻 `GetAIBestSpecialist` 的口径，发布配置下等价 |
| P2-11 | Lua 强制发任务时 RA 在 NO_PLAYER 越界 | **成立** | `CvLuaPlayer.cpp:7740`、`CvMinorCivAI.cpp:4941-4970`、`:1905-1913`、`:920-928` | 行号全对；`AddQuestForPlayer` 只校验 ePlayer/eType 范围，不校验 `IsValidQuestForPlayer`，`FAssert` 在 Release 下不停 |
| P2-12 | 停火只认"本人"的盟友城邦 | **成立** | `CvGame.cpp:11947`、`:11953`、`:11961-11970` | 行号全对；队局下队友的盟友城邦被漏掉 |
| P3-1 | `GetNumBuildingClassActive` 无下界/上界校验 | **成立** | `CvLuaCity.cpp:2404-2416`、`CvCity.cpp:23788-23795` | 只拦 `NO_BUILDINGCLASS(-1)`，`m_paiNumActiveBuildingClasses[i]` 直接下标 |
| P3-2 | 共享只读块访问器仍返回非 const | **成立** | `CvImprovementClasses.h:226/228/230/232/236`（实测 `int* GetTechYieldChangesArray(int)` 等）；共享块 `CvDatabaseUtility.cpp:186/205-224` | 表已 `PAGE_READONLY`，访问器仍给可写指针；本仓库内运行期只读 |
| P3-3 | `NO_PLAYER` 被判为友好空运起点 | **误报** | `CvUnit.cpp:8725-8743` | `CvCity` 恒有 owner（城市被夷平即销毁），`eCityOwner == NO_PLAYER` **不可达**，不存在"无主城市被当成合法起点"；`eCityOwner == eUnitOwner` 冗余属实（此时 `:8730` 已 return true），仅属整洁问题 |
| P3-4 | 四个援助点入口缺 `isAlive()` | **成立（行号需修正）** | 实际函数头：`CvGame.cpp:11770`（谴责）、`:11891`（停火）、`:11978`（永久票）、`:12019`（应急提案）；一审的 `11785-11791/11985-11987/12026-12028` 落在函数体内 | 四个入口确实都不校验 `GET_PLAYER(eMinor).isAlive()`；但只有两个是三参 `DoMinorCiv*WithAidPoints`，另两个为两参 |
| P3-7 | 第三方谴责通知泄露城邦真名 | **成立** | `CvGame.cpp:11842-11847`、`:11876-11879` | "见过城邦 **或** 见过目标"即发通知，且 `:11877` 推城邦真名；对照 `CvDiplomacyAI.cpp:22344-22358` 替换为 `TXT_KEY_UNMET_PLAYER` |
| P3-11 | 永久票显示为"奇观票" | **成立** | `CvVotingClasses.cpp:4008`、`:4065-4070`；`CvGame.cpp:12000-12002` | `iWonderVotes = GetExtraLeagueVotes()`，购买走 `ChangeExtraLeagueVotes(1)`，故被归到 `..._WONDER_VOTES` |
| P3-12 | 会期内购买本会期不生效 | **成立** | 分配 `CvVotingClasses.cpp:6494-6505`（`AssignStartingVotes`）；显示/计票 `:5336-5339` | `it->iVotes` 只在 `AssignStartingVotes` 赋值，会期内 `IsInSession()` 走 `GetRemainingVotesForMember`，不会重算 |
| P3-17 | 谴责扣点后可能什么都没改 | **成立** | `CvGame.cpp:11799`（扣点）→ `:11802-11822`（仅 `iInfluence > 0` 生效） | 对所有已相遇城邦影响力 ≤ 0 时照扣 20 点 |
| P3-19 | `ReleaseShared2DArray` 不可达分支 | **成立** | `CvDatabaseUtility.cpp:213-215` | `--iRefs == 0` 时该条目已被 `s_aShared2DArrays[i] = s_aShared2DArrays[--s_iNumShared2DArrays]` 换出（`:219`），registry 里不存在 `iRefs == 0` 的条目 |
| P3-20 | `iNumPlannedPlots/Specialists` 只写不读 | **成立** | `CvCityCitizens.cpp:1922-1923`、`:1980`、`:1985`、`:1992` | 全文件仅这 5 处出现，无任何读取 |
| P3-21 | `Reset()` 文档注释被新函数占位 | **成立** | `CvBuildingClasses.cpp:4953-4957` | `/// Reset status arrays to all false` 现在紧贴 `GetOwnedBuildings()` |
| P3-27 | `SetAidPointPermanentVote(false)` 无调用点 | **成立** | `CvPlayer.cpp:15644-15653`；唯一调用 `CvGame.cpp:12001`（传 `true`）；Lua 只暴露 `HasAidPointPermanentVote` | 清除分支属未接线 API |

---

## 二、裁决详情

### 一审 P1-1：**成立**（行号精确，无需修正）

```
CustomMods.h:36      #define MOD_DLL_VERSION_NUMBER ((uint) 168)
CvPlayer.cpp:30953   MOD_SERIALIZE_READ(168, kStream, m_uiAidPointPermanentVoteMask, 0);
CvPlayer.cpp:31932   MOD_SERIALIZE_WRITE(kStream, m_uiAidPointPermanentVoteMask);
CvVotingClasses.cpp:7629  MOD_SERIALIZE_READ(168, loadFrom, writeTo.m_eEmergencyProposalPlayer, NO_PLAYER);
CvVotingClasses.cpp:7702  MOD_SERIALIZE_WRITE(saveTo, readFrom.m_eEmergencyProposalPlayer);
```

语义复核（`CustomMods.h:1377`）：`if (uiDllSaveVersion >= version) { stream >> member; } else { member = def; }`。

- 版本号来源复核：`git log -S"((uint) 168)" -- CustomMods.h` 仅 `3c24b09 "V68"`；`git log 3c24b09..HEAD -- CustomMods.h` 只有 `541e63d`、`d03eb52`，均为新增 ModOption，**未升版本**。一审事实链完全正确。
- 读写对称性复核（一审第六节结论也正确）：Read `30947-30954` 为 `m_iExtraLeagueVotes → 新字段 → m_iSpecialPolicyBuildingHappiness`；Write `31931-31933` 同序。因此**问题只在版本号取值**，不在顺序——一审定性准确。
- 补充：`MOD_SERIALIZE_WRITE` 无条件写入（只 `CvAssert`），所以"旧 DLL 读新档"同样错位，伤害是双向的。一审只写了新读旧，建议报告补一句。
- 补充：`MOD_SERIALIZE` 在 `CustomMods.h:1373` 是**无条件 `#define`**，不存在"Release 下不门控"的缓解可能，这条没有任何可辩解的余地。

### 一审 P1-2：**成立**

候选循环实测 `CvMinorCivAI.cpp:7723-7801`，条件为：`GetEffectiveFriendshipWithMajor > 30`（7726/7782）、个人任务槽未满（7730/7786）、排除同队（7748）、排除交战（7752/7756）、排除谴责/UNFORGIVABLE/ENEMY/WAR/HOSTILE（7764-7775）、已相遇（7778）、无既有 RA（7790）。**使馆、RA 科技、`HasResearchedAllTechs` 一条都没有**。

对照 `CvDealClasses.cpp:581-610` 的 RA 硬条件（一审引用准确，`IsResearchAgreementTradingAllowed` / 双向 `HasEmbassyAtTeam` / 双向 DoF / 无既有 RA / 未全员研究完 / 非 NO_SCIENCE）。

关键补证（一审没给、但决定"死任务"必然性）：`9d38b6b` 新增的强制报价函数

```cpp
// CvDealAI.cpp:4147-4159
bool CvDealAI::IsMakeOfferForResearchAgreementForced(PlayerTypes eOtherPlayer, CvDeal* pDeal)
{
	if(!pDeal->IsPossibleToTradeItem(GetPlayer()->GetID(), eOtherPlayer, TRADE_ITEM_RESEARCH_AGREEMENT))
		return false;
	...
```

而 `IsPossibleToTradeItem` 正是上面那套硬条件 → 缺使馆时**每次**返回 false，`DoResearchAgreementOffer`（`CvDiplomacyAI.cpp:15376-15390`）随后 `pDeal->ClearItems()`，任务 30 回合内必然落空。一审"必然产出死任务"的措辞**不是过度推断**。

阈值 60→30 也已核实：`git show 9d38b6b` 中该函数两处 `<= 60` 改为 `<= 30`。

### 一审 P2-1：**部分成立**（数字全错）

结构成立：镜像 `1920-1927`、结算 `2117`、额外奖励 `2121-2139` 行号全对；镜像任务用 `eForcedTarget = m_eAssignedPlayer` 且 `IsComplete`（`925`）双向对称，双方必然同时完成，各领一份。

**但一审的数值与奖励类型都错了**。实测：

```xml
<!-- (1) CIV5MPDLL\DB\EVENTS\Quests.xml（基础行） -->
<Type>MINOR_CIV_QUEST_RESEARCH_AGREEMENT</Type>
<Enabled>false</Enabled>
<Duration>30</Duration>
<Friendship>40</Friendship>

<!-- SP: Gameplay\XML\AI\AIStrategiesTweak.xml:1179（覆盖行） -->
<Where Type="MINOR_CIV_QUEST_RESEARCH_AGREEMENT"/>
<Set Enabled="1" Friendship="50" RewardGold="100"/>
```

- 一审写"SP 配置为 `Friendship=60 RewardCulture=50`（`AIStrategiesTweak.xml:1177-1180`）"——**Friendship 是 50 不是 60，奖励是 `RewardGold=100` 不是 `RewardCulture=50`**，行号也偏 2 行。
- 因此"一次 RA 合计 **120** 影响力"应为 **100**（2×50）；"给双方各发文化"应为"**各发金钱**（100 × 时代 × 速度）"。
- 裁决仍为"双份奖励确实存在"，但报告若照原样发出去，作者按 120/文化 去核对会得出"实现不符"的错误结论，必须改。

### 一审 P2-2：**级别有误（P2 → P3）**

代码事实（成立）：`SetHasTradeAgreement(false)` 全仓只有一处 `CvDealClasses.cpp:3956`（`DoEndTradedItem`）；效果只看旗标（`CvTradeClasses.cpp:2727-2728`、`2884-2885`）。DoF 破裂/谴责确实不撤 TA。

但"效果与文本不符"这个判据不成立：

- SP 更新说明第 168-169 行原文是「新增交易项：贸易协定 / 签订后30回合（标准速度）内，双方互通商路金钱收益+20%」，**没有**"只有友谊国之间才有贸易协定"或"友谊破裂即失效"的承诺。
- 原版引擎里所有 deal 项（RA、开放边境、资源交易）都跑满期限，DoF 破裂不撤销任何一项。把 TA 做成"到期才失效"是**与引擎一致的默认语义**，不是实现缺陷。
- 真正需要确认的是策划口径，属一审第四节 4.6「口径与设计存疑」一类，不应占 P2 名额。

**建议**：降为 P3 并改写为"设计待确认：TA 是否应随 DoF 失效；若否，请在更新说明补一句'签订后不因友谊破裂而中断'"。

### 一审 P2-4：**部分成立**

成立的两点（denounce 分支）：

```cpp
// CvDiplomacyAI.cpp:22400-22401（在 DoDenouncePlayer 内）
if (!GetPlayer()->isHuman())
	DoAidPointDenounceSpend(ePlayer, NULL);      // ← pabPoolUsed 传 NULL
```

```cpp
// CvDiplomacyAI.cpp:26889-26924：自建循环，只判 GetEconomicAidPoints，不看 GetAidPointAnnexReserve
if (pMinorAI == NULL || pMinorAI->GetEconomicAidPoints(m_pPlayer->GetID()) < iCost)
	continue;
```

而 `abPoolUsed` 是 `DoCityStateAidPointAI` 的局部数组（`:27027`），`DoDenouncePlayer` 可能在本回合稍晚才触发 → 同一池一回合被花两次；吞并保证金（`:26313`）也确实被跳过。这两点成立。

**不成立的部分**：一审写「永久票/应急提案同样（自建循环绕过每池每回合一次）」。实测：

```cpp
// CvDiplomacyAI.cpp:27033-27034
DoAidPointEmergencyProposalSpend(eMe, abPoolUsed);
DoAidPointPermanentVoteSpend(eMe, abPoolUsed);
```

两者**都**拿到了 `abPoolUsed`，且内部都有 `if (pabPoolUsed != NULL && pabPoolUsed[eMinor]) continue;`（`:26945`、`:26988`）。它们只是没走 `GetAidPointPaymentMinor`，所以**只**有"吞并保证金被忽略"这一半问题，没有"同池花两次"。

**建议**：把 P2-4 拆成"denounce 绕过两道闸（P2）"＋"投票/提案忽略吞并保证金（P3）"。

### 一审 P2-7：**级别有误（P2 → P3）**

代码不对称**成立**（逐一确认无 `MOD_SP_BUILDING_CLASS_COUNT_ALL_TYPES` 门控）：

- `CvCity.cpp:12997` Ragusa 快乐、`CvCity.cpp:13757` Prague/Yerevan 产出、`CvCityStateUAClasses.cpp:2826` 建筑大科点；
- 对照 `CvCity.cpp:9045-9053`（信条）、`:12851-12866`（宗教/信条快乐）、`CvCultureClasses.cpp:4629-4630`/`4780-4781`、`CvPlayer.cpp:30236-30237`（政策/旅游）都有门控。

**但一审没核 SP 侧的实际开关取值**：

```xml
<!-- SP: Gameplay\XML\DLL_Options.xml -->
:406  <Where Name="SP_UNIQUE_CITYSTATE"/>            <Set Value="1"/>
:414  <Where Name="SP_BUILDING_CLASS_COUNT_ALL_TYPES"/><Set Value="1"/>   ← 不是 0
:418  <Where Name="SP_SPECIALIST_AI_BY_TYPE"/>       <Set Value="1"/>
:422  <Where Name="SP_CITIZEN_REALLOC_PLANNED"/>     <Set Value="1"/>
```

SP 发布配置下开关是 **1**，三处 CSUA 与五处政策/信条/旅游走的是同一口径，"一半默认生效一半不生效"这个后果**在发布配置里不存在**。它只在"别的基于 MPDLL 的内容模组启用 CSUA 但把该开关留 0"时才有害。

一审 P2-7 的标题与正文都建立在"即使开关=0"假设上，而该假设与 SP 实际情况相反 → **级别应从 P2 降到 P3（代码整洁/多内容模组兼容）**，并把 SP 的取值写进证据。

### 一审 P2-10：**级别有误（P2 → P3）**

行为差异成立：计划路径 `1909-1914` 无条件用"全城该类型槽位总量"算偏置，并按专家**类型**索引破平（`1202`）；经典路径 `1144-1153` 用单建筑 `GetNumSpecialistsAllowedByBuilding`，按**建筑**索引破平（`1149`）。

但一审漏了同一件事：SP 的 `DLL_Options.xml:418` 把 `SP_SPECIALIST_AI_BY_TYPE` 置 **1**。开启时经典路径 `CvCityCitizens.cpp:1465-1471` 走 `GetAIBestSpecialist()`，其内部（`1195-1207`）正是"全城槽位总量偏置 + 类型索引破平"——**与计划路径逐字等价**。一审所举的"同类型分散在 3 个 1 槽建筑"场景，在 SP 配置下经典路径的偏置同样是 0、同样是类型破平，不产生差异。

所以这是"两个开关的组合矩阵没测全"，不是发布配置下的行为回归 → **降 P3**，建议保留一句"若将来有人只开 PLANNED 不开 BY_TYPE，两条路径会分叉"。

### 一审 P2-9：**成立，且应把后果写重**

```cpp
// CvCityCitizens.cpp:1893
if(!IsNoAutoAssignSpecialists())     // ← 整个专家候选集被跳过
```

```cpp
// CvCityCitizens.cpp:2029-2030（应用阶段）
const int iTarget = aiForcedSpecialists[iSpecialistLoop] + aiSpecialistPlanned[iSpecialistLoop];
int iToRemove = GetSpecialistCount(eSpecialist) - iTarget;   // noAuto 时 iTarget = forced → 非强制全删
```

对照经典路径 `:1530`：`if (!GET_PLAYER(GetOwner()).isHuman() || !IsNoAutoAssignSpecialists())` → AI 城市在 noAuto 下**仍然**补专家。

一审说"地格已满的大城在 noAuto 回合把专家降为闲人"，方向对，但把触发条件说得像偶发。实测 `:320-327`：

```cpp
else if(!thisPlayer.isHuman())
{
	if(GC.getGame().getGameTurn() % 8 == 0)
	{
		SetFocusType(CITY_AI_FOCUS_TYPE_GOLD_GROWTH);
		SetNoAutoAssignSpecialists(true);      // ← 每 8 回合对所有 AI 城市置一次
```

**每个 AI 城市每 8 回合就有一次 noAuto**，也就是"每 8 回合全文明专家被清零一回合"。这已经不是"间歇丢失"，而是可测量的大范围 GPP 损失。建议一审把这条的后果描述补上这个触发频率（严重级维持 P2 合理，甚至可讨论 P1.5，但确实是"设计开关默认开启（`DLL_Options.xml:422`）"，所以必修）。

### 一审 P2-6：**成立**（前提经实测数据库验证）

一审最关键的前提是 `GetNumBuilding = max(real, free)`，即 `CITY_MAX_NUM_BUILDINGS <= 1`。一审只写了代码分支，没验证取值。实测（只读 `Civ5DebugDatabase.db`）：

```
Defines  CITY_MAX_NUM_BUILDINGS = 1
```

故 `CvBuildingClasses.cpp:5134-5137` 走 `max(...)` 分支，前提成立。

两条写入路径确认都会调 `processBuilding`（`:5479` 真实、`:5717` 免费），而 `processBuilding` 无条件 `ChangeNumBuildingClassActive(eBuildingClass, iChange)`（`CvCity.cpp:8710-8713`）→ 同种建筑真实+免费各计 1 = 2；重建（`:23813` 用 `GetNumBuilding`）只算 1。

读档必跳变也已确认：`CvCity::read`（`:21111-21115`）先 `reset()`，`reset()` 在 `:1725` 置 `m_bActiveBuildingClassCountsValid = false`，首次取值必重建。一审的修复建议（重建改 `GetNumRealBuilding + GetNumFreeBuilding`、或 `read` 末尾置无效）都可行。

**补充**：`ChangeNumBuildingClassActive`（`:23797-23800`）对 vector 直接下标、无边界检查。当前靠 `reset()`（`:1718-1722`）保证 vector 已按 `GC.getNumBuildingClassInfos()` 扩容，暂时安全；若将来出现"reset 之前就 processBuilding"的路径（如新的城市初始化顺序），会写空 vector。建议顺手加一次 `if (i < size())` 或惰性扩容。

### 一审 P2-11：**成立**

```cpp
// Lua/CvLuaPlayer.cpp:7740（lDoMinorCivStartQuestForPlayer，三参，eForcedTarget 缺省 NO_PLAYER）
pkPlayer->GetMinorCivAI()->AddQuestForPlayer(ePlayer, eType, GC.getGame().getGameTurn());
```

```cpp
// CvMinorCivAI.cpp:4941-4970：只校验 ePlayer/eType 范围，不校验 IsValidQuestForPlayer、不校验任务槽位
// CvMinorCivAI.cpp:1905-1913：eTarget 可能是 NO_PLAYER，FAssert 后直接 GET_PLAYER(eTarget)
const char* strCivKey = GET_PLAYER(eTarget).getCivilizationShortDescriptionKey();
// CvMinorCivAI.cpp:925：GET_PLAYER(eTarget).getTeam() 同样无校验
```

一审行号全对。补充两点一审没写的：

1. `AddQuestForPlayer` **也不检查个人任务槽上限**（`GetNumActivePersonalQuestsForPlayer >= GetMaxActivePersonalQuestsForPlayer()`），Lua 反复调用可以塞爆 `m_QuestsGiven[ePlayer]`，与 P2-11 同一入口、同一修法（在 `AddQuestForPlayer` 补 `IsValidQuestForPlayer` 时一并加槽位检查）。
2. `pkPlayer->GetMinorCivAI()` 不会为 NULL（`CvPlayer.cpp:622` 对**所有**玩家都 `FNEW`），所以这条不会崩在空指针上，只会在 `GET_PLAYER(-1)` 上崩——一审判断正确，此处仅确认。

### 一审 P3-3：**误报**

```cpp
// CvUnit.cpp:8725-8743
if (pCity->getTeam() == eUnitTeam) return true;
const PlayerTypes eCityOwner = pCity->getOwner();
if (eCityOwner == NO_PLAYER || eCityOwner == eUnitOwner) return true;
```

- `CvCity::getOwner()` 恒为有效玩家：城市被夷平即销毁，不存在 `NO_PLAYER` 属主的 `CvCity`。一审所述"无主城市被当成合法空运起点"**没有可达路径**，属把"代码写得怪"当成"潜在崩溃"。
- `eCityOwner == eUnitOwner` 确实冗余（此时 `:8730` 已返回 true），这一点是**整洁建议**，不是问题。
- 建议：从问题清单移除，或降级并入"注释/冗余"类（第 4.4 节），并明确写"不可达"。

### 一审 P3-4：**成立，但行号需修正**

四个入口的实际函数头与校验块：

| 函数 | 函数头 | 校验块 |
|---|---|---|
| `DoMinorCivDenounceWithAidPoints` | `CvGame.cpp:11770` | `:11772-11777` |
| `DoMinorCivPeaceWithAidPoints` | `CvGame.cpp:11891` | `:11893-11898` |
| `DoBuyPermanentVoteWithAidPoints` | `CvGame.cpp:11978` | `:11980-11983` |
| `DoRequestEmergencyProposalWithAidPoints` | `CvGame.cpp:12019` | `:12021-12024` |

四者都只校验索引区间（+ 对 eTarget `isAlive()`），**都不校验 `GET_PLAYER(eMinor).isAlive()`**，结论成立。但一审的"11985-11987、12026-12028、11785-11791、11913-11921"是函数**体内**的行（`pMinorAI` 取值块、造价块），不是校验块，读报告的人会找错地方。另外只有两个函数是三参 `DoMinorCiv*WithAidPoints`（Denounce/Peace），另两个是两参，一审"四个 `DoMinorCiv*WithAidPoints` 都做了三段 ID 区间校验"的表述（第五节）不准确。

### 一审 P3-19 / P3-20 / P3-21 / P3-27：**全部成立**

- P3-19：`CvDatabaseUtility.cpp:213-215` 的 `if(kShared.iRefs == 0) return true;` 确不可达——`:216-220` 在计数归零时已把条目换出（`s_aShared2DArrays[i] = s_aShared2DArrays[--s_iNumShared2DArrays]`），registry 中不存在 `iRefs == 0` 的条目。
- P3-20：`iNumPlannedPlots`/`iNumPlannedSpecialists` 全文件只出现在 `:1922-1923`（声明）、`:1980`、`:1985`、`:1992`（自增），无读取。
- P3-21：`CvBuildingClasses.cpp:4953` 的 `/// Reset status arrays to all false` 现在正好压在 `GetOwnedBuildings()` 上方，真正的 `Reset()` 在后面无注释。
- P3-27：`SetAidPointPermanentVote` 唯一调用点是 `CvGame.cpp:12001` 传 `true`；`CvLuaGame` 只注册了 `HasAidPointPermanentVote`。

---

## 三、一审遗漏的问题

### [L-1｜P3，新增] 援建点造价是"三源"，DB 的 `DefaultCost` 对 5 个行动完全没有效果

一审 P2-3 只谈了"**存在性**"的双源，漏了"**造价**"的源更多，而且注释是错的：

```cpp
// CvGame.cpp:12147  「The AidPointActions table is authoritative when available.」
// CvGame.cpp:12182-12185
if(s_aidPointCostOption[eAction].empty())
	return s_aiAidPointDefaultCost[eAction];
return gCustomMods.getOption(s_aidPointCostOption[eAction].c_str(), s_aiAidPointDefaultCost[eAction]);
```

也就是说：DB 行的 `DefaultCost` 只是**兜底**，只要 `CostOption` 指向的 CustomModOption 存在，就以那个选项为准。实测这些选项确实存在并已被 SP 覆盖：

```
(1) CIV5MPDLL\CustomModOptions.xml:1217-1227
  SP_AID_POINT_COST_REROLL_QUESTS=20 / NEXT_GREAT_PERSON=50 / PENDING_GIFT_UNIT=10
  HASTEN_CONGRESS=20 / ANNEX_CITY_STATE=50
SP: DLL_Options.xml:438-464 对上述 5 个选项全部 <Set Value=...>
```

后果：
- 内容模组改 `AidPointActions` 里的 `DefaultCost`，对 **reroll / 下一个大科 / 赠送单位 / 加速议会 / 吞并** 这 5 个行动**毫无作用**（要改两处，且改错地方不会报错）。
- 对 **denounce / peace / permanent vote / emergency proposal** 这 4 个（没有对应 CustomModOption）又确实以 DB 为准。
- 于是"改价该改哪儿"取决于具体行动，而代码注释宣称"表是权威" → 必然误导后续维护者。

**建议**：`GetAidPointBaseCost` 改为"DB 有该行则用 `DefaultCost`，`CostOption` 仅在 DB 缺行时兜底"，或删掉 `CostOption` 列统一走 DB，并同步修正 `:12147` 的注释与 API 说明库（`policy.sql` 的 `AidPointActions` 段）。

### [L-2｜P3，新增] 援助点表是进程级静态缓存，跨存档/跨局不会失效

```cpp
// CvGame.cpp:12124-12125
bool s_bAidPointActionsSeeded = false;
bool s_bAidPointActionsLoaded = false;
// 只有 :12168 会把 s_bAidPointActionsLoaded 置 true，全仓无任何重置点
```

全仓 grep 这两个符号只有 `12125 / 12132 / 12134 / 12149 / 12168`，没有任何 `Reset`/`uninit`/`new game` 钩子。后果：同一进程内退回主菜单、切换内容模组配置后再读另一份存档时，`AidPointActions` 的造价与 `Discountable` 仍沿用**上一局**的值（包括"上一局表为空 → 用 C++ 回退"的状态）。虽然换模组通常要重启，但"同一 DLL、不同存档"的路径是存在的，且表现为"价格莫名其妙变了"这种极难定位的问题。

**建议**：把两个 static 与该表数据的重置挂到 `CvGame::init`/`LoadAidPointActions` 的 DB 重新加载点（或至少在 `CvGame::init` 里置 `s_bAidPointActionsLoaded = false`）。

### [覆盖缺口-1｜影响级别判定] 一审没有核对 SP 内容模组的开关实际取值

`V11\...\Gameplay\XML\DLL_Options.xml:406-422` 把 `SP_UNIQUE_CITYSTATE`、`SP_BUILDING_CLASS_COUNT_ALL_TYPES`、`SP_SPECIALIST_AI_BY_TYPE`、`SP_CITIZEN_REALLOC_PLANNED` **全部置 1**。这一个事实同时影响三条裁决：

| 条目 | 一审假设 | 实际 | 影响 |
|---|---|---|---|
| P2-7 | 开关可能为 0 | 1 | P2 → P3 |
| P2-10 | 可能只开 PLANNED | 两开关都 1 | P2 → P3 |
| P2-9 | "潜在" | 计划路径是**发布默认路径** | 从"可选优化里的缺陷"变成"每局都在发生" |

一审在 P2-7 里写了"SP 内容模组的默认状态"却只核了 `SP_UNIQUE_CITYSTATE`，说明它知道要核 SP 开关，只是没核这一行。

### [覆盖缺口-2｜否定结论措辞] 三处"已核对无误"的表述与实测不符

1. **"25 个提交的 `+` 行全部为 ASCII/英文"**：实测有 **8 行非 ASCII**，全部来自 `8db447b` 的
   `(1) CIV5MPDLL\DB\_TEXT\AllText_zh_CN.xml` 与 `AllText_zh_Hant_HK.xml`（世界银行/WHO/IMO 三语摘要）。
   **这不违规**——"注释必须英文"针对的是 `.cpp/.h` 注释（VC9 按 GBK 解析），本地化 XML 本来就是 UTF-8 中文；但"全部为 ASCII"是事实错误，应改成"无中文注释；`+` 行中的非 ASCII 仅出现在 `AllText_zh_CN/zh_Hant_HK.xml` 的本地化文本，符合规范"。
2. **"四个 `DoMinorCiv*WithAidPoints` 都做了三段 ID 区间校验"**：只有 Denounce/Peace 是三参，PermanentVote/EmergencyProposal 是两参（见 P3-4 修正）。
3. **"所有会写全局状态的人类入口……实参只用显式玩家/城邦/单位 ID，不依赖 `getActivePlayer()`"**：实测 `CityStateDiploPopup.lua:1974` 就是 `local iActivePlayer = Game.GetActivePlayer();` 再作为首参广播。这在 SP 语境下**安全**（本机点击者即操作者），但与一审写下的断言相反，应改为"用本机 active player 作 actor，target/minor 用显式 ID"。

---

## 四、对一审修复建议的补充意见

1. **P1-1 的修法要顺手加固**：一审只写"168→169"。建议同时确认 `CvLeague` 与 `CvPlayer` 之外没有第三处借用 168；并把"升版本号 + 加字段必须同一提交"写进仓库约定（`CLAUDE.md`/AGENTS），因为 `3c24b09` 之后的两次 `CustomMods.h` 改动都只加了 ModOption，说明这条约定目前只靠人记。
2. **P1-2 的补丁位置要挪**：一审建议加在 `veValidPlayers.push_back` 之前的候选循环里（对）。但只堵候选循环不够——`IsValidQuestForPlayer`（`:5969-5979`）与 `lDoMinorCivStartQuestForPlayer`（`:7740`）是两条独立入口，强制发任务时不走候选循环。建议把三条前提抽成 `CvMinorCivAI::CanPairForResearchAgreementQuest(ePlayer, eOther)`，在候选循环、`IsValidQuestForPlayer`、`DoStartQuest` 三处共用，避免第三次复发（这已经是同一函数的第二次漏修）。
3. **P2-1 的修法与数字一起改**：一审建议"给镜像任务打标记（`m_iData2` 置 1）"。注意 `m_iData2` 目前在 RA 任务里**未被使用**，可以用；但 `CvMinorCivQuest` 的序列化若不含 `m_iData2` 语义标记，旧存档里镜像任务仍会双发。建议在 `DoFinishQuest` 里改为"影响力和奖励只发给 `m_eAssignedPlayer < m_iData1` 的一方"这种**无需新字段、对旧档也成立**的判定（幂等）。
4. **P2-3 的修法有陷阱**：一审建议"已加载且 Type 不在表中时返回 0"。注意 `GetAidPointBaseCost` 返回 0 后，`DoBuyPermanentVoteWithAidPoints` 等处的 `iCost <= 0 → return false` 会正常禁用；但 `CvPlayer::GetAidPointCost`（`15677`）会再叠政策折扣，UI 侧 `CityStateDiploPopup.lua` 用 `Cost==0` 判断"不可购买"的写法要同步确认。另外必须同时处理 L-1（`CostOption` 优先级），否则"删行即禁用"和"改价"仍是两套规则。
5. **P2-9 的修法**：一审建议"计划路径按经典语义处理 `noAuto`（只增不减）"。实现上最省事的做法不是加分支，而是让计划路径在 `noAuto` 时 `iTarget = max(现有, forced)`（即把 `aiSpecialistPlanned` 的初值设为现有分配），再走同一套 apply，避免出现第三条代码路径。
6. **P2-6 的修法**：一审给了三个选项。推荐"重建改 `GetNumRealBuilding + GetNumFreeBuilding`"——但要注意 `CITY_MAX_NUM_BUILDINGS > 1` 的模组（`GetNumBuilding` 走累加）要与之保持一致，否则又出现第三套口径。次优是 `read` 末尾显式置 `m_bActiveBuildingClassCountsValid = false`（这条已经天然成立），真正要修的是**增量侧**：让 `ChangeNumBuildingClassActive` 只在 `GetNumBuilding()` 变化时按差值记账。
7. **新增建议（对应 L-1）**：把 `AidPointActions.CostOption` 这一列在 API 说明库里标注为"仅当行缺失时生效"，或者干脆废弃它，把钱的问题收进 DB 一处。

---

## 五、一审做得好的地方（二审已确认无误的部分）

以下是二审**独立复核后确认成立**的否定结论与细节，一审在这些地方没有虚报：

1. **未发现中文注释违规**：全量扫描 25 个提交的 `+` 行，非 ASCII 只有 8 行，且全部在 `AllText_zh_CN.xml` / `AllText_zh_Hant_HK.xml` 的本地化文本里，`.cpp/.h` 注释无中文。
2. **未删除/改名原版 Lua 与 C++ 接口**：扫描区间内 `CvGameCoreDLL_Expansion2\Lua\` 的 `-` 行，**没有任何** `Method(...)` / `LUAAPIEXTN(...)` / `static int l...` 被删除。唯一签名变化是 `CvGame::GetMinorGiftUnitChoices` 增加 `eMinor` 参数（`CvGame.h:647`），旧单参 Lua 调用因实现里 `if(eMinor >= MAX_MAJOR_CIVS && eMinor < MAX_CIV_PLAYERS)` 而安全退化；SP UI（`AidPointChoicePopup.lua:84`）已同步传两参，功能真正接线（此点一审判断正确）。
3. **枚举一律追加在末尾**：`MINOR_CIV_QUEST_TRADE_ROUTE_TO_CITY` 位于 `CvMinorCivAI.h:97`（`NUM_MINOR_CIV_QUEST_TYPES` 前一个），与 `Quests.xml` 的 `<ID>37</ID>` 一致，38 个任务一一对应；`AID_POINT_ACTION_*` 是全新枚举（`a9c427d`），未插入任何原版枚举；`DIPLO_STATEMENT/MESSAGE_TRADE_AGREEMENT` 也未改动既有值。
4. **三语文本齐全、占位符匹配**：脚本抽取区间内全部 39 个新增 `TXT_KEY`，逐个在 SP 三语 XML 中查找，只有 2 个未命中（`TXT_KEY_POP_CSTATE_BUYOUT`、`TXT_KEY_CO_CITY_TOURISM_BUILDING_BONUS`），经只读查询 `Localization-Merged.db` 确认二者都是 BNW 原版 Tag（各 11 条），**不存在缺语 Tag**。抽验的通知类占位符与 C++ push 数量完全对应（`_ACTOR`/`_THIRD` 各 2 个、`_DENOUNCED`/`_PERMANENT_VOTE`/`_EMERGENCY_PROPOSAL` 各 1 个）。
5. **没有新增 GameEvent 回调内的重复广播**：区间内 `+` 行中 `GAMEEVENTINVOKE_HOOK`、`SendAndExecuteLuaFunction`、`OutputDebugString`、`printf(` 的出现次数**均为 0**，一审这条否定结论有据。
6. **序列化读写顺序对称**（除版本号取值外）：`CvPlayer` 与 `CvLeague` 两处新字段在 Read/Write 中位置一致（`30947-30954` ↔ `31931-31933`、`7629` ↔ `7702`）；`UINT64` 有 8 字节流重载（`FDataStream.h:119-120`），位掩码不会截断。
7. **`36c63e0` 的共享零块没有二次释放**：`SafeDelete2DArray`（`CvDatabaseUtility.cpp:138-146`）先试 `ReleaseShared2DArray`，命中则直接返回，不会落到 `delete[]`；`Share2DArrayIfZero` 在替换前 `IsShared2DArray` 去重（`:228`），并对 shape/全零做双重校验（`:235-256`）。
8. **`ed1e33a` 的 UI 刷新不需要广播**：只置 `GameData_DIRTY_BIT`，属单端本地行为，一审判断正确（二审未逐行复核该提交，但无新增广播调用已由第 5 点覆盖）。
9. **P3-1/P3-2 两条越界类判断准确**：`GetNumBuildingClassActive` 的 Lua 入口确实只拦 `NO_BUILDINGCLASS`；共享只读块的访问器确实仍返回 `int*`。两条都是**真实且低危**的隐患，保留合理。

---

## 六、二审后的最终发布建议

**结论：可以发布，但必须先把两条 P1 修掉；一审的 12 条 P2 里实际只有 8 条够级别的必修项，另有 2 条属误判级别，不要让作者按一审清单平均用力。**

### 第一优先（不修不能发）

| 序号 | 条目 | 理由 |
|---|---|---|
| 1 | **P1-1** 版本号 168→169 | 会让"用 11-14 包存档的玩家升级后读档错位"，开发机上永远复现不了 |
| 2 | **P1-2** RA 任务补三条 RA 硬前提 | 已确认强制报价路径必然失败 → 30 回合死任务 + 双方任务槽被占 |

### 第二优先（本次发布前建议修，成本都低）

| 序号 | 条目 | 一句话 |
|---|---|---|
| 3 | **P2-9** | SP 默认开启 `SP_CITIZEN_REALLOC_PLANNED`，AI 每 8 回合被清零专家 |
| 4 | **P2-6** | 唯一真实 OOS 面：存读档后建筑类 active 计数从 2 跳回 1 |
| 5 | **P2-3 + L-1** | "删行即禁用"和"改价"两套规则，且注释宣称表是权威 |
| 6 | **P2-4（仅 denounce 段）** | `DoAidPointDenounceSpend(ePlayer, NULL)` 绕过池去重与吞并保证金 |
| 7 | **P2-11** | `GET_PLAYER(NO_PLAYER)` 遗留路径，顺手加任务槽校验 |
| 8 | **P2-8 / S-1** | 政策建筑类快乐仍算过时建筑，与更新说明原文冲突（改实现或改文案二选一） |
| 9 | **P2-12** | 队局下队友的盟友城邦不跟随停火 |

### 可延后（改级别/改措辞即可，不必阻塞发布）

- **P2-7 / P2-10** → 降 P3：SP 已把相关开关置 1，代码不对称不产生可见后果；建议补一条"多内容模组兼容"备注。
- **P2-2** → 降 P3 并改写为"设计待确认"，因为更新说明没有承诺撤销，原版 deal 也一律跑满期限。
- **P2-5** → 维持 P2，但注意它是**文案问题**：若选"改文案承认正式和约"，成本最低；若要实现"不写 `TurnMadePeaceTreatyWithTeam` 的停战"，需同时改 `DoNowAtWarOrPeace` 与盟邦跟随，风险显著高于改文案。
- **P3-3** → 撤下（不可达），其"冗余分支"部分并入注释/整洁类。
- **P3-4 / P3-19 / P3-20 / P3-21 / P3-27 / L-2** → 一次提交清理即可。

### 发布前的实机验证（在二审修正后仍建议照做）

1. 用 `backup-DLC/MP_MODSPACK_20261114_131353` 的 DLL 存一档，新 DLL 读——修 P1-1 前应错乱、修后正常；再用两端不同版本 DLL 互传存档确认被拒。
2. 影响力 31、有 Education、**未互设使馆** → 观察是否下发 RA 任务；修后应不下发。再测"双方都研究完所有科技"。
3. **联机双人**：同一城市存读档后对比快乐/产出（P2-6）；永久票/应急提案/谴责/调停各点一次，确认两端一致且通知只出一条；连续 8 回合观察 AI 城市专家是否被清零（P2-9）。
4. 给 AI 攒满某个城邦的援建点到吞并阈值，观察是否被 denounce 花掉（P2-4）；删掉 `AidPointActions` 一行，确认 UI、AI、造价三处是否一致地禁用（P2-3 + L-1）。
5. 编译前按仓库规则删 `BuildTemp\VS2022_CvGameCore_Expansion2ReleaseWin32`，`dumpbin /imports` 确认只导入 `MSVCP90/MSVCR90`。

---

*二审基于 `8ea2ddc` 真实代码逐条比对，所有裁决均附 `文件:行号` 与关键代码片段；对一审的 26 条结论给出 20 成立 / 2 部分成立 / 1 误报 / 3 级别有误，另新增 2 条缺陷与 3 处覆盖缺口。*

---

## 附录：主线对二审裁决的复核补注

二审整体质量高，20 条「成立」与 P2-4 的收窄经主线复核均无误。但有一条裁决**经复核不成立**，在此更正，以免作者按错误数值去做平衡验证。

### 一、二审 P2-1「数字全错」的裁决不成立——一审原值正确

二审认为 SP 侧科研协定任务实为 `Friendship="50" RewardGold="100"`。复核结果：**该行属于相邻的另一条任务，不是科研协定任务。**

`V11/Super-Power-Remaking-of-World-Order/Super Power - Remaking of World Order (v 7)/Gameplay/XML/AI/AIStrategiesTweak.xml` 的实际内容（行号已核对）：

```xml
1177        <Update>
1178            <Set Enabled="1" Friendship="60" RewardCulture="50"/>   <!-- 科研协定任务 -->
1179            <Where Type="MINOR_CIV_QUEST_RESEARCH_AGREEMENT"/>
1180        </Update>
1181        <Update>
1182            <Set Enabled="1" Friendship="50" RewardGold="100"/>     <!-- 世界奇观竞赛任务 -->
1183            <Where Type="MINOR_CIV_QUEST_CONTEST_WORLD_WONDERS"/>
1184        </Update>
```

即 `<Where Type="MINOR_CIV_QUEST_RESEARCH_AGREEMENT"/>` 落在第 **1179** 行，它上方第 1178 行的 `<Set>` 才是科研协定任务的奖励配置：`Friendship="60" RewardCulture="50"`。

二阶误读的原因很可能是按「`<Where>` 在 `<Set>` 之后」的顺序去匹配行号，或把 1178 行的 `<Set>` 与 1182 行的 `<Set>` 混在了一起。

**因此维持一审 P2-1 的结论与数值**：一次科研协定后，origin 与 target 各自的镜像任务都完成，各领 `Friendship = 60` 与 `RewardCulture = 50 × 时代 × 速度修正` —— 该城邦合计获得 **120 影响力**，双方各得一份文化奖励。验证时请按「合计 120 影响力 + 双份文化」核对，而不是二审写的「100 影响力 + 2×100 金」。

> 附带提示：二审在核对奖励时若能同时打印 `<Set>` 与它下方 `<Where>` 两行，这类相邻行误读可以完全避免。建议以后核对 SP 数据一律用「`<Set>` 与紧随其后的 `<Where>` 成对读取」，不要按行号记忆。

### 二、二审其余裁决的复核确认

- **P2-4 收窄成立**：复核 `CvDiplomacyAI.cpp:27033-27034`，`DoAidPointEmergencyProposalSpend` / `DoAidPointPermanentVoteSpend` 确实接收 `abPoolUsed`；`DoAidPointPermanentVoteSpend`（`:26927`）虽遵守 `pabPoolUsed`，但用 `GetEconomicAidPoints < iCost` 直接判定、不走 `GetAidPointPaymentMinor`，因此仍绕过 `GetAidPointAnnexReserve`（`:26345-26350`）。一审已按此收窄为「同池双花仅谴责；吞并保证金三者皆绕过」。
- **P2-7 / P2-10 降级成立**：`DLL_Options.xml:413-420` 确已把 `SP_BUILDING_CLASS_COUNT_ALL_TYPES`、`SP_SPECIALIST_AI_BY_TYPE`（`:417`）、`SP_CITIZEN_REALLOC_PLANNED`（`:418`）都置 1。一审已加「二审意见（拟降为 P3）」并保留原编号。
- **P2-9 优先级上调成立**：正因为 `SP_CITIZEN_REALLOC_PLANNED` 默认开启，该条是线上默认行为，一审已补「优先级提示」。
- **P3-3 误报确认**：`CvCity` 生命周期内恒有 owner，`NO_PLAYER` 分支不可达；一审已在该行标注二审判定。
- **L-1（造价三源）与 L-2（进程级静态表跨存档不失效）**：一审未覆盖，二审补得对，建议作者一并纳入修复清单。

### 三、经一审 + 二审 + 主线复核后的最终必修清单

| 顺序 | 编号 | 问题 | 来源 |
|---|---|---|---|
| 1 | P1-1 | 新序列化字段复用 DLL 版本号 168 → 升 169 | 一审，二审确认 |
| 2 | P1-2 | 科研协定任务缺使馆/RA科技/全科技三条前提 → 死任务 | 一审，二审确认 |
| 3 | P2-9 | `noAuto` 回合非强制专家被清空（线上默认开启） | 一审成立，二审上调 |
| 4 | P2-6 | active 计数增量 vs 重建口径不一致 → 读档跳变/潜在 OOS | 一审，二审确认 |
| 5 | P2-3 + L-1 | 援助点行动「存在性/造价」多源，内容模组删行不能真正禁用 | 一审，二审补 L-1 |
| 6 | P2-4 | 谴责花费同池双花 + 三者绕过吞并保证金 | 一审，二审收窄 |
| 7 | P2-8 + S-1 | 政策建筑类快乐仍统计过时建筑，与 11.0 更新说明矛盾 | 一审，二审确认 |

其余 P2（P2-1、P2-2、P2-5、P2-7、P2-10、P2-11、P2-12）与全部 P3 可按常规节奏处理；P2-2、P2-7、P2-10 按二审意见降为 P3。
