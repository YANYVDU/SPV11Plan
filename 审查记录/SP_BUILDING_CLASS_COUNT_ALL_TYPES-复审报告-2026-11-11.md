# SP_BUILDING_CLASS_COUNT_ALL_TYPES 复审报告（合并版）

- **复审日期**：2026-11-11
- **复审对象**：`CIV5MPDLL` 工作区改动（`V11dev`，HEAD `89c0a67` + 未提交改动）与 `SP V11` 的配套开关
  - `(1) CIV5MPDLL/CustomModOptions.xml`
  - `CvGameCoreDLL_Expansion2/`：`CustomMods.h/.cpp`、`CvCity.h/.cpp`、`CvPlayer.cpp`、`CvCultureClasses.cpp`、`CvCityStateUAClasses.cpp`、`Lua/CvLuaCity.h/.cpp`
  - `SP V11/.../Gameplay/XML/DLL_Options.xml`
- **复审方式**：逐文件 `git diff` 复核；全仓检索政策/信条类 `BuildingClass*` 消费点；核对建筑变更的所有入口与过时状态更新时序；核对序列化与读档时序；MSBuild Release|Win32 编译验证
- **总结论**：**通过**。编译 0 error；`CvGameCore_Expansion2.dll`（5,472,256 B，2026-11-11 02:46:43）已复制到 `(1) CIV5MPDLL\DLL\`

---

## 一、最终实现

### 1.1 选项

| 位置 | 内容 |
|---|---|
| `CustomMods.h:993`、`:1847` | `MOD_SP_BUILDING_CLASS_COUNT_ALL_TYPES` 宏 + `MOD_OPT_DECL` |
| `CustomMods.cpp:613` | `MOD_OPT_CACHE` |
| `CustomModOptions.xml:1203` | `Row Class="6" Value="0"`（位于 `<CustomModOptions>` 内） |
| SP `DLL_Options.xml:413-416` | `<Update ... Set Value="1"/>` |

### 1.2 新增接口（O(1)）

| 接口 | 位置 | 说明 |
|---|---|---|
| `int CvCity::GetNumBuildingClassActive(class)` | `CvCity.cpp:23715` | 只数该 class 下非过时建筑（全部 type） |
| `void CvCity::ChangeNumBuildingClassActive(...)` | `CvCity.cpp:23723` | 在 `processBuilding` 增量维护 |
| `void CvCity::RebuildActiveBuildingClassCounts()` | `CvCity.cpp:23731` | 惰性重建（首次查询时） |
| Lua `city:GetNumBuildingClassActive(classID)` | `CvLuaCity.cpp:2404` | 已注册，UI 可直接调用 |

- 成员 `m_paiNumActiveBuildingClasses` + `m_bActiveBuildingClassCountsValid` 均**不序列化**，`reset()` 清零并置无效；首次查询时重建，避免依赖「城市/Team 谁先读档」的引擎顺序。
- 维护条件（`CvCity.cpp:8707`）：`bObsolete || !owningTeam.isObsoleteBuilding(eBuilding)`，覆盖建造/过时/取消过时/拆除/过时态赠送等全部转移。

### 1.3 消费点

| 路径 | 位置 | 计数 |
|---|---|---|
| 信条产出 | `CvCity.cpp:9049` | Active |
| 信条快乐 | `CvCity.cpp:12781` | Active |
| 信条旅游 | `CvCultureClasses.cpp:4633` | Active |
| 政策旅游 | `CvCultureClasses.cpp:4784` | Active |
| 政策产出（采纳/取消） | `CvPlayer.cpp:30139` | Active |
| 政策快乐 | `CvCity.cpp` Policy Building Mods | **保持原逻辑（含过时）** |
| CSUA 拉古萨快乐 | `CvCity.cpp:12927` | Active |
| CSUA 布拉格/埃里温产出修正 | `CvCity.cpp:13684` | Active |
| CSUA `GetBuildingGreatPersonPointsForCity` | `CvCityStateUAClasses.cpp:2821` | Active |
| CSUA 新加坡（玩家级） | `CvPlayer.cpp:18683`、`:35029` | 仍用 `getBuildingClassCount`（无 Active 变体） |

---

## 二、首轮复审发现与处理

| 编号 | 级别 | 内容 | 处理 |
|---|---|---|---|
| R-1 | 中 | 旧存档不会按新规则重算政策建筑类产出（累加器随档保存） | 用户裁定不考虑旧档，只用新局测试 |
| R-2 | 中 | UI 提示与引擎口径 | 复核后确认建筑提示框是「每座建筑」语义，开关后仍正确；未新增必填接口；另提供了 Lua `GetNumBuildingClassActive` 备用 |
| R-3 | 低 | 政策快乐未过滤过时建筑 | 用户裁定保持原样 |
| R-4 | 低 | 扫描 380 条建筑可优化 | 已改为 O(1) class 计数数组 |
| R-5 | 信息 | 覆盖范围（建筑给 class 的加成、trait、CSUA 等） | 记录在案，未纳入本开关 |
| R-6 | 信息 | CSUA 原本按 class 计数、无单型限制，但含过时建筑 | 已按用户要求把城市级 CSUA 切到 Active |
| R-7 | 信息 | MODS 内副本未更新 | 待重新部署 |
| R-8 | 信息 | 依赖 `MOD_BUGFIX_MINOR`（当前恒 true） | 无需处理 |
| R-9 | 信息 | 真正受影响的场景：被占领城市的外文明建筑、dummy 建筑等 | 记录在案 |

---

## 三、二次复审核对（针对最终代码）

| 检查项 | 结果 |
|---|---|
| 选项注册（宏 / DECL / CACHE / XML / SP 开启） | 齐全，SP 的 Update 位于 `<CustomModOptions>` 块内 |
| 建筑计数先于 `processBuilding` | 已确认：`CvBuildingClasses.cpp:5385` 先写计数，`5399` 再调 `processBuilding`；免费建筑同理（`5633`→`5636`） |
| 过时标志先于 `processBuildingObsolete` | 已确认：`CvTeam.cpp:5164` 先改计数，`5177` 再处理城市 |
| 全部建筑变更入口 | `SetNumRealBuildingTimed` / `SetNumFreeBuilding` / `acquireCity`（`CvPlayer.cpp:3370/3447/3523`）均走 processBuilding，无直接写数组旁路 |
| 惰性重建时机 | 首次查询即使在 `processBuilding → UpdateReligion` 内，建筑计数与 Team 过时标志均已就绪，结果正确 |
| 增量路径与重算路径一致性 | 政策两行（`CvCity.cpp:8393-8394`）位于 `7747` 过时门控块内，过时会回退；`processPolicies` 用 Active 重算，一致 |
| 序列化 | 新增成员不写档；`read` 不重建，首次查询重建，存档格式与版本号不变 |
| 开关关闭等价性 | 各消费点 `else` 分支与原实现逐段等价（旅游政策块仅 `pkEntry` 判空顺序有极微差异，实际不可达） |
| Lua 绑定 | `LUAAPIEXTN` 声明、`Method` 注册、`NO_BUILDINGCLASS` 防护齐全，位于 `MOD_API_LUA_EXTENSIONS` 条件块内 |
| 编译 | `BUILD_EXIT=0`，0 error |

---

## 四、遗留提示

- **F-1【信息】信条语义变化**：原版信条建筑类加成不判过时；开关开启后信条也只算非过时建筑。这是 Active 口径的必然结果，需确认符合预期。
- **F-2【信息】快乐与产出口径不同**：政策快乐仍含过时（按裁定），产出/旅游排除。
- **F-3【已处理】CSUA 已切换**：拉古萨、布拉格/埃里温、`GetBuildingGreatPersonPointsForCity` 三处城市级计数改用 Active；新加坡两处为玩家级 `getBuildingClassCount`，暂无 Active 变体。
- **F-4【低】理论风险**：若读档完成前的极早期有代码查询 Active 计数，重建会固化当时状态；当前路径中未发现此类查询，必要时可在 `CvCity::doTurn` 再强制重建兜底。
- **F-5【信息】部署**：MODS 内 `(1) CIV5MPDLL (v 68)` 与 SP 目录仍是旧拷贝，需重新部署 DLL、`CustomModOptions.xml`、`DLL_Options.xml` 后才能实测。

---

## 五、结论

开关关闭时与原逻辑等价；开启后政策/信条/城市级 CSUA 的建筑类加成统一为「按 class 统计非过时建筑」，且政策增量路径与采纳/取消时的重算路径口径一致。**实现可进入实测**，前提是完成 MODS 部署并用新开局验证。
