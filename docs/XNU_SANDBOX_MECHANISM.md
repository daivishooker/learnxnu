# XNU 沙盒机制完整分析

> 基准源码：本仓库 `xnu/` = **xnu-12377.121.6**  
> 范围：内核 **MAC Framework（开源）** + **Sandbox.kext / 应用层接口（闭源，据公开资料与 XNU 挂接点还原）**  
> 相关：[`SYSCALL_SECURITY_WHITEPAPER.md`](SYSCALL_SECURITY_WHITEPAPER.md)（`__mac_*` / `csops`）· Day 65 `csops` / Day 61 `chroot`

---

## 0. 先把边界说清楚

| 组件 | 是否在开源 XNU 里 | 角色 |
|------|-------------------|------|
| **MAC Framework**（TrustedBSD MACF） | **是**（`xnu/security/`） | 钩子总线：在 vnode/socket/进程等路径上调用策略模块 |
| **Sandbox.kext**（Seatbelt） | **否**（闭源 kext） | 真正的沙盒策略引擎：装 profile、解释规则、在 MAC 钩子里 allow/deny |
| **AppleMatch.kext** | 否 | 给 Sandbox 做正则匹配（路径等） |
| **libsandbox / libsystem_sandbox** | 否（用户态） | 编译 SBPL → 字节码；发起装载/查询 |
| **App Sandbox + Container** | 用户态 + 守护进程 | entitlement → secinit / containermanagerd → 容器目录 + 自动装 profile |
| **AMFI / Quarantine** | 部分钩子在 XNU，策略多在闭源 | 代码签名与隔离相关，和沙盒并列的 MAC 策略 |

因此：

> **XNU 开源部分实现的是「可挂载的强制访问控制框架」；**  
> **应用隔离的「规则长什么样、如何编译、如何存到进程上」主要在 `Sandbox.kext` + 用户态库里。**  
> 本文以开源挂接点为骨架，把闭源沙盒模块如何接上写完整。

---

## 1. 总体架构

```text
┌─────────────────────────────────────────────────────────────┐
│ 应用层                                                      │
│  • App Sandbox entitlement (com.apple.security.app-sandbox) │
│  • sandbox_init / sandbox_apply / sandbox_compile_*         │
│  • secinit / libsecinit → __sandbox_ms                      │
│  • ContainerManager / AppContainer（容器路径）              │
└────────────────────────────┬────────────────────────────────┘
                             │ BSD syscall
                             │ 尤其 __mac_syscall("Sandbox", call, arg)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ XNU MAC Framework  (security/mac_*.c)                       │
│  • mac_policy_register / mac_policy_list                    │
│  • MAC_CHECK(vnode_check_open, …) 等宏                    │
│  • __mac_syscall → mpo_policy_syscall                       │
│  • label slot（cred / vnode / socket …）                    │
└────────────────────────────┬────────────────────────────────┘
                             │ 函数指针回调
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ Sandbox.kext  (com.apple.security.sandbox / Seatbelt)       │
│  • 注册 mac_policy_ops（大量 mpo_*_check_*）                │
│  • 保存每进程 profile 字节码                                │
│  • 在钩子里求值 → 0 允许 / EPERM 等拒绝                     │
│  • 常配合 AppleMatch.kext 做路径正则                        │
└─────────────────────────────────────────────────────────────┘
```

**DAC 与 MAC 的关系（直觉）：**

1. 传统 Unix 权限（uid/gid/mode）先或并行做一遍（Kauth / VFS）。  
2. 若进程受 MAC 约束，再走 `mac_*_check_*`；**任一策略拒绝则失败**（`MAC_CHECK` 合成错误）。  
3. 沙盒是「默认少权限 + 白名单放行」，比「有没有 rwx 位」更细（网络、Mach、IPC、sysctl…）。

---

## 2. 内核侧：MAC Framework 如何实现「可挂策略」

### 2.1 源码地图（本树）

| 路径 | 内容 |
|------|------|
| `xnu/security/mac_policy.h` | 策略操作向量 `mac_policy_ops`、`mac_policy_register`、OPS 版本（当前 **93**） |
| `xnu/security/mac_base.c` | 策略列表、注册/注销、`__mac_syscall`、若干 `__mac_get/set_*` |
| `xnu/security/mac_internal.h` | **`MAC_CHECK` / `MAC_GRANT`** 宏 |
| `xnu/security/mac_vfs.c` | vnode 检查：`mac_vnode_check_open/access/exec/...` |
| `xnu/security/mac_process.c` | 进程/凭证标签与 `mac_proc_check_*` |
| `xnu/security/mac_socket.c` / `mac_file.c` / `mac_mach.c` / … | 套接字、文件、Mach 等子系统钩子封装 |
| `xnu/security/mac.h` | 用户态可见的 MAC 常量与 `__mac_*` 声明 |
| `xnu/bsd/vfs/vfs_syscalls.c` 等 | 在 open/chdir/… 路径上**调用** `mac_vnode_check_*` |

### 2.2 策略注册

闭源 `Sandbox.kext` 在加载时调用：

```c
int mac_policy_register(struct mac_policy_conf *mpc,
                        mac_policy_handle_t *handlep, void *xd);
```

关键结构（`mac_policy.h`）：

```c
struct mac_policy_conf {
    const char *mpc_name;           // 如 "Sandbox"
    const char *mpc_fullname;
    char const * const *mpc_labelnames;
    unsigned int mpc_labelname_count;
    const struct mac_policy_ops *mpc_ops;  // 钩子表
    int mpc_loadtime_flags;
    int *mpc_field_off;             // label 槽位
    // ...
};
```

`mac_policy_ops` 是一张巨大的函数指针表（版本用 `MAC_POLICY_OPS_VERSION` 对齐），包括例如：

- `mpo_vnode_check_open` / `mpo_vnode_check_unlink` / …  
- `mpo_socket_check_bind` / `mpo_socket_check_connect` / …  
- `mpo_proc_check_signal` / `mpo_proc_check_debug` / …  
- `mpo_cred_label_*`（进程标签生命周期）  
- **`mpo_policy_syscall`**（策略私有 syscall：装 profile、查询等）

XNU 自己**不实现**这些 `mpo_*` 的沙盒语义；它只负责迭代已注册策略并调用。

### 2.3 强制检查宏 `MAC_CHECK`

定义于 `mac_internal.h`（简化）：

```c
#define MAC_CHECK(check, args...) do { \
    error = 0; \
    MAC_POLICY_ITERATE({ \
        if (mpc->mpc_ops->mpo_ ## check != NULL) { \
            int __step_err = mpc->mpc_ops->mpo_ ## check (args); \
            error = mac_error_select(__step_err, error); \
        } \
    }); \
} while (0)
```

语义：

- 遍历所有已加载策略；  
- 某策略未实现该钩子 → 跳过；  
- 实现了则调用；**错误按 `mac_error_select` 合成**（通常「拒绝优先」）；  
- 调用方看到非 0 → 系统调用失败（常见 `EPERM`）。

对比 `MAC_GRANT`：默认拒绝，**任一策略返回 0 则放行**（用于少数「授出」场景）。

### 2.4 子系统如何接到 MAC（以文件 open 为例）

典型路径：

```text
用户 openat(...)
  → bsd/vfs/vfs_syscalls.c（namei 解析路径）
  → mac_vnode_check_open(ctx, dvp, cnp, vp, acc_mode)   // mac_vfs.c
       → MAC_CHECK(vnode_check_open, cred, ...)
            → Sandbox.kext: mpo_vnode_check_open(...)
                 → 用当前进程 profile 字节码求值
                 → allow / deny
  → 若 error==0 再真正打开 vnode
```

`mac_vnode_check_access` 一类封装还会先看全局开关（如 `mac_vnode_enforce`）以及是否对 `kernproc` 豁免（`mac_proc_check_enforce`）。

同类挂接点遍布：

| 操作类 | MAC 封装示例 | 常见触发点 |
|--------|--------------|------------|
| 文件/目录 | `mac_vnode_check_open/create/unlink/chdir/chroot/exec/...` | `vfs_syscalls.c`, `vfs_vnops.c` |
| FD | `mac_file_check_lock/ioctl/...` | flock、fcntl 等 |
| 套接字 | `mac_socket_check_*` | `mac_socket.c` ← 网络栈 |
| 进程 | `mac_proc_check_signal/debug/sched/proc_info/...` | kill、ptrace、proc_info |
| Mach | `mac_mach_*` | task/port 相关（`mac_mach.c`） |
| 系统 | `mac_system_*` / sysctl 检查 | 系统配置类操作 |

**这就是「内核沙盒模块」对外的真实强制面：不是单独一个 `sandbox()` syscall 包一切，而是几百个 MAC 钩子。**

### 2.5 Label（标签）与生命周期

MAC 给对象挂 `struct label`（槽位由策略注册时经 `mpc_field_off` 申请，用 `mac_label_get` / `mac_label_set` 读写）：

| 对象 | 典型 API | Sandbox 用途（闭源侧） |
|------|----------|------------------------|
| 凭证 / 进程 | `mac_cred_label_*` | **主状态**：是否已沙盒、profile 句柄/字节码引用 |
| vnode | `mac_vnode_label` / `mac_label_vnodes` | 文件标签（若策略使用）；多数路径靠路径匹配而非 vnode 标签 |
| socket / pipe / POSIX shm·sem / SysV IPC | 各 `mac_*_label_*` | 与网络/IPC 规则求值相关的对象侧状态 |
| mount | `mnt_mntlabel` | 挂载点相关检查 |

**exec 时标签更新（开源路径，`mac_vfs.c`）：**

```text
execve / posix_spawn
  → mac_cred_label_update_execve(ctx, new_cred, vp, …, macextensions, …)
       → 标记 CRF_MAC_ENFORCE
       → 遍历 mac_policy_list
       → 对每个策略：exec_spawnattr_getmacpolicyinfo(macextensions, mpc_name, …)
       → 调用 mpo_cred_label_update_execve(...)
            → Sandbox：按新映像 / spawn MAC 扩展信息决定
               继承旧 profile、换新 profile、或保持无沙盒
```

要点：

- `macextensions` 可携带**按策略名**的 spawn 属性（`posix_spawn` 扩展），供 Sandbox 在 exec 边界装载/切换规则。  
- fork 路径走 `mpo_cred_label_associate_fork`：子进程通常**继承**父进程沙盒状态。  
- 一旦装上 profile，用户态一般**不能卸掉**；换规则靠重新 exec（或平台在 exec 边界重写）。

### 2.6 策略专用入口：`__mac_syscall`

实现：`security/mac_base.c` → `__mac_syscall`（BSD #381）。

```text
__mac_syscall(policy_name, call, arg)
  1. copyinstr(policy_name)          // 如 "Sandbox"
  2. mac_proc_check_mac_syscall(...) // 其它策略可限制谁能调
  3. 在 mac_policy_list 里找 mpc_name 匹配的策略
  4. 调用 mpc_ops->mpo_policy_syscall(p, call, arg)
```

用户态声明（`security/mac.h`）：

```c
int __mac_syscall(const char *_policyname, int _call, void *_arg);
```

**Sandbox 用户态装载 profile、查询状态等，最终几乎都汇到这里**（经 `__sandbox_ms` 一类包装，policy 名指向 Sandbox）。

同族还有 `__mac_get_proc` / `__mac_set_file` / `__mac_execve` 等，用于标签读写与带标签 exec；沙盒日常路径更偏 `mpo_policy_syscall`。

### 2.7 内核给 Sandbox 的「回调挂接」

`bsd/sys/proc_private.h`：

```c
struct sandbox_info_callbacks {
    int version;
    const sandbox_profile_cbfunc_t sandbox_profile_cbfunc;
};
int proc_set_sandbox_info_callbacks(sandbox_info_cbs_t callback);
```

`kern_proc.c` 里把 `sandbox_profile_cbfunc` 存成 `mac_proc_get_sandbox_profile`，供内核其它路径（如诊断/导出 profile）回调到 **Sandbox.kext 注册的函数**。

另有 **syscall filter mask**（`proc_set_syscall_filter_*`）：沙盒/平台策略可按进程屏蔽部分 BSD syscall 号，与 MAC 钩子互补（粗粒度入口过滤）。

---

## 3. 闭源侧：Sandbox.kext 在做什么（机制还原）

下列内容**不在本树源码中**，综合 Apple 文档、公开研究（Blazakis Seatbelt、Mac Internals、逆向文章）与上文 XNU 挂接点：

### 3.1 身份

- Bundle / 策略名常作 **`Sandbox`** / Seatbelt  
- 依赖 **AppleMatch.kext** 做字符串/路径匹配  

### 3.2 Profile 生命周期

1. **编写**：SBPL（Sandbox Profile Language，Scheme 方言），文件常见 `.sb`  
2. **编译**：用户态 `libsandbox` 把文本/模板编成**内核字节码**（不是把 Scheme 解释器放进内核）  
3. **装载**：经 `__mac_syscall` → `mpo_policy_syscall` 把字节码绑到**当前进程**（或 exec 时由平台装好）  
4. **求值**：之后每个相关 MAC 钩子触发时，用当前操作参数跑字节码  
5. **不可撤销（典型）**：进程一旦进入沙盒，用户态无法「卸掉」；要换规则通常需重新 exec  

### 3.3 规则形态（概念）与 SBPL → MAC 钩子映射

SBPL 里是操作类 + 过滤器，例如：

- `(allow file-read* (subpath "/usr/lib"))`  
- `(deny network-outbound)`  
- `(allow mach-lookup (global-name "com.apple.foo"))`  

编译后的字节码在钩子里求值时，大致对应关系（概念映射，非一一公开 ABI）：

| SBPL 操作类（示例） | 主要落到的 MAC 钩子族 |
|---------------------|----------------------|
| `file-read*` / `file-write*` / `file-map-executable` | `mpo_vnode_check_open/read/write/mmap/exec/...` |
| `file-ioctl` / 元数据 | `mpo_vnode_check_*`、`mpo_file_check_ioctl` |
| `network-inbound` / `network-outbound` / `network-*` | `mpo_socket_check_bind/connect/send/...` |
| `mach-lookup` / `mach-register` / `mach-priv-*` | `mpo_mach_*` / 相关 proc·task 检查 |
| `process-exec` / `process-fork` / `signal` | `mpo_vnode_check_exec`、`mpo_proc_check_*` |
| `sysctl-read` / `sysctl-write` | sysctl 路径上的 MAC 检查 |
| `ipc-posix-*` / `ipc-sysv-*` | POSIX/SysV shm·sem·msg 的 `mpo_*_check_*` |
| `job-creation` / `system-*` | 系统/作业类 `mpo_system_*` 等 |

过滤器（`subpath`、`literal`、`regex`、`global-name`…）多在 **AppleMatch + Sandbox** 内解释；XNU 只把 vnode/路径/端口名等参数传进钩子。

App Sandbox 不会让你手写整份 profile，而是：

```text
com.apple.security.app-sandbox = true
+ com.apple.security.network.client
+ com.apple.security.files.user-selected.read-write
+ …
    ↓
平台生成：基础容器 profile + 各 entitlement 对应的规则片段
```

### 3.4 与其它 MAC 策略并存

同一进程上可同时有：

| 策略 | 作用 |
|------|------|
| Sandbox | 应用能力边界 |
| AMFI | 代码签名 / 库验证 /  entitlement 真实性 |
| Quarantine | 隔离属性（下载标记等） |
| （其它） | 平台内部策略 |

`MAC_CHECK` 会问**所有**已注册且实现了该钩子的策略。

---

## 4. 应用层：用哪些接口完成「隔离」

分三条主路径：**显式 Seatbelt**、**App Sandbox（entitlement）**、**容器文件系统**。

### 4.1 显式 API（libsandbox / libsystem_sandbox）

公开/半公开能力（名称以 SDK 为准；内部测试代码见 `xnu/tests/vfs/sandbox_*.c`）：

| 接口（概念） | 作用 |
|--------------|------|
| `sandbox_init` / `sandbox_init_with_parameters` | （较旧）用命名 profile 或字符串进入沙盒 |
| `sandbox_create_params` / `sandbox_set_param` | 编译参数（路径变量等） |
| `sandbox_compile_string` / `sandbox_compile_file` | SBPL → `sandbox_profile_t` |
| `sandbox_apply` / `sandbox_apply_container` | 把已编译 profile 应用到**当前进程** |
| `sandbox_free_profile` / `sandbox_free_params` | 释放 |
| `sandbox-exec`（工具） | 在沙盒中启动进程（现代系统受限更多） |

本树测试示例（`xnu/tests/vfs/sandbox_fstat.c` 等）：

```c
params  = sandbox_create_params();
profile = sandbox_compile_string(profile_string, params, &sberror);
sandbox_apply(profile);   // 之后 open/stat 等受规则约束
```

底层链路：

```text
sandbox_apply / sandbox_init
  → libsandbox 准备字节码
  → __sandbox_ms(...) 或等价包装
  → __mac_syscall("Sandbox", SANDBOX_CALL_*, arg)
  → Sandbox.kext: mpo_policy_syscall
  → 进程标记为已沙盒 + 保存 profile
```

**注意：** 调用 `sandbox_init` **之前**的代码不受该 profile 约束；之后子进程通常继承（除非 exec 换策略）。

### 4.2 App Sandbox（macOS 商店/现代桌面应用主流）

应用层「接口」主要是 **entitlement + 系统运行时**，而不是自己 `sandbox_apply`：

| 层次 | 机制 |
|------|------|
| 签名 entitlement | `com.apple.security.app-sandbox` = true（必须） |
| 能力 entitlement | `network.client`、`files.user-selected.read-write`、`application-groups` 等 |
| 启动时 | `libsecinit` / secinit 路径检测 entitlement → 向 Sandbox.kext 装生成好的 profile（仍经 MAC/`__sandbox_ms`） |
| 容器目录 | `~/Library/Containers/<bundle-id>/`（Data、临时目录等）由 ContainerManager 管理 |
| 用户选文件 | Powerbox / security-scoped bookmarks：临时扩展文件权限，不整盘放开 |

隔离效果：

- 默认**不能**任意读用户家目录；  
- 网络/硬件/IPC 需对应 entitlement；  
- 数据落在容器内，与其它 App 隔离（配合 MAC + 目录 ACL/权限）。

iOS 上「每个 App 一个容器」是平台默认模型，同样落到内核沙盒 + 容器路径，但用户不可像 macOS 那样关 App Sandbox。

### 4.3 用户态可见的「内核沙盒模块」接口汇总

从**应用/库作者**视角，能碰到的与内核沙盒相关的入口：

| # | 接口 | 所在层 | 说明 |
|---|------|--------|------|
| 1 | `__mac_syscall` | BSD syscall | **策略私有调用总线**；Sandbox 装载/控制走这里 |
| 2 | `__mac_get_*` / `__mac_set_*` / `__mac_execve` | BSD syscall | MAC 标签读写；沙盒旁路/诊断偶用 |
| 3 | `sandbox_*`（libsandbox） | 用户库 | 编译+应用 profile 的稳定包装 |
| 4 | `__sandbox_ms` | 用户库内部 | 对 `__mac_syscall("Sandbox", …)` 的薄封装 |
| 5 | Entitlements（代码签名 blob） | 签名/AMFI | 决定是否自动沙盒及规则片段 |
| 6 | Container / App Group 路径 | 用户态服务 | 文件系统层面的家目录隔离 |
| 7 | security-scoped bookmark / Powerbox | 用户态框架 | 运行时受控放开文件访问 |
| 8 | （内核）MAC 钩子 | 无直接 API | **强制点**：open/connect/mach_lookup… 时自动触发 |

应用**不会**直接调用 `mpo_vnode_check_open`；那是 kext 提供给 MAC 框架的回调。

### 4.4 容器与「文件系统隔离」vs「沙盒规则」

两者常一起出现，但不是同一层：

| | 容器目录 | Sandbox profile |
|--|----------|-----------------|
| 管什么 | 默认写入位置、Library 重定位 | 允许/拒绝哪些系统调用语义操作 |
| 实现 | containermanagerd、路径约定、chmod/ACL | Sandbox.kext + MAC 钩子 |
| 单独够不够 | 不够（仍可能 open 到容器外） | 需要；容器只是常用允许的「家」 |

### 4.5 iOS / iPadOS 与 macOS 的差异（应用层视角）

| | macOS App Sandbox | iOS 容器模型 |
|--|-------------------|--------------|
| 是否可选 | 可选（商店 App 强制；开发可关） | **平台默认强制** |
| 开发者入口 | entitlement + Xcode 能力面板 | 几乎无「关沙盒」；靠 entitlement 开能力 |
| 显式 `sandbox_apply` | 工具/daemon/测试可用 | 一般不对第三方开放 |
| 用户选文件 | Powerbox / NSOpenPanel 常见 | Files / document picker / security-scoped URL |
| 容器根 | `~/Library/Containers/<id>/` | 应用 sandbox 目录（Documents/Library/tmp） |

两边**内核强制面相同**：仍是 MACF + Sandbox.kext；差别在**谁、何时、用哪份 profile 装载**。

---

## 5. 一次完整时序：从 App 启动到 open 被拒

以 macOS App Sandbox 应用为例：

```text
1. 用户启动 App
2. dyld/libSystem 初始化 → libsecinit 发现 app-sandbox entitlement
3. 与平台服务协商容器路径与 profile 参数
4. __sandbox_ms / __mac_syscall("Sandbox", APPLY, bytecode)
5. Sandbox.kext 将 profile 绑到当前 proc 的 MAC label
6. 应用调用 open("/Users/me/Documents/a.txt")
7. VFS namei → mac_vnode_check_open
8. MAC_CHECK → Sandbox mpo_vnode_check_open
9. 字节码：无 user-selected / 无 home-relative 允许 → deny
10. 返回 EPERM；控制台可见 sandbox violation 日志（用户态可观察）
```

若用户通过 NSOpenPanel 选了该文件：

```text
Powerbox 授予 security-scoped 权利
  → 内核/沙盒侧增加对该路径（或书签）的临时允许
  → 再次 open 可通过 vnode 检查
```

---

## 6. 与 XNU 其它安全机制的拼图

| 机制 | 和沙盒的分工 |
|------|----------------|
| **DAC**（uid/mode） | 经典「谁拥有文件」；沙盒是「就算 uid 允许，策略仍可拒绝」 |
| **chroot**（Day 61） | 只改路径根；**不是**完整沙盒；可被配合使用但远弱于 Seatbelt |
| **csops / AMFI**（Day 65） | 验证代码与 entitlement **真伪**；沙盒用 entitlement **内容**生成规则 |
| **MAC 多策略** | Sandbox + AMFI + Quarantine 同时挂在 MACF 上 |
| **syscall filter** | 可直接关掉某些 syscall 号；沙盒规则更语义化 |
| **LiveContainer 等** | 用户态「假安装」；**客应用仍受宿主进程沙盒/签名约束**，且客容器互不隔离（见 livecontainer 文档） |

---

## 7. 开源树里能亲手验证的点

不依赖闭源 kext 符号时，建议：

1. 读 `mac_policy.h` 里 `mpo_vnode_check_open_t` 等原型 → 知道钩子参数。  
2. 在 `vfs_syscalls.c` 搜 `mac_vnode_check_open` → 看 open 路径。  
3. 读 `mac_base.c` 的 `__mac_syscall` → 理解应用如何把 call 送到名为 `"Sandbox"` 的策略。  
4. 读 `xnu/tests/vfs/sandbox_*.c` → 看 **libsandbox** 用户态用法（需 Apple 内部 SDK 链接 `-lsandbox`）。  
5. 对照安全白皮书 SEC-H：`__mac_*`、`csops`、`task_*_for_pid`。

---

## 8. 小结（可背）

1. **XNU 实现的是 MAC 钩子框架**；沙盒策略引擎在 **Sandbox.kext**。  
2. 强制点是分散的：`mac_*_check_*` → `MAC_CHECK` → `mpo_*`。  
3. 应用层装载/配置沙盒的主内核接口是 **`__mac_syscall` → `mpo_policy_syscall`**（经 libsandbox / `__sandbox_ms`）。  
4. 现代 App 隔离 = **entitlement 驱动的 App Sandbox profile** + **Container 文件系统** + （可选）Powerbox 临时授权。  
5. 显式 `sandbox_compile_*` + `sandbox_apply` 仍是理解 Seatbelt 的最佳实验路径（测试代码已在本树 `xnu/tests/vfs/`）。

---

## 9. 参考

### 本树

- `xnu/security/mac_policy.h` / `mac_base.c` / `mac_internal.h` / `mac_vfs.c` / `mac_process.c`  
- `xnu/security/mac.h`（`__mac_syscall` 等）  
- `xnu/bsd/sys/proc_private.h`（`sandbox_info_callbacks`）  
- `xnu/tests/vfs/sandbox_*.c`  
- `xnu/bsd/vfs/vfs_syscalls.c`（`mac_vnode_check_*` 调用点）

### 外部（闭源行为与 SBPL）

- Apple: [Configuring the macOS App Sandbox](https://developer.apple.com/documentation/xcode/configuring-the-macos-app-sandbox)  
- Dion Blazakis, *The Apple Sandbox*（Black Hat DC 2011，Seatbelt / Sandbox.kext）  
- Mac Internals: Sandbox profiles / SBPL  
- 公开逆向笔记：App Sandbox startup（`libsecinit` → `__sandbox_ms`）

---

*文档生成说明：Sandbox.kext 无开源实现；凡标注「闭源侧」的内容均为基于 MAC 挂接点与公开资料的机制还原，非 Apple 内部源码逐行注释。*
