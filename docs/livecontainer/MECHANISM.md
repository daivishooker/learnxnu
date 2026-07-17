# LiveContainer 机制说明

源码：[`projects/LiveContainer/`](../../projects/LiveContainer/)  
上游：[LiveContainer/LiveContainer](https://github.com/LiveContainer/LiveContainer)（**AGPL-3.0**）  
快照：见 [`SOURCE.md`](../../projects/LiveContainer/SOURCE.md)

一句话：**不是模拟器**。宿主 App（LiveContainer）把客应用的 Mach-O **改造成可被 `dlopen` 的动态库形态**，伪造「我就是这个 App」的路径/Bundle/Home，再跳进客应用入口跑 `UIApplicationMain`。

---

## 1. 它解决什么问题

| 痛点 | LiveContainer 做法 |
|------|-------------------|
| 免费开发者账号安装 App 数量有限 | 客应用装在容器目录里，**不占独立系统安装槽** |
| 想多开/多数据 | 同一 IPA 多个 data container |
| 签名成本 | 有 JIT：可绕过库验证；无 JIT：用宿主证书 **ZSign** 重签 |

官方强调：第三方闭源改版能看到容器内全部数据（含 keychain）——只信官方构建。

---

## 2. 仓库模块地图（贴近代码）

```text
projects/LiveContainer/
├── LiveContainer/                 # 主执行体（LiveContainerShared）
│   ├── main.c                     # LiveContainerMainC：preload → dlopen Shared → LiveContainerMain
│   ├── LCBootstrap.m              # LiveContainerMain / invokeAppMain（核心）
│   ├── LCMachOUtils.m             # LCPatchExecSlice：MH_EXECUTE→MH_DYLIB、PAGEZERO、注入 TweakLoader
│   ├── dyld_bypass_validation.m   # JIT：hook dyld 内部 mmap/fcntl，绕过 library validation
│   ├── LCSharedUtils.*            # App Group、证书、容器占用探测
│   └── Tweaks/
│       ├── Dyld.m                 # hide LC、spoof SDK、JIT-less dlopen、入口伪装
│       ├── SecItem.m              # keychain access group 半隔离
│       ├── NSUserDefaults.m       # 偏好写入客容器
│       ├── NSFileManager+GuestHooks.m
│       └── …
├── LiveContainerSwiftUI/          # 管理 UI；无选中 App 时由 dlsym("main") 进入
│   └── Utilities/LCUtils.m        # 安装/重签时调用 ZSigner
├── TweakLoader/                   # constructor：加载 CydiaSubstrate + Tweaks/*.dylib
├── ZSign/                         # JIT-less 签名（ZSigner ObjC 门面）
├── MultitaskSupport/              # FrontBoard FBScene 多窗口 / PiP
├── LiveProcess/                   # appex：在扩展进程里跑客应用（多开协作）
├── SideStore/ ShareExtension/ LaunchAppExtension/
├── litehook/                      # 符号重绑 / 函数 hook（vendored）
├── OpenSSL/                       # 未 vendored（见 OpenSSL/README.VENDOR.md）
└── entitlements.xml               # 宿主 entitlement：128 个 keychain-access-groups
```

分支语义：

- **无 App 被选中** → `dlopen LiveContainerSwiftUI` → `LiveContainerSwiftUIMain`
- **有 App 被选中** → `invokeAppMain` → `dlopen` 客可执行文件 → `appMain(argc,argv)`

---

## 3. 冷启动时序（函数级）

```text
进程入口
  LiveContainerMainC (LiveContainer/main.c)
    ├─ 可选：读 ~/Library/preloadLibraries.txt → dlopen 每行
    ├─ dlopen Frameworks/LiveContainerShared.framework
    └─ musttail → LiveContainerMain (LCBootstrap.m)

LiveContainerMain
  ├─ 读 selected / selectedContainer / LaunchExtension 任务
  ├─ 若另一 LC 实例正占用该容器 → openURL 切过去，本进程不跑客 App
  ├─ if selectedApp || isSideStore:
  │     invokeAppMain(...)          ← 客环境 + dlopen + 跳入口
  │     （正常客 App 不会返回；返回则写 error）
  └─ else:
        dlopen LiveContainerSwiftUI → dlsym("main") → 管理 UI

invokeAppMain (LCBootstrap.m)
  1. checkJITEnabled()
       - 越狱可读 /var/mobile → 视为可用
       - iOS 26+ 强制 JIT-less（函数直接返回 false）
       - 否则 csops(pid,0,&flags) 看 CS_DEBUGGED
  2. 定位客 Bundle：Documents/Applications/<id> 或 App Group 共享目录
  3. 解析 LCDataUUID → 数据目录；设 HOME / CFFIXED_USER_HOME
  4. JIT? → init_bypassDyldLibValidation()
  5. 伪造路径：
       *_CFGetProcessPath() = 客 executable
       overwriteExecPath → hook dyld4::_NSGetExecutablePath 改 mainExecutablePath
       overwriteMainNSBundle / overwriteMainCFBundle
  6. Guest hooks：
       NUDGuestHooksInit / SecItemGuestHooksInit / NSFMGuestHooksInit / …
       DyldHooksInit(hideLC, hookDlopen, spoofSDK)
  7. dlopen_nolock(客 executable, RTLD_LAZY|GLOBAL|FIRST)
  8. getAppEntryPoint：扫 LC_MAIN.entryoff → appMain
  9. appMain(argc, argv)  → 客应用内部通常进 UIApplicationMain
```

入口文件：

- [`LiveContainer/main.c`](../../projects/LiveContainer/LiveContainer/main.c)
- [`LiveContainer/LCBootstrap.m`](../../projects/LiveContainer/LiveContainer/LCBootstrap.m)
- [`LiveContainer/Tweaks/Dyld.m`](../../projects/LiveContainer/LiveContainer/Tweaks/Dyld.m)

---

## 4. 客 Mach-O 怎么改（`LCPatchExecSlice`）

实现：[`LCMachOUtils.m`](../../projects/LiveContainer/LiveContainer/LCMachOUtils.m) 的 `LCPatchExecSlice`。

| 改动 | 代码意图 |
|------|----------|
| `header->filetype = MH_DYLIB` | 主程序变成可 `dlopen` 的库 |
| `flags \|= MH_NO_REEXPORTED_DYLIBS`；`flags &= ~MH_PIE` | 按 dylib 约定收旗标 |
| `__PAGEZERO`：`vmaddr = 0x100000000-0x4000`，`vmsize = 0x4000` | 缩小零页，避免「地址空间不够」 |
| 补 `LC_ID_DYLIB`（空间不够则把 `LC_LOAD_DYLINKER` 改成 ID） | dylib 身份 |
| 注入 `LC_LOAD_DYLIB` → `@loader_path/../../Tweaks/TweakLoader.dylib`（或占位 `0x114514`） | 客映像加载时带上 TweakLoader |
| 去重重复 `LC_LOAD_*DYLIB`（标成无效 cmd `0x114515`） | 防错误注入导致 dyld 拒载 |

安装时由 SwiftUI/`LCUtils` 解包 IPA 后调用上述修补；JIT-less 再走 ZSign。

运行时还有一次「伪装回来」：`Dyld.m` 的 `overwriteAppExecutableFileType` 用 `builtin_vm_protect` 把内存里 header 的 `filetype` 改回 `MH_EXECUTE`，骗那些按主镜像类型检查的代码。

---

## 5. JIT vs JIT-less（代码分叉）

| | JIT | JIT-less |
|--|-----|----------|
| 判定 | `checkJITEnabled()`：`CS_DEBUGGED` / 越狱路径；**iOS 26+ 直接否** | 导入 SideStore/证书密码（`LCSharedUtils.certificatePassword`） |
| 签名 | 可不签客二进制 | `ZSigner`（`LCUtils.m` → `ZSign/zsign.mm`）用宿主证签 |
| 加载 | `init_bypassDyldLibValidation()`：hook dyld 内 `fcntl`/`mmap` | 正规签名校验；`DyldHooksInit` 可再 hook `dlopen` |
| fcntl 绕过要点 | `F_ADDFILESIGS_RETURN` 把覆盖范围标满；`F_CHECK_LV` 直接返回 0 | 不适用 |
| mmap 绕过要点 | 映射失败或无 EXEC 时：匿名 RW 页 + 拷贝文件 + `mprotect` 出 EXEC | 不适用 |

参考：[Restoring Dyld Memory Loading (xpn)](https://blog.xpnsec.com/restoring-dyld-memory-loading)

`builtin_vm_protect` 在 `dyld_bypass_validation.m` 里是手写 `svc #0x80` 的 Mach trap 包装（对应 `mach_vm_protect`），用来改 dyld/镜像页权限。

---

## 6. Guest hooks 清单

在 `invokeAppMain` 里、`dlopen` 客应用之前安装：

| 模块 | 改了什么 | 目的 |
|------|----------|------|
| `overwriteExecPath` / `_CFGetProcessPath` | dyld `mainExecutablePath` | `@executable_path` 指向客 App |
| `overwriteMainNSBundle` / `overwriteMainCFBundle` | `NSBundle.mainBundle` / CFBundle | 资源与 Info.plist |
| `NUDGuestHooksInit` | CFPreferences 容器路径 | 偏好写进客数据目录 |
| `SecItemGuestHooksInit` | `SecItem*` / `SecKey*` | 按容器分配 keychain group |
| `NSFMGuestHooksInit` | App Group 路径等 | 文件容器隔离感 |
| `DyldHooksInit` | `dlsym`、`_dyld_image_*`、可选 `dlopen`、SDK 版本 | 藏宿主镜像、伪装主镜像 |
| `IDFVHookInit`（可选） | identifierForVendor | 多容器伪装 |
| `TweakLoader` constructor | `dlopen` Substrate + Tweaks | 插件 |

`entitlements.xml` 里有 **128** 个 `com.kdt.livecontainer.shared[.N]` keychain access groups，用于多账号半隔离（不是完整沙箱）。

---

## 7. 多任务 / LiveProcess（概要）

- **MultitaskSupport**：`AppSceneViewController` 用私有 `FBSceneManager` 建 `FBScene`，窗口可缩放 / PiP；基于 FrontBoardAppLauncher 路线。
- **LiveProcess.appex**：扩展进程里再跑一套客环境（`isLiveProcess`），便于多开与宿主协作；失败时通过 `NSExtensionContext cancelRequestWithError` 回报。

---

## 8. 与「真安装」的差别（限制）

- 客应用 **entitlement 不会**变成宿主 entitlement  
- 权限往往是**全局**的（宿主级）  
- 客容器之间 **不是**完整沙箱隔离  
- App Extension / 远程推送受限（SpringBoard 不知道容器里「安装」了谁）  
- iOS 26+：JIT 路径关掉，必须 JIT-less + 证书  

---

## 9. 和 learnxnu / 安全学习的接口

| LiveContainer 概念 | 可对照的 XNU/安全话题 |
|--------------------|----------------------|
| Mach-O 头/段/load command | 装载、`mmap`/`mprotect`、Day 15+ |
| `dlopen` / dyld4 / `LC_MAIN` | 动态链接、入口点 |
| `csops` + `CS_DEBUGGED` | Day 65 `csops`、调试态与代码签名 |
| `builtin_vm_protect` / `vm_protect` | Mach VM trap、`mprotect` |
| `F_CHECK_LV` / AMFI | 库验证、codesign |
| keychain access groups | 凭证隔离、entitlement |
| `task_info(TASK_DYLD_INFO)` | dyld all_image_infos |

建议：先把启动链路（第 3 节）跟完，再对照白皮书 SEC-H（`csops`、`task_*`、MAC）。

---

## 10. 本地能做什么

本环境是 Linux CI，**不能真机编译/运行 iOS App**。学习方式：

1. 读源码 + 官方 docs  
2. 在 macOS + Xcode 上改 `xcconfigs/Global.xcconfig` 的 Team 再编（需自行拉取 OpenSSL 子模块）  
3. 真机需 SideStore/AltStore 侧载  

```bash
# 仅阅读源码（已在仓库内）
ls projects/LiveContainer/LiveContainer
```

更细的跟读清单与进度见 [LEARNING_BOARD.md](LEARNING_BOARD.md)、[STARTUP_TRACE.md](STARTUP_TRACE.md)。
