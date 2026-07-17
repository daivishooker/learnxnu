# LiveContainer 启动链路跟读

配合 [MECHANISM.md](MECHANISM.md)。路径相对 `projects/LiveContainer/`。

上游快照：`e370a92d`（3.8.0）。

---

## Pass 1 — 进程入口

**文件：** `LiveContainer/main.c`

1. `LiveContainerMainC`
2. 若存在 `$HOME/Library/preloadLibraries.txt`：逐行 `dlopen(..., RTLD_LAZY|RTLD_GLOBAL)`，读完删除文件
3. `dlopen("@executable_path/Frameworks/LiveContainerShared.framework/LiveContainerShared", …)`
4. `dlsym(..., "LiveContainerMain")` → **musttail** 调用

DEBUG 下另有 `main` → `callAppMain`（直接跳已解析的客 `appMain`）。

**读完问题：** 为什么 Shared 要单独做成 framework，而不是链进主可执行文件？

---

## Pass 2 — 调度：跑 UI 还是跑客 App

**文件：** `LiveContainer/LCBootstrap.m` → `LiveContainerMain`

关键状态：

| 来源 | Key / 条件 |
|------|------------|
| 本地 | `selected` / `selectedContainer` / `launchAppUrlScheme` |
| App Group | `LCLaunchExtension*`（Share/Launch 扩展下发，3 秒内有效） |
| 特殊值 | `selected == "ui"` → 清选择，进管理 UI |
| SideStore | `LCOpenSideStore` 或 `builtinSideStore` + 存在 `SideStoreApp.framework` |

逻辑要点：

1. `getContainerUsingLCSchemeWithFolderName`：若别的 LC 实例已占用容器 → `openURL(livecontainer-launch…)` 切过去
2. 有客 App → `invokeAppMain`；失败写 `error` 或 LiveProcess `cancelRequestWithError`
3. 无客 App → `dlopen LiveContainerSwiftUI` → `dlsym("main")`

---

## Pass 3 — `invokeAppMain` 环境伪造

**同一文件** `invokeAppMain`。建议按编号对照源码：

| # | 动作 | 符号 |
|---|------|------|
| 1 | JIT / 证书门槛 | `checkJITEnabled`，`certificatePassword` |
| 2 | 找 Bundle | `Documents/Applications/` 或 App Group `LiveContainer/Applications/` + `LCAppInfo.plist` |
| 3 | 数据 UUID | `selectedContainer` / `LCDataUUID` / bookmark |
| 4 | Tweak 目录 | `LC_GLOBAL_TWEAKS_FOLDER`，symlink `TweakLoader.dylib` |
| 5 | JIT 绕过 | `init_bypassDyldLibValidation` |
| 6 | 可执行路径 | `*_CFGetProcessPath()=`；`overwriteExecPath` |
| 7 | Home | `setenv HOME` / `CFFIXED_USER_HOME`；建 Library/Documents… |
| 8 | Bundle | `overwriteMainNSBundle`；`overwriteMainCFBundle` |
| 9 | argv / 进程名 | `NSProcessInfo` arguments[0]、`_CFGetProgname` |
| 10 | Hooks | `NUD*` / `SecItem*` / `NSFM*` / `DyldHooksInit` |
| 11 | 加载 | `dlopen_nolock(appExecPath, …)`（iOS 27+ 可 `bypass_seg_count_check`） |
| 12 | 入口 | `getAppEntryPoint` 扫 `LC_MAIN` → `appMain(argc,argv)` |

`overwriteExecPath` 细节：

1. `performHookDyldApi("_NSGetExecutablePath", …, hook__NSGetExecutablePath_overwriteExecPath)`
2. 调用一次 `_NSGetExecutablePath(newPath, NULL)`，hook 里改 `DyldConfig.mainExecutablePath_*`
3. 立刻把原函数装回去

`DyldConfig` 偏移随系统变：旧版 `0x10`，iOS 18.4+ `0x20`，另有长度字段。

---

## Pass 4 — Mach-O 改造（安装期）

**文件：** `LiveContainer/LCMachOUtils.m` → `LCPatchExecSlice`

跟读顺序：

1. `filetype` / flags  
2. `__PAGEZERO` vmaddr/vmsize  
3. 遍历 load commands：是否已有 ID/TweakLoader、`LC_CODE_SIGNATURE`、chained fixups 段数  
4. 插入或改写 `LC_ID_DYLIB` / `LC_LOAD_DYLIB`  
5. 去重依赖  

安装与重签调用点：`LiveContainerSwiftUI/Utilities/LCUtils.m`（`ZSigner signWithAppPath` / `signMachOPathArr` / `adhocSignMachOAtPath`）。

---

## Pass 5 — JIT 库验证绕过

**文件：** `LiveContainer/dyld_bypass_validation.m`

1. `searchDyldFunctions`：在 dyld 映像里按字节特征找内部 `fcntl`/`mmap`
2. `litehook_hook_function` 换成 `hooked___fcntl` / `hooked_mmap`
3. `F_CHECK_LV` → 恒成功；`F_ADDFILESIGS_RETURN` → 覆盖整文件
4. EXEC 映射失败 → 匿名页拷贝 + `mprotect`

对照 learnxnu：Day 15 `mmap`/`mprotect`，Day 65 `csops`。

---

## Pass 6 — Dyld 伪装与 TweakLoader

**文件：**

- `LiveContainer/Tweaks/Dyld.m` → `DyldHooksInit`
- `TweakLoader/TweakLoader.m` → `TweakLoaderConstructor`

Dyld hooks（按需）：

- `dlsym(RTLD_MAIN_ONLY, …)` → 客主镜像  
- `_dyld_image_count/header/name/slide` → 藏宿主与 TweakLoader  
- 可选 `jitless_hook_dlopen`  
- 可选 spoof `dyld_program_sdk_at_least`

TweakLoader：`dlopen` CydiaSubstrate → 扫全局 Tweaks 与 per-app 目录。

---

## Pass 7 — 多任务（可选）

**文件：** `MultitaskSupport/AppSceneViewController.m`

`createSceneWithDefinition`（`FBSceneManager`）→ 展示场景；`PiPManager` 管画中画。  
与主链路关系：多任务往往经 LiveProcess/扩展再进 `invokeAppMain`，而不是在同一 UI 进程里第二次 `UIApplicationMain`。

---

## 建议自测问题

1. 为什么要把 `MH_EXECUTE` 改成 `MH_DYLIB`，运行时又改回 `MH_EXECUTE`？  
2. iOS 26 之后为什么必须导入证书？`checkJITEnabled` 哪一行封死了 JIT？  
3. 128 个 keychain group 如何映射到「同 App 多容器」？看 `SecItem.m`。  
4. `0xdead10cc` 相关修复在哪（`Dead10ccFix.m` / App Group 迁移）？  
5. `builtin_vm_protect` 的 syscall 号 `-0xe` 对应哪个 Mach trap？
