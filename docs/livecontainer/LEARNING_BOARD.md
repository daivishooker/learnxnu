# LiveContainer 学习看板

源码（vendored）：[`projects/LiveContainer/`](../../projects/LiveContainer/)  
上游：https://github.com/LiveContainer/LiveContainer  
官方文档：https://livecontainer.github.io/docs/intro  
机制：[MECHANISM.md](MECHANISM.md)

状态：`[ ]` 待学 · `[~]` 进行中 · `[x]` 完成

---

## Backlog

### A. 产品与边界
- [ ] 分清：启动器 ≠ 模拟器 ≠ 虚拟机
- [ ] 理解免费开发者账号「3 App ID」为何被绕开（客应用不占独立安装槽）
- [ ] 读 Limitations：客应用容器互不隔离、扩展/远程推送限制
- [ ] 对照安全白皮书：`csops` / `task_*` / codesign 相关概念

### B. 仓库地图
- [ ] `LiveContainer/` 主执行体（环境搭建 + 加载客应用）
- [ ] `LiveContainerSwiftUI/` 管理 UI
- [ ] `TweakLoader/` 注入到客应用的 tweak 加载器
- [ ] `ZSign/` JIT-less 签名路径
- [ ] `MultitaskSupport/` 多任务窗口
- [ ] `SideStore/` / `LiveProcess/` / Extensions 集成入口

### C. 启动链路（核心）
- [ ] 读 `LiveContainer/main.c`：preload → `LiveContainerShared` → `LiveContainerMain`
- [ ] 读 README「How does it work」五步
- [ ] 客 Mach-O：`MH_EXECUTE`→`MH_DYLIB`、`__PAGEZERO`、注入 `TweakLoader`
- [ ] Hook `_NSGetExecutablePath` / `mainExecutablePath`
- [ ] 覆盖 `NSBundle.mainBundle`
- [ ] JIT vs JIT-less：库验证绕过 vs 用同一证书重签（ZSign）
- [ ] `dlopen` 客可执行文件 → 找入口 → `UIApplicationMain`

### D. 数据与权能
- [ ] 多容器 / App Group / keychain access group（128 组半隔离）
- [ ] `entitlements.xml` 里有什么、客应用 entitlement 为何不生效
- [ ] ShareExtension / URL「Open In App」路径

### E. 与 XNU 对照（加分）
- [ ] `dlopen` / dyld4 API 与 Day 66–70 线程/凭证话题的边界
- [ ] `mprotect` / `vm_protect`（改 dyld 配置可写）对应 Mach VM trap
- [ ] codesign / AMFI 直觉：JIT 路径为何能跳过校验

## Doing

- [~] 开板：vendored 源码 + 机制文档

## Done

- [x] 定位上游并浅克隆到 `projects/LiveContainer/`
- [x] 写出模块地图与启动链路说明

---

## 建议阅读顺序（约 5 段）

1. 上游 README「How does it work」  
2. `LiveContainer/main.c` + `LCBootstrap.m` 开头  
3. `LiveContainer/Tweaks/Dyld.m`（dlopen / JIT-less）  
4. `LCMachOUtils.*`（改 Mach-O）  
5. `TweakLoader/` + `ZSign/`（注入与签名）
