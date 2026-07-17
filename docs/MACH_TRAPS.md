# Mach Trap 地图（需单独记账）

源码：`xnu/osfmk/kern/syscall_sw.c` → **`mach_trap_table`**（共 **128** 槽；大量 `kern_invalid`）。

## 为什么之前没进「剩余 syscall」表？

| | BSD syscall | Mach trap |
|--|-------------|-----------|
| 表 | `syscalls.master` → `sysent` | `mach_trap_table` |
| 编号空间 | 0…500+（BSD） | 0…127（Mach） |
| 用户入口 | 常见 `syscall` / libSystem BSD 包装 | `mach_msg`、libmach、部分 libSystem 内部 |
| 本仓库 Day 1–71 | 主要扫 BSD；只标「BSD→Mach」落点 | **几乎未按 trap 编号逐条学** |

之前 [REMAINING_SYSCALLS.md](REMAINING_SYSCALLS.md) 只统计 BSD，文末提了一句 Mach——**不够，Mach trap 必须单独登录**。本文即该账本。

> Day 66 起正文标签里的 **Mach trap** = 走本表；若只是 BSD 实现调用了 `osfmk`，仍标 **BSD→Mach**，不算本表条目。

---

## 安全向：建议优先学（精选）

| 优先级 | 组 | 代表 trap | 为什么 |
|--------|----|-----------|--------|
| ★★★ | Task 权能 | `task_for_pid`(#45) / `task_name_for_pid`(#44) / `debug_control_port_for_pid`(#96) | 拿别的进程 task/debug port；经典安全边界 |
| ★★★ | IPC 主干 | `mach_msg_trap`(#31) / `mach_msg2_trap`(#47) / `mach_msg_overwrite_trap`(#32) | 几乎所有 Mach 服务通信 |
| ★★★ | Port 权能 | `mach_port_insert_right` / `mod_refs` / `guard`/`unguard` | 权利传递、引用、port guard |
| ★★ | Self ports | `task_self_trap` / `thread_self_trap` / `host_self_trap` / `mach_reply_port` | 认识「自己是谁」的 port 世界 |
| ★★ | VM traps | `mach_vm_allocate/map/protect/deallocate` | 与 BSD `mmap` 平行的 Mach VM 入口 |
| ★★ | Voucher | `host_create_mach_voucher` / `mach_voucher_extract_attr_recipe` | 活动/身份凭证在 IPC 上传递 |
| ★ | 信号量 | `semaphore_*` | 对照 Day 71 `__semwait_signal` |
| ★ | IOKit | `iokit_user_client_trap`(#100) | 用户态驱动通信总入口 |
| ★ | Exclaves | `_exclaves_ctl_trap`(#88) | 隔离执行环境控制（新平台） |

---

## A. VM（#10–15）

| # | 名字 | 一句话 |
|---|------|--------|
| 10 | `_kernelrpc_mach_vm_allocate_trap` | 分配虚拟内存 |
| 11 | `_kernelrpc_mach_vm_purgable_control_trap` | 可清除内存控制 |
| 12 | `_kernelrpc_mach_vm_deallocate_trap` | 释放虚拟内存 |
| 13 | `task_dyld_process_info_notify_get_trap` | dyld process info notify |
| 14 | `_kernelrpc_mach_vm_protect_trap` | 改保护位（对照 `mprotect`） |
| 15 | `_kernelrpc_mach_vm_map_trap` | 映射（对照 `mmap` 的 Mach 侧） |
| 63 | `mach_vm_reclaim_update_kernel_accounting_trap` | reclaim 记账更新（LP64） |

---

## B. Port 权能（#16–25, #40–42, #76–77）★★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 16 | `_kernelrpc_mach_port_allocate_trap` | 分配 port 名 |
| 18 | `_kernelrpc_mach_port_deallocate_trap` | 释放 port 名/权利 |
| 19 | `_kernelrpc_mach_port_mod_refs_trap` | 改 user/send 引用计数 |
| 20 | `_kernelrpc_mach_port_move_member_trap` | 端口集移入成员 |
| 21 | `_kernelrpc_mach_port_insert_right_trap` | **插入权利**（安全核心） |
| 22 | `_kernelrpc_mach_port_insert_member_trap` | 插入端口集成员 |
| 23 | `_kernelrpc_mach_port_extract_member_trap` | 抽出成员 |
| 24 | `_kernelrpc_mach_port_construct_trap` | 构造 port |
| 25 | `_kernelrpc_mach_port_destruct_trap` | 析构 port |
| 40 | `_kernelrpc_mach_port_get_attributes_trap` | 读 port 属性 |
| 41 | `_kernelrpc_mach_port_guard_trap` | **port guard**（防误用） |
| 42 | `_kernelrpc_mach_port_unguard_trap` | 去 guard |
| 76 | `_kernelrpc_mach_port_type_trap` | 查 port 类型 |
| 77 | `_kernelrpc_mach_port_request_notification_trap` | 请求 port 通知 |

---

## C. Self / Host ports（#26–29, #50）

| # | 名字 | 一句话 |
|---|------|--------|
| 26 | `mach_reply_port` | 当前线程 reply port |
| 27 | `thread_self_trap` | 当前 thread port |
| 28 | `task_self_trap` | 当前 task port |
| 29 | `host_self_trap` | host port |
| 50 | `thread_get_special_reply_port` | 特殊 reply port |

---

## D. Mach 消息（#31–32, #47）★★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 31 | `mach_msg_trap` | **Mach IPC 主入口** |
| 32 | `mach_msg_overwrite_trap` | 带 overwrite 的 msg |
| 47 | `mach_msg2_trap` | 新版 mach_msg2（LP64/arm64） |

---

## E. 信号量（#33–39）— 对照 Day 71

| # | 名字 | 一句话 |
|---|------|--------|
| 33 | `semaphore_signal_trap` | 释放信号量 |
| 34 | `semaphore_signal_all_trap` | 全醒 |
| 35 | `semaphore_signal_thread_trap` | 定向唤醒线程 |
| 36 | `semaphore_wait_trap` | 等待 |
| 37 | `semaphore_wait_signal_trap` | wait + signal 另一把 |
| 38 | `semaphore_timedwait_trap` | 超时等待 |
| 39 | `semaphore_timedwait_signal_trap` | 超时 wait+signal |

BSD `__semwait_signal` 底下常落到这组。

---

## F. Task↔PID（#44–46, #96）★★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 44 | `task_name_for_pid` | pid → task **name** port（权限较弱） |
| 45 | `task_for_pid` | pid → task port（**强权能**；受 SIP/AMFI/策略限制） |
| 46 | `pid_for_task` | task → pid |
| 96 | `debug_control_port_for_pid` | pid → debug control port |

对照 BSD：`task_inspect_for_pid` / `task_read_for_pid`（`sysent`）是更细分的权能变体。

---

## G. 调度 / 时间 / Timer

| # | 名字 | 一句话 |
|---|------|--------|
| 43 | `mach_generate_activity_id` | 生成 activity id |
| 58 | `pfz_exit` | preemptible function zone 退出 |
| 59 | `swtch_pri` | 带优先级提示的让出 |
| 60 | `swtch` | 让出 CPU |
| 61 | `thread_switch` | 线程切换/handoff |
| 62 | `clock_sleep_trap` | 睡到某时刻 |
| 89 | `mach_timebase_info_trap` | timebase 信息 |
| 90 | `mach_wait_until_trap` | 等到绝对时间 |
| 91–95 | `mk_timer_*` | Mach 内核定时器 create/destroy/arm/cancel |

---

## H. Voucher（#70, #72）★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 70 | `host_create_mach_voucher_trap` | 创建 Mach voucher |
| 72 | `mach_voucher_extract_attr_recipe_trap` | 抽取 voucher 属性 recipe |

---

## I. macx / 交换 / backing store（遗留味）

| # | 名字 | 一句话 |
|---|------|--------|
| 48 | `macx_swapon` | 交换开启类（macx） |
| 49 | `macx_swapoff` | 交换关闭 |
| 51 | `macx_triggers` | macx 触发 |
| 52–53 | `macx_backing_store_*` | backing store 挂起/恢复 |

---

## J. IOKit / Exclaves / 其它

| # | 名字 | 一句话 |
|---|------|--------|
| 88 | `_exclaves_ctl_trap` | Exclave 控制 |
| 100 | `iokit_user_client_trap` | **IOKit user client** 统一 trap |
| 101–127 | （多 `kern_invalid` / 保留） | 空槽或保留 |

---

## 建议学习顺序（Mach 安全主线）

1. **Self ports** → 知道 task/thread/host/reply  
2. **mach_msg / mach_msg2** → IPC 怎么进内核  
3. **port rights + guard** → 权利模型  
4. **task_for_pid 族** → 跨进程权能与现代限制  
5. **VM traps** → 与 BSD mmap 对照  
6. **voucher / semaphore / IOKit** → 按需  

可在每日计划中另开「Mach 周」，与 BSD Day 并行或插在安全专题后。

---

## 和维护

- 权威表：`xnu/osfmk/kern/syscall_sw.c`  
- 与 BSD 剩余表交叉：[REMAINING_SYSCALLS.md](REMAINING_SYSCALLS.md)  
- 学完某 trap 后，可在每日正文总表标 **Mach trap** 并链到本文编号
