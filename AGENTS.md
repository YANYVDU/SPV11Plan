# SP V11 项目规则

> 本文件供 DeepSeek Harness 读取（等价于 Claude Code 的 `CLAUDE.md`）。
> 详细背景见 `Super-Power-Remaking-of-World-Order/README.md` 与 MPDLL 仓库的 API 说明库。

## 项目定位

- **超级大国（Super Power，SP）** 是基于 MPDLL 的文明五（Sid Meier's Civilization V）大型玩法修正模组。
- 当前版本 **V11**，正式全名 **Super Power V11 - Pillars of Sovereignty**。改版本号不改文件夹/仓库名，改工程文件内名称即可让构建出的模组文件夹名跟着变。
- 分工：**MPDLL 提供功能与 API，SP 写数据库完成功能应用**。
- 相关仓库（同处 `D:\Git\CIV5\dyy`）：

| 仓库 | 作用 | 分支 |
|---|---|---|
| `SP V11`（本仓库） | 主模组（本目录） | main |
| `CIV5MPDLL` | 游戏核心 DLL + MOD 壳 | V11dev |
| `Civ5-MPDLL-API-INSTRUCTION` | API 说明库 | main |
| `world-power` | 世界强权（SP 的衍生模组） | V10FGUI |
| `Community-Patch-DLL` | 上游参考 | master |

## 代码检索：先选对工具，再动手

| 要找什么 | 用什么 | 注意 |
|---|---|---|
| C++ 某文件有哪些函数/类 | `ast_outline(path, lang=cpp)` | 一次拿到全部符号+行号，替代整文件阅读 |
| C++ 某符号在哪定义、谁在调用 | `code_search(query)` + `code_refs(symbol)` | **必须显式传 `repoRoot="D:\\Git\\CIV5\\dyy\\CIV5MPDLL"`**；`code_refs` 按名字解析，不同类的同名函数会误连，结论要看它的 exact/name-only 标注 |
| C++ 结构化模式（"所有 Xxx 调用点"、"所有 if(bBroadcast…) 分支"） | `ast_search(pattern, lang=cpp)` | pattern **必须带具体函数名**，写 `$FUNC($$$)` 这类宽模式会爆 stdout buffer |
| 改 C++ 前想摸清影响面 | `code_change_context(repoRoot=...)` | 给出改动符号、直接调用方、受影响测试 |
| Lua 函数定义 / 调用点 | `ast_search(lang=lua)` | `ast_outline` 不支持 lua（白名单里没有）；检索仍可用，实测能扫出全部 `:SendAndExecuteLuaFunction(...)` 调用点 |
| XML / SQL 内容 | `grep` / `glob` | 两种 AST 工具都不支持这两种格式 |
| 游戏里**实际生效**的数值/文本 | Python `sqlite3` 只读查 `cache\*.db` | 不要 grep 源文件（注释、Row/Replace 覆盖顺序会骗人） |
| 大范围找文件 | `glob` | 别用 shell 的 find |

联机规则自查套路：`ast_search(lang=lua, pattern="$OBJ:SendAndExecuteLuaFunction($$$)")` 列出全部广播点 → 逐个确认是否在 GameEvent 回调内（在回调内即违规，应改直调）。

## 构建与打包

### 编 DLL（CIV5MPDLL）

```cmd
D:\Git\CIV5\build-mpdll.cmd
```

该脚本做三件事：删 `BuildTemp\VS2022_CvGameCore_Expansion2ReleaseWin32`（**必须先删，否则 PCH 陈旧会报大量"成员不存在"假错误**）→ 跑 MSBuild Release|Win32 → post-build 自动拷到 `(1) CIV5MPDLL\DLL`。

**工具链约束（2026-10-17 实测，别随意改）**

- 工程是 **VS2022 v143（MSVC 14.43.34808）+ VS2008 的 STL 头 + v90 C++ 运行库** 的混合体：
  - `CIV5MPDLL\MPDLLCompile.props` 把 `IncludePath`/`LibraryPath` 写死指向
    `C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\...` 与 `C:\Program Files\Microsoft SDKs\Windows\v6.0A\...`
  - **这两个目录不能删**，删了立刻编不过
- 产物必须导入 **`MSVCP90.dll` / `MSVCR90.dll`**。用 `dumpbin /imports` 核对；若变成 `MSVCP140`，说明 STL ABI 换了——游戏主程序是 VS2008 编的，`CvDllInterfaces.h` 里 `ICvGameSetup1` 的 `setVersionString(const std::string&)`/`versionString()`/`setVictories(const std::vector<bool>&)` 会跨 exe↔DLL 传 `std::string`，ABI 一变联机建局会崩。
- 导出表只应有 `DllGetGameContext`。
- 额外开关在 `D:\mig\extra.props`（命令行 `ForceImportAfterCppTargets` 传入，**不改仓库文件**）：`VCToolsVersion=14.43.34808`、`/Zc:threadSafeInit-`、`/Zc:sizedDealloc-`、显式链 VS2008 的 `msvcprt.lib`、`/FORCE:MULTIPLE`。

### 打包成 MOD

```cmd
D:\Git\CIV5\dyy\civ5-mod-builder.exe --from "<工程.civ5proj>" --to "<MODS目录>"
```

- MODS 目录：`C:\Users\123\Documents\My Games\Sid Meier's Civilization 5\MODS`
- 运行前清掉 `ELECTRON_RUN_AS_NODE`（PowerShell：`Remove-Item Env:ELECTRON_RUN_AS_NODE`）
- MPDLL 工程：`CIV5MPDLL\(1) CIV5MPDLL\(1) CIV5MPDLL.civ5proj`
- SP 工程：`V11\Super-Power-Remaking-of-World-Order\Super Power - Remaking of World Order (v 7)\Super Power - Remaking of World Order (v 7).civ5proj`
- 时机：DLL 编译成功 + SQL/C++ 改完后的收尾阶段，**先问用户**要不要打包
- 发布版：功能全部提交、用户主动升级版本号后，打包前询问是否出"发布版"，发布版模组文件夹名要带 `-<最新提交短哈希>`

## MPDLL 编码约定

- **CIV5MPDLL 仓库里所有代码注释一律英文，禁止中文**：源文件是无 BOM 的 UTF-8，VC9 工具链按 GBK 解析，中文注释会引发 C4716/C4700 之类误报。
- 新增序列化成员（`CvPlayer`/`CvCity`/`CvUnit` 的新字段）必须做版本门控，用 `CustomMods.h` 里 `MOD_SERIALIZE` 系列宏包 Read/Write，保旧档兼容；没有现成脚本时先问用户是否补。
- 当前 DLL 版本号 **164**（`CvGameCoreDLL_Expansion2/CustomMods.h`），与工作区不一致时主动问是否同步。
- 新增数据库表要在 API 说明库对应分类 `.sql` 里补带中文注释的建表文档：政策→`policy.sql`、特性→`trait.sql`、信条→`belief.sql`、建筑→`building.sql`、单位→`unit.sql`、晋升→`promotion.sql`、游戏速度→`gamespeed.sql`。

## 数据核对：优先查数据库，不要 grep 源文件

`C:\Users\123\Documents\My Games\Sid Meier's Civilization 5\cache\` 下：

- `Civ5DebugDatabase.db` — 游戏数据（晋升/单位/建筑/政策等表），确认模组是否写入成功
- `Localization-Merged.db` — 合并后的语言文本，主表 `LocalizedText`（列 Language/Tag/Text）
- 原版文本查 `Localization-BaseGame.db`、`Localization-Expansion - Brave New World.db`、`Localization-Expansion - Gods and Kings.db`、`Localization-Civilization 5 Complete.db`

**不要再翻游戏安装目录**（旧指南里的 `D:\steam\...` 已失效）。用 Python 的 `sqlite3` 标准库查（只读打开，避免锁库）。

## SP 模组规则

- 文本文件在 `...\Gameplay\XML\Localization`，三份：简中 / 繁中 / 英文。**新增 Tag 必须三份都加**。
- 文本里适量用 `[ICON_XXX]`（如 `+20[ICON_RESEARCH]科研`），ICON 名称见 `IconFontMapping`。
- **默认加载组合**：只说"测一下"时，默认只启用 `(1) CIV5MPDLL` + `(2) Super Power - Pillars of Sovereignty`；要加世界强权/单位拓展等，用户会明说。
- **UI/Lua 可热更新**：改完直接复制到 MODS 里对应文件夹替换，用户读档即生效；**数据库类改动必须新开存档**，强行替换会坏档。
- 城邦独特能力（CSUA）内容在 `...\Gameplay\XML\CSUA`，由 `CustomModOptions-SP_UNIQUE_CITYSTATE` 控制。
- 城邦 UA 文本里的"假建筑"映射：
  - 城市规模：`SP_CityScales.sql`，`CITYSCALE_TOWN(1)→BUILDINGCLASS_CITY_SIZE_TOWN`、`SMALL(6)→_SMALL`、`MEDIUM(15)→_MEDIUM`、`LARGE(26)→_LARGE`、`XL(40)→_XL`、`XXL(60)→_XXL`、`GLOBAL(80)→_GLOBAL`
  - 腐败：`SPCorruptions.sql` + `Buildings\Corruption.xml`，`CORRUPTION_LV1..LV5 → BUILDINGCLASS_CITY_HALL_LV1..LV5`，由 `CvCorruption.cpp` 按分数动态授予

## 联机（多人生效）规则

- 文明五联机是"锁步确定性模拟 + 主机权威"。
- **引擎 GameEvent 回调**（PantheonFounded、PlayerDoTurn、PlayerCityFounded 等）：各端同步触发，**直接改状态**，禁止在里面 `SendAndExecuteLuaFunction`（会叠加成双倍）。
- **UI 单端交互**（按钮、`LuaEvents.*Add`、`Controls:RegisterCallback`、InputHandler）：只有点击者触发，**必须 `obj:SendAndExecuteLuaFunction(...)` 广播**，否则 desync。
- 同一函数两路共用时用 `bBroadcast` 参数隔离（参考 `UtilityFunctions.lua` 的 `SatelliteLaunchEffects`）。
- 广播参数必须确定性一致（用显式玩家/城邦 ID，别依赖 `getActivePlayer()`；别传端间未同步的瞬时值）。
- 只读 `GetXxx`、`Game.Rand`、纯布尔判定 → 直调，不加 send。
- 改动联机路径后必须**双人实机**验证不叠加、不 desync。

## DLC 整合分发版

- 仅当"联机魔改"/"超级信条"被打进**无 .modinfo 的 DLC 副本**时才需要手动装载：在生效的 `InGame.lua` 的 `if not bAddinsLoaded` 块内，用 `ContextPtr:LoadNewContext("Assets/DLC/<该DLC名>/Mods/...")` 补两行（`超级信条V9/LUA/myth_religions`，`LUA` 大写）。
- 顶层 `UI/InGame.lua` 与 `Mods/(2) Super Power.../UI/InGame/InGame.lua` **都要补**。
- 不要用 `include("Lua/tool")` 这种相对子路径（跨模组不解析）；该补丁是 DLC 专属，**不要写进 SP 主仓库**的 InGame.lua。

## 世界强权

- `world-power` 是 SP 的衍生模组，加载需 SP 前置；覆盖层级：原版 → MPDLL → SP → 世界强权。
- SP 改 UI/Lua 时若工作区有强权仓库，要查它有没有替换同名文件并同步。
- **SP 新功能开发期不用管强权**，等强权适配当前 SP 版本时统一处理。
