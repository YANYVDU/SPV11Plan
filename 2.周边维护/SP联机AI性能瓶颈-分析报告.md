# SP 联机 AI 性能瓶颈分析报告

- 日期：2026-10-14
- 分析对象：Super Power 联机对局中的 AI 回合计算耗时
- DLL 基准：`CIV5MPDLL` 仓库 `V11dev` 分支
- 参考对照：`Community-Patch-DLL` 工作区副本
- 性质：**数据驱动的瓶颈定位报告，未包含任何已实施的修改**。所有结论均可按第 1 节方法复现。

---

## 0. 摘要

一份 15 回合（Turn 59–73）的 AI 性能采样显示：

| 指标 | 数值 |
|---|---|
| 单回合 AI 总计算时间（`CvGame::doTurn`） | 均值 **22.08 秒**，峰值 **31.67 秒** |
| 样本内趋势 | 首段 14–17 秒 → 末段 26–31 秒 |
| 最大单项 | `Do City Turns` 394.41 秒 / 15 回合 |
| 第二大项 | `Tactical AI` 378.95 秒 / 15 回合 |
| 单次调用最大 | `Tactical AI` **43.29 秒**（一次调用） |

识别出三个瓶颈，按可操作性排序：

1. **劫掠战术 AI（`PlotPillageMoves` 的 next-turn 分支）** —— 全局第一耗时的 Move Type，且 **85% 集中在单个文明（印尼）**，单次调用最慢 22.79 秒，随回合爆炸式增长。**代码层面有明确、可定位的根因，是最值得动手的一项。**
2. **城市生长（`CvCity::doGrowth`）** —— 占城市回合的 68%，随城市人口放大，人口最高的文明最贵。属原版机制成本，优化空间有限。
3. **`CvPlayer::doResearch` 尖峰** —— 均值正常但单次最高 15.36 秒，成因未知，需另行排查。

---

## 1. 数据来源与复现方法

### 1.1 原始数据

采样来自游戏 `Config.ini` 的 `[Debug] AIPerfLog = 1`（该开关默认关闭，本机在对局中被打开）。产出文件位于：

```
%USERPROFILE%\Documents\My Games\Sid Meier's Civilization 5\Logs\
```

本次分析使用其中 8 个（另有 `RandCalls.csv` 未使用）：

| 文件 | 大小 | 含义 |
|---|---|---|
| `AI-perf.csv` | 837 KB | 玩家/游戏级 AI 主流程 |
| `City-AI-perf.csv` | 4.47 MB | 城市级 |
| `AI-perf-tact.csv` | 3.06 MB | 战术 AI + Move Type |
| `Homeland-perf.csv` | 443 KB | 后方 AI |
| `Military-AI-perf.csv` | 364 KB | 军事 AI |
| `Homeland-GetBest-perf.csv` | 329 KB | 后方 AI 细分 |
| `Homeland-ExecuteMove-perf.csv` | 167 KB | 后方 AI 细分 |
| `Homeland-ExecuteWorkerMoves-perf.csv` | 116 KB | 后方 AI 细分 |

### 1.2 CSV 格式（**复核时务必注意**）

每行形如：

```
, <数字>, <函数名/Move Type>, Turn NNN, <文明名>, <城市名>, <若干空字段>, <耗时秒>
```

两个易踩的坑：

1. **耗时在最后一列，列数不固定。** 例如 `', 0, CvTacticalAnalysisMap::Init(), 0.000103'` 只有 4 列（没有 Turn/文明/城市）。因此聚合必须取**末列**，不能按固定下标取。shell 可用 `awk -F',' '{t=$NF; ...}'`。
2. **第 2 个字段目前含义不明。** 最初误判为 playerID，但实测同一数值会同时出现在印尼 / 奥斯曼 / 葡萄牙 / 迦太基等不同文明上，因此**它不是玩家 ID**（推测是调用缩进层级）。**本报告一律不使用该字段**，文明判定只用第 5 列。

### 1.3 采样范围

- 15 个回合：Turn 059 – Turn 073（Turn 059 可能不完整）
- 文明数：约 15 个主要文明 + 约 40 个城邦
- 城市规模：以 `CvCity::doTurn` 调用数 1814 / 15 回合 ≈ 每回合 121 座城

### 1.4 复现脚本

```python
import os, io, collections
base = os.path.join(os.path.expanduser('~'), 'Documents', 'My Games',
                    "Sid Meier's Civilization 5", 'Logs')
def rows(fname):
    with io.open(os.path.join(base, fname), 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            parts = [x.strip() for x in line.rstrip('\n').split(',')]
            if len(parts) < 4: continue
            try: t = float(parts[-1])
            except ValueError: continue
            yield parts, t
```

---

## 2. 总体量级

### 2.1 逐回合 `CvGame::doTurn` 耗时（秒）

| 回合 | 59 | 60 | 61 | 62 | 63 | 64 | 65 | 66 | 67 | 68 | 69 | 70 | 71 | 72 | 73 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 秒 | 17.10 | 14.13 | 15.70 | 18.73 | 23.16 | 22.76 | 23.32 | 18.88 | 19.38 | 26.60 | 24.26 | 26.50 | **31.67** | 26.50 | 22.55 |

**注意：不是单调递增。** 整体呈上升趋势（前段 14–17 秒，后段 26–31 秒），但 T66 有明显回落。不要把"每回合都在变慢"当作结论。

### 2.2 主流程分项（15 回合累计）

| 项目 | 累计秒 | 次数 | 均值 | 单次最大 |
|---|---|---|---|---|
| `CvPlayer::doTurn()` | 516.66 | 587 | 0.8802 | 22.60 |
| `Do City Turns` | 394.41 | 587 | 0.6719 | 17.54 |
| `Tactical AI` | 378.95 | 561 | 0.6755 | **43.29** |
| `Homeland AI` | 135.02 | 619 | 0.2181 | 8.05 |
| `CvPlayer::doResearch` | 44.44 | 587 | 0.0757 | **15.36** |
| `Plots/Danger` | 23.89 | 587 | 0.0407 | 0.62 |
| `Tactical Analysis Map` | 12.10 | 587 | 0.0206 | 0.51 |
| `CvGameReligions::DoPlayerTurn` | 10.21 | 587 | 0.0174 | 0.18 |
| `CvEconomicAI::DoTurn` | 5.89 | 572 | 0.0103 | 0.26 |
| `MilitaryAI DoTurn` | 5.14 | 572 | 0.0090 | 0.24 |
| `CvMinorCivAI::DoTurn` | 3.26 | 425 | 0.0077 | 0.28 |

> 注：`CvPlayer::doTurn()` 累计 516.66 秒 < 其子项 `Do City Turns + Tactical AI + Homeland AI` 之和（908 秒），这是因为子项的计时嵌套层级不同（如 `Do City Turns` 内部还包含城市级计时）。**各项之间不可直接相加**，本报告只做同层级横向比较。

---

## 3. 瓶颈 A：城市生长 `CvCity::doGrowth`

### 3.1 数据

`City-AI-perf.csv`，15 回合累计：

| 项目 | 累计秒 | 次数 | 均值 | 单次最大 | 占比 |
|---|---|---|---|---|---|
| `CvCity::doTurn` | 394.33 | 1814 | 0.2174 | 1.44 | 100% |
| **`CvCity::doGrowth`** | **267.12** | 1814 | 0.1473 | 1.33 | **67.7%** |
| `CvCity::doProduction` | 53.15 | 1814 | 0.0293 | 0.49 | 13.5% |
| `CvCityCitizens::DoTurn` | 45.08 | 1814 | 0.0249 | 0.24 | 11.4% |
| `CvCityStrategyAI::DoTurn` | 25.04 | 1823 | 0.0137 | 0.14 | 6.4% |

`doGrowth` 耗时分布（n=1814）：**p50 = 0.059s，p90 = 0.439s，p99 = 1.025s，max = 1.335s**。

### 3.2 按文明分解

| 文明 | `doGrowth` 均值/城 | 次数 | `doTurn` 均值/城 |
|---|---|---|---|
| 迦太基 | **0.4303** | 283 | 0.4923 |
| 波兰 | 0.2314 | 221 | 0.3435 |
| 加德满都（城邦） | 0.2215 | 15 | 0.2483 |
| 布拉迪斯拉发（城邦） | 0.1615 | 15 | 0.1831 |
| 苏黎世（城邦） | 0.1541 | 15 | 0.1804 |
| 印尼 | 0.1524 | 186 | 0.2863 |
| 奥斯曼 | 0.1135 | 163 | 0.2060 |
| 葡萄牙 | 0.0642 | 143 | 0.1526 |

**重要更正**：早期口头结论曾称"城邦约 0.01 秒，比主要文明低 55 倍"——**这是错的**。实测城邦单城耗时在 0.09–0.22 秒区间，与波兰、印尼同量级。真实差异是**最高（迦太基 0.430）到最低（葡萄牙 0.064）约 7 倍**，而非 55 倍。

### 3.3 代码侧

函数位于 `CvGameCoreDLL_Expansion2/CvCity.cpp` 的 `CvCity::doGrowth()`。其函数体本身很轻：

```cpp
int iDiff = foodDifferenceTimes100();
changeFoodTimes100(iDiff);
changeFoodKept(iDiff / 100);
int iGrowthThreshold = growthThreshold();
setFoodKept(range(getFoodKept(), 0, ((iGrowthThreshold * getMaxFoodKeptPercent()) / 100)));
int iLoopTime = 1;
#ifdef MOD_GLOBAL_UNLIMITED_ONE_TURN_GROWTH
    if (MOD_GLOBAL_UNLIMITED_ONE_TURN_GROWTH) iLoopTime = 1000;
#endif
while (getFood() >= iGrowthThreshold && iLoopTime--) { ... changePopulation(1); ... }
```

**已核实**：`GLOBAL_UNLIMITED_ONE_TURN_GROWTH` 在 `Civ5DebugDatabase.db` 的 `CustomModOptions` 表中为 `0`，即该循环最多执行 1–2 次。因此**不是循环次数导致的**。

推断（**待复核**）：开销落在 `changePopulation()` 触发的市民重分配上，成本随城市人口增长，因此人口最高的文明最贵。若此推断成立，则这是原版机制成本，优化空间有限。

**待复核问题**：需要一次定点采样确认 `changePopulation` 是否真是热点。建议在 `doGrowth` 内部对 `foodDifferenceTimes100` / `growthThreshold` / `changePopulation` 分别打 `AI_PERF_FORMAT` 计时（或用 VS 采样分析器）。

---

## 4. 瓶颈 B：劫掠战术 AI（重点）

### 4.1 数据

`AI-perf-tact.csv` 中 Move Type 累计排名：

| Move Type | 累计秒 | 次数 | 均值 | 单次最大 |
|---|---|---|---|---|
| **`TACTICAL_PILLAGE_RESOURCE_NEXT_TURN (51)`** | **100.76** | 546 | 0.1845 | **22.79** |
| `TACTICAL_DAMAGE_CITY (3)` | 82.52 | 545 | 0.1514 | 10.13 |
| `TACTICAL_CAPTURE_CITY (2)` | 46.59 | 546 | 0.0853 | 3.50 |
| `TACTICAL_PILLAGE_RESOURCE (49)`（首遍） | 30.14 | 546 | 0.0552 | 5.30 |
| `TACTICAL_MOVE_OPERATIONS (31)` | 19.95 | 546 | 0.0365 | 1.80 |
| `TACTICAL_DESTROY_MEDIUM_UNIT (5)` | 14.97 | 546 | 0.0274 | 1.95 |
| `TACTICAL_ATTRIT_LOW_UNIT (10)` | 13.41 | 546 | 0.0246 | 4.05 |

### 4.2 关键异常：85% 集中在一个文明

`TACTICAL_PILLAGE_RESOURCE_NEXT_TURN` 按文明分解：

| 文明 | 累计秒 | 次数 | 均值 | 单次最大 |
|---|---|---|---|---|
| **印尼** | **86.06** | 17 | **5.0624** | **22.79** |
| 波斯 | 7.84 | 15 | 0.5229 | 1.72 |
| 日本 | 4.84 | 15 | 0.3229 | 1.52 |
| 奥斯曼 | 1.16 | 16 | 0.0726 | 0.80 |
| 希腊 | 0.58 | 15 | 0.0389 | 0.09 |
| 葡萄牙 | 0.20 | 16 | 0.0124 | 0.04 |
| 其余 30+ 文明 | ≈0 | — | — | — |

印尼的均值是第二名的 **9.7 倍**，占该项总耗时的 **85.4%**。

印尼自身按回合的战术 AI 总耗时（`AI-perf-tact.csv` 按文明+回合求和）：

| 回合 | 64 | 65 | 66 | 67 | 68 | 69 | 70 | 71 | 72 | 73 | 74 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 秒 | 8.69 | 8.21 | 9.98 | 10.75 | 19.37 | 17.33 | 33.30 | 36.79 | 30.70 | **49.63** | 26.10 |

**从 8 秒量级涨到 49.63 秒，约 6 倍，且明显随时间恶化。**

另：`AI-perf.csv` 中 `Tactical AI` 项的单次最大值 **43.29 秒**，同样来自印尼。

### 4.3 代码证据链

#### (1) 调用点

`CvGameCoreDLL_Expansion2/CvTacticalAI.cpp:1813-1816`：

```cpp
else if(move.m_eMoveType == (TacticalAIMoveTypes)m_CachedInfoTypes[eTACTICAL_PILLAGE_RESOURCE_NEXT_TURN])
{
    PlotPillageMoves(AI_TACTICAL_TARGET_IMPROVEMENT_RESOURCE, false /*bFirstPass*/);
}
```

#### (2) 被调函数

`CvTacticalAI.cpp:2680-2751`：

```cpp
void CvTacticalAI::PlotPillageMoves(AITacticalTargetType eTarget, bool bFirstPass)
{
    ...
    pTarget = GetFirstZoneTarget(eTarget);
    while(pTarget != NULL)
    {
        CvPlot* pPlot = GC.getMap().plot(pTarget->GetTargetX(), pTarget->GetTargetY());

        if (bFirstPass && FindParatroopersWithinStrikingDistance(pPlot)) { ... }
        else if (bFirstPass && FindUnitsWithinStrikingDistance(pPlot, 0, iPillageHeal, false, false,
                     true /*bMustMoveThrough*/, false, true /*bWillPillage*/))
        {
            ExecutePillage(pPlot);
        }
        // No one can reach it this turn, what about next turn?
        else if(!bFirstPass && FindUnitsWithinStrikingDistance(pPlot, 2, iPillageHeal, false, false,
                     false /*bMustMoveThrough*/, false, true /*bWillPillage*/))
        {
            ExecuteMoveToTarget(pPlot);
        }
        pTarget = GetNextZoneTarget();
    }
}
```

**注意第 2737 行的 `2`（第二参数 `iNumTurnsAway`）。**

#### (3) `FindUnitsWithinStrikingDistance` 内部

`CvTacticalAI.cpp:9035-9231`。结构为：遍历 `m_CurrentTurnUnits` → 逐单位过滤 → 三选一分支。关键分支条件在 **第 9118 行**：

```cpp
else if(!bNoRangedUnits && !bWillPillage && pLoopUnit->IsCanAttackRanged())
```

劫掠调用传 `bWillPillage = true`，使 `!bWillPillage` 恒为假 → **整个远程分支被跳过**，直接落入第 9179 行的 `else`，走第 9191 行：

```cpp
else if ( (iTurnsCalculated != -1 && iTurnsCalculated <= iNumTurnsAway)
          || (iTurnsCalculated == -1 && CanReachInXTurns(pLoopUnit, pTarget, iNumTurnsAway, false)) )
```

而 `iTurnsCalculated` 在第 9107 行初始化为 `-1`，只在 `bTargetUndefended = true` 时才会被第 9108 行赋值。劫掠调用未传该参数 → **恒为 -1** → `||` 左侧必假 → **右侧必然求值**。

> **结论：只要一个单位通过了第 9072 行的 `canPillage(pTarget)` 过滤，本函数每次调用都必然对它执行一次真实寻路，没有任何短路。**

#### (4) 寻路本身的代价

`CanReachInXTurns`（`CvAStar.cpp:3845-3876`）在寻路前有一层廉价预筛：

```cpp
iDistance = plotDistance(pUnit->getX(), pUnit->getY(), pTarget->getX(), pTarget->getY());
if(iTurns == 0 && iDistance >= pUnit->baseMoves())            return false;
else if(iTurns > 0 && iDistance > (pUnit->baseMoves() * iTurns)) return false;
else { TurnsToReachTarget(pUnit, pTarget, false /*bReusePaths*/, bIgnoreUnits); }
```

以 `baseMoves = 2` 的步兵为例：

| 调用点 | `iTurns` | 预筛阈值 | 实际进入 A* 的单位 |
|---|---|---|---|
| 首遍（`CvTacticalAI.cpp:2723`） | 0 | `iDistance >= 2` 即排除 | 仅相邻格 |
| **次遍（`CvTacticalAI.cpp:2737`）** | **2** | `iDistance > 4` 才排除 | **半径 4 内全部（约 61 格）** |

**第二遍的寻路候选集比第一遍大一个数量级。**

进入后的 `TurnsToReachTarget`（`CvAStar.cpp:3882-3951`）在第 3871 行**硬编码 `bReusePaths = false`**，即每次都是全新搜索。而 `CvAStar::GeneratePath`（`CvAStar.cpp:193-244`）在 `bReuse = false` 时，会先遍历并 `clear()` 上一次搜索遗留的 `m_pOpen` / `m_pClosed` 链表（第 223–244 行），即 **O(上次展开节点数) 的额外清理开销**。

#### (5) 成本模型

```
总成本 ≈ 目标地块数 × 通过 canPillage 的单位数 × (完整 A* + 上次残留清理)
```

外层遍历 target、内层遍历 unit，因此**同一单位的两次寻路被其他单位隔开**。这还有一个副作用：`GeneratePath` 第 202 行的复用判据只看 `m_iXstart` / `m_iYstart` / `m_iInfo`（**不含 dest**），所以即使把 `bReusePaths` 改成 `true`，在当前循环顺序下也复用不了。

### 4.4 与 Community-Patch-DLL 对照

CP 在**同一位置**（`Community-Patch-DLL/CvGameCoreDLL_Expansion2/CvTacticalAI.cpp:1279`）用的是**另一个专用函数**：

```cpp
else if (FindUnitsForHarassing(pPlot, 2, GD_INT_GET(MAX_HIT_POINTS) / 2,
                               GD_INT_GET(MAX_HIT_POINTS) - iMinDamage,
                               DOMAIN_LAND, false, false, 1))
```

两点差异：

1. **MPDLL 仓库中不存在 `FindUnitsForHarassing`**（全仓 grep 零结果）。它从原版继承，原版没有 next-turn 劫掠这条路径，因此补这条路径时直接复用了通用的 `FindUnitsWithinStrikingDistance`。
2. CP 的循环内还有三道 MPDLL 缺失的提前退出（`Community-Patch-DLL/.../CvTacticalAI.cpp:1237-1248, 1283`）：

```cpp
if (pZone->GetPosture() == TACTICAL_POSTURE_WITHDRAW) continue;
if (pPlot->getVisibleEnemyDefender(m_pPlayer->GetID()) != NULL) continue;
// 后续还有：
if (!pZone || pZone->GetOverallDominanceFlag() == TACTICAL_DOMINANCE_ENEMY) continue;
```

其中**"目标地块上有可见敌方守军则跳过"**最关键——这类地块派兵"下回合去劫掠"本就是送死，CP 认为不值得计算。

> **注意**：CP 与 MPDLL 是互不兼容的独立实现，此处仅作对照参考。移植任何逻辑都需按 MPDLL 自身接口重写，不能直接套用。

---

## 5. 瓶颈 C：`CvPlayer::doResearch` 尖峰

`CvPlayer::doResearch` 15 回合累计 44.44 秒 / 587 次，均值 0.0757 秒（正常）。但单次排名异常：

| 秒 | 文明 | 回合 |
|---|---|---|
| **15.36** | 迦太基 | Turn 066 |
| 8.38 | 迦太基 | Turn 065 |
| 6.55 | 迦太基 | Turn 068 |
| 3.58 | 迦太基 | Turn 067 |
| 2.06 | 迦太基 | Turn 071 |
| 2.01 | 印尼 | Turn 069 |
| 1.17 | 奥斯曼 | Turn 066 |
| 其余 | — | 均 < 1.0 |

**前 5 名全部是迦太基，集中在 Turn 065–068**，其他文明无一超过 2.1 秒。

一个附带观察（**待验证**）：迦太基在游戏对局中是**人类玩家所控文明**（此结论来自 `Logs/net_message_debug.log` 的玩家映射，player 0 = 迦太基）。人类玩家本不应产生 AI 的 `doTurn` / `doResearch` 记录。合理解释是该玩家在这几个回合处于**掉线被 AI 接管**状态。但本次未对该假设做交叉验证（例如与掉线时间戳对齐）。

**成因未查。** 均值正常而尖峰极高，说明是特定的输入条件（某些科技的评估代价极高）触发，而非普遍劣化。

---

## 6. 已排除项（量级过小，不构成瓶颈）

| 文件 | 项目 | 累计秒 | 单次最大 |
|---|---|---|---|
| `Homeland-perf.csv` | `PlotSentryMoves` | 8.71 | 0.11 |
| `Homeland-ExecuteMove-perf.csv` | `ExecuteMoveToTarget` | 17.13 | 0.20 |
| `Homeland-ExecuteWorkerMoves-perf.csv` | `ExecuteWorkerMoves` | 13.21 | 0.04 |
| `Homeland-GetBest-perf.csv` | `GetBestUnitToReachTarget` | 8.25 | 0.27 |
| `Military-AI-perf.csv` | `UpdateOperations` | 3.36 | 0.23 |
| `Military-AI-perf.csv` | `UpdateMilitaryStrategies` | 1.43 | 0.06 |

后方 AI 与军事 AI 的时间高度分散（`Homeland-perf.csv` 中除 `PlotSentryMoves` 外没有任何单项累计超过 0.5 秒，但文件总量 443 KB），说明**尾部大量小调用**，无单一热点。

---

## 7. 存疑点与待复核清单

| # | 问题 | 影响 | 建议验证方式 |
|---|---|---|---|
| 1 | CSV 第 2 个字段的真实含义 | 本报告已回避使用；若它是玩家 ID，则部分按文明聚合需重算 | 对照同一回合的多个文明记录，或在 DLL 中定位该字段的写入点 |
| 2 | `doGrowth` 的热点是否确为 `changePopulation` | 决定第 3 节能否给出优化建议 | 在 `doGrowth` 内部分段打点计时 |
| 3 | `doResearch` 15.36 秒的成因 | 未知 | 在 `doResearch` 内部打点，定位到具体科技/评估环节 |
| 4 | 迦太基的记录是否确为"掉线被 AI 接管" | 影响到线分析 | 与 `net_message_debug.log` 的断线时间戳做回合对齐 |
| 5 | `TACTICAL_PILLAGE_RESOURCE_NEXT_TURN` 的来源 | 确认是新增还是改造 | 该枚举位于 `CvTacticalAI.h:732`（枚举尾部），CP 中不存在；但 MPDLL 的 git 历史被 squash 为单个 `6d5b853 SDK baseline` 提交，**无法用 blame 追溯** |
| 6 | 印尼为何远比其他文明严重 | 定位到具体触发条件 | 采集印尼的目标地块数与 `m_CurrentTurnUnits` 规模 |

**第 5 项的佐证**：CP 的 `TacticalAIMoveTypes` 枚举中不存在 `_NEXT_TURN` 系列，且 CP 采用 `FindUnitsForHarassing` 实现同一语义。这**强烈指向**该分支是 MPDLL 侧新增，但无法从版本历史确证。

---

## 8. 优化选项（未实施）

针对瓶颈 B，按风险从低到高：

| 方案 | 预期收益 | 风险 | 说明 |
|---|---|---|---|
| **A. 补回 `getVisibleEnemyDefender` 提前退出** | 直接砍掉"目标有守军"这一类目标 | **极低** | 被跳过的目标本就不可能被选中，CP 已验证过该口径 |
| **B. 次遍 `iTurns` 由 2 改为 1** | 预筛阈值从 `baseMoves × 2` 收紧到 `baseMoves`，进入 A* 的单位数骤减 | 中 | 会改变 AI 行为（只看一回合内可达） |
| **C. 移植 `FindUnitsForHarassing` 式轻量搜索** | 治本 | 高 | 需按 MPDLL 接口重写一个新函数 |
| **D. 限制每回合处理的目标数/单位数上限** | 可控削峰 | 低 | 损失少量战术选择 |

**建议顺序**：先做 A（近乎零行为风险，且有 CP 作为先例），观察印尼该项 Move Type 的耗时变化，再评估是否需要 B。

针对瓶颈 A、C：**暂不建议动手**，需先完成第 7 节第 2、3 项的验证。

### 附带事项

`AIPerfLog = 1` 在联机对局期间持续输出 9 个 CSV（合计约 10 MB，`City-AI-perf.csv` 单文件 4.47 MB 并在每回合追加写入）。采样结束后应关闭该开关。这与性能瓶颈本身无关，但对联机稳定性是额外负担。

---

## 附：关键文件索引

| 路径 | 说明 |
|---|---|
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvTacticalAI.cpp:1813` | `_NEXT_TURN` Move Type 分派 |
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvTacticalAI.cpp:2680-2751` | `PlotPillageMoves` |
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvTacticalAI.cpp:9035-9231` | `FindUnitsWithinStrikingDistance` |
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvTacticalAI.cpp:9072` | `canPillage` 过滤 |
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvTacticalAI.cpp:9118` | `bWillPillage` 短路远程分支 |
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvTacticalAI.cpp:9191` | 必然执行的寻路调用 |
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvAStar.cpp:3845-3876` | `CanReachInXTurns` 及其距离预筛 |
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvAStar.cpp:3882-3951` | `TurnsToReachTarget`（硬编码 `bReusePaths=false`） |
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvAStar.cpp:193-244` | `CvAStar::GeneratePath` 的清理开销 |
| `CIV5MPDLL/CvGameCoreDLL_Expansion2/CvCity.cpp` | `CvCity::doGrowth` |
| `Community-Patch-DLL/CvGameCoreDLL_Expansion2/CvTacticalAI.cpp:1203-1302` | CP 的对照实现 |
