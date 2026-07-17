# 剩余 BSD Syscall 地图（学完 Day 71 后）

基于 `xnu/` = **xnu-12377.121.6** 的 `syscalls.master`。  
统计口径：有效入口（去掉 `nosys`/`enosys`）约 **455**；已覆盖约 **245**（含计划中的 Day 72）；**本文约 210 个未学**。

> 不含 Mach trap 表（那是另一套入口）。  
> `*_nocancel` 与可取消版语义几乎相同，单独成组，学习时可扫尾。

---

## 安全向：建议优先学（精选）

按「看安全机制 / 权限边界 / 沙箱与审计」价值排序，不是攻击教程。

| 优先级 | 组 | 代表调用 | 为什么值得学 |
|--------|----|----------|--------------|
| ★★★ | MAC | `__mac_syscall` / `__mac_get_*` / `__mac_set_*` / `__mac_execve` / `__mac_mount` | 强制访问控制钩子；沙箱/AMFI 相关策略入口 |
| ★★★ | Audit | `audit` / `auditon` / `auditctl` / `getaudit_addr` / `setaudit_addr` / `audit_session_*` | 安全记账与会话；谁做了什么 |
| ★★★ | Persona / 身份 | `persona` / `sys_settid_with_pid`(Day72) / `setsgroups`/`getsgroups` / `setwgroups`/`getwgroups` / `identitysvc` | 身份切换、多身份、扩展组解析 |
| ★★★ | 代码/进程检查延伸 | `task_inspect_for_pid` / `task_read_for_pid` / `kas_info` / `setprivexec` | 跨进程 task 权能、内核地址信息、特权 exec |
| ★★ | Guarded FD | `guarded_open_np` / `guarded_close_np` / `change_fdguard_np` / `guarded_*` | FD 防误关/防劫持；安全工程常用 |
| ★★ | Fileport | `sys_fileport_makeport` / `sys_fileport_makefd` | FD ↔ Mach port；跨任务传文件权能 |
| ★★ | ACL/扩展属性权限 | `chmod_extended` / `fchmod_extended` / `*_extended` / `open_dprotected_np` | ACL、数据保护类打开 |
| ★★ | 内存/镜像完整性 | `mremap_encrypted` / `map_with_linking_np` / `shared_region_map_and_slide_2_np` / `getentropy` | 加密映射、共享区 slide、熵源 |
| ★★ | 网络策略 | `necp_*` / `proc_uuid_policy` | 每应用网络策略、UUID 策略 |
| ★★ | 进程生命周期管控 | `pid_suspend`/`resume`/`hibernate` / `memorystatus_*` / `terminate_with_payload` / `abort_with_payload` | Jetsam/挂起/带理由终止 |
| ★ | Coalition / 覆盖 | `coalition*` / `system_override` / `usrctl` / `sfi_*` | 进程联盟、系统级覆盖、SFI |
| ★ | 调试与拒绝 | `debug_syscall_reject*` / `stack_snapshot*` / `proc_trace_log` | 系统调用拒绝、栈快照、追踪 |
| ★ | 根枢纽 | `pivot_root` / `fs_snapshot` / `graftdmg`/`ungraftdmg` | 根切换、快照、DMG 挂载相关 |

已学且安全向很重要、可对照复习：`ptrace`、`csops*`、`chroot`、`setuid*`、`ulock`、`proc_info`、凭证/会话族。

---

## A. `*_nocancel` 族（约 32 个）— 扫尾即可

与已学同名调用相同，只是**不是 pthread 取消点**（或走 nocancel 入口）。

| # | 名字 | 一句话 |
|---|------|--------|
| 395 | pselect_nocancel | `pselect` 无取消 |
| 396–399 | read/write/open/close_nocancel | 基础 IO 无取消 |
| 400 | wait4_nocancel | wait 无取消 |
| 401–403 | recvmsg/sendmsg/recvfrom_nocancel | 套接字收发无取消 |
| 405–409 | msync/fcntl/select/fsync/connect_nocancel | 杂项无取消 |
| 410 | sigsuspend_nocancel | 信号挂起无取消 |
| 411–415 | readv/writev/sendto/pread/pwrite_nocancel | 向量/定位 IO 无取消 |
| 416–417 | waitid/poll_nocancel | 等待/轮询无取消 |
| 418–420 | msgsnd/msgrcv/sem_wait_nocancel | IPC/信号量无取消 |
| 421–422 | aio_suspend/__sigwait_nocancel | AIO/sigwait 无取消 |
| 464 | openat_nocancel | openat 无取消 |
| 542–543 | preadv/pwritev_nocancel | 向量定位 IO 无取消 |

---

## B. 信号 / 定时器 / 时间

| # | 名字 | 一句话 |
|---|------|--------|
| 83 | setitimer | 设间隔定时器 |
| 86 | getitimer | 读间隔定时器 |
| 111 | sigsuspend | 原子换掩码并挂起等信号 |
| 184 | sigreturn | 从信号上下文返回（平台相关） |
| 140 | adjtime | 平滑校正系统时间 |
| 527 | ntp_adjtime | NTP 调时 |
| 528 | ntp_gettime | NTP 读时 |
| 329 | __pthread_sigmask | 线程信号掩码 |
| 330 | __sigwait | 等待信号集中的信号 |

---

## C. IO 向量 / 杂项文件

| # | 名字 | 一句话 |
|---|------|--------|
| 120 | readv | 分散读 |
| 121 | writev | 聚集写 |
| 540 | sys_preadv | 定位分散读 |
| 541 | sys_pwritev | 定位聚集写 |
| 173 | waitid | 更细的子进程等待 |
| 205 | undelete | 恢复已删（旧/特殊 FS） |
| 226 | delete | 删除路径（Carbon 遗留风格） |
| 161 | getfh | 取文件句柄（NFS 类） |
| 165 | quotactl | 磁盘配额 |
| 155 | nfssvc | NFS 服务控制 |
| 479 | openbyid_np | 按文件系统 id 打开 |
| 518 | fs_snapshot | APFS 等快照操作 |
| 455 | vfs_purge | 丢弃 VFS 缓存 |
| 537 | pivot_root | 切换根文件系统 |

---

## D. 数据保护 / ACL「extended」族  ★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 216 | open_dprotected_np | 带数据保护类打开 |
| 218 | openat_dprotected_np | dirfd + 数据保护打开 |
| 277 | open_extended | 扩展打开（含 ACL 等） |
| 278 | umask_extended | 扩展 umask |
| 279–281 | stat/lstat/fstat_extended | 带扩展安全信息的 stat |
| 282–283 | chmod/fchmod_extended | 设 ACL/扩展权限 |
| 291–292 | mkfifo/mkdir_extended | 创建时带扩展安全信息 |
| 341–343 | *stat64_extended | 64 位扩展 stat |

---

## E. SysV IPC / POSIX 信号量（剩余）

| # | 名字 | 一句话 |
|---|------|--------|
| 251–253 | semsys/msgsys/shmsys | 旧多路复用入口 |
| 254–255 | semctl/semget | SysV 信号量 |
| 258–259 | msgctl/msgget | SysV 消息队列 |
| 261 | msgrcv | 收消息（msgsnd 若已覆盖可对照） |
| 262–265 | shmat/shmctl/shmdt/shmget | SysV 共享内存 |
| 272–273 | sem_trywait/sem_post | POSIX 信号量试等/释放 |

---

## F. AIO（异步 IO）

| # | 名字 | 一句话 |
|---|------|--------|
| 314 | aio_return | 取异步结果 |
| 315 | aio_suspend | 等异步完成 |
| 316 | aio_cancel | 取消异步请求 |
| 317 | aio_error | 查异步错误 |
| 320 | lio_listio | 批量异步列表 |

（`aio_fsync` / `aio_read` / `aio_write` 若已在别日覆盖，对照即可。）

---

## G. MAC（强制访问控制）★★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 380 | __mac_execve | 带 MAC 标签的 exec |
| 381 | __mac_syscall | MAC 策略通用调用 |
| 382–385 | __mac_get/set_file/link | 文件/符号链接 MAC 标签 |
| 386–387 | __mac_get/set_proc | 进程 MAC 标签 |
| 388–389 | __mac_get/set_fd | FD 上 MAC 标签 |
| 390 | __mac_get_pid | 按 pid 取 MAC |
| 424 | __mac_mount | 带 MAC 的 mount |
| 425–426 | __mac_get_mount / __mac_getfsstat | 挂载点 MAC / fsstat |

---

## H. Audit（审计）★★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 350 | audit | 写审计记录 |
| 351 | auditon | 审计子系统控制 |
| 357–358 | getaudit_addr / setaudit_addr | 读/设审计身份（含地址） |
| 359 | auditctl | 审计控制设备 |
| 428 | audit_session_self | 本审计会话 port |
| 429 | audit_session_join | 加入审计会话 |
| 432 | audit_session_port | 审计会话 port 操作 |

Day 72 计划：`getauid` / `setauid`。

---

## I. 身份 / 组解析 / Persona ★★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 287–288 | setsgroups / getsgroups | 补充 GUID 组集 |
| 289–290 | setwgroups / getwgroups | 工作组 GUID 集 |
| 293 | identitysvc | 身份解析服务（扩展组等） |
| 494 | persona | 进程 persona（多用户身份容器） |
| 152 | setprivexec | 特权 exec 相关标志 |

---

## J. pthread / kqueue 边角

| # | 名字 | 一句话 |
|---|------|--------|
| 375 | kevent_id | 按 id 的 kevent（workloop 相关） |
| 530 | kqueue_workloop_ctl | workloop 控制 |
| 544 | sys_ulock_wait2 | ulock_wait 扩展版（对照 Day 66） |
| 186 | thread_selfcounts | 线程计数类信息 |
| 499 | work_interval_ctl | work interval（功耗/调度提示） |
| 496–498 | mach_eventlink_* | Mach eventlink 信号/等待 |

---

## K. Guarded FD / Fileport ★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 441 | guarded_open_np | 带 guard 的 open |
| 442 | guarded_close_np | 校验 guard 再 close |
| 443 | guarded_kqueue_np | 带 guard 的 kqueue |
| 444 | change_fdguard_np | 改 FD guard |
| 484 | guarded_open_dprotected_np | guard + 数据保护打开 |
| 485–487 | guarded_write/pwrite/writev_np | 带 guard 的写 |
| 430 | sys_fileport_makeport | FD → fileport |
| 431 | sys_fileport_makefd | fileport → FD |

---

## L. 进程控制 / Jetsam / Coalition ★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 433–436 | pid_suspend/resume/hibernate/shutdown_sockets | 挂起/恢复/休眠/关套接字 |
| 440 | memorystatus_control | Jetsam/内存状态控制 |
| 453 | memorystatus_get_level | 内存压力级别 |
| 534 | memorystatus_available_memory | 可用内存查询 |
| 446 | proc_rlimit_control | 进程 rlimit 扩展控制 |
| 452 | proc_uuid_policy | 按进程 UUID 的策略 |
| 458–459 | coalition / coalition_info | 进程联盟 |
| 532 | coalition_ledger | 联盟 ledger |
| 556–557 | coalition_policy_set/get | 联盟策略 |
| 520–521 | terminate/abort_with_payload | 带 payload 终止/中止 |
| 529 | os_fault_with_data | 故障上报类 |
| 185 | sys_panic_with_data | 带数据 panic（调试/诊断） |

---

## M. 网络扩展：connectx / NECP / Skywalk ★★安全（NECP）

| # | 名字 | 一句话 |
|---|------|--------|
| 447 | connectx | 扩展 connect（多路径等） |
| 448 | disconnectx | 扩展断开 |
| 449 | peeloff | 从关联连接剥离套接字 |
| 450 | socket_delegate | 套接字委托 |
| 480–481 | recvmsg_x / sendmsg_x | 扩展消息收发 |
| 525 | net_qos_guideline | 网络 QoS 指引 |
| 460 | necp_match_policy | 匹配 NECP 策略 |
| 501–502 | necp_open / necp_client_action | NECP 客户端 |
| 522–523 | necp_session_open / action | NECP 会话 |
| 490 | netagent_trigger | 网络 agent 触发 |
| 503–509 | __nexus_* | Skywalk nexus |
| 510–514 | __channel_* | Skywalk channel |

---

## N. 内存 / 共享区 / 熵 / 映射 ★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 489 | mremap_encrypted | 加密区域重映射 |
| 500 | getentropy | 密码学安全熵 |
| 536 | shared_region_map_and_slide_2_np | dyld 共享缓存映射/slide |
| 550 | map_with_linking_np | 带链接信息的映射 |
| 294 | shared_region_check_np | （Day 72）共享区检查 |
| 296 | vm_pressure_monitor | （Day 72）内存压力监视 |

---

## O. 可观测性 / 调试 / 遥测

| # | 名字 | 一句话 |
|---|------|--------|
| 177–180 | kdebug_typefilter/trace* | kdebug 追踪 |
| 274 | sys_sysctlbyname | 按名字 sysctl |
| 451 | telemetry | 遥测 |
| 477 | proc_trace_log | 进程追踪日志 |
| 491 | stack_snapshot_with_config | 栈快照 |
| 492 | microstackshot | 微栈快照 |
| 493 | grab_pgo_data | PGO 数据 |
| 533 | log_data | 日志数据通道 |
| 67–68 | oslog_coproc* | 协处理器侧日志 |
| 547–548 | debug_syscall_reject* | 调试：拒绝某些 syscall |
| 552 | sys_record_system_event | 记录系统事件 |
| 535 | objc_bp_assist_cfg_np | ObjC 断点辅助 |

---

## P. Task 权能 / 内核信息 ★★★安全

| # | 名字 | 一句话 |
|---|------|--------|
| 538 | task_inspect_for_pid | 按 pid 取 inspect 权 task port |
| 539 | task_read_for_pid | 按 pid 取 read 权 task port |
| 439 | kas_info | 内核地址空间相关信息（受控） |
| 531 | __mach_bridge_remote_time | 桥接远程时间 |
| 38 | sys_crossarch_trap | 跨架构陷阱相关 |

---

## Q. 系统级控制 / 其它

| # | 名字 | 一句话 |
|---|------|--------|
| 55 | reboot | 重启 |
| 445 | usrctl | 用户级控制杂项 |
| 454 | system_override | 系统行为覆盖 |
| 456–457 | sfi_ctl / sfi_pidctl | Selective Forced Idle |
| 549 / 555 | graftdmg / ungraftdmg | DMG graft 挂载相关 |
| 546 | tracker_action | tracker 动作 |

---

## 建议学习顺序（安全主线）

若目标是 **Darwin/XNU 安全机制**，剩余部分建议按周打包（每天仍 5–10 个）：

1. **Audit 周**：`audit*` + `audit_session_*` +（Day 72 auid）  
2. **MAC 周**：`__mac_*` 全组  
3. **身份周**：`persona` / sgroups/wgroups / `identitysvc` / `setprivexec`  
4. **FD 权能周**：`guarded_*` + `fileport_*` + extended ACL  
5. **Task/进程周**：`task_*_for_pid` / `kas_info` / `pid_suspend*` / `memorystatus_*`  
6. **网络策略周**：`necp_*`（Skywalk 可后置）  
7. **其余**：IPC/AIO/nocancel/遥测 按兴趣扫尾  

Mach trap（`mach_vm_*`、`task_*` trap 等）不在本表；安全向也应另开一张 trap 地图。

---

## 维护

- 每学完一天，可从对应组勾掉，或靠 `DAILY_SYSCALL_PLAN.md` 自动视为已覆盖。  
- 重新统计：对照 `syscalls.master` 与 `docs/day-*.md` / 计划表编号列。
