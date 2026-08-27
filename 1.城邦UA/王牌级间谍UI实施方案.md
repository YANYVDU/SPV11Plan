# 王牌级间谍（第 4 级）UI 实施方案 —— 方案一：图标复用 + 金色染色

## 一、背景与目标

- 在现有 3 级间谍（新手 / 特工 / 特级特工）之上，新增第 4 级"王牌级间谍"（Master Spy）。
- **硬约束：不新增任何图片文件**，仅复用现有资源完成 UI 区分。
- 采用**方案一**：等级图标复用图集中最高级（特级特工）的徽章，再用 `SetColor` 将其染成金色，形成视觉区分。

## 二、前提确认（为什么不能"加一格图集"）

- 等级图标共用图集 `Esp_Spy_Upgrades21.dds`，为 **21px 一格、共 3 格**（竖排 y=0 / 21 / 42），已被 3 个等级占满，**没有第 4 格**，无法通过偏移 y=63 显示独有图标。
- 游戏本体 BNW 本地化文本仅有 `TXT_KEY_SPY_RANK_0/1/2`（Recruit / Agent / Special Agent），原版本来就是 3 级，无第 4 级文本可复用。

## 三、C++ 侧改动（CIV5MPDLL 仓库，注释一律英文）

1. **枚举加等级**：[CvEspionageClasses.h:19-25](CvEspionageClasses.h#L19-L25) 的 `CvSpyRank` 增加 `SPY_RANK_MASTER_SPY`（置于 `SPY_RANK_SPECIAL_AGENT` 之后，值 = 3）。
2. **等级转文本键**：[CvEspionageClasses.cpp:2026-2042](CvEspionageClasses.cpp#L2026-L2042) 的 `GetSpyRankName` 增加：
   ```cpp
   case SPY_RANK_MASTER_SPY:
       return "TXT_KEY_SPY_RANK_3";
       break;
   ```
3. **升级逻辑覆盖**：[CvEspionageClasses.cpp:1049](CvEspionageClasses.cpp#L1049) 附近 `LevelUpSpy` 中 `iSpyRank >= SPY_RANK_AGENT` 的分支（升级提示 / 奖励文本等），确认覆盖到新等级。
4. **Tooltip 覆盖**：`GetInfluenceSpyRankTooltip`（CvCulture 相关）同步覆盖第 4 级，否则提示文字不显示等级说明。
5. **序列化 / 版本控制**：若本次改动涉及新增成员变量，按 MPDLL 规则使用 `MOD_SERIALIZE` 包裹 + 版本门控读取，保证旧存档兼容；`MOD_DLL_VERSION_NUMBER`（当前 164）是否需提升，与用户确认。
6. **编译前清理 PCH 缓存**：修改了被 PCH 包含的头文件（CvEspionageClasses.h），先删除 `BuildTemp/VS2022_CvGameCore_Expansion2ReleaseWin32` 再编译，避免复用旧 PCH 报假错误。

## 四、Lua 侧改动（EspionageOverview.lua）

> 该文件属于游戏本体 DLC（`Assets/DLC/Expansion2/UI/InGame/Popups/EspionageOverview.lua`），需要**复制进模组**后覆盖发布。

1. **偏移表加一行**（约 26-30 行 `g_RankOffsets`）：
   ```lua
   local g_RankOffsets = {
       TXT_KEY_SPY_RANK_0 = {x = 0,y = 42},
       TXT_KEY_SPY_RANK_1 = {x = 0,y = 21},
       TXT_KEY_SPY_RANK_2 = {x = 0,y = 0},
       TXT_KEY_SPY_RANK_3 = {x = 0,y = 0}   -- 王牌复用最高级徽章
   };
   ```

2. **详情面板渲染处**（约 378 行，`Controls.AgentRank:SetTextureOffset(...)` 后）加金色染色：
   ```lua
   Controls.AgentRank:SetTextureOffset(rankOffsets[agent.Rank]);
   if agent.Rank == "TXT_KEY_SPY_RANK_3" then
       Controls.AgentRank:SetColor(255, 205, 60, 255);  -- 金色
   end
   ```

3. **列表条目渲染处**（约 562 行 `agentEntry.AgentRank:SetTextureOffset(...)` 后）同样处理：
   ```lua
   agentEntry.AgentRank:SetTextureOffset(rankOffsets[v.Rank]);
   if v.Rank == "TXT_KEY_SPY_RANK_3" then
       agentEntry.AgentRank:SetColor(255, 205, 60, 255);
   end
   ```

> 说明：`SetColor` 为整图染色，仅当徽章主色接近白/灰时效果最佳，需实机验证观感。

## 五、本地化文本（SP 三语言都要加）

新增 `TXT_KEY_SPY_RANK_3`，三个语言文件同步（`Gameplay/XML/Localization` 下的简中 / 繁中 / 英文）：

| 语言 | 文本 |
|---|---|
| 简中 | 王牌间谍 |
| 繁中 | 王牌間諜 |
| 英文 | Master Spy |

## 六、文件覆盖与发布提醒

- 改动涉及游戏本体 DLC 的 `EspionageOverview.lua`（及 XML 若需叠加层），须将文件放入模组覆盖；UI 覆盖层级为 **原版 → MPDLL → SP → 世界强权**。
- **当前开发阶段不管世界强权**：SP 未适配世界强权前，无需同步到强权仓库。
- UI / Lua 文件**支持热读取**：调试时直接把修改后的文件复制进 MOD 构建目录替换旧文件，读档即可看到变化，无需重开存档。

## 七、验证要点

1. 王牌级间谍在列表和详情面板均显示**金色特级特工徽章**，其余等级保持原色。
2. 等级名 tooltip 正确显示"王牌间谍 / Master Spy"。
3. 间谍升级到王牌级后，图标即时变金。
4. 确认染色不影响其它等级图标（颜色状态只按当前 rank 设置，重新渲染会覆盖）。

## 八、方案取舍

- **方案一（本方案）**：改动最小、零资源。缺点——图标形状与特级特工相同，仅靠颜色区分。
- **方案二（进阶）**：叠加层做高亮框 / Unicode `★` 徽章，视觉更强但改动更多。
- **终极方案（放开"不新增图片"约束时）**：把 `Esp_Spy_Upgrades21.dds` 换成 4 格图集（84px 高，新增王牌徽章），Lua 加 `TXT_KEY_SPY_RANK_3 = {x = 0, y = 63}`。一张图解决全部问题，视觉最统一，建议长期采用。
