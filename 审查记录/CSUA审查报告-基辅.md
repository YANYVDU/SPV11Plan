# CSUA 审查报告：基辅（Kiev）

- 审查日期：2026-09-27
- 审查对象：工作区未提交改动（审查时尚未 commit；审查通过后提交）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 7 文件 +237 / −1；SP 5 文件 +114
- 提交：MPDLL `1aa0cc0`、SP `8516b2c`
- 结论摘要：三个效果各自复用既有挂点（`getGreatPeopleRateModifier` / `CalculateStartingVotesForMember` / `GetCSUAYieldPercentModifier`），**一审无严重问题**。一审提出 1 项一般问题（效果① 最多 1 回合生效延迟）与 4 条建议，其中 2 条已修复、2 条保留。复审通过。**注意：本城邦的 `LeagueVoteYieldModifiers` 表用 basis points，与相邻的布加勒斯特两张表（普通百分比）口径相反，是复制粘贴陷阱。**

> 审查方式：由独立子代理完成（上下文与实现过程完全隔离，只拿到设计文本、方案文档路径与 `git diff`）。

---

## 一、改动清单

### MPDLL `1aa0cc0`

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +16 / −1 | 主表两列 `GreatPersonRateModifierPerNationalWonder` / `LeagueVotesPerDoF` + 新表 `CityStateUAEffect_LeagueVoteYieldModifiers`（注释注明 basis points） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +46 | `LeagueVoteYieldModifierEntry`、两标量列 getter/成员、`CacheNationalWonderCount()` / `CacheLeagueVotes()` 声明 |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +89 | 构造函数初始化、`CacheResults` 解析（两标量列 + 子表）、`ApplyEffect` 累加、`Reset` 清零、两个 Cache 方法实现 |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +62 | `GetCSUAYieldPercentModifier` 选票段；`GetNumNationalWonders()`、`GetCSUAGreatPersonRateModifierFromNationalWonders()`、`GetCSUALeagueVotesFromDoF()`；`RefreshCSAllUAEffects` 两处缓存调用 |
| `CvGameCoreDLL_Expansion2/CvPlayer.h` | +8 | 三个方法声明 |
| `CvGameCoreDLL_Expansion2/CvCity.cpp` | +6 | `getGreatPeopleRateModifier()` 挂钩（仿拉本塔 `GetCSUAGreatPersonRateModifierFromGreatWorks`） |
| `CvGameCoreDLL_Expansion2/CvVotingClasses.cpp` | +10 | `CalculateStartingVotesForMember()` 加票 + vote-sources tooltip 明细 |

### SP `8516b2c`

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 | 基辅 `UAType` 绑定（`MINOR_CIV_KIEV` → `CSUA_KIEV`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +29 | 2 个效果（`GreatPersonRateModifierPerNationalWonder=2/1`、`LeagueVotesPerDoF=1`）、1 个 UA 行、`LeagueVoteYieldModifiers` 表 1 行（CULTURE 100） |
| `Gameplay/XML/Localization/TextInfos_{en_US,zh_CN,zh_Hant_HK}.xml` | 各 +28 | 4 个 Tag × 3 语言（含世界议会 vote-sources 明细 Tag），追加于各文件末尾 |

### 效果设计（已核对与三语文本、XML 三方一致）

| 对象 | 设计文本 | 实现 |
| --- | --- | --- |
| 盟友 | 每完成一个国家奇观，全国伟人点数积累 +2% | 主表列 `GreatPersonRateModifierPerNationalWonder=2`，在 `CvCity::getGreatPeopleRateModifier()` 累加 |
| 盟友 | 每与一个文明宣布友好，世界议会 +1 选票 | 主表列 `LeagueVotesPerDoF=1`，在 `CvLeague::CalculateStartingVotesForMember()` 加票 |
| 盟友 | 每持有 1 张世界议会选票，全国文化 +1% | `LeagueVoteYieldModifiers` × CULTURE × 100（**basis points**），在 `GetCSUAYieldPercentModifier` 累加 |
| 朋友 | 每完成一个国家奇观，全国伟人点数积累 +1% | 同上，值 = 1 |

### 实现前的用户拍板决策（已按此实现）

- **宫殿计入国家奇观**：`BUILDINGCLASS_PALACE` 的 `MaxPlayerInstances == 1`，故任何有首都的玩家恒定白送 +2%（盟友）/ +1%（朋友）。
- **效果③统计全部选票**：含基础票、城邦盟友票、奇观票、教廷票；会自动把效果②因 DoF 产生的票折算成文化。

---

## 二、问题清单

### P2-1　效果① 存在最多 1 回合生效延迟 —— **保留，已补注释**

- 位置：`CvCityStateUAClasses.cpp:2374` `CacheNationalWonderCount()`
- 现象：国家奇观数按每回合缓存，而模板拉本塔在 `getGreatPeopleRateModifier()` 中是实时读 `GetNumGreatWorks()`。本回合刚落成的国家奇观要到下回合才计入伟人点数。
- 判断：维持缓存（实时调用代价是每城 O(城市数)），已在注释中点明该差异。设计文本未提延迟，实机验证时需注意。

### P3-1　两个 `Has*` 方法定义后无调用 —— **保留**

- 位置：`CvCityStateUAClasses.cpp:2367` `HasNationalWonderGreatPersonModifier()`、`:2384` `HasLeagueVotesPerDoF()`
- 判断：该类既有 4 个同类未调用的 `Has*`（`HasFaithInfluencePurchase`、`HasGoldenAgeYieldModifiers`、`HasGreatWorkGreatPersonPoints`、`HasTradeRouteGoldPerSurplusResource`），属既有惯例，保留。

### P3-2　`GetCSUALeagueVotesFromDoF()` 未判空 `GetDiplomacyAI()` —— **已修复**

- 位置：`CvPlayer.cpp:32808`
- 处理：加判空。已核实 `m_pDiplomacyAI` 在 `CvPlayer.cpp:614` 无条件 `FNEW`，永不为 NULL，故判空不会把合法情况误判为 0。

### P3-3　`CacheLeagueVotes()` 注释「只读重算」措辞误导 —— **已修复**

- 位置：`CvCityStateUAClasses.cpp`（`CacheLeagueVotes`）
- 现象：所调 `CalculateStartingVotesForMember()` 在 `!IsInSession()` 时会重建 `Member::sVoteSources`（`CvVotingClasses.cpp:3940`），是带副作用的调用。
- 处理：结果幂等无害；注释已补充说明该写入幂等、无持久副作用。

### P3-4　`GetNumNationalWonders()` 可加 `const` —— **未改**

- 原因：内部使用非 const 的 `firstCity()` / `nextCity()`，无法加 `const`。

### P3-5　（复审追加修复）初始化列表顺序

- 位置：`CvCityStateUAClasses.cpp` 构造函数
- 现象：`m_iGreatPersonRateModifierPerNationalWonder(0)` / `m_iLeagueVotesPerDoF(0)` 初版插在 `m_iGreatPersonRateModifierPerGreatWork(0)` 之后，而声明在类末尾，可能触发 C5038。
- 处理：已把两行移到初始化列表末尾（`m_iHolySiteHappiness(0)` 之后），编译后 `C5038` 计数为 0。

### P3-6　（复审追加）注释措辞

- `CvPlayer.cpp` 注释「so this is never 0」对无城存活玩家不成立 → 已收紧为「any player with a capital always scores at least 1」。

---

## 三、已验证无误项

- **数值与盟友/朋友区分**：+2% / +1% 伟人点数、每 DoF +1 票、每票 +1% 文化；`LeagueVotesPerDoF` 与选票文化行**均只在 ALLY 行**，无设计外多余效果。
- **basis point 三处自洽**：代码 `iMod += iVotes * vLV[i].m_iYieldMod` **不乘 100**（与 Ife 的 `GreatWorkYieldModifierEntry` 同口径）、SQL 建表注释注明 basis points、XML 值 100；`/100` 后即每票 +1%。消费方 `CvCity.cpp:13605` 按普通百分比使用，走 `TXT_KEY_PRODMOD_CITYSTATE_UA` 全局归属。
- **递归/重复计入**：`CacheLeagueVotes → CalculateStartingVotesForMember → GetCSUALeagueVotesFromDoF` **单向无回环**（效果③不进效果②）；`iDoFVotes` 声明与使用同处一个 `#if` 块、同作用域；`ApplyEffect` 仅在 `RefreshCSAllUAEffects`（先 `Reset`）后调用，不会累积。
- **计数纯净**：城市规模 / 腐败假建筑类未设 `MaxPlayerInstances`（默认 -1，非国家奇观类）且经 `CityScale_FreeBuildingClass` 授予，不会虚增国家奇观数。
- **边界安全**：`GetGameLeagues` / `GetActiveLeague` / `m_pCityStateUA` / `m_pPlayer` 均判空；`Reset` 清 `m_iCached*` 且提前返回不残留旧值；无除零。
- **六处完整性**：构造函数初始化（顺序符合 `-Wreorder`）、`CacheResults` 解析、`ApplyEffect` 累加、`Reset` 清零、`RefreshCSAllUAEffects` 刷新点、三语言文本 4 个 Tag 各 1 条。
- **tooltip 一致性**：`TXT_KEY_LEAGUE_OVERVIEW_MEMBER_DETAILS_KIEV_DOF_VOTES` 与 `CvVotingClasses.cpp:3999` 的 Lookup 完全一致（`{1_NumVotes}` 与教廷条目同格式）。
- **数据完整性**：新表建表 / 查询 / XML 三处表名列名与外键一致；`CityStateUAEffects` 两新列在本仓库建表中唯一定义，无 ALTER 冲突；`TXT_KEY_CITYSTATE_KIEV` 来自本体 Expansion2。
- **规范**：MPDLL 新增行全英文注释，无中文；无行尾破坏；CSUA 状态每回合重建，未加 `MOD_SERIALIZE` 门控符合规则。

---

## 四、验证方法

由独立子代理执行，未运行 MSBuild（编译由主流程单独完成）：

1. 两仓库 `git diff` 通读，核对设计文本逐条
2. 阅读 `GetResearchCost` / `CalculateStartingVotesForMember` / `getGreatPeopleRateModifier` / `GetCSUAYieldPercentModifier` 的完整上下文
3. 追踪 `CacheLeagueVotes → CalculateStartingVotesForMember → GetCSUALeagueVotesFromDoF` 确认无递归
4. 三语言 Tag 与 C++ Lookup 程序化比对
5. 四个改动 XML 经 `ElementTree` 解析校验 well-formed

编译验证：清 PCH 全量重建，`exit=0`，`error C` / `error LNK` 计数为 0，`warning C5038` 计数为 0。

---

## 五、当前状态与建议处理顺序

### 状态

- 已提交：MPDLL `1aa0cc0`、SP `8516b2c`（均未 push）
- 已构建模组到 MODS 目录
- 一审无严重问题；1 项一般问题保留（已补注释）、4 条建议中 2 条已修复
- **未做实机验证**（实现期间用户不在）

### 建议顺序

1. 先做实机验证（重点：宫殿白送 +2% 是否符合预期、DoF 选票明细是否出现在世界议会界面）
2. 再评估 P2-1 的 1 回合延迟是否可接受
3. **特别注意**：若将来给其他城邦加选票类效果，勿照抄本城邦的 basis point 口径到普通百分比的表（或反之）
