# XNU 学习计划（从系统调用切入）

目标：先把 **用户态 → 内核 → 返回用户态** 这条系统调用路径吃透，再向外扩展到 Mach、进程、内存、VFS、驱动等子系统。

学习材料以 Apple 开源的 [xnu](https://github.com/apple-oss-distributions/xnu) 源码为主；版本尽量固定一个（如 `xnu-10002` / 对应 macOS 版本），读代码时始终对着同一棵树。

---

## 总览路线

```
预备知识
   ↓
阶段 0：XNU 地图与双内核心智模型
   ↓
阶段 1：系统调用主线（本计划重点，先完成）
   ↓
阶段 2：进程 / 线程 / 凭证
   ↓
阶段 3：虚拟内存 (VM)
   ↓
阶段 4：VFS / 文件描述符
   ↓
阶段 5：IPC（Mach ports / messages）
   ↓
阶段 6：驱动 / IOKit / 调试与实验
```

**原则：** 每个阶段只跟一条调用链；能画出路图、能指到源码文件与函数名，再进入下一阶段。

---

## 预备知识（建议先过一遍）

| 主题 | 需要到什么程度 |
|------|----------------|
| C / 汇编（arm64 优先） | 能读函数序言、`svc`/`syscall`、寄存器约定 |
| 操作系统概念 | 用户态/内核态、陷阱、进程、页表、FD |
| Unix 编程 | `open`/`read`/`fork`/`exec`/`mmap` 的用户态语义 |
| Mach 概念（粗略） | task / thread / port / message 是什么 |

不必先啃完整本 OS 书；缺什么补什么，以跟得上 syscall 路径为准。

---

## 阶段 0：建立 XNU 地图（1–2 个学习单元）

**要搞清楚：**

1. XNU = Mach 微内核核心 + BSD 子系统 + IOKit 等
2. 用户可见的「系统调用」其实有两条入口：
   - **BSD Unix syscalls**（`open`、`read`、`fork`…）
   - **Mach traps**（`mach_msg`、`task_self`…）
3. 源码顶层目录大致分工：
   - `bsd/` — Unix 语义、syscall 表、VFS、进程等
   - `osfmk/` — Mach 内核、调度、VM、IPC
   - `iokit/` — 驱动框架
   - `libsyscall/` / `libsystem_*`（在 libplatform / Libc 相关树）— 用户态包装

**产出：**

- 自己写一页笔记：画「用户程序 → libsystem → 内核入口 → BSD/Mach 分发」框图
- 能回答：为什么 `getpid()` 和 `mach_task_self()` 走的不是同一张表

---

## 阶段 1：系统调用主线（先学这个）

这是整个计划的第一深挖点。按下面子阶段顺序推进。

### 1.1 用户态入口

**学什么：**

- libc / libsystem 如何把 `open()` 变成一次陷阱指令
- arm64：`svc`；x86_64：`syscall`
- 参数怎么放进寄存器、返回值与 `errno` 如何约定
- `_kernelrpc_*` / Mach trap 用户态包装长什么样

**建议动手：**

1. 写一个最小 C 程序调用 `getpid()` / `open()`
2. 用 `otool -tv` 或 lldb 看实际发出的指令与寄存器
3. 对比同一程序在 Linux 上的差异（建立对照，不要求精通）

**关键线索（名称会随版本微调）：**

- 用户态：`libsyscall`、`libc` 中的 syscall stub
- 可对照：`man 2 syscall`、Darwin 的 `syscalls.master` 编号

### 1.2 内核陷阱入口与分发

**学什么：**

- 异常/陷阱向量如何进入内核
- 如何区分 BSD syscall vs Mach trap（trap number / 调用约定）
- 线程状态保存、内核栈切换的大致流程

**建议读码顺序：**

1. 架构入口（`osfmk` 下 arm64 / x86_64 的 exception / syscall 入口汇编）
2. 进入 C 层的 unix syscall / mach syscall 分发函数
3. 找到「根据编号查表 → 调处理函数」的那几行

**产出：**

- 笔记里列出：入口符号名 → 分发函数 → 查表结构 → 具体 handler 的调用链（至少一条完整路径）

### 1.3 BSD 系统调用表

**学什么：**

- `syscalls.master` 如何生成 `sysent[]`
- 一个 syscall 描述符包含什么（参数个数、参数类型、处理函数、返回类型）
- 编号、名字、兼容性（旧 ABI / 新 ABI）问题

**建议读码：**

1. `bsd/kern/syscalls.master`
2. 由其生成的 `sysent` / 头文件
3. 挑 3 个 handler 精读实现：
   - 极简：`getpid` / `getuid`
   - 有拷贝入参：`open` / `read`
   - 会创建对象：`fork` 或 `mmap`（可稍浅）

**每个 handler 强制问自己：**

1. 参数从哪来？如何 `copyin`？
2. 当前线程/进程上下文对象是什么（`proc` / `uthread` / `task`）？
3. 失败时如何设 `errno`、如何返回？
4. 有没有锁、有没有可能 sleep？

### 1.4 Mach traps（与 BSD 对照）

**学什么：**

- Mach trap 表与 BSD `sysent` 的对称结构
- 为什么很多「系统服务」其实是 Mach message，而不是 BSD syscall
- `mach_msg` 在系统调用层扮演的角色（先概念，细节放到阶段 5）

**建议动手：**

- 从用户态调用一个简单 Mach trap（如 `mach_task_self` / `thread_self` 一类）
- 在源码里找到对应 trap 表项与实现
- 写对照表：同一个用户意图，BSD 路径 vs Mach 路径各走哪里

### 1.5 参数拷贝、凭证与安全边界

**学什么：**

- `copyin` / `copyout` / `copyinstr`
- 用户指针不可信的含义
- `ucred` / sandbox / entitlement 在 syscall 路径上的挂钩点（先识别调用点，不要求精通策略引擎）

**产出：**

- 选 `open` 或 `ioctl`，标出所有跨安全边界的拷贝与检查点

### 1.6 观测与调试（把路径「看见」）

**推荐工具（macOS 上）：**

| 工具 | 用途 |
|------|------|
| `dtruss` / DTrace | 跟踪进程的 syscall |
| `fs_usage` | 文件相关系统调用 |
| lldb + 内核调试（进阶） | 断在入口/handler |
| `sc_usage` | 系统调用计数 |

**练习：**

1. 对自写程序跑 `dtruss`，对照源码编号与名字
2. 故意制造失败（坏路径、无权限），观察返回值与 `errno`
3. 记录一次完整的 `open → read → close` 内核侧函数序列

### 阶段 1 验收标准（全部满足再进入阶段 2）

- [ ] 能手绘：用户态 stub → 陷阱 → 分发 → `sysent` → handler → 返回
- [ ] 能指出至少 5 个关键源文件/符号，并说明各自职责
- [ ] 精读过 ≥3 个 BSD syscall handler
- [ ] 能说明 BSD syscall 与 Mach trap 的差异
- [ ] 能用观测工具验证自己的理解

---

## 阶段 2：进程 / 线程 / 凭证（syscall 之后的第一扩展）

从 syscall 里已经碰到的 `proc`、`uthread`、`task`、`thread` 出发：

1. `proc` vs Mach `task` 的对应关系
2. `fork` / `execve` / `exit` / `wait` 的实现骨架
3. Unix 线程与 Mach thread、`pthread` 如何落到内核
4. 凭证：`uid`/`gid`、saved ids、如何在 syscall 中检查

**入口 syscall 建议精读：** `fork`、`execve`、`exit`、`kill`

---

## 阶段 3：虚拟内存

1. Mach VM：`vm_map`、`vm_object`、region
2. BSD 侧：`mmap`、`munmap`、`mprotect`
3. 缺页异常路径与 syscall 路径的交汇
4. copy-on-write 与 `fork` 的关系（回扣阶段 2）

**入口 syscall：** `mmap`、`madvise`、`mincore`

---

## 阶段 4：VFS 与文件描述符

1. `fileproc` / `fileglob` / `vnode`
2. namei 路径查找
3. UBC（Unified Buffer Cache）与读写路径
4. 常见 FS 挂钩点（APFS 可先当黑盒）

**入口 syscall：** `open`、`read`、`write`、`stat`、`dup2`

---

## 阶段 5：Mach IPC（系统调用之上的「真正 IPC」）

1. port / port right / port name
2. `mach_msg` 发送与接收
3. 内核如何把消息递到另一 task
4. 与 MIG、用户态 RPC 的关系

到这里会回头理解：很多「看起来像系统调用的服务」其实是消息。

---

## 阶段 6：驱动、安全与综合实验

1. IOKit 对象模型与用户态 `IOConnectCall*`（仍可从「像 syscall 的接口」切入）
2. KEXT / DriverKit 边界（按你目标取舍）
3. 综合小实验（选 1–2 个）：
   - 给某个 syscall 路径写详细注释补丁笔记（只读分析也行）
   - 实现用户态「伪 strace」：统计并分类本进程 syscall
   - 跟踪一个真实程序（如 `ls` / `cat`）的完整 syscall 图谱

---

## 推荐阅读顺序（资料）

1. **源码**：Apple OSS `xnu`（固定版本）+ 对应 `Libc` / `libsyscall`（若可获取）
2. **经典概念**：《Mac OS X Internals》/《OS X and iOS Kernel Programming》中 syscall / Mach 章节（作地图，细节以源码为准）
3. **WWDC / Apple 文档**：Virtual Memory、System Trace 等相关会话（辅助观测）
4. **对照**：Linux `syscall` 路径（帮助区分 Darwin 特殊性，避免概念串台）

---

## 建议的仓库学习用法（本仓库）

后续可按阶段往本仓库追加笔记，例如：

```
docs/
  LEARNING_PLAN.md          # 本计划
  00-map/                   # XNU 地图
  01-syscall/               # 系统调用笔记与调用链
  02-process/
  03-vm/
  ...
notes/
  syscall-open.md           # 单条路径深挖
```

**阶段 1 建议立刻写的第一篇笔记：**

`notes/syscall-getpid.md` — 从用户态到 `sysent` 再到返回，逐函数记录。

---

## 每周节奏建议（强度自定）

| 单元 | 内容 |
|------|------|
| 单元 A | 阶段 0 + 1.1 用户态 stub |
| 单元 B | 1.2 内核入口与分发 |
| 单元 C | 1.3 `syscalls.master` + 精读 `getpid`/`open` |
| 单元 D | 1.4 Mach traps 对照 |
| 单元 E | 1.5–1.6 安全边界 + 观测验收 |

完成单元 E 的验收清单后，再开阶段 2。

---

## 开始行动（下一步）

1. Clone 并固定一版 `xnu` 源码
2. 完成阶段 0 的一页框图
3. 精读 `getpid` 全路径，写 `notes/syscall-getpid.md`
4. 用 `dtruss` 验证后，再攻 `open`/`read`
