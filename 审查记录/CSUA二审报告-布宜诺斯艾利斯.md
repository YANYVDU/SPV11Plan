# CSUA 二审报告：布宜诺斯艾利斯（Buenos Aires）

- 二审日期：2026-10-02
- 审查对象：工作区未提交改动（**含一审修复**，尚未 commit）
- 涉及仓库：
  - MPDLL：`d:\Git\CIV5\dyy\CIV5MPDLL`（分支 `EconomicAid`）
  - SP：`d:\Git\CIV5\dyy\V11\Super-Power-Remaking-of-World-Order`（分支 `EconomicAid`），HEAD `285b443`（CSUA: KYZYL）
- 改动规模：MPDLL 2 文件 **+37 / −5**；SP 5 文件 **+158 / −0**（较一审的 `+34/−5`、`+118`，其增量即 A-1/B-1/C-1/P-2 的修复）
- 权威设计稿：`d:\Git\CIV5\dyy\SP V11\1.城邦UA\文化型.txt:25-29`
- 一审报告：`CSUA审查报告-布宜诺斯艾利斯.md`（3 应修正：A-1【严重】/ B-1【中】/ C-1【中】；5 提示）

**二审结论摘要**：

- 一审 **3 项应修正全部已修复**，逐条有证据（见第一节）：A-1 主表补录、B-1 数值改 `500`、C-1 限定 `GREAT_WORK_MUSIC`；一并补做的 P-2 三语主表 Help Tag 亦已落地。
- **二审独立复核确认效果③ 确实生效**（一审仅断言、未追踪赋值点）：`SetTourismBlastStrength` 全生命周期核验——仅在单位诞生时赋值、音乐会执行时**不重算**，故创作杰作时的 ×50% 会延续到后续演唱会；`canCreateGreatWork` 首行即阻断重复创作；`canBlastTourism` 不依赖 `GetGreatWork()`，存活大音乐家仍可开演唱会。
- **二审修正一审的一处连锁判断**：一审 C-1 后果中「盟军消耗奖励丢失」**不成立**——存活大音乐家最终开演唱会时 `DoGreatPersonExpended` + `kill` 仍执行（`CvUnit.cpp:13255-13264`），消耗奖励**延后发放而非丢失**。
- **二审新发现：应修正 0 项，待拍板 0 项，提示 3 项**（`retention=0` 语义反转、字符串查找健壮性、未编译验证），均非缺陷。

---

## 一、一审修复验证（逐条，附证据）

| 一审项 | 一审建议 | 最终状态 | 是否修复 | 证据 |
| --- | --- | --- | --- | --- |
| **A-1**【严重】主表 `<CityStateUAs>` 缺 `CSUA_BUENOS_AIRES` | 在 `</CityStateUAs>` 前补主记录 | **已修复**：`<CityStateUAs>` 新增末条 `Type=CSUA_BUENOS_AIRES`、`Description=TXT_KEY_CITYSTATE_BUENOS_AIRES`、`AllyEffectType=EFFECT_CSUA_BUENOS_AIRES_ALLY`、`FriendEffectType=EFFECT_CSUA_BUENOS_AIRES_FRIEND` | ✅ | `CSUA.xml:2029-2035` |
| **B-1**【中】效果④ `YieldMod=5` 单位误用（+0.05%） | 改为 `500`（+5%） | **已修复**：`<YieldMod>500</YieldMod>` | ✅ | `CSUA.xml:2217-2221`（值在 `:2220`） |
| **C-1**【中】效果③「不死亡」未限定大音乐家 | 条件加 `eClass == GREAT_WORK_MUSIC` | **已修复**：条件为 `pCSUA->IsGPNoDeathAfterGreatWork() && eClass == (GreatWorkClass)GC.getInfoTypeForString("GREAT_WORK_MUSIC")` | ✅ | `CvUnit.cpp:9926-9927` |
| **P-2** 三语缺主表 `Help` Tag | 补 `TXT_KEY_CSUA_BUENOS_AIRES_HELP` | **已修复**：英/简/繁三文件各 +11 行，主表 `Help` 引用可解析 | ✅ | `TextInfos_en_US.xml:20634`、`zh_CN:19103`、`zh_Hant_HK:18909` |

### A-1 复核细节

- 主表记录（`CSUA.xml:2029-2035`）紧随 `CSUA_KYZYL`（`:2022-2028`）之后，字段齐全。
- `Description` 引用的 `TXT_KEY_CITYSTATE_BUENOS_AIRES` 系**文明 5 本体**既有 Tag（`D:\steam\...\Expansion2\Gameplay\XML\Text\en_US\CIV5GameTextInfos_CityStates_Expansion2.xml:40`，且各语种目录均存在），可解析。
- `Help` 引用的 `TXT_KEY_CSUA_BUENOS_AIRES_HELP` 已随 P-2 补齐三语（见上表）。
- 加载链恢复：`CvPlayer::RefreshCSAllUAEffects` 的 `GetEntryByType("CSUA_BUENOS_AIRES")` 现在能取到非 NULL 条目，`EFFECT_CSUA_BUENOS_AIRES_ALLY/FRIEND` 得以实例化——该城邦 4 条效果**由「完全不生效」转为生效**。

### B-1 复核细节

- 单位标定复核：`GetCSUAYieldPercentModifier`（`CvPlayer.cpp:18262`）以**基点**累加、末尾 `/100` 归一；`GreatWorkYieldModifiers` 分支（`:18293-18304`）直接累加**不乘 100**，故表值单位即基点。`500 → +5%`，与设计「每个音乐杰作提高全国 5% 魅力」一致。同表 Ife「+2%=200」仍可作标定。
- 文本一致性：三语帮助文本均写「每个音乐杰作提高全国 **5%** 魅力」，与 `500` 语义对齐（一审 B-1 的「文本与数值表面一致但数值错」耦合风险已解除）。

### C-1 复核细节

- 判定落在 `createGreatWork()`（`CvUnit.cpp:9875`，大艺术家/大作家/大音乐家共用入口）内，新增条件用同函数 `:9898` 已算出的 `eClass` 限定为音乐杰作类别，作用域正确、无需新增变量。
- 注释随修复补入（`CvUnit.cpp:9919-9925`，英文）：说明仅大音乐家受影响、艺术/文学伟人照常死亡，符合 [[sp-english-comments-only]]。

---

## 二、二审独立复核（一审未覆盖的维度）

### 2.1 效果③ 演唱会魅力保留的**有效性**验证（核心）

一审断言「×50% 与设计一致」，但未验证「该值是否会延续到后续演唱会」。二审追踪 `TourismBlastStrength` 全生命周期：

- **赋值点仅 3 处、均在单位诞生/产出时，音乐会路径不重写**：
  - `CvUnit::init`（`CvUnit.cpp:1037-1040`）：单位诞生时按 `GetOneShotTourism()` 设置；
  - `CvCity` 产出单位时（`CvCity.cpp:20208`）；
  - 专家诞生伟人时（`CvCityCitizens.cpp:2982`）。
  - 复制/转移（`CvUnit.cpp:2088`）、俘获（`:2668`）为搬运同一值，非重算。
- **消费点只读不重算**：`getBlastTourism()`（`CvUnit.cpp:13154`）`int iTourismBlast = GetTourismBlastStrength();` 后再乘 `culturePercent` 与（布鲁塞尔的）`OneShotMod`，**不重新派生**基础值。
- **结论**：布宜诺斯艾利斯的大音乐家在**创作杰作时**执行 `SetTourismBlastStrength(GetTourismBlastStrength() * 50 / 100)`（`CvUnit.cpp:9934`），此后再无重算点，故后续演唱会自然读到 50%。设计「保留 50% 演唱会魅力」**真实生效**，而非一次性空转。
- 顺序无关性：音乐会本身 `kill(true)`（`CvUnit.cpp:13264`）会消耗单位，故实际流程只能是「创作杰作→存活→演唱会」，不存在「先演唱会（已死）再创作」的错序。

### 2.2 效果③ 消耗奖励「延后而非丢失」（修正一审连锁判断）

- 一审 C-1 曾提出后果：不进入 `if (!bNoDeathAfterGreatWork)` 分支 → `DoGreatPersonExpended` 不被调用 → 盟友损失消耗奖励。**二审发现该后果对存活大音乐家并不成立**：
  - 存活大音乐家最终执行**演唱会**时，`blastTourism()` 在 `kill(true)` 前仍调用 `kUnitOwner.DoGreatPersonExpended(...)`（`CvUnit.cpp:13255-13264`），并触发 `GAMEEVENT_TourismDiscover`（`:13248-13253`）。
  - 即「伟人消耗产出（金币/信仰/宗教收益）与 `GAMEEVENT_GreatPersonExpended` 钩子」**延后到演唱会时发放**，而非丢失。
- 边界：若存活大音乐家始终不开演唱会（闲置或被歼灭），则消耗奖励不发——属合理语义（伟人未真正被消耗）。
- C-1 修复后，**艺术/文学伟人**在创作后照常 `DoGreatPersonExpended + kill`，一审担忧的「非预期免消耗」已消除。

### 2.3 效果②「丧失杰作产出能力」确被 `canCreateGreatWork` 阻断

- `canCreateGreatWork`（`CvUnit.cpp:9814-9820`）**首行**即 `if(GetGreatWork() == NO_GREAT_WORK) return false;`。
- 修复路径在存活分支执行 `SetGreatWork(NO_GREAT_WORK)`（`CvUnit.cpp:9930`）→ `GetGreatWork()` 归空 → 该单位**永远无法再次创作**，设计「丧失杰作产出能力」严格成立。
- 与 `CvEconomicAI::GetBestGreatWorkCity` 的 `NO_GREAT_WORK` 提前返回（`CvEconomicAI.cpp:897-902`，一审已验证）配套，AI 亦不会再指派该单位。

### 2.4 存活大音乐家仍可开演唱会（`canBlastTourism` 不依赖 `GetGreatWork`）

- `canBlastTourism`（`CvUnit.cpp:13104-13132`）判据为 `isBlastTourism()` + 目标地块为**他国主要文明所有**；`isBlastTourism()`（`:15110-15119`）仅判 `!isDelayedDeath()` 且 `GetOneShotTourism() > 0`。
- 两处**均不读取 `GetGreatWork()`**，故 `SetGreatWork(NO_GREAT_WORK)` 不会误关演唱会按钮。设计「创作→存活→（50% 强度）演唱会」链路完整可走。

### 2.5 通用标记建筑/资源：布宜诺斯艾利斯无需登记

- `CSUA.xml` 的 `<MinorCivilization_FreeBuildingClasses>`（`:2037-2046`）仅两条：`MINOR_CIV_ALMATY → BUILDINGCLASS_CSUA`、`MINOR_CIV_ORMUS → BUILDINGCLASS_CSUA_HORMUZ`；`<Building_ResourceQuantity>`（`:2047-2058`）亦仅对应这两城邦——二者是**额外授予战略资源**（马/石油）的特例。
- 布宜诺斯艾利斯四条效果全部由 UA 子表（`GreatPersonPoints` / `BuildingGreatPersonPoints` / `GreatWorkYieldModifiers`）+ 引擎字段驱动，**无任何需要假建筑承载的机制**，故不登记标记建筑是正确的（非遗漏）。

### 2.6 效果① 与 ② 的接入点复核（沿用一审，重新抽样）

- `CvCityCitizens.cpp:2316-2317` 两行分别 `GetGreatPersonPointsFromUA(eSpecialist)` 与 `GetGreatPersonPointsFromUA_Building(eSpecialist)`，均 `×100` 计入 `Times100` 量纲；布宜诺斯艾利斯 ALLY 行分别为 `GreatPersonPoints: SPECIALIST_MUSICIAN=1`（`CSUA.xml:575-579`）与 `BuildingGreatPersonPoints: TOWN…GLOBAL 各=1`（`:685-721`）。城市规模假建筑为累积制（一审验证项 4），故 80 人口城得 +1（每城）+7（七档假建筑）＝+8 大音乐家点数/回合。
- 朋友档仅 `SMALL=1`、`MEDIUM=1`（`:727-737`）；因假建筑累积，中型城市同时持 TOWN+SMALL+MEDIUM → 朋友得 +2，精确对应设计「小型 +1、中型额外 +1」，且**未**获得每城基础 +1（朋友无 `GreatPersonPoints` 行）。

### 2.7 文本、绑定、图标核对

- 绑定：`CSUA.sql:71` `UPDATE MinorCivilizations SET UAType = 'CSUA_BUENOS_AIRES' WHERE Type = 'MINOR_CIV_BUENOS_AIRES';` 与主表 `Type` 同构匹配。
- 三语文本新增 3 个 Tag（`_HELP` / `_ALLY_HELP` / `_FRIEND_HELP`）× 3 语言，各文件末尾追加、未打乱既有分组；中英文语义逐条对应，「5% 魅力」与数值 `500` 一致；图标 `[ICON_GREAT_MUSICIAN]` / `[ICON_GREAT_WORK]` / `[ICON_TOURISM]` / `[ICON_BULLET]` 使用得当。
- 本体侧 `MINOR_CIV_BUENOS_AIRES` 为文化型（`MINOR_TRAIT_CULTURED`），与设计归类一致。

---

## 三、二审新发现的问题

### 应修正

**无。** 逐条回读被改代码、追踪 `TourismBlastStrength` 生命周期、核对 `canCreateGreatWork`/`canBlastTourism` 依赖后，**未发现功能性缺陷、数值错误、挂钩位置错误或数据/文本不一致**。

### 待拍板

**无。** 四条盟友 + 一条朋友的档位、叠加口径均与设计稿字面一致。

### 提示（非缺陷，二审新发现 3 项）

#### N-1　`GPConcertTourismRetentionPercent = 0` 存在语义反转

- 位置：`CvUnit.cpp:9931-9935`。
- 说明：保留比例以 `if (iRetention > 0)` 守卫乘法。若某城邦把该列配为 `0`（语义应为「保留 **0%** 演唱会魅力」），代码会**跳过乘法、保留 100%**——即边界值 `0` 被解释为「不处理」而非「归零」。当前布宜诺斯艾利斯配置为 `50`，**无实际影响**；仅当未来有城邦需要「演唱会魅力全失」时才会踩到。
- 建议（可选）：如需支持零保留，将守卫改为「列被显式配置」（例如以 `-1` 表未配置、`>= 0` 表生效），或直接去掉守卫、令缺省值本身即 `100`。

#### N-2　`GC.getInfoTypeForString("GREAT_WORK_MUSIC")` 依赖精确字符串、无编译期保障

- 位置：`CvUnit.cpp:9927`。
- 说明：C-1 修复以运行时字符串查表得到 `GREAT_WORK_MUSIC` 类型再与 `eClass` 比较。若字符串拼写与 DB 不符，`getInfoTypeForString` 返回 `-1`，比较恒假 → 效果③ **静默失效**（无报错）。当前字符串正确（`CSUA.xml` 同用 `GREAT_WORK_MUSIC`），功能正常；相较之下，直接复用同函数已算出的 `eGreatWorkType` 属更稳写法。
- 建议（可选）：改用可编译期校验的常量（若头文件已有 `GREAT_WORK_MUSIC` 枚举）或对 `getInfoTypeForString` 结果做非负断言。

#### N-3　改动尚未编译/实机验证（与一审 P-1 同）

- 说明：MPDLL（`CvUnit.cpp` / `CvEconomicAI.cpp`）与 SP（5 文件）仍为**工作区未提交改动**，未取编译日志、未实机运行。本报告为静态审查结论。按 [[build-requires-game-closed]]，编译前需关闭文明 5；本次改动未触及 `CvGameCoreDLLPCH.h` 包含链，一般无需清 PCH 缓存。

### 沿用一审（不改，提示级）

- **效果①+② 叠加致每城最低 +2 大音乐家点数**（一审 P-3）：忠实于设计字面（「盟友的城市 +1」与「每个城市规模假建筑各提供 1」为两笔），仅供确认是否为设计本意。
- **`CvCity::GetGreatPersonPointsFromUA` 未使用局部变量 `szType`**（一审 P-5，既存于 Ife 时期，`CvCity.cpp:12119`）：仅编译警告，顺手可清。
- **未完成清单同步**（一审 P-4）：A-1/B-1/C-1 修复并提交后，应将布宜诺斯艾利斯移出 `未完成/未完成清单.md`（文化型未完成数 2 → 1）。

---

## 四、结论与建议

### 结论

1. 一审 **3 项应修正（A-1/B-1/C-1）与 P-2 提示全部修复完毕**，逐条有证据（第一节）；改动规模从 MPDLL +34/−5、SP +118 增至 +37/−5、+158，增量与四处分修一致。
2. 四条盟友效果 + 一条朋友效果的**数值、档位、方向**在修复后与设计稿（`文化型.txt:25-29`）**逐条对得上**：每城 +1、七档假建筑各 +1、不死亡 + 保留 50%、每音乐杰作 +5%（`500`）、朋友小型/中型 +1。
3. **效果③ 的机制经独立追踪确认生效**：`TourismBlastStrength` 在单位诞生时固化、音乐会不重算，故 ×50% 延续至演唱会；`SetGreatWork(NO_GREAT_WORK)` 经 `canCreateGreatWork` 阻断重复创作；`canBlastTourism` 不依赖 `GetGreatWork()`，演唱会仍可用。
4. **二审修正一审一处连锁判断**：存活大音乐家的「伟人消耗奖励」延后至演唱会发放，非丢失；C-1 修复后艺术/文学伟人回归正常消耗。
5. 工程规范达标：MPDLL 注释全英文、无 CJK；SP 改动集中于 `.sql`/`.xml` 数据文件；三语文本齐备且末尾追加；行尾未破坏（`git diff --numstat` 均为纯新增、无整篇重写）。
6. **二审新发现：应修正 0 项，待拍板 0 项，提示 3 项（N-1 `retention=0` 语义反转、N-2 字符串查找健壮性、N-3 未编译验证）**，均非缺陷。

### 是否建议构建实机验证

**建议构建实机验证。** 静态审查已覆盖全部逻辑，但以下依赖运行期状态的行为需实机确认：

| 优先级 | 场景 | 重点观察 |
| --- | --- | --- |
| 1 | **回归 A-1**：与新结盟的布宜诺斯艾利斯（盟友档） | 城邦面板显示 UA 总述；城市伟人进度条出现大音乐家点数；断盟后全部消失 |
| 2 | **效果①②**：盟友建有城市规模假建筑的城市 | GPP 增量 = 每城 +1 + 假建筑数（80 人口城应为 +8） |
| 3 | **效果③ 主链**：盟友大音乐家在城市创作音乐杰作后 | 单位**存活**、杰作按钮消失（不可再创作）、可移动至他国开演唱会且旅游增量为常规的 50% |
| 4 | **回归 C-1**：盟友大艺术家/大作家创作对应杰作后 | **照常消耗**（不死亡、无 50% 一说） |
| 5 | **回归 B-1**：盟友拥有 1 个音乐杰作 | 全国旅游 +5%（对比无杰作基线） |
| 6 | **朋友档**：仅小型/中型城市规模点数生效 | 无每城基础 +1、无杰作旅游加成；断交当回合全部消失 |

### 建议处理顺序

| 优先级 | 项 | 工作量 |
| --- | --- | --- |
| 1 | 构建 SP V11 + MPDLL（[[build-project-paths]]、关闭文明 5），按上表实机验证 | 小 |
| 2 | 实机通过后提交 MPDLL + SP 改动（按 [[commit-split-by-feature-csua]] 标题规范：MPDLL 列新增接口名 + 城邦名，SP 只用城邦名） | 小 |
| 3 | 同步 `未完成/未完成清单.md`（文化型未完成数 2 → 1） | 极小 |
| 4 | （可选）N-1 守卫语义、N-2 常量校验、一审 P-3/P-5 提示项 | 极小 |

---

## 附：审查方法

- 逐仓库比对 `git status --short` / `git diff --numstat` 确认改动规模与未提交状态（MPDLL 2 文件 +37/−5；SP 5 文件 +158/−0，HEAD `285b443`）。
- 逐条定位一审修复点：`CSUA.xml:2029-2035`（A-1 主记录）、`:2217-2221`（B-1 `YieldMod 500`）、`CvUnit.cpp:9926-9927`（C-1 类别限定）、三语 `TXT_KEY_CSUA_BUENOS_AIRES_HELP`（P-2）。
- 追踪 `TourismBlastStrength` 全生命周期：`grep` 全仓读写点 → `CvUnit.cpp:1037-1040`（init 赋值）、`CvCity.cpp:20208`、`CvCityCitizens.cpp:2982`（产出赋值）、`CvUnit.cpp:2088/2668`（搬运）、`CvUnit.cpp:13154`（只读消费）、`:9934`（本次减半）；确认音乐会路径无重算。
- 回读 `canCreateGreatWork`（`CvUnit.cpp:9814-9872`）、`canBlastTourism`（`:13104-13132`）、`isBlastTourism`（`:15110-15119`）、`blastTourism` 尾部（`:13242-13264`），验证「重复创作拦截」「演唱会可用」「消耗奖励延后」三点。
- 交叉核对 C++ 实现、`CSUA.xml` 数据、三语文本、设计稿（`1.城邦UA/文化型.txt:25-29`）四者数值与语义。
- 以本体安装目录核实 `TXT_KEY_CITYSTATE_BUENOS_AIRES` 存在（`Expansion2/.../CIV5GameTextInfos_CityStates_Expansion2.xml:40`）与城邦文化型定义。
- 以 `git diff --numstat` 的「纯新增、无整篇重写」佐证行尾未破坏。
