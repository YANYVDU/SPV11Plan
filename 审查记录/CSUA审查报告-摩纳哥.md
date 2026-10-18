# CSUA 审查报告：摩纳哥（Monaco）

- 审查日期：2026-10-01
- 审查对象：工作区未提交改动（尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`）
- 改动规模：MPDLL 11 文件 **+236 / −2**；SP 6 文件 **+93 / −0**
- 权威设计稿：`d:\Git\CIV5\dyy\SP V11\1.城邦UA\文化型.txt:64-69`；实现方案：`d:\Git\CIV5\dyy\SP V11\未完成\摩纳哥-实现清单.md`
- 结论摘要：三条盟友效果（A 旅游转化 / B 首次馈赠下注 / C 黄金时代维护费）+ 一条朋友效果（D 旅游转化缩水版）**数值与档位逐条对得上设计稿**，两张新子表、主表新列、序列化、Lua 导出、UI tooltip、三语文本均已落地。**发现 1 项应修正缺陷（B-1：下注未按「城邦」限定，对任意城邦赠金都会触发）**——该缺陷沿袭自既有加德满都「首次馈赠信仰返还」实现，根因相同，建议一并修。另有 5 项提示（非缺陷）。

---

## 一、改动清单

### MPDLL

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `(1) CIV5MPDLL/DB/UNIQUE_CITYSTATES/UNIQUE_CITYSTATES.sql` | +26 / −1 | 主表 `CityStateUAEffects` 增列 `GoldenAgeBuildingMaintenanceMod`（`:205-209`）；新增子表 `CityStateUAEffect_YieldToYield`（`:354-362`）与 `CityStateUAEffect_GoldDonationGamble`（`:364-373`） |
| `CvGameCoreDLL_Expansion2/CvCity.cpp` | +14 / −0 | `GetYieldRateFromUCSConversion` 城邦循环内追加无条件 yield→yield 转化分支（`:15327-15339`），含 `YIELD_TOURISM` → `GetBaseTourism()` 特判 |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.h` | +31 / −0 | 新结构体 `YieldToYieldEntry`/`GoldDonationGambleEntry`（`:84-95`）；effect 级 `GetYieldToYield` 声明（`:445`）、`GetGoldDonationGambleEntries`（`:447`）、成员 `m_iGoldenAgeBuildingMaintenanceMod`/`m_vYieldToYield`/`m_vGoldDonationGamble`（`:630 / 658-659`）；player 级 `m_iGoldenAgeBuildingMaintenanceMod`/`m_vGoldDonationGamble`（`:1198-1199`）与 `HasGoldDonationGamble`/`GetGoldDonationGambleEntries`（`:902-903`） |
| `CvGameCoreDLL_Expansion2/CvCityStateUAClasses.cpp` | +66 / −0 | effect 构造初始化（`:341`）、主表列读取（`:510`）、两张子表解析块（`:752-788`）、`GetGoldenAgeBuildingMaintenanceMod`（`:1320`）、`GetYieldToYield`（`:1484-1493`）；player 构造（`:1679`）/`Reset`（`:1811`）/`ApplyEffect`（`:2089-2097`）/getter（`:2585`） |
| `CvGameCoreDLL_Expansion2/CvMinorCivAI.h` | +2 / −0 | 成员 `m_abGoldGambleUsedThisTurn[MAX_MAJOR_CIVS]`（`:682-683`） |
| `CvGameCoreDLL_Expansion2/CvMinorCivAI.cpp` | +19 / −0 | `Reset` 清零（`:1977`）、序列化读/写（`:2120 / 2199`）、`DoTurn` 每回合重置（`:2380-2382`）、`DoGoldGiftFromMajor` 下注段（`:10909-10919`） |
| `CvGameCoreDLL_Expansion2/CvPlayer.h` | +6 / −0 | 三个新公开声明（`:1907-1912`） |
| `CvGameCoreDLL_Expansion2/CvPlayer.cpp` | +49 / −0 | `HasCSUAGoldDonationGamble`（`:33105-33110`）、`GetCSUAGoldDonationGambleMultiplier`（`:33112-33141`，含掷骰）、`GetCSUABuildingMaintenanceMod`（`:33143-33152`） |
| `CvGameCoreDLL_Expansion2/CvTreasury.cpp` | +12 / −1 | `GetBuildingGoldMaintenance` 并入 CSUA 维护费修正（`:823-831`）+ 全局非负钳位（`:856-858`） |
| `CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.h` | +1 / −0 | `lHasCSUAGoldDonationGamble` 声明（`:335`） |
| `CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.cpp` | +10 / −0 | `Method(HasCSUAGoldDonationGamble)` 注册（`:448`）+ 实现（`:3649-3654`） |

### SP

| 文件 | 增/删 | 说明 |
| --- | --- | --- |
| `Gameplay/XML/CSUA/CSUA.sql` | +1 / −0 | 城邦绑定 `MINOR_CIV_MONACO` → `CSUA_MONACO`（`:69`） |
| `Gameplay/XML/CSUA/CSUA.xml` | +52 / −0 | 2 个效果行（`:531-539`）+ 两张子表数据（`:768-803`）+ 1 个 UA 条目（`:1933-1939`） |
| `Gameplay/XML/Localization/TextInfos_en_US.xml` | +12 / −0 | 4 个文本 Tag（`:20588-20599`） |
| `Gameplay/XML/Localization/TextInfos_zh_CN.xml` | +12 / −0 | 4 个文本 Tag（`:19057-19068`） |
| `Gameplay/XML/Localization/TextInfos_zh_Hant_HK.xml` | +12 / −0 | 4 个文本 Tag（`:18863-18874`） |
| `UI/InGame/Popups/CityStateDiploPopup.lua` | +4 / −0 | 馈赠按钮 tooltip 追加「下注」说明（`:1147-1150`） |

### 效果设计对照表

| 对象 | 设计文本 | 实现 | 判定 |
| --- | --- | --- | --- |
| 盟友 A | 盟友城市 100% 的魅力转化为城市的金钱产出 | `CityStateUAEffect_YieldToYield`：ALLY 行 `YIELD_TOURISM → YIELD_GOLD`，`Mod=100`；`CvCity.cpp:15329-15339` 以 `GetBaseTourism()` 为源、`×100/100` 累加，返回值在 `getBaseYieldRateModifier` **之后**经 `getBasicYieldRateTimes100` 追加（`CvCity.cpp:14233-14242`） | **符合设计** |
| 盟友 B | 首次金钱馈赠视为下注——45% 无收益、35% 全额返还、15% 双倍、4% 三倍、1% 十倍 | `GoldDonationGamble` ALLY 4 行 `3500/100`、`1500/200`、`400/300`、`100/1000`（Σ=5500）；`CvPlayer.cpp:33129` `denom=max(Σ,10000)` → 45% 落空、35/15/4/1 依次；`CvMinorCivAI.cpp:10909-10919` 挂点 | **数值符合、触发范围不符**（见 B-1） |
| 盟友 C | 盟友黄金时代内来自建筑的维护费 −50% | `GoldenAgeBuildingMaintenanceMod=-50`；`CvTreasury.cpp:823-831` 并入政策同一乘池，`GetCSUABuildingMaintenanceMod`（`CvPlayer.cpp:33143-33152`）以 `isGoldenAge()` 门控；末尾非负钳位 | **符合设计** |
| 朋友 D | 朋友城市 40% 的魅力转化为城市的金钱产出 | `CityStateUAEffect_YieldToYield`：FRIEND 行 `Mod=40`；朋友 effect 行无 B/C 数据 | **符合设计** |

设计稿来源：`1.城邦UA/文化型.txt:64-69`。绑定 `MINOR_CIV_MONACO`、`CSUA_MONACO` 与 `CityStateUAs` 条目一致，无命名错位；`MINOR_CIV_MONACO` / `TXT_KEY_CITYSTATE_MONACO` 均确在 Expansion2 本体定义（`Assets/DLC/Expansion2/Gameplay/XML/Civilizations/CIV5MinorCivilizations.xml:187-190`），属文化型城邦（`MINOR_TRAIT_CULTURED`），与设计归类一致。

---

## 二、问题清单

### 应修正

#### B-1　效果 B 的下注未按「城邦」限定：对任意城邦赠金都会触发（沿袭自加德满都）

- 位置：判定 `CvMinorCivAI.cpp:10911-10912`（`GET_PLAYER(ePlayer).HasCSUAGoldDonationGamble()`），取值 `CvPlayer.cpp:33105-33110`。
- 现象：`HasCSUAGoldDonationGamble()` 读的是 `m_pCityStateUA->HasGoldDonationGamble()`，即「**该玩家**是否处于摩纳哥盟友态」，**与当前正在收款的城邦 `this` 无关**。于是玩家同时为摩纳哥与其它城邦盟友时：
  1. 给**布鲁塞尔**（任意非摩纳哥城邦）赠金 → 仍落在布鲁塞尔的 `DoGoldGiftFromMajor`，守卫通过、掷骰并返还金钱；且置位的是**布鲁塞尔**的 `m_abGoldGambleUsedThisTurn`；
  2. 随后同回合再给**摩纳哥**赠金 → 摩纳哥自己的标记仍为 false → **再次掷骰**。
- 后果：(a) 下注可被**任意城邦的馈赠**触发；(b) 一回合内可**多次触发**（每赠一个城邦各一次）。与设计清单 §3「对其它城邦馈赠不计入、不消耗」直接相悖（`摩纳哥-实现清单.md:178`）。
- 同类既有问题：加德满都的信仰返还为完全相同的写法——`CvMinorCivAI.cpp:10899` 守卫 + `CvPlayer.cpp:33100`（`GetCSUAFaithRefundPerDonationPercent`）同样是玩家级判定。即加德满都亦会「给别的城邦也返还信仰、可一回合多次」。摩纳哥属复制该模式，非新引入。
- 建议修复：在 `DoGoldGiftFromMajor` 内改判「**本城邦自身**的 UA 是否带该效果」，与既有 `CvPlayer::HasCSUAFaithPantheonPurchaseUA`（`CvPlayer.cpp:33083-33096`，检查 minor 自己的 UAType → effect）同构——取 `GC.getMinorCivInfo(GetMinorCivType())->GetUAType()` → `GC.GetGameCityStateUAs()->GetEntryByType()` → 依 `IsAllies/IsFriends` 选 effect → 判 `GetGoldDonationGambleEntries()` 是否非空。加德满都建议同法一并修，保持两处一致。

#### B-1a　（B-1 派生）UI tooltip 会显示在任意城邦的馈赠面板

- 位置：`UI/InGame/Popups/CityStateDiploPopup.lua:1147-1150`。
- 现象：判定用 `Players[iActivePlayer]:HasCSUAGoldDonationGamble()`（玩家级），与弹窗所看的城邦 `g_iMinorCivID` 无关。玩家为摩纳哥盟友时，打开**任意**城邦的馈赠面板都会显示「下注」说明。加德满都 tooltip（`:1142-1146`）同理。
- 建议修复：与 B-1 同源修复后，UI 侧需对 `g_iMinorCivID` 的 UA 做判定。当前 Lua 层**无**查询城邦 UAType/CSUA effect 的接口（`CvLuaPlayer` 仅有玩家级 CSUA 导出），需随修复新增一个按城邦查询的导出（仿 `HasCSUAFaithPantheonPurchaseUA` 做 Lua 转发，返回该城邦盟友/朋友 effect 是否带对应特性）。

### 待拍板（需确认，非缺陷）

**无。** 设计清单决策 1-9 已由用户两轮问答拍板，实现与决策一致（旅游口径取 `GetBaseTourism()`、下注照常给影响力、维护费相加、`getJonRandNum` 同步 RNG、子表非空即启用、傀儡城市生效、全局钳位、AI 享受）。

### 提示（非缺陷）

#### P-1　维护费钳位落在 mod 开关之外，关闭选项时亦改变原版行为

- 位置：`CvTreasury.cpp:856-858`，该 `if (iMaintenance < 0) iMaintenance = 0;` 不在 `#if defined(MOD_SP_UNIQUE_CITYSTATE)` 内。
- 说明：设计决策 8 明确选「全局钳位」，故此为实现预期；仅提示关闭 `SP_UNIQUE_CITYSTATE` 后该钳位仍生效，会顺带修正原版「政策叠加致负」的边缘情形。如需最小化改动，可改为仅在 `iMaintenanceMod` 含 CSUA 修正时钳位。

#### P-2　新增序列化数组成员门控 164，旧 164 档读入错位

- 位置：`CvMinorCivAI.cpp:2120`，`MOD_SERIALIZE_READ_ARRAY(164, ...)`；`MOD_DLL_VERSION_NUMBER` 仍为 164（`CustomMods.h:36`）。
- 说明：与既有加德满都字段（`m_abFaithRefundUsedThisTurn`）完全同款，符合「内测期不升版本号」约定（[[dev-build-version-control]]）。代价是**旧 164 内测档读入会字节错位坏档**；内测期若约定每次大改重开档则无影响，否则需升 165。读/写顺序一致（Belief→FaithRefund→GoldGamble→PantheonCount），无错序。

#### P-3　旅游转化存在 1 回合滞后

- 位置：`CvCity.cpp:15335-15336` 取 `GetBaseTourism()`（缓存成员 `m_iBaseTourism`，每回合由 `CalculateBaseTourism` 刷新）。
- 说明：属设计已接受项（清单 §6/§7）。读缓存 O(1)、不触发重算、递归安全（旅游源不经 `getBasicYieldRateTimes100`，无自引用）。

#### P-4　联机确定性未覆盖

- 说明：下注用 `GC.getGame().getJonRandNum`（同步 RNG），单机无碍；但馈赠入口（`CvDllNetMessageHandler`）是否各端都跑 `DoGoldGiftFromMajor` 未验证。SP 联机为独立分支（[[world-power-sync-on-demand]] 同域的联机约束），此处仅记录，非本次范围。

#### P-5　未加 `m_abGoldGambleUsedThisTurn` 的 getter/setter（无碍）

- 说明：设计清单 §3 表格曾列 `.h:456-457` 的 getter/setter，实现仅加成员、未加访问器。因该标记仅在 `CvMinorCivAI` 内部使用，省略访问器**正确**（避免无用代码）。成员初始化依赖 `Reset()`（`:1977`）与既有 `m_abFaithRefundUsedThisTurn` 处理方式一致。

---

## 三、已验证无误项

1. **转化整合点正确，满足「转化是最终值」**。`GetYieldRateFromUCSConversion` 的返回值经 `CvCity.cpp:14233-14242` 在 `getBaseYieldRateModifier` **之后**、以 `× 100` 追加，故不参与目标 yield 的百分比修正（[[csua-yield-conversion-final-value]]）。`YIELD_TOURISM` 源走 `GetBaseTourism()`（点数口径），非旅游源走 `getBasicYieldRateTimes100(..., false, true)`（`bIgnoreFromOtherYield=true` 防递归），量纲一致（点数×Mod/100，返回后统一 ×100）。
2. **子表解析与既有模式同构**。`CvCityStateUAClasses.cpp:752-788` 两张子表块逐字对照既有 `YieldToYieldViaTRToUCS` 块（`:732-751`），`YieldsIn.ID / YieldsOut.ID` 的 join 取 ID 方式完全一致；`GetYieldToYield` 对 (in,out) 匹配行**累加** Mod（`:1483-1492`），与 [[csua-special-city-yield-modifier-stacking]] 的累加口径一致。
3. **下注概率算法正确**。`CvPlayer.cpp:33122-33140`：`ΣWeight=5500` → `denom=max(5500,10000)=10000`；累计区间 3500/5000/5400/5500 → 35%/15%/4%/1%，余 4500/10000=45% 落空 → 与设计 45/35/15/4/1 精确对应。`Σ>10000` 分支按 `Σ` 归一化亦正确。
4. **下注返还语义正确**。返还经 `GET_PLAYER(ePlayer).GetTreasury()->ChangeGold((iGold * iMultiplier)/100)` 凭空加钱，不扣城邦、不影响影响力；影响力经 `GetFriendshipFromGoldGift` 正常结算（决策 2）。
5. **维护费并入语义正确**。`CvTreasury.cpp:823-831` 动态并入 `GetCSUABuildingMaintenanceMod()`，**不修改** `m_iBuildingGoldMaintenanceMod` 同步变量（决策 3），等价相加、每回合实时、无需序列化；`GetCSUABuildingMaintenanceMod`（`CvPlayer.cpp:33143-33152`）以 `isGoldenAge()` 门控，城邦无黄金时代，故恒指盟友自身处于黄金时代。
6. **钳位防倒加钱**。`CvTreasury.cpp:856-858` 位于全部乘数（难度/人类或 AI/起始时代）之后统一 `if <0 → 0`，唯一负值来源 `(100+mod)<0` 被拦下，满足「不得为负」要求。
7. **条件向量仅在 `Reset()` 后以 `+1` 重建，无累积**。`ApplyEffect` 仅被 `CvPlayer::RefreshCSAllUAEffects` 调用（`:20205 / :20209`），恒在 `Reset()`（`:20182`）之后、`iChange=1`；故 `m_vGoldDonationGamble.push_back` 每回合全量重建、无重复累积；`Reset()` 中已 `clear()`（`:1811`+clear）。
8. **盟友/朋友档位互斥且正确**。`RefreshCSAllUAEffects`（`:20203-20210`）`IsAllies` 优先、`else if IsFriends` 择一 `ApplyEffect`；朋友档 effect 行无 B/C 数据 → 朋友无下注、无维护费减免、无 tooltip（设计「朋友只共享第一条」）。
9. **序列化四处接入齐备且顺序一致**。`Reset` 清零（`:1977`）、`Read`（`:2120`）、`Write`（`:2199`）、`DoTurn` 每回合重置（`:2380-2382`）、成员声明（`.h:683`）；读/写宏守卫与相邻加德满都/拉文塔字段一致。
10. **UI 与 DLL 判定同源**。tooltip 的 `HasCSUAGoldDonationGamble()` 与实际掷骰的守卫用**同一** getter（决策 10），无「提示了但没触发」或反之（B-1a 属**城门限**问题，非「提示/触发不一致」）。
11. **Lua 导出合规**。`CvLuaPlayer.cpp:448` 注册、`:3649-3654` 实现（`lua_pushboolean` 返回 bool），仿既有 `lGetCSUAFaithRefundPerDonationPercent`；`.h:335` 声明齐。
12. **空安全/除零/越界**。`GetCSUAGoldDonationGambleMultiplier` 首行 `if (!m_pCityStateUA) return 0;`、`iWeightTotal <= 0` 短路（`:33126`）；`GetCSUABuildingMaintenanceMod` 判 `m_pCityStateUA`；循环均限 `MAX_MAJOR_CIVS`；除数均为常量 100 / 10000。
13. **注释全英文**。以脚本扫描 MPDLL 全部新增行，CJK 计数 **0**；SP 新增 `.sql` / `.xml`（数据文件）无注释；Lua 新增行无注释。符合 [[sp-english-comments-only]]。
14. **数据面校验**。`YIELD_TOURISM` 在 `(1) CIV5MPDLL/DB/YIELDS/UnifiedYieldsMoreYield.xml:8` 定义；`[ICON_CITY_STATE]`/`[ICON_TOURISM]`/`[ICON_GOLD]`/`[ICON_BULLET]`/`[COLOR_POSITIVE_TEXT]` 均在基座 `CIV5IconFontMapping.xml` 或 `_TEXT` 中有效。
15. **三语文本齐全、末尾插入、无重复**。4 个 Tag（`TXT_KEY_CSUA_MONACO_HELP` / `_EFFECT_..._ALLY_HELP` / `_EFFECT_..._FRIEND_HELP` / `TXT_KEY_CSUA_MONACO_DONATION_TT`）在英/简/繁三文件各存在且仅一处，均追加于各文件 `</Language_*>` 之前（末尾），未打乱既有分组。
16. **城邦名文本 Tag 正确**。`CSUA.xml:1935` `<Description>TXT_KEY_CITYSTATE_MONACO</Description>` 与本体定义一致，无「_CITY」后缀类命名错位。
17. **无重复主键**。`CSUA_MONACO` / `EFFECT_CSUA_MONACO_ALLY` / `EFFECT_CSUA_MONACO_FRIEND` / 四个文本 Tag 全 SP 各仅一处定义。
18. **未误改无关代码**。两仓库 diff 全部集中本次功能；`CvTreasury.cpp` 仅 1 处 `−`（原 `iMaintenance *= (100 + m_pPlayer->GetBuildingGoldMaintenanceMod());` 拆分为先取变量），逻辑等价。

---

## 四、验证方法

- 逐文件比对 MPDLL 与 SP 两仓库工作区 `git diff` / `git diff --numstat` / `git status --short`，核对改动规模与提交状态。
- 交叉核对 C++ 实现、XML 数据、三语文本、设计稿四者数值与语义。
- 回读引擎侧被调用函数确认语义：`CvCity::GetYieldRateFromUCSConversion`（`CvCity.cpp:15255-15343`）与整合点 `getBasicYieldRateTimes100`（`CvCity.cpp:14233-14242`）；`CvMinorCivAI::DoGoldGiftFromMajor`（`CvMinorCivAI.cpp:10880-10919`）及其加德满都先例（`:10899-10907`）；`CvTreasury::GetBuildingGoldMaintenance`（`CvTreasury.cpp:819-861`）。
- 追踪玩家级 CSUA 缓存构建路径：`CvPlayer::RefreshCSAllUAEffects`（`CvPlayer.cpp:20171-20211`）→ `CvPlayerCityStateUA::Reset`/`ApplyEffect`（`CvCityStateUAClasses.cpp:1808 / 2086`），验证盟友/朋友择一与 `iChange=1` 唯一性。
- 以全仓 grep 检索基座 `CIV5MinorCivilizations.xml` 确认 `MINOR_CIV_MONACO` / `TXT_KEY_CITYSTATE_MONACO` 定义；检索 `CIV5IconFontMapping.xml` 与 `_TEXT` 确认图标/颜色标记有效；检索 `UnifiedYieldsMoreYield.xml` 确认 `YIELD_TOURISM` 存在。
- 以脚本扫描新增行 CJK 字符；核对五处序列化读/写顺序一致。

---

## 五、结论

摩纳哥（Monaco）CSUA 的三条盟友效果（A 旅游转化 / B 首次馈赠下注 / C 黄金时代维护费）+ 朋友效果（D 旅游转化缩水版）**数值与档位均正确落地，与设计稿逐条对得上**；两张新子表与既有 `YieldToYieldViaTRToUCS` 同构、主表新列接入合规、序列化门控符合内测约定、注释/三语文本/图标/空安全均达标。

**须修复 1 项（B-1）**：效果 B 的下注判定误用玩家级 `HasCSUAGoldDonationGamble()`，导致对**任意城邦**赠金都触发下注、且一回合可多次触发；根因与既有加德满都信仰返还相同，建议两处一并改为「按本城邦自身的 UA effect」判定。派生项 B-1a（UI tooltip 错位）随同源修复处理，并需补一个按城邦查询的 Lua 导出。

其余 5 项均为提示（钳位在 mod 开关外、164 门控旧档错位、旅游 1 回合滞后、联机未覆盖、访问器省略）。

建议处理顺序：先修 B-1 / B-1a（含加德满都同类问题），再按 [[build-project-paths]] 构建 SP V11 与 MPDLL（含清理 PCH 缓存、编译前关闭文明 5）实机验证——重点验：**给非摩纳哥城邦赠金是否仍误触发下注**（回归 B-1）、同回合对摩纳哥二次赠金是否只掷一次、45/35/15/4/1 分布采样、旅游转化金额与 1 回合刷新、黄金时代维护费减半及与政策相加不为负、朋友档无 B/C。
