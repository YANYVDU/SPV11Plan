# 城邦争夺分数计算器

复刻 MPDLL `CvDiplomacyAI::GetBestApproachTowardsMinorCiv` 的权重逻辑，计算
**每个大文明领袖 × 每个城邦** 的「争夺分数」（FRIENDLY + PROTECTIVE 权重之和），
用于设计 SP V11 城邦独特能力（CSUA）的「争夺倾向」数值。

## 快速开始

```bash
python cs_contest_calculator.py
```

默认读取 `Civ5DebugDatabase.db`（游戏上次加载模组后形成的数据库存根，含 SP 覆盖后的最终权重值），
使用内置的城邦倾向默认值，输出终端摘要 + HTML 交互报告（`cs_contest_report.html`）。

## 常用参数

| 参数 | 说明 |
|---|---|
| `--db 路径` | Civ5 数据库路径（默认 `Civ5DebugDatabase.db`） |
| `--csv 路径` | 城邦争夺倾向 CSV（覆盖内置默认值） |
| `--strategy DIPLO\|CULTURE\|CONQUEST\|SCIENCE\|ALL` | 胜利路线（默认 DIPLO） |
| `--full` | 终端输出完整 43 领袖矩阵（默认只输出每城邦 Top5） |
| `--top N` | 摘要里每城邦显示的领袖数（默认 5） |
| `--out 路径` | HTML 报告输出路径 |

## 城邦倾向 CSV 格式

列：`MinorCivType,CULTURE,SCIENCE,MILITARY,GOLD,RELIGION,GROWTH,DIPLOMACY`
每行一个城邦，倾向数值 0–10（可只填部分维度）。示例见 `sample_inclination.csv`。

```csv
MinorCivType,CULTURE,SCIENCE,MILITARY,GOLD,RELIGION,GROWTH,DIPLOMACY
MINOR_CIV_ZURICH,3,10,0,0,0,0,0
MINOR_CIV_VALLETTA,0,0,10,0,0,2,0
```

## 数据来源（全部直接从 db 读取）

- `Defines` 表：49 个 `MINOR_APPROACH_*` 权重常量（SP 覆盖后的最终值）
- `Leaders` / `Civilization_Leaders`：领袖与文明映射
- `Leader_Flavors`：领袖倾向数值（38 种 flavor，工具聚合成 7 个玩法维度）
- `Leader_MinorCivApproachBiases`：领袖对城邦各 approach 的个性偏置
- `Leader_Traits` / `Traits`：领袖城邦 trait 修正（希腊友谊/暹罗加成）
- `MinorCivilizations`：城邦列表（原生 trait + SP V11 `UAType`）
- `CityStateUAs`：SP V11 城邦 UA 映射

## 复刻的权重项

1. IGNORE 默认
2. 领袖 approach 个性偏置
3. 胜利路线 Grand Strategy（征服/外交/文化）
4. 领袖城邦 trait 修正
5. 城邦原生 trait（军事城邦更难被勒索）
6. 城邦性格（场景参数）
7. 距离（场景参数）
8. **CSUA 倾向匹配**（核心新增）：城邦倾向 × 领袖倾向的余弦相似度 × 系数（默认 20）

运行时状态（资源缺乏/贸易价值/征服目标值/战争状态/随机因子等）未复刻，
作为场景参数之外的可扩展项。

## 已知发现

原版 Civ5 领袖 flavor 中「军事」维度（聚合了 11 种军事 flavor）天然偏大，
因此纯科技向城邦（如 Zurich）倾向匹配到的常是「均衡型」领袖而非纯科技领袖。
这是 flavor 数据的固有特性，可通过调整 `DIMENSION_FLAVORS` 映射或城邦倾向数值校准。
