# XNU 系统调用安全白皮书（BSD + Mach Trap）

> 版本基准：`xnu-12377.121.6`  
> 覆盖：**全部有效 BSD syscall（455）** + **全部有效 Mach trap（62，不含 `kern_invalid`）**  
> 生成脚本：[`scripts/gen_syscall_whitepaper.py`](../scripts/gen_syscall_whitepaper.py)  
> 配套 Demo：[`demos/whitepaper/`](../demos/whitepaper/)  
> 相关：[REMAINING_SYSCALLS.md](REMAINING_SYSCALLS.md) · [MACH_TRAPS.md](MACH_TRAPS.md)

---

## 0. 阅读指南

| 标记 | 含义 |
|------|------|
| **SEC-H** | 安全核心：身份、MAC、审计、权能、跨进程、沙箱/策略 |
| **SEC-M** | 安全相关：影响隔离/资源/同步边界 |
| **—** | 常规功能 |

```text
用户态
 ├─ BSD syscall  → sysent            （xnu/bsd/kern/syscalls.master）
 └─ Mach trap    → mach_trap_table  （xnu/osfmk/kern/syscall_sw.c）
```

**安全主线：** 凭证/Audit → MAC/csops → Mach task/port → Guarded FD/fileport → 内存/共享区 → NECP → Jetsam/coalition → 其余。

Demo 说明：能在 Linux CI 跑通的用可移植 POSIX；Darwin 专用 API 放在 `*_darwin.c`（`#ifdef __APPLE__`）。
无法用户态直接调用的私有 syscall/trap，用「同族可移植包装」或注释说明对应关系。

---

## 1. 安全重点抽提（SEC-H）

### 1.1 BSD SEC-H

| # | 名字 | 分组 | 一句话 |
|---|------|------|--------|
| 23 | `setuid` | 凭证 / 身份 / Audit | 设 real/effective uid |
| 24 | `getuid` | 凭证 / 身份 / Audit | 身份与审计 |
| 25 | `geteuid` | 凭证 / 身份 / Audit | 身份与审计 |
| 26 | `ptrace` | 调试 / 追踪 / sysctl / 遥测 | 调试器附着/控制 |
| 43 | `getegid` | 凭证 / 身份 / Audit | 身份与审计 |
| 47 | `getgid` | 凭证 / 身份 / Audit | 身份与审计 |
| 49 | `getlogin` | 凭证 / 身份 / Audit | 身份与审计 |
| 50 | `setlogin` | 凭证 / 身份 / Audit | 身份与审计 |
| 51 | `acct` | 杂项 / 平台特殊 | 其它 |
| 56 | `revoke` | 杂项 / 平台特殊 | 其它 |
| 61 | `chroot` | 文件 / 路径 / VFS / 属性 | 切换根目录 |
| 74 | `mprotect` | 内存 / VM / 共享区 / ulock | 改映射保护 |
| 79 | `getgroups` | 凭证 / 身份 / Audit | 身份与审计 |
| 80 | `setgroups` | 凭证 / 身份 / Audit | 身份与审计 |
| 126 | `setreuid` | 凭证 / 身份 / Audit | 身份与审计 |
| 127 | `setregid` | 凭证 / 身份 / Audit | 身份与审计 |
| 152 | `setprivexec` | 凭证 / 身份 / Audit | 身份与审计 |
| 169 | `csops` | MAC / 代码签名 / 系统策略 | 代码签名操作 |
| 170 | `csops_audittoken` | 凭证 / 身份 / Audit | 带 audit_token 的 csops |
| 181 | `setgid` | 凭证 / 身份 / Audit | 身份与审计 |
| 182 | `setegid` | 凭证 / 身份 / Audit | 身份与审计 |
| 183 | `seteuid` | 凭证 / 身份 / Audit | 身份与审计 |
| 197 | `mmap` | 内存 / VM / 共享区 / ulock | 映射内存 |
| 216 | `open_dprotected_np` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 218 | `openat_dprotected_np` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 243 | `initgroups` | 凭证 / 身份 / Audit | 身份与审计 |
| 253 | `shmsys` | 内存 / VM / 共享区 / ulock | 内存与共享 |
| 262 | `shmat` | 内存 / VM / 共享区 / ulock | 内存与共享 |
| 263 | `shmctl` | 内存 / VM / 共享区 / ulock | 内存与共享 |
| 264 | `shmdt` | 内存 / VM / 共享区 / ulock | 内存与共享 |
| 265 | `shmget` | 内存 / VM / 共享区 / ulock | 内存与共享 |
| 266 | `shm_open` | 内存 / VM / 共享区 / ulock | 内存与共享 |
| 267 | `shm_unlink` | 内存 / VM / 共享区 / ulock | 内存与共享 |
| 277 | `open_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 278 | `umask_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 279 | `stat_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 280 | `lstat_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 281 | `sys_fstat_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 282 | `chmod_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 283 | `fchmod_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 284 | `access_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 285 | `sys_settid` | 凭证 / 身份 / Audit | 身份与审计 |
| 286 | `gettid` | 凭证 / 身份 / Audit | 身份与审计 |
| 287 | `setsgroups` | 凭证 / 身份 / Audit | 身份与审计 |
| 288 | `getsgroups` | 凭证 / 身份 / Audit | 身份与审计 |
| 289 | `setwgroups` | 凭证 / 身份 / Audit | 身份与审计 |
| 290 | `getwgroups` | 凭证 / 身份 / Audit | 身份与审计 |
| 291 | `mkfifo_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 292 | `mkdir_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 293 | `identitysvc` | 凭证 / 身份 / Audit | 身份与审计 |
| 311 | `sys_settid_with_pid` | 凭证 / 身份 / Audit | 身份与审计 |
| 327 | `issetugid` | 进程 / 作业控制 / Jetsam | 是否经历过提权/降权敏感路径 |
| 341 | `stat64_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 342 | `lstat64_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 343 | `sys_fstat64_extended` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 350 | `audit` | 凭证 / 身份 / Audit | 写审计记录 |
| 351 | `auditon` | 凭证 / 身份 / Audit | 身份与审计 |
| 353 | `getauid` | 凭证 / 身份 / Audit | 身份与审计 |
| 354 | `setauid` | 凭证 / 身份 / Audit | 身份与审计 |
| 357 | `getaudit_addr` | 凭证 / 身份 / Audit | 身份与审计 |
| 358 | `setaudit_addr` | 凭证 / 身份 / Audit | 身份与审计 |
| 359 | `auditctl` | 凭证 / 身份 / Audit | 身份与审计 |
| 380 | `__mac_execve` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 381 | `__mac_syscall` | MAC / 代码签名 / 系统策略 | MAC 策略通用调用 |
| 382 | `__mac_get_file` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 383 | `__mac_set_file` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 384 | `__mac_get_link` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 385 | `__mac_set_link` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 386 | `__mac_get_proc` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 387 | `__mac_set_proc` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 388 | `__mac_get_fd` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 389 | `__mac_set_fd` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 390 | `__mac_get_pid` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 424 | `__mac_mount` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 425 | `__mac_get_mount` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 426 | `__mac_getfsstat` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 428 | `audit_session_self` | 凭证 / 身份 / Audit | 身份与审计 |
| 429 | `audit_session_join` | 凭证 / 身份 / Audit | 身份与审计 |
| 430 | `sys_fileport_makeport` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 431 | `sys_fileport_makefd` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 432 | `audit_session_port` | 凭证 / 身份 / Audit | 身份与审计 |
| 433 | `pid_suspend` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 434 | `pid_resume` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 435 | `pid_hibernate` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 436 | `pid_shutdown_sockets` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 439 | `kas_info` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 440 | `memorystatus_control` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 441 | `guarded_open_np` | FD Guard / Fileport / Task 权能 | 带 guard 打开 FD |
| 442 | `guarded_close_np` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 443 | `guarded_kqueue_np` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 452 | `proc_uuid_policy` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 453 | `memorystatus_get_level` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 458 | `coalition` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 459 | `coalition_info` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 460 | `necp_match_policy` | 网络 / NECP / Skywalk | 网络与策略 |
| 483 | `csrctl` | MAC / 代码签名 / 系统策略 | 强制访问控制与策略 |
| 484 | `guarded_open_dprotected_np` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 485 | `guarded_write_np` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 486 | `guarded_pwrite_np` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 487 | `guarded_writev_np` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 489 | `mremap_encrypted` | 内存 / VM / 共享区 / ulock | 内存与共享 |
| 494 | `persona` | 进程 / 作业控制 / Jetsam | 进程 persona |
| 500 | `getentropy` | 内存 / VM / 共享区 / ulock | 密码学熵 |
| 501 | `necp_open` | 网络 / NECP / Skywalk | NECP 客户端打开 |
| 502 | `necp_client_action` | 网络 / NECP / Skywalk | 网络与策略 |
| 520 | `terminate_with_payload` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 521 | `abort_with_payload` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 522 | `necp_session_open` | 网络 / NECP / Skywalk | 网络与策略 |
| 523 | `necp_session_action` | 网络 / NECP / Skywalk | 网络与策略 |
| 532 | `coalition_ledger` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 534 | `memorystatus_available_memory` | 进程 / 作业控制 / Jetsam | 进程生命周期与控制 |
| 536 | `shared_region_map_and_slide_2_np` | 内存 / VM / 共享区 / ulock | 内存与共享 |
| 537 | `pivot_root` | 文件 / 路径 / VFS / 属性 | 文件系统与路径 |
| 538 | `task_inspect_for_pid` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 539 | `task_read_for_pid` | FD Guard / Fileport / Task 权能 | 权能与句柄安全 |
| 547 | `debug_syscall_reject` | 调试 / 追踪 / sysctl / 遥测 | 可观测与调试 |
| 548 | `sys_debug_syscall_reject_config` | 调试 / 追踪 / sysctl / 遥测 | 可观测与调试 |
| 550 | `map_with_linking_np` | 内存 / VM / 共享区 / ulock | 内存与共享 |

### 1.2 Mach Trap SEC-H

| # | 名字 | 分组 | 一句话 |
|---|------|------|--------|
| 10 | `_kernelrpc_mach_vm_allocate_trap` | Mach：VM | Mach VM |
| 12 | `_kernelrpc_mach_vm_deallocate_trap` | Mach：VM | Mach VM |
| 14 | `_kernelrpc_mach_vm_protect_trap` | Mach：VM | Mach VM |
| 15 | `_kernelrpc_mach_vm_map_trap` | Mach：VM | Mach VM |
| 19 | `_kernelrpc_mach_port_mod_refs_trap` | Mach：Port 权能 | port 权利模型 |
| 21 | `_kernelrpc_mach_port_insert_right_trap` | Mach：Port 权能 | 插入 port 权利 |
| 24 | `_kernelrpc_mach_port_construct_trap` | Mach：Port 权能 | port 权利模型 |
| 25 | `_kernelrpc_mach_port_destruct_trap` | Mach：Port 权能 | port 权利模型 |
| 31 | `mach_msg_trap` | Mach：消息 IPC | Mach IPC 主入口 |
| 32 | `mach_msg_overwrite_trap` | Mach：消息 IPC | Mach IPC overwrite |
| 41 | `_kernelrpc_mach_port_guard_trap` | Mach：Port 权能 | port guard |
| 42 | `_kernelrpc_mach_port_unguard_trap` | Mach：Port 权能 | port 权利模型 |
| 44 | `task_name_for_pid` | Mach：Task↔PID 权能 | pid→task name port |
| 45 | `task_for_pid` | Mach：Task↔PID 权能 | pid→task port（强权能） |
| 46 | `pid_for_task` | Mach：Task↔PID 权能 | task→pid |
| 47 | `mach_msg2_trap` | Mach：消息 IPC | Mach IPC（msg2） |
| 70 | `host_create_mach_voucher_trap` | Mach：Voucher | 创建 Mach voucher |
| 72 | `mach_voucher_extract_attr_recipe_trap` | Mach：Voucher | IPC 凭证 |
| 88 | `_exclaves_ctl_trap` | Mach：Exclaves | Exclave 控制 |
| 96 | `debug_control_port_for_pid` | Mach：Task↔PID 权能 | pid→debug control port |
| 100 | `iokit_user_client_trap` | Mach：IOKit | IOKit user client |

---

## 2. BSD：按主题完整目录

### 进程 / 作业控制 / Jetsam

共 **42** · SEC-H **15** · SEC-M **11**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| — | 1 | `exit` | 进程生命周期与控制 |
| SEC-M | 2 | `fork` | 进程生命周期与控制 |
| SEC-M | 7 | `wait4` | 进程生命周期与控制 |
| — | 20 | `getpid` | 进程生命周期与控制 |
| SEC-M | 37 | `kill` | 进程生命周期与控制 |
| — | 39 | `getppid` | 进程生命周期与控制 |
| — | 55 | `reboot` | 进程生命周期与控制 |
| SEC-M | 59 | `execve` | 装载新映像 |
| SEC-M | 66 | `vfork` | 进程生命周期与控制 |
| — | 81 | `getpgrp` | 进程生命周期与控制 |
| — | 82 | `setpgid` | 进程生命周期与控制 |
| — | 96 | `setpriority` | 进程生命周期与控制 |
| — | 100 | `getpriority` | 进程生命周期与控制 |
| — | 117 | `getrusage` | 进程生命周期与控制 |
| — | 147 | `setsid` | 进程生命周期与控制 |
| — | 151 | `getpgid` | 进程生命周期与控制 |
| — | 173 | `waitid` | 进程生命周期与控制 |
| — | 185 | `sys_panic_with_data` | 进程生命周期与控制 |
| SEC-M | 194 | `getrlimit` | 进程生命周期与控制 |
| SEC-M | 195 | `setrlimit` | 进程生命周期与控制 |
| SEC-M | 244 | `posix_spawn` | 创建并执行 |
| — | 310 | `getsid` | 进程生命周期与控制 |
| **SEC-H** | 327 | `issetugid` | 是否经历过提权/降权敏感路径 |
| — | 328 | `__pthread_kill` | 进程生命周期与控制 |
| SEC-M | 336 | `proc_info` | 进程信息查询 SPI |
| **SEC-H** | 433 | `pid_suspend` | 进程生命周期与控制 |
| **SEC-H** | 434 | `pid_resume` | 进程生命周期与控制 |
| **SEC-H** | 435 | `pid_hibernate` | 进程生命周期与控制 |
| **SEC-H** | 436 | `pid_shutdown_sockets` | 进程生命周期与控制 |
| **SEC-H** | 440 | `memorystatus_control` | 进程生命周期与控制 |
| SEC-M | 446 | `proc_rlimit_control` | 进程生命周期与控制 |
| **SEC-H** | 452 | `proc_uuid_policy` | 进程生命周期与控制 |
| **SEC-H** | 453 | `memorystatus_get_level` | 进程生命周期与控制 |
| **SEC-H** | 458 | `coalition` | 进程生命周期与控制 |
| **SEC-H** | 459 | `coalition_info` | 进程生命周期与控制 |
| SEC-M | 477 | `proc_trace_log` | 进程生命周期与控制 |
| **SEC-H** | 494 | `persona` | 进程 persona |
| **SEC-H** | 520 | `terminate_with_payload` | 进程生命周期与控制 |
| **SEC-H** | 521 | `abort_with_payload` | 进程生命周期与控制 |
| — | 529 | `os_fault_with_payload` | 进程生命周期与控制 |
| **SEC-H** | 532 | `coalition_ledger` | 进程生命周期与控制 |
| **SEC-H** | 534 | `memorystatus_available_memory` | 进程生命周期与控制 |

### 文件 / 路径 / VFS / 属性

共 **115** · SEC-H **17** · SEC-M **7**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| — | 3 | `read` | 文件系统与路径 |
| — | 4 | `write` | 文件系统与路径 |
| SEC-M | 5 | `open` | 文件系统与路径 |
| — | 6 | `sys_close` | 文件系统与路径 |
| — | 9 | `link` | 文件系统与路径 |
| SEC-M | 10 | `unlink` | 文件系统与路径 |
| — | 14 | `mknod` | 文件系统与路径 |
| SEC-M | 15 | `chmod` | 文件系统与路径 |
| SEC-M | 16 | `chown` | 文件系统与路径 |
| — | 33 | `access` | 文件系统与路径 |
| — | 34 | `chflags` | 文件系统与路径 |
| — | 35 | `fchflags` | 文件系统与路径 |
| — | 42 | `pipe` | 文件系统与路径 |
| SEC-M | 54 | `ioctl` | 文件系统与路径 |
| — | 57 | `symlink` | 文件系统与路径 |
| — | 58 | `readlink` | 文件系统与路径 |
| — | 60 | `umask` | 文件系统与路径 |
| **SEC-H** | 61 | `chroot` | 切换根目录 |
| — | 92 | `sys_fcntl` | 文件系统与路径 |
| — | 95 | `fsync` | 文件系统与路径 |
| — | 120 | `readv` | 文件系统与路径 |
| — | 121 | `writev` | 文件系统与路径 |
| — | 123 | `fchown` | 文件系统与路径 |
| — | 124 | `fchmod` | 文件系统与路径 |
| SEC-M | 128 | `rename` | 文件系统与路径 |
| — | 131 | `sys_flock` | 文件系统与路径 |
| — | 132 | `mkfifo` | 文件系统与路径 |
| — | 136 | `mkdir` | 文件系统与路径 |
| — | 137 | `rmdir` | 文件系统与路径 |
| — | 153 | `pread` | 文件系统与路径 |
| — | 154 | `pwrite` | 文件系统与路径 |
| — | 155 | `nfssvc` | 文件系统与路径 |
| — | 159 | `unmount` | 文件系统与路径 |
| — | 161 | `getfh` | 文件系统与路径 |
| — | 164 | `funmount` | 文件系统与路径 |
| — | 165 | `quotactl` | 文件系统与路径 |
| — | 187 | `fdatasync` | 文件系统与路径 |
| — | 188 | `stat` | 文件系统与路径 |
| — | 189 | `sys_fstat` | 文件系统与路径 |
| — | 190 | `lstat` | 文件系统与路径 |
| — | 191 | `pathconf` | 文件系统与路径 |
| — | 196 | `getdirentries` | 文件系统与路径 |
| — | 199 | `lseek` | 文件系统与路径 |
| — | 200 | `truncate` | 文件系统与路径 |
| — | 201 | `ftruncate` | 文件系统与路径 |
| — | 205 | `undelete` | 文件系统与路径 |
| **SEC-H** | 216 | `open_dprotected_np` | 文件系统与路径 |
| **SEC-H** | 218 | `openat_dprotected_np` | 文件系统与路径 |
| — | 220 | `getattrlist` | 文件系统与路径 |
| — | 221 | `setattrlist` | 文件系统与路径 |
| — | 222 | `getdirentriesattr` | 文件系统与路径 |
| — | 223 | `exchangedata` | 文件系统与路径 |
| — | 225 | `searchfs` | 文件系统与路径 |
| — | 226 | `delete` | 文件系统与路径 |
| — | 227 | `copyfile` | 文件系统与路径 |
| — | 228 | `fgetattrlist` | 文件系统与路径 |
| — | 229 | `fsetattrlist` | 文件系统与路径 |
| — | 234 | `getxattr` | 文件系统与路径 |
| — | 235 | `fgetxattr` | 文件系统与路径 |
| — | 236 | `setxattr` | 文件系统与路径 |
| — | 237 | `fsetxattr` | 文件系统与路径 |
| — | 238 | `removexattr` | 文件系统与路径 |
| — | 239 | `fremovexattr` | 文件系统与路径 |
| — | 240 | `listxattr` | 文件系统与路径 |
| — | 241 | `flistxattr` | 文件系统与路径 |
| — | 242 | `fsctl` | 文件系统与路径 |
| — | 245 | `ffsctl` | 文件系统与路径 |
| — | 248 | `fhopen` | 文件系统与路径 |
| **SEC-H** | 277 | `open_extended` | 文件系统与路径 |
| **SEC-H** | 278 | `umask_extended` | 文件系统与路径 |
| **SEC-H** | 279 | `stat_extended` | 文件系统与路径 |
| **SEC-H** | 280 | `lstat_extended` | 文件系统与路径 |
| **SEC-H** | 281 | `sys_fstat_extended` | 文件系统与路径 |
| **SEC-H** | 282 | `chmod_extended` | 文件系统与路径 |
| **SEC-H** | 283 | `fchmod_extended` | 文件系统与路径 |
| **SEC-H** | 284 | `access_extended` | 文件系统与路径 |
| **SEC-H** | 291 | `mkfifo_extended` | 文件系统与路径 |
| **SEC-H** | 292 | `mkdir_extended` | 文件系统与路径 |
| — | 338 | `stat64` | 文件系统与路径 |
| — | 339 | `sys_fstat64` | 文件系统与路径 |
| — | 340 | `lstat64` | 文件系统与路径 |
| **SEC-H** | 341 | `stat64_extended` | 文件系统与路径 |
| **SEC-H** | 342 | `lstat64_extended` | 文件系统与路径 |
| **SEC-H** | 343 | `sys_fstat64_extended` | 文件系统与路径 |
| — | 344 | `getdirentries64` | 文件系统与路径 |
| — | 364 | `lchown` | 文件系统与路径 |
| — | 427 | `fsgetpath` | 文件系统与路径 |
| — | 455 | `vfs_purge` | 文件系统与路径 |
| — | 461 | `getattrlistbulk` | 文件系统与路径 |
| — | 462 | `clonefileat` | 文件系统与路径 |
| SEC-M | 463 | `openat` | 相对 dirfd 打开 |
| — | 465 | `renameat` | 文件系统与路径 |
| — | 466 | `faccessat` | 文件系统与路径 |
| — | 467 | `fchmodat` | 文件系统与路径 |
| — | 468 | `fchownat` | 文件系统与路径 |
| — | 469 | `fstatat` | 文件系统与路径 |
| — | 471 | `linkat` | 文件系统与路径 |
| — | 472 | `unlinkat` | 文件系统与路径 |
| — | 473 | `readlinkat` | 文件系统与路径 |
| — | 474 | `symlinkat` | 文件系统与路径 |
| — | 475 | `mkdirat` | 文件系统与路径 |
| — | 476 | `getattrlistat` | 文件系统与路径 |
| — | 479 | `openbyid_np` | 文件系统与路径 |
| — | 488 | `renameatx_np` | 文件系统与路径 |
| — | 517 | `fclonefileat` | 文件系统与路径 |
| — | 518 | `fs_snapshot` | 文件系统与路径 |
| — | 524 | `setattrlistat` | 文件系统与路径 |
| — | 526 | `fmount` | 文件系统与路径 |
| **SEC-H** | 537 | `pivot_root` | 文件系统与路径 |
| — | 540 | `sys_preadv` | 文件系统与路径 |
| — | 541 | `sys_pwritev` | 文件系统与路径 |
| — | 549 | `graftdmg` | 文件系统与路径 |
| — | 553 | `mkfifoat` | 文件系统与路径 |
| — | 554 | `mknodat` | 文件系统与路径 |
| — | 555 | `ungraftdmg` | 文件系统与路径 |

### 杂项 / 平台特殊

共 **35** · SEC-H **2** · SEC-M **1**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| — | 12 | `sys_chdir` | 其它 |
| — | 13 | `sys_fchdir` | 其它 |
| — | 18 | `getfsstat` | 其它 |
| — | 36 | `sync` | 其它 |
| — | 38 | `sys_crossarch_trap` | 其它 |
| — | 41 | `sys_dup` | 其它 |
| **SEC-H** | 51 | `acct` | 其它 |
| **SEC-H** | 56 | `revoke` | 其它 |
| — | 85 | `swapon` | 其它 |
| — | 89 | `sys_getdtablesize` | 其它 |
| — | 90 | `sys_dup2` | 其它 |
| — | 122 | `settimeofday` | 其它 |
| — | 138 | `utimes` | 其它 |
| — | 139 | `futimes` | 其它 |
| — | 142 | `gethostuuid` | 其它 |
| — | 157 | `statfs` | 其它 |
| — | 158 | `fstatfs` | 其它 |
| — | 167 | `mount` | 其它 |
| — | 192 | `sys_fpathconf` | 其它 |
| — | 217 | `fsgetpath_ext` | 其它 |
| — | 345 | `statfs64` | 其它 |
| — | 346 | `fstatfs64` | 其它 |
| — | 347 | `getfsstat64` | 其它 |
| — | 348 | `__pthread_chdir` | 其它 |
| — | 349 | `__pthread_fchdir` | 其它 |
| — | 444 | `change_fdguard_np` | 其它 |
| — | 470 | `fstatat64` | 其它 |
| — | 497 | `mach_eventlink_wait_until` | 其它 |
| — | 515 | `sys_ulock_wait` | 其它 |
| — | 516 | `sys_ulock_wake` | 其它 |
| — | 531 | `__mach_bridge_remote_time` | 其它 |
| SEC-M | 545 | `proc_info_extended_id` | 其它 |
| — | 551 | `freadlink` | 其它 |
| — | 556 | `sys_coalition_policy_set` | 其它 |
| — | 557 | `sys_coalition_policy_get` | 其它 |

### 凭证 / 身份 / Audit

共 **35** · SEC-H **35** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 23 | `setuid` | 设 real/effective uid |
| **SEC-H** | 24 | `getuid` | 身份与审计 |
| **SEC-H** | 25 | `geteuid` | 身份与审计 |
| **SEC-H** | 43 | `getegid` | 身份与审计 |
| **SEC-H** | 47 | `getgid` | 身份与审计 |
| **SEC-H** | 49 | `getlogin` | 身份与审计 |
| **SEC-H** | 50 | `setlogin` | 身份与审计 |
| **SEC-H** | 79 | `getgroups` | 身份与审计 |
| **SEC-H** | 80 | `setgroups` | 身份与审计 |
| **SEC-H** | 126 | `setreuid` | 身份与审计 |
| **SEC-H** | 127 | `setregid` | 身份与审计 |
| **SEC-H** | 152 | `setprivexec` | 身份与审计 |
| **SEC-H** | 170 | `csops_audittoken` | 带 audit_token 的 csops |
| **SEC-H** | 181 | `setgid` | 身份与审计 |
| **SEC-H** | 182 | `setegid` | 身份与审计 |
| **SEC-H** | 183 | `seteuid` | 身份与审计 |
| **SEC-H** | 243 | `initgroups` | 身份与审计 |
| **SEC-H** | 285 | `sys_settid` | 身份与审计 |
| **SEC-H** | 286 | `gettid` | 身份与审计 |
| **SEC-H** | 287 | `setsgroups` | 身份与审计 |
| **SEC-H** | 288 | `getsgroups` | 身份与审计 |
| **SEC-H** | 289 | `setwgroups` | 身份与审计 |
| **SEC-H** | 290 | `getwgroups` | 身份与审计 |
| **SEC-H** | 293 | `identitysvc` | 身份与审计 |
| **SEC-H** | 311 | `sys_settid_with_pid` | 身份与审计 |
| **SEC-H** | 350 | `audit` | 写审计记录 |
| **SEC-H** | 351 | `auditon` | 身份与审计 |
| **SEC-H** | 353 | `getauid` | 身份与审计 |
| **SEC-H** | 354 | `setauid` | 身份与审计 |
| **SEC-H** | 357 | `getaudit_addr` | 身份与审计 |
| **SEC-H** | 358 | `setaudit_addr` | 身份与审计 |
| **SEC-H** | 359 | `auditctl` | 身份与审计 |
| **SEC-H** | 428 | `audit_session_self` | 身份与审计 |
| **SEC-H** | 429 | `audit_session_join` | 身份与审计 |
| **SEC-H** | 432 | `audit_session_port` | 身份与审计 |

### 调试 / 追踪 / sysctl / 遥测

共 **19** · SEC-H **3** · SEC-M **16**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 26 | `ptrace` | 调试器附着/控制 |
| SEC-M | 67 | `oslog_coproc_reg` | 可观测与调试 |
| SEC-M | 68 | `oslog_coproc` | 可观测与调试 |
| SEC-M | 177 | `kdebug_typefilter` | 可观测与调试 |
| SEC-M | 178 | `kdebug_trace_string` | 可观测与调试 |
| SEC-M | 179 | `kdebug_trace64` | 可观测与调试 |
| SEC-M | 180 | `kdebug_trace` | 可观测与调试 |
| SEC-M | 202 | `sysctl` | 可观测与调试 |
| SEC-M | 274 | `sys_sysctlbyname` | 可观测与调试 |
| SEC-M | 451 | `telemetry` | 可观测与调试 |
| SEC-M | 491 | `stack_snapshot_with_config` | 可观测与调试 |
| SEC-M | 492 | `microstackshot` | 可观测与调试 |
| SEC-M | 493 | `grab_pgo_data` | 可观测与调试 |
| SEC-M | 533 | `log_data` | 可观测与调试 |
| SEC-M | 535 | `objc_bp_assist_cfg_np` | 可观测与调试 |
| SEC-M | 546 | `tracker_action` | 可观测与调试 |
| **SEC-H** | 547 | `debug_syscall_reject` | 可观测与调试 |
| **SEC-H** | 548 | `sys_debug_syscall_reject_config` | 可观测与调试 |
| SEC-M | 552 | `sys_record_system_event` | 可观测与调试 |

### 网络 / NECP / Skywalk

共 **41** · SEC-H **5** · SEC-M **36**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| SEC-M | 27 | `recvmsg` | 网络与策略 |
| SEC-M | 28 | `sendmsg` | 网络与策略 |
| SEC-M | 29 | `recvfrom` | 网络与策略 |
| SEC-M | 30 | `accept` | 网络与策略 |
| SEC-M | 31 | `getpeername` | 网络与策略 |
| SEC-M | 32 | `getsockname` | 网络与策略 |
| SEC-M | 97 | `socket` | 网络与策略 |
| SEC-M | 98 | `connect` | 网络与策略 |
| SEC-M | 104 | `bind` | 网络与策略 |
| SEC-M | 105 | `setsockopt` | 网络与策略 |
| SEC-M | 106 | `listen` | 网络与策略 |
| SEC-M | 118 | `getsockopt` | 网络与策略 |
| SEC-M | 133 | `sendto` | 网络与策略 |
| SEC-M | 134 | `shutdown` | 网络与策略 |
| SEC-M | 135 | `socketpair` | 网络与策略 |
| SEC-M | 337 | `sendfile` | 网络与策略 |
| SEC-M | 447 | `connectx` | 网络与策略 |
| SEC-M | 448 | `disconnectx` | 网络与策略 |
| SEC-M | 449 | `peeloff` | 网络与策略 |
| SEC-M | 450 | `socket_delegate` | 网络与策略 |
| **SEC-H** | 460 | `necp_match_policy` | 网络与策略 |
| SEC-M | 480 | `recvmsg_x` | 网络与策略 |
| SEC-M | 481 | `sendmsg_x` | 网络与策略 |
| SEC-M | 490 | `netagent_trigger` | 网络与策略 |
| **SEC-H** | 501 | `necp_open` | NECP 客户端打开 |
| **SEC-H** | 502 | `necp_client_action` | 网络与策略 |
| SEC-M | 503 | `__nexus_open` | 网络与策略 |
| SEC-M | 504 | `__nexus_register` | 网络与策略 |
| SEC-M | 505 | `__nexus_deregister` | 网络与策略 |
| SEC-M | 506 | `__nexus_create` | 网络与策略 |
| SEC-M | 507 | `__nexus_destroy` | 网络与策略 |
| SEC-M | 508 | `__nexus_get_opt` | 网络与策略 |
| SEC-M | 509 | `__nexus_set_opt` | 网络与策略 |
| SEC-M | 510 | `__channel_open` | 网络与策略 |
| SEC-M | 511 | `__channel_get_info` | 网络与策略 |
| SEC-M | 512 | `__channel_sync` | 网络与策略 |
| SEC-M | 513 | `__channel_get_opt` | 网络与策略 |
| SEC-M | 514 | `__channel_set_opt` | 网络与策略 |
| **SEC-H** | 522 | `necp_session_open` | 网络与策略 |
| **SEC-H** | 523 | `necp_session_action` | 网络与策略 |
| SEC-M | 525 | `net_qos_guideline` | 网络与策略 |

### 信号

共 **8** · SEC-H **0** · SEC-M **8**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| SEC-M | 46 | `sigaction` | 信号投递与掩码 |
| SEC-M | 48 | `sigprocmask` | 信号投递与掩码 |
| SEC-M | 52 | `sigpending` | 信号投递与掩码 |
| SEC-M | 53 | `sigaltstack` | 信号投递与掩码 |
| SEC-M | 111 | `sigsuspend` | 信号投递与掩码 |
| SEC-M | 184 | `sigreturn` | 信号投递与掩码 |
| SEC-M | 496 | `mach_eventlink_signal` | 信号投递与掩码 |
| SEC-M | 498 | `mach_eventlink_signal_wait_until` | 信号投递与掩码 |

### 内存 / VM / 共享区 / ulock

共 **25** · SEC-H **13** · SEC-M **12**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| SEC-M | 65 | `msync` | 内存与共享 |
| SEC-M | 73 | `munmap` | 内存与共享 |
| **SEC-H** | 74 | `mprotect` | 改映射保护 |
| SEC-M | 75 | `madvise` | 内存与共享 |
| SEC-M | 78 | `mincore` | 内存与共享 |
| **SEC-H** | 197 | `mmap` | 映射内存 |
| SEC-M | 203 | `mlock` | 内存与共享 |
| SEC-M | 204 | `munlock` | 内存与共享 |
| SEC-M | 250 | `minherit` | 内存与共享 |
| **SEC-H** | 253 | `shmsys` | 内存与共享 |
| **SEC-H** | 262 | `shmat` | 内存与共享 |
| **SEC-H** | 263 | `shmctl` | 内存与共享 |
| **SEC-H** | 264 | `shmdt` | 内存与共享 |
| **SEC-H** | 265 | `shmget` | 内存与共享 |
| **SEC-H** | 266 | `shm_open` | 内存与共享 |
| **SEC-H** | 267 | `shm_unlink` | 内存与共享 |
| SEC-M | 294 | `shared_region_check_np` | 内存与共享 |
| SEC-M | 296 | `vm_pressure_monitor` | 内存与共享 |
| SEC-M | 324 | `mlockall` | 内存与共享 |
| SEC-M | 325 | `munlockall` | 内存与共享 |
| **SEC-H** | 489 | `mremap_encrypted` | 内存与共享 |
| **SEC-H** | 500 | `getentropy` | 密码学熵 |
| **SEC-H** | 536 | `shared_region_map_and_slide_2_np` | 内存与共享 |
| SEC-M | 544 | `sys_ulock_wait2` | 内存与共享 |
| **SEC-H** | 550 | `map_with_linking_np` | 内存与共享 |

### 时间 / 定时器

共 **6** · SEC-H **0** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| — | 83 | `setitimer` | 时间 |
| — | 86 | `getitimer` | 时间 |
| — | 116 | `gettimeofday` | 时间 |
| — | 140 | `adjtime` | 时间 |
| — | 527 | `ntp_adjtime` | 时间 |
| — | 528 | `ntp_gettime` | 时间 |

### 事件通知 / kqueue

共 **9** · SEC-H **0** · SEC-M **9**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| SEC-M | 93 | `select` | 事件与多路复用 |
| SEC-M | 230 | `poll` | 事件与多路复用 |
| SEC-M | 362 | `kqueue` | 事件与多路复用 |
| SEC-M | 363 | `kevent` | 事件与多路复用 |
| SEC-M | 369 | `kevent64` | 事件与多路复用 |
| SEC-M | 374 | `kevent_qos` | 事件与多路复用 |
| SEC-M | 375 | `kevent_id` | 事件与多路复用 |
| SEC-M | 394 | `pselect` | 事件与多路复用 |
| SEC-M | 530 | `kqueue_workloop_ctl` | 事件与多路复用 |

### MAC / 代码签名 / 系统策略

共 **23** · SEC-H **17** · SEC-M **6**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 169 | `csops` | 代码签名操作 |
| SEC-M | 322 | `iopolicysys` | 强制访问控制与策略 |
| SEC-M | 323 | `process_policy` | 强制访问控制与策略 |
| **SEC-H** | 380 | `__mac_execve` | 强制访问控制与策略 |
| **SEC-H** | 381 | `__mac_syscall` | MAC 策略通用调用 |
| **SEC-H** | 382 | `__mac_get_file` | 强制访问控制与策略 |
| **SEC-H** | 383 | `__mac_set_file` | 强制访问控制与策略 |
| **SEC-H** | 384 | `__mac_get_link` | 强制访问控制与策略 |
| **SEC-H** | 385 | `__mac_set_link` | 强制访问控制与策略 |
| **SEC-H** | 386 | `__mac_get_proc` | 强制访问控制与策略 |
| **SEC-H** | 387 | `__mac_set_proc` | 强制访问控制与策略 |
| **SEC-H** | 388 | `__mac_get_fd` | 强制访问控制与策略 |
| **SEC-H** | 389 | `__mac_set_fd` | 强制访问控制与策略 |
| **SEC-H** | 390 | `__mac_get_pid` | 强制访问控制与策略 |
| **SEC-H** | 424 | `__mac_mount` | 强制访问控制与策略 |
| **SEC-H** | 425 | `__mac_get_mount` | 强制访问控制与策略 |
| **SEC-H** | 426 | `__mac_getfsstat` | 强制访问控制与策略 |
| **SEC-H** | 439 | `kas_info` | 强制访问控制与策略 |
| SEC-M | 445 | `usrctl` | 强制访问控制与策略 |
| SEC-M | 454 | `system_override` | 强制访问控制与策略 |
| SEC-M | 456 | `sfi_ctl` | 强制访问控制与策略 |
| SEC-M | 457 | `sfi_pidctl` | 强制访问控制与策略 |
| **SEC-H** | 483 | `csrctl` | 强制访问控制与策略 |

### 线程 / pthread / workq / IPC 同步

共 **54** · SEC-H **0** · SEC-M **54**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| SEC-M | 186 | `thread_selfcounts` | 线程与同步 |
| SEC-M | 251 | `semsys` | 线程与同步 |
| SEC-M | 252 | `msgsys` | 线程与同步 |
| SEC-M | 254 | `semctl` | 线程与同步 |
| SEC-M | 255 | `semget` | 线程与同步 |
| SEC-M | 256 | `semop` | 线程与同步 |
| SEC-M | 258 | `msgctl` | 线程与同步 |
| SEC-M | 259 | `msgget` | 线程与同步 |
| SEC-M | 260 | `msgsnd` | 线程与同步 |
| SEC-M | 261 | `msgrcv` | 线程与同步 |
| SEC-M | 268 | `sem_open` | 线程与同步 |
| SEC-M | 269 | `sem_close` | 线程与同步 |
| SEC-M | 270 | `sem_unlink` | 线程与同步 |
| SEC-M | 271 | `sem_wait` | 线程与同步 |
| SEC-M | 272 | `sem_trywait` | 线程与同步 |
| SEC-M | 273 | `sem_post` | 线程与同步 |
| SEC-M | 297 | `psynch_rw_longrdlock` | 线程与同步 |
| SEC-M | 298 | `psynch_rw_yieldwrlock` | 线程与同步 |
| SEC-M | 299 | `psynch_rw_downgrade` | 线程与同步 |
| SEC-M | 300 | `psynch_rw_upgrade` | 线程与同步 |
| SEC-M | 301 | `psynch_mutexwait` | 线程与同步 |
| SEC-M | 302 | `psynch_mutexdrop` | 线程与同步 |
| SEC-M | 303 | `psynch_cvbroad` | 线程与同步 |
| SEC-M | 304 | `psynch_cvsignal` | 线程与同步 |
| SEC-M | 305 | `psynch_cvwait` | 线程与同步 |
| SEC-M | 306 | `psynch_rw_rdlock` | 线程与同步 |
| SEC-M | 307 | `psynch_rw_wrlock` | 线程与同步 |
| SEC-M | 308 | `psynch_rw_unlock` | 线程与同步 |
| SEC-M | 309 | `psynch_rw_unlock2` | 线程与同步 |
| SEC-M | 312 | `psynch_cvclrprepost` | 线程与同步 |
| SEC-M | 313 | `aio_fsync` | 线程与同步 |
| SEC-M | 314 | `aio_return` | 线程与同步 |
| SEC-M | 315 | `aio_suspend` | 线程与同步 |
| SEC-M | 316 | `aio_cancel` | 线程与同步 |
| SEC-M | 317 | `aio_error` | 线程与同步 |
| SEC-M | 318 | `aio_read` | 线程与同步 |
| SEC-M | 319 | `aio_write` | 线程与同步 |
| SEC-M | 320 | `lio_listio` | 线程与同步 |
| SEC-M | 329 | `__pthread_sigmask` | 线程与同步 |
| SEC-M | 330 | `__sigwait` | 线程与同步 |
| SEC-M | 331 | `__disable_threadsignal` | 线程与同步 |
| SEC-M | 332 | `__pthread_markcancel` | 线程与同步 |
| SEC-M | 333 | `__pthread_canceled` | 线程与同步 |
| SEC-M | 334 | `__semwait_signal` | 线程与同步 |
| SEC-M | 360 | `bsdthread_create` | pthread_create 内核路径 |
| SEC-M | 361 | `bsdthread_terminate` | 线程与同步 |
| SEC-M | 366 | `bsdthread_register` | 线程与同步 |
| SEC-M | 367 | `workq_open` | 线程与同步 |
| SEC-M | 368 | `workq_kernreturn` | workqueue 内核返回/调度 |
| SEC-M | 372 | `thread_selfid` | 线程与同步 |
| SEC-M | 373 | `ledger` | 线程与同步 |
| SEC-M | 478 | `bsdthread_ctl` | 线程与同步 |
| SEC-M | 482 | `thread_selfusage` | 线程与同步 |
| SEC-M | 499 | `work_interval_ctl` | 线程与同步 |

### Nocancel 变体

共 **32** · SEC-H **0** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| — | 395 | `pselect_nocancel` | 与可取消版同语义 |
| — | 396 | `read_nocancel` | 与可取消版同语义 |
| — | 397 | `write_nocancel` | 与可取消版同语义 |
| — | 398 | `open_nocancel` | 与可取消版同语义 |
| — | 399 | `sys_close_nocancel` | 与可取消版同语义 |
| — | 400 | `wait4_nocancel` | 与可取消版同语义 |
| — | 401 | `recvmsg_nocancel` | 与可取消版同语义 |
| — | 402 | `sendmsg_nocancel` | 与可取消版同语义 |
| — | 403 | `recvfrom_nocancel` | 与可取消版同语义 |
| — | 404 | `accept_nocancel` | 与可取消版同语义 |
| — | 405 | `msync_nocancel` | 与可取消版同语义 |
| — | 406 | `sys_fcntl_nocancel` | 与可取消版同语义 |
| — | 407 | `select_nocancel` | 与可取消版同语义 |
| — | 408 | `fsync_nocancel` | 与可取消版同语义 |
| — | 409 | `connect_nocancel` | 与可取消版同语义 |
| — | 410 | `sigsuspend_nocancel` | 与可取消版同语义 |
| — | 411 | `readv_nocancel` | 与可取消版同语义 |
| — | 412 | `writev_nocancel` | 与可取消版同语义 |
| — | 413 | `sendto_nocancel` | 与可取消版同语义 |
| — | 414 | `pread_nocancel` | 与可取消版同语义 |
| — | 415 | `pwrite_nocancel` | 与可取消版同语义 |
| — | 416 | `waitid_nocancel` | 与可取消版同语义 |
| — | 417 | `poll_nocancel` | 与可取消版同语义 |
| — | 418 | `msgsnd_nocancel` | 与可取消版同语义 |
| — | 419 | `msgrcv_nocancel` | 与可取消版同语义 |
| — | 420 | `sem_wait_nocancel` | 与可取消版同语义 |
| — | 421 | `aio_suspend_nocancel` | 与可取消版同语义 |
| — | 422 | `__sigwait_nocancel` | 与可取消版同语义 |
| — | 423 | `__semwait_signal_nocancel` | 与可取消版同语义 |
| — | 464 | `openat_nocancel` | 与可取消版同语义 |
| — | 542 | `sys_preadv_nocancel` | 与可取消版同语义 |
| — | 543 | `sys_pwritev_nocancel` | 与可取消版同语义 |

### FD Guard / Fileport / Task 权能

共 **11** · SEC-H **11** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 430 | `sys_fileport_makeport` | 权能与句柄安全 |
| **SEC-H** | 431 | `sys_fileport_makefd` | 权能与句柄安全 |
| **SEC-H** | 441 | `guarded_open_np` | 带 guard 打开 FD |
| **SEC-H** | 442 | `guarded_close_np` | 权能与句柄安全 |
| **SEC-H** | 443 | `guarded_kqueue_np` | 权能与句柄安全 |
| **SEC-H** | 484 | `guarded_open_dprotected_np` | 权能与句柄安全 |
| **SEC-H** | 485 | `guarded_write_np` | 权能与句柄安全 |
| **SEC-H** | 486 | `guarded_pwrite_np` | 权能与句柄安全 |
| **SEC-H** | 487 | `guarded_writev_np` | 权能与句柄安全 |
| **SEC-H** | 538 | `task_inspect_for_pid` | 权能与句柄安全 |
| **SEC-H** | 539 | `task_read_for_pid` | 权能与句柄安全 |

---

## 3. Mach Trap：按主题完整目录

### Mach：VM

共 **7** · SEC-H **4** · SEC-M **3**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 10 | `_kernelrpc_mach_vm_allocate_trap` | Mach VM |
| SEC-M | 11 | `_kernelrpc_mach_vm_purgable_control_trap` | Mach VM |
| **SEC-H** | 12 | `_kernelrpc_mach_vm_deallocate_trap` | Mach VM |
| SEC-M | 13 | `task_dyld_process_info_notify_get_trap` | Mach VM |
| **SEC-H** | 14 | `_kernelrpc_mach_vm_protect_trap` | Mach VM |
| **SEC-H** | 15 | `_kernelrpc_mach_vm_map_trap` | Mach VM |
| SEC-M | 63 | `mach_vm_reclaim_update_kernel_accounting_trap` | Mach VM |

### Mach：Port 权能

共 **19** · SEC-H **6** · SEC-M **13**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| SEC-M | 16 | `_kernelrpc_mach_port_allocate_trap` | port 权利模型 |
| SEC-M | 18 | `_kernelrpc_mach_port_deallocate_trap` | port 权利模型 |
| **SEC-H** | 19 | `_kernelrpc_mach_port_mod_refs_trap` | port 权利模型 |
| SEC-M | 20 | `_kernelrpc_mach_port_move_member_trap` | port 权利模型 |
| **SEC-H** | 21 | `_kernelrpc_mach_port_insert_right_trap` | 插入 port 权利 |
| SEC-M | 22 | `_kernelrpc_mach_port_insert_member_trap` | port 权利模型 |
| SEC-M | 23 | `_kernelrpc_mach_port_extract_member_trap` | port 权利模型 |
| **SEC-H** | 24 | `_kernelrpc_mach_port_construct_trap` | port 权利模型 |
| **SEC-H** | 25 | `_kernelrpc_mach_port_destruct_trap` | port 权利模型 |
| SEC-M | 26 | `mach_reply_port` | port 权利模型 |
| SEC-M | 27 | `thread_self_trap` | 当前 thread port |
| SEC-M | 28 | `task_self_trap` | 当前 task port |
| SEC-M | 29 | `host_self_trap` | port 权利模型 |
| SEC-M | 40 | `_kernelrpc_mach_port_get_attributes_trap` | port 权利模型 |
| **SEC-H** | 41 | `_kernelrpc_mach_port_guard_trap` | port guard |
| **SEC-H** | 42 | `_kernelrpc_mach_port_unguard_trap` | port 权利模型 |
| SEC-M | 50 | `thread_get_special_reply_port` | port 权利模型 |
| SEC-M | 76 | `_kernelrpc_mach_port_type_trap` | port 权利模型 |
| SEC-M | 77 | `_kernelrpc_mach_port_request_notification_trap` | port 权利模型 |

### Mach：消息 IPC

共 **3** · SEC-H **3** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 31 | `mach_msg_trap` | Mach IPC 主入口 |
| **SEC-H** | 32 | `mach_msg_overwrite_trap` | Mach IPC overwrite |
| **SEC-H** | 47 | `mach_msg2_trap` | Mach IPC（msg2） |

### Mach：信号量

共 **7** · SEC-H **0** · SEC-M **7**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| SEC-M | 33 | `semaphore_signal_trap` | Mach semaphore |
| SEC-M | 34 | `semaphore_signal_all_trap` | Mach semaphore |
| SEC-M | 35 | `semaphore_signal_thread_trap` | Mach semaphore |
| SEC-M | 36 | `semaphore_wait_trap` | Mach semaphore |
| SEC-M | 37 | `semaphore_wait_signal_trap` | Mach semaphore |
| SEC-M | 38 | `semaphore_timedwait_trap` | Mach semaphore |
| SEC-M | 39 | `semaphore_timedwait_signal_trap` | Mach semaphore |

### Mach：调度 / 时间 / Timer

共 **13** · SEC-H **0** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| — | 43 | `mach_generate_activity_id` | 调度与时间 |
| — | 58 | `pfz_exit` | 调度与时间 |
| — | 59 | `swtch_pri` | 调度与时间 |
| — | 60 | `swtch` | 调度与时间 |
| — | 61 | `thread_switch` | 调度与时间 |
| — | 62 | `clock_sleep_trap` | 调度与时间 |
| — | 89 | `mach_timebase_info_trap` | 调度与时间 |
| — | 90 | `mach_wait_until_trap` | 调度与时间 |
| — | 91 | `mk_timer_create_trap` | 调度与时间 |
| — | 92 | `mk_timer_destroy_trap` | 调度与时间 |
| — | 93 | `mk_timer_arm_trap` | 调度与时间 |
| — | 94 | `mk_timer_cancel_trap` | 调度与时间 |
| — | 95 | `mk_timer_arm_leeway_trap` | 调度与时间 |

### Mach：Task↔PID 权能

共 **4** · SEC-H **4** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 44 | `task_name_for_pid` | pid→task name port |
| **SEC-H** | 45 | `task_for_pid` | pid→task port（强权能） |
| **SEC-H** | 46 | `pid_for_task` | task→pid |
| **SEC-H** | 96 | `debug_control_port_for_pid` | pid→debug control port |

### Mach：macx / swap

共 **5** · SEC-H **0** · SEC-M **5**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| SEC-M | 48 | `macx_swapon` | 遗留 macx |
| SEC-M | 49 | `macx_swapoff` | 遗留 macx |
| SEC-M | 51 | `macx_triggers` | 遗留 macx |
| SEC-M | 52 | `macx_backing_store_suspend` | 遗留 macx |
| SEC-M | 53 | `macx_backing_store_recovery` | 遗留 macx |

### Mach：Voucher

共 **2** · SEC-H **2** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 70 | `host_create_mach_voucher_trap` | 创建 Mach voucher |
| **SEC-H** | 72 | `mach_voucher_extract_attr_recipe_trap` | IPC 凭证 |

### Mach：Exclaves

共 **1** · SEC-H **1** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 88 | `_exclaves_ctl_trap` | Exclave 控制 |

### Mach：IOKit

共 **1** · SEC-H **1** · SEC-M **0**

| 安全 | # | 名字 | 一句话 |
|------|---|------|--------|
| **SEC-H** | 100 | `iokit_user_client_trap` | IOKit user client |

---

## 4. Demo 索引

| Demo | 覆盖主题 | 平台 |
|------|----------|------|
| [`01_process_ids.c`](../demos/whitepaper/01_process_ids.c) | 进程身份 getpid/ppid/uid/gid | 可移植 |
| [`02_file_basic.c`](../demos/whitepaper/02_file_basic.c) | 文件 open/read/write/close/stat | 可移植 |
| [`03_file_at.c`](../demos/whitepaper/03_file_at.c) | *at 族 openat/fstatat/unlinkat | 可移植 |
| [`04_memory_mmap.c`](../demos/whitepaper/04_memory_mmap.c) | mmap/mprotect/munmap | 可移植 |
| [`05_pipe_fcntl.c`](../demos/whitepaper/05_pipe_fcntl.c) | pipe/fcntl | 可移植 |
| [`06_socket_udp.c`](../demos/whitepaper/06_socket_udp.c) | socket/bind/sendto/recvfrom | 可移植 |
| [`07_signal_basic.c`](../demos/whitepaper/07_signal_basic.c) | sigaction/kill | 可移植 |
| [`08_pthread_sync.c`](../demos/whitepaper/08_pthread_sync.c) | mutex/cond/rwlock（Darwin→psynch） | 可移植 |
| [`09_pthread_cancel.c`](../demos/whitepaper/09_pthread_cancel.c) | pthread_cancel（→markcancel） | 可移植 |
| [`10_time_rusage.c`](../demos/whitepaper/10_time_rusage.c) | gettimeofday/getrusage | 可移植 |
| [`11_entropy.c`](../demos/whitepaper/11_entropy.c) | getentropy | 可移植* |
| [`12_shm_posix.c`](../demos/whitepaper/12_shm_posix.c) | shm_open/mmap | 可移植 |
| [`13_spawn_wait.c`](../demos/whitepaper/13_spawn_wait.c) | posix_spawn/wait | 可移植 |
| [`14_event_poll.c`](../demos/whitepaper/14_event_poll.c) | poll | 可移植 |
| [`20_mach_self_ports.c`](../demos/whitepaper/20_mach_self_ports.c) | task/thread/host self traps | Darwin |
| [`21_mach_vm.c`](../demos/whitepaper/21_mach_vm.c) | mach_vm_allocate/protect/deallocate | Darwin |
| [`22_mach_msg_bootstrap.c`](../demos/whitepaper/22_mach_msg_bootstrap.c) | mach_msg 探测 bootstrap | Darwin |
| [`23_csops_darwin.c`](../demos/whitepaper/23_csops_darwin.c) | csops 状态位 | Darwin |

```bash
cd demos/whitepaper && make check          # 可移植 Demo
cd demos/whitepaper && make check-darwin  # 仅 macOS
```

---

## 5. 统计

- BSD 有效条目：**455**
- Mach 有效 trap：**62**
- BSD SEC-H：**118**
- Mach SEC-H：**21**

重新生成：

```bash
python3 scripts/gen_syscall_whitepaper.py
```

