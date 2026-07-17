# LiveContainer 机制说明

源码：[`projects/LiveContainer/`](../../projects/LiveContainer/)  
上游：[LiveContainer/LiveContainer](https://github.com/LiveContainer/LiveContainer)（**AGPL-3.0**）

一句话：**不是模拟器**。宿主 App（LiveContainer）把客应用的 Mach-O **改造成可被 `dlopen` 的动态库形态**，伪造「我就是这个 App」的路径/Bundle，再跳进客应用入口跑 `UIApplicationMain`。

---

## 1. 它解决什么问题

| 痛点 | LiveContainer 做法 |
|------|-------------------|
| 免费开发者账号安装 App 数量有限 | 客应用装在容器目录里，**不占独立系统安装槽** |
| 想多开/多数据 | 同一 IPA 多个 data container |
| 签名成本 | 有 JIT：可绕过库验证；无 JIT：用宿主证书 **ZSign** 重签 |

官方强调：第三方闭源改版能看到容器内全部数据（含 keychain）——只信官方构建。

---

## 2. 仓库模块地图

```text
projects/LiveContainer/
├── LiveContainer/           # 主执行体：搭客环境、加载客 App
│   ├── main.c               # 入口：preload → LiveContainerShared → LiveContainerMain
│   ├── LCBootstrap.m        # 引导 / Bundle 等环境修补
│   ├── LCMachOUtils.*       # Mach-O 工具
│   ├── dyld_bypass_validation.*
│   └── Tweaks/              # dyld/dlopen、Guest hooks 等
├── LiveContainerSwiftUI/    # 管理界面（装 IPA、选下次启动的 App…）
├── TweakLoader/             # 注入到每个客应用的 tweak 加载器
├── ZSign/                   # JIT-less 签名
├── MultitaskSupport/        # 应用内多窗口（FrontBoard 路线）
├── LiveProcess/             # 相关进程/SideStore 协作
├── SideStore/               # SideStore 刷新集成
├── ShareExtension/ LaunchAppExtension/
├── litehook/                # 符号重绑/hook 基础设施
└── entitlements.xml         # 宿主权能（含大量 keychain groups）
```

无 App 被选中时：主程序加载 **LiveContainerSwiftUI** 管理界面。  
有 App 被选中：走客环境搭建 → `dlopen` 客可执行文件。

---

## 3. 启动链路（核心）

```text
1) 安装 IPA（UI）
   → 解包到容器目录
   → 改客 Mach-O（见下）
   → JIT-less 时 ZSign 签名

2) 下次冷启动宿主
   main.c
     → 可选 preloadLibraries.txt 里 dlopen 一批库
     → dlopen LiveContainerShared.framework
     → LiveContainerMain(...)

3) 搭客环境
   → 改 @executable_path / dyld mainExecutablePath
   → 覆盖 NSBundle.mainBundle → 客 Bundle
   → （JIT）绕过 library validation
   → （可选）TweakLoader 加载插件

4) dlopen(客可执行文件)
   → 找入口点
   → 跳入 → UIApplicationMain → 像普通 UIKit App 一样跑
```

入口线索：

- [`LiveContainer/main.c`](../../projects/LiveContainer/LiveContainer/main.c)  
- [`LiveContainer/LCBootstrap.m`](../../projects/LiveContainer/LiveContainer/LCBootstrap.m)  
- [`LiveContainer/Tweaks/Dyld.m`](../../projects/LiveContainer/LiveContainer/Tweaks/Dyld.m)

---

## 4. 客 Mach-O 怎么改（官方 README 摘要）

| 改动 | 目的 |
|------|------|
| `__PAGEZERO`：`vmaddr/vmsize` 调成小页零区 | 让映像能以 dylib 方式被映射/加载 |
| `MH_EXECUTE` → `MH_DYLIB` | 从「主程序」变成「可被 dlopen 的库」 |
| 注入 load command → `TweakLoader.dylib` | 客进程里先加载 tweak 注入器 |

然后还要骗运行时：

| 修补 | 目的 |
|------|------|
| Hook `dyld4::APIs::_NSGetExecutablePath` / 改 `mainExecutablePath` | `@executable_path` 指向客应用 |
| 覆盖 `NSBundle.mainBundle` | 资源/Info.plist 走客 Bundle |
| JIT 路径绕过 library validation | 未按常规签名的代码也能被 dyld 加载 |
| JIT-less：ZSign 用宿主证签名 | 无 JIT 时走正规签名校验 |

参考文章：[Restoring Dyld Memory Loading (xpn)](https://blog.xpnsec.com/restoring-dyld-memory-loading)

---

## 5. 与「真安装」的差别（限制）

- 客应用 **entitlement 不会**变成宿主 entitlement  
- 权限往往是**全局**的（宿主级）  
- 客容器之间 **不是**完整沙箱隔离（一个客应用可能读到另一个的数据）  
- App Extension / 远程推送等能力受限（SpringBoard 不知道容器里「安装」了谁）  
- 多开：多个 LiveContainer 实例，或 MultitaskSupport 窗口

---

## 6. 和 learnxnu / 安全学习的接口

| LiveContainer 概念 | 可对照的 XNU/安全话题 |
|--------------------|----------------------|
| Mach-O 头/段/load command | 装载、`mmap`/`mprotect`、Day 15+ |
| `dlopen` / dyld4 | 动态链接、库验证 |
| JIT vs 签名 | `csops`、AMFI、代码签名 |
| keychain access groups | 凭证隔离、entitlement |
| task/port（调试 JIT） | Mach trap：`task_for_pid` 族（受限） |

建议：先把本看板 C 区「启动链路」走通，再回头对照安全白皮书 SEC-H（`csops`、`task_*`、MAC）。

---

## 7. 本地能做什么

本环境是 Linux CI，**不能真机编译/运行 iOS App**。学习方式：

1. 读源码 + 官方 docs  
2. 在 macOS + Xcode 上按 README `xcconfigs/Global.xcconfig` 改 Team 再编  
3. 真机需 SideStore/AltStore 侧载（见官方安装指南）

```bash
# 仅阅读源码（已在仓库内）
ls projects/LiveContainer/LiveContainer
```
