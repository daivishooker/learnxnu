# LiveContainer 学习看板

源码（vendored）：[`projects/LiveContainer/`](../../projects/LiveContainer/)  
上游：https://github.com/LiveContainer/LiveContainer  
快照：`e370a92d`（3.8.0）— 见 [`SOURCE.md`](../../projects/LiveContainer/SOURCE.md)  
官方文档：https://livecontainer.github.io/docs/intro  
机制：[MECHANISM.md](MECHANISM.md) · 跟读：[STARTUP_TRACE.md](STARTUP_TRACE.md)

状态：`[ ]` 待学 · `[~]` 进行中 · `[x]` 完成

---

## Backlog

### A. 产品与边界
- [x] 分清：启动器 ≠ 模拟器 ≠ 虚拟机
- [x] 理解免费开发者账号「3 App ID」为何被绕开（客应用不占独立安装槽）
- [x] 读 Limitations：客应用容器互不隔离、扩展/远程推送限制
- [ ] 对照安全白皮书：`csops` / `task_*` / codesign 相关概念（建议结合 Day 65）

### B. 仓库地图
- [x] `LiveContainer/` 主执行体（环境搭建 + 加载客应用）
- [x] `LiveContainerSwiftUI/` 管理 UI
- [x] `TweakLoader/` 注入到客应用的 tweak 加载器
- [x] `ZSign/` JIT-less 签名路径（`LCUtils.m` → `ZSigner`）
- [x] `MultitaskSupport/` 多任务窗口（FBScene 概要）
- [x] `SideStore/` / `LiveProcess/` / Extensions 集成入口（地图级）
- [x] `litehook/` 已 vendored；`OpenSSL/` 仅 stub（体积过大）

### C. 启动链路（核心）
- [x] 读 `LiveContainer/main.c`：preload → `LiveContainerShared` → `LiveContainerMain`
- [x] 读 README「How does it work」五步
- [x] 客 Mach-O：`MH_EXECUTE`→`MH_DYLIB`、`__PAGEZERO`、注入 `TweakLoader`（`LCPatchExecSlice`）
- [x] Hook `_NSGetExecutablePath` / `mainExecutablePath`（`overwriteExecPath`）
- [x] 覆盖 `NSBundle.mainBundle`（`overwriteMainNSBundle` / CF）
- [x] JIT vs JIT-less：`init_bypassDyldLibValidation` vs ZSign；iOS 26+ 强制 JIT-less
- [x] `dlopen` 客可执行文件 → `LC_MAIN` 入口 → 客 `main`
- [ ] 精读 `Dyld.m` 后半：JIT-less `dlopen` hook、seg_count bypass、异常端口

### D. 数据与权能
- [x] 多容器 / App Group / keychain access group（**128** 组半隔离，见 `entitlements.xml`）
- [x] `entitlements.xml` 里有什么、客应用 entitlement 为何不生效
- [ ] ShareExtension / URL「Open In App」路径逐步跟读
- [ ] `SecItem.m`：容器如何抽到具体 access group

### E. 与 XNU 对照（加分）
- [ ] `dlopen` / dyld4 API 与 Day 66–70 线程/凭证话题的边界
- [x] `mprotect` / `vm_protect`（`builtin_vm_protect` svc）对应 Mach VM trap
- [x] codesign / AMFI 直觉：JIT 路径 `F_CHECK_LV` 为何能跳过校验
- [ ] 把 `csops(CS_DEBUGGED)` 写进 Day 65 笔记交叉链接

## Doing

- [~] 对照白皮书 + 精读 Dyld/SecItem/ShareExtension

## Done

- [x] 定位上游并刷新 vendored 快照到 `projects/LiveContainer/`（含 `litehook`）
- [x] 写出模块地图与启动链路说明（MECHANISM + STARTUP_TRACE）
- [x] 从源码核对：`LiveContainerMain` / `invokeAppMain` / `LCPatchExecSlice` / JIT bypass

---

## 建议阅读顺序（约 5 段）

1. 上游 README「How does it work」  
2. `LiveContainer/main.c` + `LCBootstrap.m`（`LiveContainerMain` → `invokeAppMain`）  
3. `LiveContainer/Tweaks/Dyld.m`（dlopen / 伪装 / JIT-less）  
4. `LCMachOUtils.m`（改 Mach-O）  
5. `TweakLoader/` + `ZSign/` + `LCUtils.m`（注入与签名）  

逐步 checklist 见 [STARTUP_TRACE.md](STARTUP_TRACE.md)。
