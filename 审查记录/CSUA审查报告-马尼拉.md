# CSUA 审查报告：马尼拉（Manila）

- 审查日期：2026-09-27
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 5 文件 +86 / −0；SP 5 文件 +97 / −0
- 结论摘要：三条效果与设计稿逐条一致，**未发现功能性缺陷**。DLL 已重编且产物含马尼拉三列。有 **3 个需要拍板的口径 / 强度点**（效果②是否含通往城邦的商路、效果③的数值与上限、效果③是否计入进口奢侈品），另有 4 项非缺陷提示（编译时序疑点、预览计数偏差、缓存一致性、跨城邦叠加）。

---

## 一、改动清单

### MPDLL

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +7 | `CityStateUAEffects` 建表新增 3 列及注释（`:128-134`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +16 | 效果条目类新增 3 个 getter（`:257-260`）与 3 个成员（`:431-434`）；玩家聚合类新增 3 个 getter（`:660-663`）与 3 个成员（`:833-836`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +23 | 两处构造函数初始化（`:279-281`、`:1236-1238`）、`CacheResults` 读取（`:429-431`）、6 个 getter（`:920-922`、`:1899-1901`）、`Reset` 清零（`:1350-1352`）、`ApplyEffect` 累加（`:1568-1570`） |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +21 | 商路金接入：`GetCSUATradeRouteGoldModifier` 内新增平百分数与按条计数（`:18361-18380`） |
| `CvGameCoreDLL_Expansion2/CvCity.cpp` | +19 | 食物接入：`getBaseYieldRateModifier` 内按快乐奢侈品种类数加成（`:13509-13526`） |

### SP

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 | 马尼拉 `UAType` 绑定（`:52`，`MINOR_CIV_MANILA` → `CSUA_MANILA`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +21 | 2 个效果（`:384-397`）、1 个 UA 条目（`:1599-1605`） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +25 | 3 个文本 Tag（`:20094-20120`） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +25 | 3 个文本 Tag（`:18563-18589`） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +25 | 3 个文本 Tag（`:18369-18395`） |

### 效果设计（已核对与三语文本、XML 三方一致）

| 对象 | 设计文本 | 实现 |
| --- | --- | --- |
| 盟友① | 盟友的国际商路金钱收益 +25% | `TradeRouteGoldPercentInternational=25`（平百分数） |
| 盟友② | 盟友每有一条国际商路，所有国际商路金钱额外 +2% | `TradeRouteGoldModifierPerInternationalRoute=2`，按本国国际商路条数计数后施加于每条 |
| 盟友③ | 盟友每有一种提供快乐的奢侈品，全国食物 +2% | `FoodModifierPerHappyLuxuryType=2`，落 `CvCity::getBaseYieldRateModifier(YIELD_FOOD)` |
| 朋友① | 朋友的国际商路金钱收益 +10% | `EFFECT_CSUA_MANILA_FRIEND` × `TradeRouteGoldPercentInternational=10`（盟友①的 2.5 倍缩水） |

设计稿来源：`1.城邦UA/海洋型.txt:12-16`（与 `未完成/海洋型-未完成.txt:1-5` 一致）。马尼拉在 `1.城邦UA/城邦类型.txt:17` 归类为海洋型，对应 `Gameplay/XML/CSUA/CSUA.xml` 第 38 条 `CityStateUAs` 条目。

---

## 二、问题清单

### 决策点（需拍板，非缺陷）

#### D1-1　效果②的"国际商路"是否应包含通往城邦的商路

- 位置：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvPlayer.cpp:18374`；口径注释见 `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql:131` 与 `CvPlayer.cpp:18365`
- 现象：计数条件为 `m_eOriginOwner == GetID() && IsConnectionInternational(kConnection)`。`IsConnectionInternational` 只比较起点与终点**所属队伍是否相同**（`CvTradeClasses.cpp:542-558`），因此**通往城邦的商路计入**。代码注释亦明确写了 `city-state destinations included`。
- 分歧点：设计稿中摩加迪沙特意写"每有一条**通往城邦的**国际商路"（`海洋型.txt:19`），说明设计语言里"国际商路"与"通往城邦的国际商路"是**区分开的**；马尼拉仅写"国际商路"，按此惯例应理解为**包含**城邦。实现与注释一致。
- 影响：玩家为拉影响力常把商路大量送往城邦，若计入则效果②极易拉满（商路槽位上限约 8~10，即最多 +16%~20%）。口径不同会带来明显的强度差。
- 建议：确认"包含城邦"为设计本意；若是，无需改动，但建议在设计稿中把"国际商路"统一补一句口径说明，避免后续城邦各自解释。

#### D1-2　效果③的数值与上限

- 位置：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvCity.cpp:13519`
- 现象：`iTempMod = iHappyLuxuryCount * 2`，即 **+2% × 玩家持有（含进口）的快乐奢侈品种类数**，**无上限**。
- 规模测算：缓存数据库存根（`Civ5DebugDatabase.db`，2026-09-26 23:55）中 `ResourceUsage=2`（奢侈品）且 `Happiness>0` 的资源共 **36 种**；中后期玩家常见持有 + 进口 15~25 种 → **全国食物 +30%~50%**。
- 对照：同类的温哥华是"每点快乐全国食物 +1%、魅力 +1%，**上限均为 50%**"（`CSUA.xml:322`）。马尼拉无上限，且 SP 的 58 种高级奢侈品可由盟友城邦永久供给（`1.城邦UA/高级奢侈品.txt`），盟友越多、奢侈品越多，食物加成可继续堆高。
- 影响：食物百分比直接作用于每座城市产出（与神庙等既有修正同一路径），是较强的成长加成。设计规则 15 要求加成类以"达到 100% 以上几乎不可能"为目标，单项 +50% 已接近该目标的边界。
- 建议：三选一——① 加 50% 上限与温哥华对齐；② 降为 1%/种；③ 限定为"本国拥有的奢侈品"（不含进口，见 D1-3）。若维持现状，建议在设计稿标注"无上限、预期 +30%~50%"作为已知强度。

#### D1-3　效果③是否应计入进口奢侈品

- 位置：`CIV5MPDLL/CvGameCoreDLL_Expansion2/CvPlayer.cpp:14066`（`GetHappinessFromLuxury` 内 `getNumResourceAvailable(eResource, /*bIncludeImport*/ true) > 0`）
- 现象：`GetHappyLuxuryTypeCount`（`CvPlayer.cpp:14114-14126`）以 `GetHappinessFromLuxury(eResource) > 0` 为判据，而该判据**计入进口**，故进口奢侈品同样抬升食物加成。
- 评价：作为"商路进口奢侈品 → 换取食物"的路径设计是自洽的（且与效果①②的商路主题呼应），但需确认这是设计本意；若本意是"本国物产"，需改为 `bIncludeImport=false`。
- 注：此处同时受"奢侈品衰减时代"影响——快乐随时代衰减但有 `std::max(1, …)` 下限（`CvPlayer.cpp:14044-14052`），故衰减**不会**使已持有的奢侈品从计数中掉出。

### 提示（非缺陷）

#### P3-1　DLL 编译存在头文件时序疑点，建议清理后全量重编一次

- 事实：源码与产物时间戳为 —— `CvCityStateUAClasses.h` 00:12:17、`CvPlayer.obj` 00:12:10、`CvCity.obj` 00:12:05、`CvCityStateUAClasses.obj` 00:12:23、`CvGameCore_Expansion2.dll` 00:12:34。
- 已确认：DLL **确实已重编并包含马尼拉改动**——DLL 二进制内含 `TradeRouteGoldPercentInternational` / `TradeRouteGoldModifierPerInternationalRoute` / `FoodModifierPerHappyLuxuryType` 三个新列名字符串（`grep -a -o` 各命中 1 次），且三个 `.obj` 均晚于对应 `.cpp`。
- 疑点：`.h` 的最后保存时间（00:12:17）**晚于** `CvPlayer.obj`（00:12:10）与 `CvCity.obj`（00:12:05），说明该次头文件保存发生在构建过程中。若 00:12:17 的改动仅为注释 / 空白，则无影响；若含成员布局变更，这两个目标文件可能未覆盖。
- 建议：按 CLAUDE.md 的 PCH 清理规则，删除 `BuildTemp/VS2022_CvGameCore_Expansion2ReleaseWin32` 后全量重编一次，成本很小且可彻底消除疑点。

#### P3-2　预览与 AI 对"候选商路"的计数少 1 条

- 位置：`CvPlayer.cpp:18369-18379` 遍历 `m_aTradeConnections` 计数。
- 现象：预览 / AI 评估的候选商路**尚未进入** `m_aTradeConnections`，故效果②的计数比该商路真正建立后少 1 条（少 +2%）。Tooltip 因此存在约 2% 的系统性低估。
- 评价：属可接受偏差（不影响结算值，仅影响预览显示与 AI 排序的精度），且与 `GetTradeConnectionValueTimes100` 唯一接入点（`CvTradeClasses.cpp:2663-2668`）的设计一致。仅记录。

#### P3-3　`GetHappyLuxuryTypeCount()` 未做每回合缓存，与既有优化模式不一致

- 位置：调用点 `CvCity.cpp:13516`（`getBaseYieldRateModifier`，每城 / 每产出类型反复调用的热路径）与 `CvPlayer.cpp:18359`（马六甲，商路金路径）。
- 现象：该函数每次遍历全部资源（约 56 项）。本仓库对同类"每回合不变的计数"已有既定做法：`CacheGreatWorkCounts` / `CacheWorkedHolySites` / `CacheSpecialCityMatches` / `RefreshCoastalCityCount` 均在 `RefreshCSAllUAEffects`（`CvPlayer.cpp:19931-19987`）里每回合缓存一次。
- 评价：当前绝对开销很小（每回合数万次迭代量级），不构成性能问题；但按仓库既有模式把快乐奢侈品种类数也做成每回合缓存，可统一风格并顺带省掉马六甲路径上的重复扫描。可选。

#### P3-4　食物加成的 Tooltip 无来源标识

- 位置：`CvCity.cpp:13522` 使用通用 `TXT_KEY_PRODMOD_YIELD`。
- 现象：玩家在城市产出明细里只看到一条通用"产量修正"，无法得知来自马尼拉。同文件的布拉格 / 梅尔本等用法亦同，但若希望城邦 UA 可辨识，可另立一条专属文本。

#### P3-5　跨城邦商路金叠加已突破设计规则 15（非马尼拉问题）

- 事实：马六甲 `TradeRouteGoldModifierPerLuxuryType=300`（+3%/种，20 种即 +60%，`CSUA.xml:37`）、霍尔木兹 `Modifier=400`（+4%/单位富余石油，20 单位即 +80%，`CSUA.xml:1690-1695`）、巴拿马 `TradeRouteGoldModifierPerDistance=100`（+1%/格）。
- 评价：三者同为盟友时（规则 16/17 允许电气后 5~8 盟友），单是国际商路金修正即可轻易超过 +100%，与规则 15"加成类达到 100% 以上几乎不可能"的目标不符。马尼拉自身约 +41%（25 + 8×2），属温和，**不是主要来源**；若要收敛规则 15，应优先处理马六甲 / 霍尔木兹。仅作系统性问题登记。

---

## 三、已验证无误项

1. **城邦绑定与基础数据存在**：缓存数据库中 `MINOR_CIV_MANILA` 存在，`Description` 即 `TXT_KEY_CITYSTATE_MANILA`，`UAType` 当前为空（符合"尚未用含马尼拉的模组加载过"的预期），与 `CSUA.sql:52` 的 UPDATE 匹配。
2. **描述 Tag 可解析**：`TXT_KEY_CITYSTATE_MANILA` 由基础游戏提供，`en_US` / `zh_CN` / `ZH_Hant_HK` 三套均在 `Assets/DLC/Expansion2/Gameplay/XML/Text/<lang>/CIV5GameTextInfos_CityStates_Inherited_Expansion2.xml` 有定义，SP 无需自建。
3. **写法与既有城邦同构**：`CityStateUAs` 行采用 `<Description>TXT_KEY_CITYSTATE_*</Description>` + `<Help>TXT_KEY_CSUA_*_HELP</Help>`，与 Sydney / Hormuz / Vancouver / Ife / Yerevan / Bogota / Bratislava / Riga 等既有条目一致；马尼拉为该表第 38 条。
4. **三列建表齐全且单位有注释**：`UNIQUE_CITYSTATES.sql:128-134` 三列均为 `integer DEFAULT 0`，并注明为"平百分数"（25 = +25%、2 = +2%/条、2 = +2%/种），与 C++ 的取用方式一致（`TradeRouteGoldPercentInternational` 直接相加、其余两条在代码中按整数乘法后相加，均未再除 100）。
5. **读取链路完整**：`CacheResults`（`CvCityStateUAClasses.cpp:429-431`）→ 两处构造函数初始化（`:279-281`、`:1236-1238`）→ 6 个 getter（`:920-922`、`:1899-1901`）→ `Reset` 清零（`:1350-1352`）→ `ApplyEffect` 按 `iChange` 累加（`:1568-1570`），无遗漏分支。
6. **盟友 / 朋友互斥且归属正确**：`RefreshCSAllUAEffects` 以 `IsAllies` 优先、`else if IsFriends` 择一应用（`CvPlayer.cpp:19957-19964`），盟友不会叠加朋友效果；效果存于**盟友玩家**的 `m_pCityStateUA`，城市级消费点取 `owner.GetPlayerCityStateUA()`（`CvCity.cpp:13490`），故食物加成落在盟友的城市而非城邦自身。
7. **商路金唯一接入点、三路径全覆盖**：`GetCSUATradeRouteGoldModifier` 仅在 `GetTradeConnectionValueTimes100` 的 `YIELD_GOLD` 国际分支被调用（`CvTradeClasses.cpp:2663-2668`），结算、预览总分项、AI 评估共用该函数；且该函数首行即 `if (!IsConnectionInternational(...)) return 0`（`CvPlayer.cpp:18354`），与设计"仅国际商路"一致。
8. **百分比语义正确**：马尼拉的 +25% / +2%×N 并入 `iModifier`（初值 100）后由 `iValue *= iModifier; iValue /= 100` 整体乘算（`CvTradeClasses.cpp:2710-2711`），即"商路金钱收益 +25%"作用于基础值 + 全部加成之和，符合既有商路金修正的通用语义。
9. **只作用于起点方**：`kOriginPlayer.GetCSUATradeRouteGoldModifier(...)` 取的是**起点玩家**的聚合效果（`CvTradeClasses.cpp:2667`），而 YIELD_GOLD 分支整体位于 `if (bAsOriginPlayer)` 内（`:2624`），故终点方不受影响——与设计"盟友的商路收益"（终点方本就不获得商路金）一致。
10. **食物加成落点正确**：`CvCity::getBaseYieldRateModifier`（函数起于 `:13399`）是城市产出百分比的统一入口（产出 = `iBaseYield × getBaseYieldRateModifier / 100`），逐城施加 +2%×种类数即等价于设计所述"全国食物 +2%/种"；且与神庙等既有食物修正同一路径，可正常作用于人口增长。
11. **预览 Tooltip 与实际同源**：`TradeRouteHelpers.lua:24` 调用 `pPlayer:GetCSUATradeRouteGoldModifier(...)`，`:111` 计入百分比合计、`:126-129` 单独列出 CSUA 条目（Tag `TXT_KEY_CHOOSE_INTERNATIONAL_TRADE_ROUTE_ITEM_TT_CS_UA`，已存在于 `TextInfos_zh_CN.xml:18484`）；Lua 侧构造 `TradeConnection` 时显式给出起点 / 终点所属玩家，`IsConnectionInternational` 按队伍比较故可正确判定（`CvLuaPlayer.cpp:4417-4437`，注册于 `:1250`）。
12. **数值三方一致**：设计稿（`海洋型.txt:12-16`）、SP XML、三语文本的 25 / 2 / 2 / 10 逐条对应，无偏差；盟友①为朋友①的 2.5 倍，符合设计规则 2 的 2~3 倍要求；三条效果均为百分比乘数或按数量缩放，无固定数值，符合规则 9/12 的"路径"原则。
13. **文本规范**：三个 Tag 均追加于各语言文件**末尾**（未打乱既有分组）；`[ICON_GOLD]奢侈品` 的写法与既有 9 处一致，`[ICON_INTERNATIONAL_TRADE]` 在三个文件中分别有 24 / 22 / 24 处既有用例；`TXT_KEY_CSUA_MANILA_HELP`（含盟友 + 朋友两段）与 `TXT_KEY_EFFECT_CSUA_MANILA_ALLY_HELP` / `..._FRIEND_HELP`（各一段）的分工与 Riga / Bogota / Bratislava 写法一致，服务于不同 UI 位置，无需改动。
14. **行尾格式保持**：SP 与 MPDLL 的 10 个改动文件均为纯新增（`git diff --stat` 无删除行、无整文件重写）；`CvCity.cpp` 保持 CRLF（CR=6625 / LF=6625），其余文件保持 LF（CR=0），未发生行尾破坏。
15. **每回合重建、无需版本门控**：`CvPlayerCityStateUA` 无 `Read` / `Write`，效果在 `RefreshCSAllUAEffects` 中 `Reset()` 后全量重建，随 `doTurn` 与盟友 / 朋友关系变化触发；本次新增数据不涉及存档序列化，符合 CLAUDE.md 的版本门控适用条件（无新增序列化成员）。
16. **DLL 已包含本次改动**：`(1) CIV5MPDLL/DLL/CvGameCore_Expansion2.dll` 时间戳 2026-09-27 00:12:34，二进制内含三个新列名字符串；`CvPlayer.obj` / `CvCity.obj` / `CvCityStateUAClasses.obj` 均晚于对应 `.cpp`（时序细节见 P3-1）。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff`，核对改动规模与行尾。
- 交叉核对 C++ 实现、SQL 建表语句与注释、XML 数据、三语文本四者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvGameTrade::IsConnectionInternational`（`CvTradeClasses.cpp:542`）、`CvPlayer::GetTradeConnectionValueTimes100` 的 `YIELD_GOLD` 分支（`:2624-2712`）、`CvPlayer::GetCSUATradeRouteGoldModifier`（`CvPlayer.cpp:18350`）、`CvPlayer::GetHappyLuxuryTypeCount`（`:14114`）、`CvPlayer::GetHappinessFromLuxury`（`:14037`，进口判定 `:14066`）、`CvCity::getBaseYieldRateModifier`（`CvCity.cpp:13399`，加成本次落点 `:13509`）、`CvPlayer::RefreshCSAllUAEffects`（`CvPlayer.cpp:19931`）、`CvPlayerCityStateUA::ApplyEffect`（`CvCityStateUAClasses.cpp:1784` 附近）。
- 查询缓存数据库 `Civ5DebugDatabase.db`：确认 `MINOR_CIV_MANILA` 存在及其 `UAType` 现状；统计 `ResourceUsage=2` 且 `Happiness>0` 的奢侈品种类共 36 种，作为效果③强度测算依据。
- 查询基础游戏 `Assets/DLC/Expansion2/.../Text/{en_US,zh_CN,ZH_Hant_HK}/` 确认三语言 `TXT_KEY_CITYSTATE_MANILA` 均有定义。
- 以 `grep -a -o` 在 DLL 二进制中检索三个新列名字符串，确认产物包含本次改动；比对 `.cpp` / `.obj` / `.dll` 时间戳判断构建完整性。
- 与既有同类实现横向对照：马六甲（`TradeRouteGoldModifierPerLuxuryType=300`，`CvPlayer.cpp:18359`）、巴拿马（`TradeRouteGoldModifierPerDistance=100`）、霍尔木兹（`Modifier=400`）、温哥华（50% 上限）作为强度与写法基准。

---

## 五、当前状态与建议处理顺序

### 状态

- MPDLL 工作区：5 文件 +86 / −0（未 commit）；DLL 已重编，产物在 `(1) CIV5MPDLL/DLL/`（00:12:34）
- SP 工作区：5 文件 +97 / −0（未 commit）
- 游戏根目录 DLL（`Documents\My Games\Sid Meier's Civilization 5\CvGameCore_Expansion2.dll`）仍为 2026-08-11 旧版，**尚未覆盖**
- 尚未构建模组（MODS 目录下无 SP 文件夹）
- 附带发现：`未完成/未完成清单.md`（写于 09-26 23:27）已滞后——里加已于 09-27 00:02 提交（`392d0d3`）却仍列在未完成中；马尼拉完成后该表海洋型未完成应剩 5 项（摩加迪沙、蒙巴萨、魁北克、拉古萨、乌尔）

### 建议顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | D1-1 / D1-2 / D1-3 拍板（商路口径、食物数值与上限、是否含进口） | 小 |
| 2 | P3-1 清理 `BuildTemp` 后全量重编一次，消除头文件时序疑点 | 小 |
| 3 | 覆盖根目录 DLL 或构建模组，按下述步骤实机验证 | 小 |
| 4 | ~~P3-3 缓存快乐奢侈品种类数 / P3-4 专属 Tooltip 文本~~ → **已完成**（见第七节） | — |
| 5 | P3-5 规则 15 的系统性收敛（马六甲 / 霍尔木兹） | 另议 |

### 实机验证步骤

1. **盟友效果①**：与马尼拉结盟，跑一条**国际**商路（起点为自己），对比无盟友时的商路金，应见 +25%（再叠加效果②的按条部分）。
2. **盟友效果②**：增加国际商路条数，逐条观察每条国际商路金同步上升；把商路改送城邦，确认**计数同样增加**（验证 D1-1 的当前口径）。
3. **预览一致性**：打开商路选择界面，Tooltip 中应出现 CS UA 百分比条目，其值 = 25 + 2×当前国际商路条数，且与百分比合计、总分一致。
4. **盟友效果③**：城市产出明细（或鼠标悬停食物）应出现 +2%×持有（含进口）快乐奢侈品种类数的食物修正；进口一种新奢侈品后应再 +2%。
5. **朋友效果**：与马尼拉为朋友（非盟友），应仅见 +10%，**无**按条计数、**无**食物加成。
6. **负例**：与马尼拉断交后，上述条目应全部消失（验证 `RefreshCSAllUAEffects` 的重建路径）。

---

# 六、审查问题处理回应（2026-09-27）

> 处置人：Claude；处置范围：全部决策点 + 全部提示项。DLL 已按 P3-1 建议清理中间产物后**全量重编**（`EXIT=0`）。

## 决策点

### D1-1　效果②的"国际商路"是否包含通往城邦的商路 —— **维持包含，不改代码**

- 处置：维持现状，计数条件不变（`m_eOriginOwner == GetID() && IsConnectionInternational`），代码注释 `city-state destinations included` 保留。
- 依据：设计已确认"城邦也算国际"。设计稿用词上，摩加迪沙特意写"每有一条**通往城邦的**国际商路"，而马尼拉只写"国际商路"，二者用词区分即表明马尼拉的"国际商路"是**上位概念**（含城邦）。
- 强度确认：商路槽位上限约 8~10，效果②封顶 +16%~20%；叠加效果①的 +25%，马尼拉自身商路金合计约 **+41%~45%**，属温和区间（对照 P3-5 中马六甲单城邦即可 +60%）。
- 未采纳的备选：无。

### D1-2　效果③的数值与上限 —— **已加 +50% 上限（采纳建议①）**

- 处置：新增数据列 `FoodModifierPerHappyLuxuryCap`（`integer DEFAULT 0`，**0 = 不限制**），马尼拉 `EFFECT_CSUA_MANILA_ALLY` 设 **50**。上限作用于效果③自身产生的百分比（`iTempMod` 截断），不波及其他来源的城市食物修正。
- 方式选择：采用**数据驱动**而非硬编码常量——与既有 cap 类字段（温哥华 `HappinessYieldModifierCap`）风格一致，且后续其他城邦可复用。
- 触顶点：36 种奢侈品 × 2% = 72% 的理论值被截到 +50%，即**持有 25 种快乐奢侈品时触顶**；中后期常见的 15~25 种对应 +30%~50%，上限只在极端堆叠时生效。
- 同步更新：三语文本在效果③后补"（上限+50%）"/"(up to +50%)"，避免玩家误读为无上限。
- 改动文件：`UNIQUE_CITYSTATES.sql`、`CvCityStateUAClasses.h/.cpp`（Effect 与聚合类各 +1 字段）、`CvCity.cpp`（应用截断）、`CSUA.xml`、三语 `TextInfos_*.xml`。
- 未采纳的备选：② 降为 1%/种 —— 会使盟友③显著弱于朋友①的相对强度关系，且设计稿明写 2%，故不采纳；③ 限定本国物产 —— 见 D1-3。

### D1-3　效果③是否计入进口奢侈品 —— **维持计入，不改代码**

- 处置：维持 `GetHappyLuxuryTypeCount()` 现有口径（`bIncludeImport = true`）。
- 理由：
  1. **口径统一**：该函数同时被马六甲 `TradeRouteGoldModifierPerLuxuryType` 使用，单方面改为不含进口会造成两个城邦对"奢侈品"定义不一致；
  2. **主题自洽**：效果①②均围绕国际商路，进口奢侈品恰是经由商路流入，三条效果共享"商路 → 收益"的设计闭环；
  3. **计数稳定**：报告注 74 已确认时代衰减有 `std::max(1, …)` 下限，已持有奢侈品不会掉出计数，不存在"加成随时代缩水"的副作用。
- 备选路径（若日后需改）：为 `GetHappyLuxuryTypeCount` 增加 `bIncludeImport` 参数并同步评估马六甲口径；当前无此需求。

## 提示项

### P3-1　DLL 编译时序疑点 —— **已按建议清理并全量重编**

- 处置：删除 `BuildTemp/VS2022_CvGameCore_Expansion2ReleaseWin32` 后全量重编，`EXIT=0`，无 error。
- 验证：产物 `BuildOutput/VS2022_ReleaseWin32/CvGameCore_Expansion2.dll` 内含 4 个新列名字符串，各命中 1 次——`TradeRouteGoldPercentInternational`、`TradeRouteGoldModifierPerInternationalRoute`、`FoodModifierPerHappyLuxuryType`、`FoodModifierPerHappyLuxuryCap`。时序疑点已消除。

### P3-2　预览与 AI 对候选商路的计数少 1 条 —— **接受，不修改**

- 处置：维持现状。系统性约 −2% 的低估仅影响 Tooltip 显示与 AI 排序精度，不影响实际结算值；且与 `GetTradeConnectionValueTimes100` 唯一接入点的既有设计保持一致。若为此在候选路径上打补丁，反而会引入"预览与结算两条计数逻辑"的维护负担。

### P3-3　`GetHappyLuxuryTypeCount()` 未做每回合缓存 —— **已修复**（2026-09-27 补做，见第七节）

- 处置：按 `RefreshCSAllUAEffects` 既有模式新增 `CvPlayerCityStateUA::CacheHappyLuxuryCount()`（`.h` 加声明 + `m_iCachedHappyLuxuryCount` 成员；`.cpp` 加构造初始化、`Reset`、getter 与实现），在 `CvPlayer::RefreshCSAllUAEffects` 中紧随 `CacheSpecialCityMatches()` 每回合刷新一次。
- 免开销设计：缓存函数以 `m_iFoodModifierPerHappyLuxuryType == 0` 提前返回——未持有马尼拉食物效果的玩家（绝大多数）不做任何资源扫描。
- 覆盖范围：只覆盖马尼拉所在的热路径（见 P3-4 的新落点）。马六甲的 `GetCSUATradeRouteGoldModifier` 商路金路径仍直调 `GetHappyLuxuryTypeCount()`；该路径仅在商路结算 / 预览 / AI 评估时触发，频率远低于"逐城逐产出"的产出修正热路径，暂不纳入，避免缓存失效时机（盟友关系、资源进出口在回合内可变）扩散到商路金。

### P3-4　食物加成的 Tooltip 无来源标识 —— **已修复**（2026-09-27 补做，见第七节）

- 根因：`TXT_KEY_PRODMOD_CITYSTATE_UA`（"来自城邦修正: {1_Num}%"）此前只用于走 `CvPlayer` 全局聚合层的四类 CSUA（热那亚 / 维尔纽斯 `GetCSUAYieldPercentModifier`、悉尼 `GetCSUAImmigrantYieldModifierFromImmigrants`、耶路撒冷 / 维滕贝格 `GetCSUACapitalYieldModifierPerFollowingCity`、梵蒂冈 `GetCSUAHolyCityYieldModifierPerFollowingCity`，见 `CvCity.cpp:13619-13669`）；而按城市本地条件逐城判定的 CSUA（布拉格 / 梅尔本 / 波哥大 / 布拉迪斯拉发 / 塔那那利佛）统一用通用 `TXT_KEY_PRODMOD_YIELD`。马尼拉初版被放进后一族，故显示为通用"产量修正"。
- 口径确立：**全局型加成一律走 `GetCSUAYieldPercentModifier`（专属 tag），本地型继续用通用 tag**。马尼拉食物加成虽然按城市展示，但数值是**全国统一**的（只依赖 `owner.GetHappyLuxuryTypeCount()`，与城市自身无关），语义上属全局型。
- 实施：删除 `CvCity.cpp` 中的马尼拉食物块，改并入 `CvPlayer::GetCSUAYieldPercentModifier`（`CvPlayer.cpp:18324-18338`）。该函数由 `CvCity.cpp:13621` 每城调用并以 `TXT_KEY_PRODMOD_CITYSTATE_UA` 输出，显示随之变为"来自城邦修正: X%"。
- 无需新增文本：`TXT_KEY_PRODMOD_CITYSTATE_UA` 三语文本均已存在。
- 未改动：布拉格 / 梅尔本 / 波哥大 / 布拉迪斯拉发 / 塔那那利佛五处逐城型落点保持通用 tag，符合上述口径。

### P3-5　跨城邦商路金叠加突破规则 15 —— **登记，非本次范围**

- 处置：本次不处理。马尼拉自身约 +41%（25 + 8×2），且效果②受商路槽位天然上限约束，**不是主要来源**；规则 15 的收敛应优先处理马六甲（+3%/种）与霍尔木兹（+4%/富余单位），另议。

## 其他

- **附带发现（未完成清单滞后）**：`未完成/未完成清单.md` 仍将里加列为未完成，而里加已于 09-27 00:02 提交（`392d0d3`）。马尼拉完成后，海洋型未完成项应为 5 项（摩加迪沙、蒙巴萨、魁北克、拉古萨、乌尔）。本次未改动该清单，待用户确认后统一刷新。
- **改动规模（更新，含上限改动与第七节补做）**：
  - MPDLL：4 文件 **+120 / −0**（较首轮 +86 增加 34 行：SQL +2、`CvCityStateUAClasses.h` +8、`.cpp` +14、`CvPlayer.cpp` +40；`CvCity.cpp` 经第七节回退后净变动为 0）
  - SP：5 文件 **+98 / −0**（较首轮 +97 增加 1 行：`CSUA.xml` 的 cap 行；三语文本为同行内追加，不计增行）
- **行尾格式**：本轮新增/修改的文件均复检通过，`CvCity.cpp` 保持 CRLF，其余保持 LF，无混合。
- **DLL 状态**：已全量重编（本轮），产物在 `BuildOutput/VS2022_ReleaseWin32/`；游戏根目录 DLL 与 MODS 目录仍**未更新**（用户选择暂不构建）。
- **实机验证补充**：第 4 步"盟友效果③"需追加一项——持有 25 种以上快乐奢侈品时，食物加成应**停在 +50%** 不再上升（验证新上限）；且该条目应显示为「来自城邦修正: X%」而非通用「产量修正」。

---

# 七、Tooltip 归属问题与补做（2026-09-27）

> 触发：用户实机观察到效果③的食物加成显示在**通用"产量修正"**条目，而非**城邦 UA 专属**条目，询问原因。

## 现象与根因

城市产出明细由 C++ 侧 `CvGame::BuildProdModHelpText` 输出，每个加成点自带一个文本 tag。CSUA 在此文件里分两族：

| 族 | 判定方式 | 代表城邦 | 使用的 tag |
| --- | --- | --- | --- |
| 全局聚合型 | 走 `CvPlayer` 聚合层，数值全国统一 | 热那亚 / 维尔纽斯、悉尼、耶路撒冷 / 维滕贝格、梵蒂冈 | `TXT_KEY_PRODMOD_CITYSTATE_UA` |
| 逐城本地条件型 | 每座城市各自判定本地条件 | 布拉格、梅尔本、波哥大、布拉迪斯拉发、塔那那利佛 | `TXT_KEY_PRODMOD_YIELD` |

马尼拉初版被插在布拉格块旁并沿用了后一族的通用 tag（`CvCity.cpp:13525`），因此显示为通用条目。但其食物加成实际是**全国统一值**，语义上属前一族——这是 P3-4 所述现象的根因，初版判断有偏差。

## 处置（用户口径）

> "全局加成都要写入 `GetCSUAYieldPercentModifier`，本地的可以用通用的。"

1. **删除** `CvCity.cpp` 中的马尼拉食物块（该文件回退至与 HEAD 一致，净变动 0）。
2. **并入** `CvPlayer::GetCSUAYieldPercentModifier`（`CvPlayer.cpp:18324-18338`），以平百分数转 basis points（`iTotal * 100`）累加，与 Bogota / Vancouver 等全局项的写法一致。该函数由 `CvCity.cpp:13621` 每城调用并以 `TXT_KEY_PRODMOD_CITYSTATE_UA` 输出，显示自动变为「来自城邦修正: X%」。
3. **新增缓存**（同时解决 P3-3）：`CvPlayerCityStateUA::CacheHappyLuxuryCount()` + `m_iCachedHappyLuxuryCount`，在 `RefreshCSAllUAEffects` 中紧随 `CacheSpecialCityMatches()` 每回合刷新；`m_iFoodModifierPerHappyLuxuryType == 0` 时提前返回，未结盟玩家零开销。
4. **不改动**五处逐城型落点（符合上述口径，避免影响既有城邦的显示风格）。

## 验证

- 编译：清理 `BuildTemp/VS2022_CvGameCore_Expansion2ReleaseWin32` 后全量重编，`EXIT=0`、0 error。
- 符号：产物 DLL 内含 `FoodModifierPerHappyLuxuryCap` 字符串（`CacheHappyLuxuryCount` 等函数名在 Release 下被内联，不保留符号，属正常）。
- 行尾：`CvCity.cpp` 保持 CRLF；`CvPlayer.cpp`、`CvCityStateUAClasses.h/.cpp` 保持 LF。
- 待实机：与马尼拉结盟后，城市产出明细中食物加成应出现在**「来自城邦修正: X%」**条目；持有奢侈品数量变化时，该值应于**下一回合**更新（缓存刷新时机）。

---

# 八、复审结论（2026-09-27）

> 触发：用户要求「根据回应进行复审」，即对第六、七节所声明的每一处处置，逐条与实际代码、产物对账。

## 8.1 逐条核验结果

| # | 回应声明 | 核验方式 | 结论 |
| --- | --- | --- | --- |
| D1-1 | 效果②维持「含城邦商路」 | 读 `CvPlayer.cpp:18385` 附近循环，仅以 `IsConnectionInternational` 判定 | **属实**（口径确认，非缺陷） |
| D1-2 | 新增 `FoodModifierPerHappyLuxuryCap`=50 | `UNIQUE_CITYSTATES.sql` 建表列、`CSUA.xml` 取值、三语文本说明 | **属实**（详见 8.2） |
| D1-3 | 效果③维持「计入进口」 | `CvPlayer.cpp:14066` `bIncludeImport=true`；`std::max(1,…)` 衰减下限 | **属实**（口径确认） |
| P3-1 | 清理 BuildTemp 后全量重编 | 见 8.3 时间戳链 | **属实** |
| P3-2 | 接受不修改（分项预览函数） | 未改动 `TradeRouteHelpers.lua` | **属实** |
| P3-3 | 新增 `CacheHappyLuxuryCount()` | 类声明 `.h:766-770`、成员 `.h:922-923`、实现 `.cpp:2191-2202`、调用 `CvPlayer.cpp:20002` | **属实** |
| P3-4 | 马尼拉食物块迁入 `GetCSUAYieldPercentModifier` | `CvPlayer.cpp:18324-18338` 存在；`CvCity.cpp` 不在 `git status` 中（净 0） | **属实** |
| P3-5 | 登记另议 | — | 无需核验 |

**改动规模对账**：MPDLL `git diff --stat` = 4 文件 **+120 / −0**；SP = 5 文件 **+98 / −0**。与第六节声明完全一致。

## 8.2 上限链路完整性（三语言 + 三层）

- **SQL 建表**：`UNIQUE_CITYSTATES.sql:128-137` 含 `FoodModifierPerHappyLuxuryCap integer DEFAULT 0`，注释「0 = uncapped」。
- **聚合层**：`ApplyEffect`（`.cpp:1578`）累加 → `Reset`（`:1358`）归零 → 构造（`:1242`）初始化 → getter（`:1910`）。
- **消费层**：`CvPlayer.cpp:18324-18338` 仅截断马尼拉自身贡献（`iCap > 0 && iTotal > iCap`），`iMod += iTotal * 100` 与函数末尾 `return iMod / 100` 单位自洽。
- **文本**：三语言均已同步，**第七节遗留的待确认项已闭环**：
  - `zh_CN:18568/18579`「…全国食物+2%（上限+50%）」
  - `en_US:20099/20110`「…the nation gains +2% Food (up to +50%)」
  - `zh_Hant:18374/18385`「…全國食物+2%（上限+50%）」

## 8.3 编译时序疑点已澄清

上一轮存疑的「`.h` 晚于 `.obj`」在本次复核中已被新时间戳链推翻——期间发生过一次完整重编：

| 文件 | 时间 |
| --- | --- |
| `CvCityStateUAClasses.h` | 01:00:13 |
| `CvCityStateUAClasses.cpp` | 01:01:15 |
| `CvCity.cpp`（回退，内容净 0） | 01:01:46 |
| `CvPlayer.cpp` | 01:02:04 |
| `CvGameCore_Expansion2.pch` | **01:02:53**（晚于全部头文件改动 → PCH 确已重建） |
| `CvCity.obj` / `CvPlayer.obj` | 01:03:35 / 01:04:04 |
| `CvGameCore_Expansion2.dll` | **01:04:13**（晚于全部源码） |

产物共两份，内容一致（5317120 字节，均含 `FoodModifierPerHappyLuxuryCap`、`FoodModifierPerHappyLuxuryType`、`TradeRouteGoldModifierPerInternationalRoute` 三个字符串，各命中 1 次）：
`BuildOutput/VS2022_ReleaseWin32/` 与 `(1) CIV5MPDLL/DLL/`。
游戏根目录 DLL 与 MODS 目录仍未更新，与「用户选择暂不构建」一致。

**行尾复检**：`CvPlayer.cpp`、`CvCityStateUAClasses.h/.cpp`、`UNIQUE_CITYSTATES.sql` 均 CR=0（LF）；`CvCity.cpp` CR=25751/LF=25751（CRLF）；SP 三个文本文件 CR=0（LF）。无混合、无破坏。

## 8.4 复审新发现

### D2-1（文档级）第七节引用的行号已过时

第七节写「该函数由 `CvCity.cpp:13621` 每城调用」，实测调用点为 **`CvCity.cpp:13599`**；`13621` 现在是耶路撒冷/维滕贝格块的 `if (isCapital())`。属文档笔误，不影响功能，建议顺手订正以免后续检索误导。

### D2-2（代码级，当前无害）cap 在聚合层用加法而非取最大值

`CvCityStateUAClasses.cpp:1578`：

```cpp
m_iFoodModifierPerHappyLuxuryCap += pEffect->GetFoodModifierPerHappyLuxuryCap() * iChange;
```

cap 的语义是「上限」，多个来源并存时应当是**取更严者（max）**，而不是**相加**。当前只有马尼拉一条效果携带非零 cap（朋友行未填该列），因此相加与取最大值结果相同，**暂无实际影响**。但若未来第二个城邦也带 cap（例如「每 X 得 +2% 食物，上限 +30%」），两者的上限会被叠加成 80%，玩家反而获得超出任一设计意图的额度。

建议二选一：改为 `if (pEffect->Get…Cap() * iChange > m_i…Cap) m_i…Cap = …;`，或保留加法但在该行加英文注释明确「本列设计为全局唯一，多城邦同时携带时上限相加，属已知取舍」。此条**不阻塞**马尼拉上线。

## 8.5 复审总体结论

第六、七节声明的处置**全部属实且已落地**，无虚假陈述；马尼拉 UA 的效果① ② ③ 全链路（设计稿 → SQL → XML → C++ 读取/聚合/缓存/消费 → 预览 → 三语文本）一致，DLL 为改动后全量重编产物。仅剩 8.4 两项非阻塞项，其中 D2-2 建议在下一个带 cap 的城邦设计定稿前处理。

**仍未决（待用户拍板）**：
1. `未完成/未完成清单.md` 是否刷新（仍滞后：将已提交的里加列为未完成）。
2. 是否覆盖游戏根目录 DLL / 构建模组（当前选择暂不构建）。
