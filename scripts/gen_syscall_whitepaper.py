#!/usr/bin/env python3
"""Generate docs/SYSCALL_SECURITY_WHITEPAPER.md from xnu tables."""
from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_bsd() -> dict[int, str]:
    bsd: dict[int, str] = {}
    for line in (ROOT / "xnu/bsd/kern/syscalls.master").read_text(errors="replace").splitlines():
        line = line.split(";")[0].strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(
            r"^(\d+)\s+\S+\s+\S+\s+\{\s*(?:[^}]*?\s)?([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            line,
        )
        if not m:
            continue
        num, name = int(m.group(1)), m.group(2)
        if name in ("nosys", "enosys"):
            continue
        bsd[num] = name
    return bsd


def load_mach() -> dict[int, str]:
    mach: dict[int, str] = {}
    text = (ROOT / "xnu/osfmk/kern/syscall_sw.c").read_text(errors="replace")
    for m in re.finditer(r"/\*\s*(\d+)\s*\*/\s*MACH_TRAP\(([A-Za-z_][A-Za-z0-9_]*)", text):
        num, name = int(m.group(1)), m.group(2)
        if name != "kern_invalid":
            mach[num] = name
    return mach


EXTRA = {
    "task_for_pid": "pid→task port（强权能）",
    "task_name_for_pid": "pid→task name port",
    "debug_control_port_for_pid": "pid→debug control port",
    "pid_for_task": "task→pid",
    "mach_msg_trap": "Mach IPC 主入口",
    "mach_msg2_trap": "Mach IPC（msg2）",
    "mach_msg_overwrite_trap": "Mach IPC overwrite",
    "ptrace": "调试器附着/控制",
    "csops": "代码签名操作",
    "csops_audittoken": "带 audit_token 的 csops",
    "chroot": "切换根目录",
    "getentropy": "密码学熵",
    "__mac_syscall": "MAC 策略通用调用",
    "audit": "写审计记录",
    "persona": "进程 persona",
    "guarded_open_np": "带 guard 打开 FD",
    "necp_open": "NECP 客户端打开",
    "ulock_wait": "用户锁等待（futex 类）",
    "ulock_wake": "用户锁唤醒",
    "mmap": "映射内存",
    "mprotect": "改映射保护",
    "openat": "相对 dirfd 打开",
    "posix_spawn": "创建并执行",
    "execve": "装载新映像",
    "setuid": "设 real/effective uid",
    "issetugid": "是否经历过提权/降权敏感路径",
    "proc_info": "进程信息查询 SPI",
    "workq_kernreturn": "workqueue 内核返回/调度",
    "bsdthread_create": "pthread_create 内核路径",
    "iokit_user_client_trap": "IOKit user client",
    "_exclaves_ctl_trap": "Exclave 控制",
    "_kernelrpc_mach_port_insert_right_trap": "插入 port 权利",
    "_kernelrpc_mach_port_guard_trap": "port guard",
    "host_create_mach_voucher_trap": "创建 Mach voucher",
    "task_self_trap": "当前 task port",
    "thread_self_trap": "当前 thread port",
}


def classify_bsd(name: str) -> tuple[str, str, str, str]:
    n = name
    sec = "-"

    if n.endswith("_nocancel") or n.endswith("nocancel"):
        return ("Z-nocancel", "Nocancel 变体", "-", "与可取消版同语义")

    high_names = {
        "csops",
        "csops_audittoken",
        "persona",
        "setprivexec",
        "kas_info",
        "identitysvc",
        "chroot",
        "ptrace",
        "pivot_root",
        "getentropy",
        "mremap_encrypted",
        "map_with_linking_np",
        "system_override",
        "usrctl",
        "setsgroups",
        "getsgroups",
        "setwgroups",
        "getwgroups",
        "setuid",
        "seteuid",
        "setgid",
        "setegid",
        "setreuid",
        "setregid",
        "setgroups",
        "initgroups",
        "sys_settid",
        "gettid",
        "sys_settid_with_pid",
        "setlogin",
        "getlogin",
        "revoke",
        "acct",
        "task_inspect_for_pid",
        "task_read_for_pid",
        "terminate_with_payload",
        "abort_with_payload",
        "proc_uuid_policy",
        "shared_region_map_and_slide_2_np",
        "shared_region_check_np",
        "debug_syscall_reject",
        "sys_debug_syscall_reject_config",
        "getauid",
        "setauid",
        "issetugid",
        "csrctl",
    }
    if (
        n.startswith("__mac_")
        or "audit" in n
        or n.startswith("necp_")
        or "guarded_" in n
        or "fileport" in n
        or n.endswith("_extended")
        or "dprotected" in n
        or n in high_names
        or n.startswith("memorystatus")
        or n.startswith("pid_suspend")
        or n.startswith("pid_resume")
        or n.startswith("pid_hibernate")
        or n.startswith("pid_shutdown")
        or n.startswith("coalition")
    ):
        sec = "H"

    med_names = {
        "proc_info",
        "workq_open",
        "workq_kernreturn",
        "bsdthread_ctl",
        "bsdthread_create",
        "bsdthread_terminate",
        "bsdthread_register",
        "ledger",
        "process_policy",
        "iopolicysys",
        "ulock_wait",
        "ulock_wake",
        "sys_ulock_wait2",
        "mmap",
        "mprotect",
        "munmap",
        "shm_open",
        "shm_unlink",
        "fork",
        "vfork",
        "execve",
        "posix_spawn",
        "kill",
        "open",
        "openat",
        "chmod",
        "chown",
        "unlink",
        "rename",
        "ioctl",
        "setsockopt",
        "getsockopt",
        "sendmsg",
        "recvmsg",
        "accept",
        "connect",
        "socket",
    }
    if sec != "H" and (
        n in med_names
        or n.startswith("proc_")
        or n.startswith("psynch_")
        or n.startswith("bsdthread")
        or n.startswith("workq_")
        or n.startswith("shm")
        or n.startswith("sem")
        or n.startswith("msg")
        or "cancel" in n
    ):
        sec = "M"

    process = {
        "getpid",
        "getppid",
        "getpgrp",
        "getpgid",
        "setpgid",
        "setsid",
        "getsid",
        "fork",
        "vfork",
        "exit",
        "wait4",
        "waitid",
        "execve",
        "posix_spawn",
        "kill",
        "__pthread_kill",
        "proc_info",
        "proc_rlimit_control",
        "proc_trace_log",
        "proc_uuid_policy",
        "pid_suspend",
        "pid_resume",
        "pid_hibernate",
        "pid_shutdown_sockets",
        "terminate_with_payload",
        "abort_with_payload",
        "os_fault_with_payload",
        "sys_panic_with_data",
        "getpriority",
        "setpriority",
        "getrlimit",
        "setrlimit",
        "getrusage",
        "issetugid",
        "reboot",
        "persona",
    }
    if (
        n in process
        or n.startswith("coalition")
        or n.startswith("memorystatus")
        or n.startswith("pid_")
    ):
        if sec == "-":
            sec = (
                "H"
                if n
                in {
                    "kill",
                    "execve",
                    "posix_spawn",
                    "proc_info",
                    "issetugid",
                    "persona",
                }
                or n.startswith("pid_")
                or n.startswith("memorystatus")
                or n.startswith("coalition")
                else "M"
                if n in {"fork", "wait4", "getrlimit", "setrlimit", "vfork"}
                else "-"
            )
        return ("A-process", "进程 / 作业控制 / Jetsam", sec, "进程生命周期与控制")

    cred = {
        "getuid",
        "geteuid",
        "getgid",
        "getegid",
        "getgroups",
        "setgroups",
        "initgroups",
        "setuid",
        "seteuid",
        "setgid",
        "setegid",
        "setreuid",
        "setregid",
        "sys_settid",
        "gettid",
        "sys_settid_with_pid",
        "getlogin",
        "setlogin",
        "setsgroups",
        "getsgroups",
        "setwgroups",
        "getwgroups",
        "identitysvc",
        "setprivexec",
        "getauid",
        "setauid",
    }
    if n in cred or "audit" in n:
        return ("B-cred-audit", "凭证 / 身份 / Audit", "H", "身份与审计")

    if (
        n.startswith("__mac_")
        or n in {"csops", "csops_audittoken", "csrctl", "kas_info", "system_override", "usrctl"}
        or n.startswith("sfi_")
        or n in {"iopolicysys", "process_policy"}
    ):
        s = "H" if n.startswith("__mac_") or n.startswith("csops") or n in {"csrctl", "kas_info"} else "M"
        return ("C-mac-policy", "MAC / 代码签名 / 系统策略", s, "强制访问控制与策略")

    if "guarded_" in n or "fileport" in n or n in {"task_inspect_for_pid", "task_read_for_pid"}:
        return ("D-capability", "FD Guard / Fileport / Task 权能", "H", "权能与句柄安全")

    if (
        n.startswith("necp_")
        or n.startswith("__nexus_")
        or n.startswith("__channel_")
        or n
        in {
            "connectx",
            "disconnectx",
            "peeloff",
            "socket_delegate",
            "recvmsg_x",
            "sendmsg_x",
            "netagent_trigger",
            "net_qos_guideline",
            "socket",
            "bind",
            "listen",
            "accept",
            "connect",
            "socketpair",
            "sendto",
            "recvfrom",
            "sendmsg",
            "recvmsg",
            "shutdown",
            "getsockname",
            "getpeername",
            "getsockopt",
            "setsockopt",
            "sendfile",
        }
    ):
        s = "H" if n.startswith("necp_") else ("M" if sec == "-" else sec)
        if sec == "H":
            s = "H"
        return ("E-net", "网络 / NECP / Skywalk", s, "网络与策略")

    file_names = {
        "open",
        "openat",
        "close",
        "read",
        "write",
        "pread",
        "pwrite",
        "lseek",
        "dup",
        "dup2",
        "pipe",
        "fcntl",
        "flock",
        "fsync",
        "fdatasync",
        "ioctl",
        "access",
        "faccessat",
        "stat",
        "fstat",
        "lstat",
        "fstatat",
        "fstat64",
        "stat64",
        "lstat64",
        "mkdir",
        "mkdirat",
        "rmdir",
        "unlink",
        "unlinkat",
        "link",
        "linkat",
        "rename",
        "renameat",
        "renameatx_np",
        "symlink",
        "symlinkat",
        "readlink",
        "readlinkat",
        "chmod",
        "fchmod",
        "fchmodat",
        "chown",
        "fchown",
        "fchownat",
        "lchown",
        "chflags",
        "fchflags",
        "truncate",
        "ftruncate",
        "mknod",
        "mknodat",
        "mkfifo",
        "mkfifoat",
        "umask",
        "chdir",
        "fchdir",
        "chroot",
        "pathconf",
        "fpathconf",
        "getdirentries",
        "getdirentries64",
        "getdirentriesattr",
        "getattrlist",
        "fgetattrlist",
        "getattrlistbulk",
        "getattrlistat",
        "setattrlist",
        "fsetattrlist",
        "setattrlistat",
        "exchangedata",
        "copyfile",
        "clonefileat",
        "fclonefileat",
        "searchfs",
        "fsgetpath",
        "getxattr",
        "fgetxattr",
        "setxattr",
        "fsetxattr",
        "listxattr",
        "flistxattr",
        "removexattr",
        "fremovexattr",
        "fsctl",
        "ffsctl",
        "open_dprotected_np",
        "openat_dprotected_np",
        "delete",
        "undelete",
        "getfh",
        "fhopen",
        "quotactl",
        "nfssvc",
        "unmount",
        "funmount",
        "fs_snapshot",
        "vfs_purge",
        "pivot_root",
        "openbyid_np",
        "fmount",
        "graftdmg",
        "ungraftdmg",
        "sys_close",
        "sys_fcntl",
        "sys_flock",
        "sys_fstat",
        "sys_fstat64",
        "sys_fstat_extended",
        "sys_fstat64_extended",
        "sys_preadv",
        "sys_pwritev",
        "readv",
        "writev",
    }
    if (
        n in file_names
        or n.endswith("_extended")
        or "xattr" in n
        or "getattr" in n
        or "setattr" in n
        or n.startswith("getdirentries")
    ):
        s = (
            "H"
            if sec == "H" or n == "chroot" or "dprotected" in n or n.endswith("_extended") or n == "pivot_root"
            else ("M" if n in {"chmod", "chown", "open", "openat", "unlink", "rename", "ioctl"} else sec)
        )
        return ("F-file", "文件 / 路径 / VFS / 属性", s if s != "-" else "-", "文件系统与路径")

    mem = {
        "mmap",
        "munmap",
        "mprotect",
        "msync",
        "mincore",
        "madvise",
        "mlock",
        "munlock",
        "mlockall",
        "munlockall",
        "minherit",
        "shm_open",
        "shm_unlink",
        "getentropy",
        "mremap_encrypted",
        "map_with_linking_np",
        "shared_region_check_np",
        "shared_region_map_and_slide_2_np",
        "vm_pressure_monitor",
        "sys_ulock_wait2",
        "ulock_wait",
        "ulock_wake",
    }
    if n in mem or n.startswith("shm"):
        s = (
            "H"
            if n
            in {
                "getentropy",
                "mremap_encrypted",
                "map_with_linking_np",
                "shared_region_map_and_slide_2_np",
                "mprotect",
                "mmap",
            }
            or n.startswith("shm")
            else "M"
        )
        return ("G-memory", "内存 / VM / 共享区 / ulock", s, "内存与共享")

    if (
        n.startswith("psynch_")
        or n.startswith("bsdthread")
        or n.startswith("workq_")
        or n.startswith("sem_")
        or n.startswith("aio_")
        or n.startswith("semsys")
        or n.startswith("msgsys")
        or n.startswith("shmsys")
        or n
        in {
            "thread_selfid",
            "thread_selfusage",
            "thread_selfcounts",
            "__disable_threadsignal",
            "__pthread_markcancel",
            "__pthread_canceled",
            "__pthread_sigmask",
            "__sigwait",
            "__semwait_signal",
            "__semwait_signal_nocancel",
            "ledger",
            "work_interval_ctl",
            "lio_listio",
            "semctl",
            "semget",
            "semop",
            "msgctl",
            "msgget",
            "msgsnd",
            "msgrcv",
            "shmat",
            "shmctl",
            "shmdt",
            "shmget",
        }
    ):
        return ("H-thread-ipc", "线程 / pthread / workq / IPC 同步", "M" if sec == "-" else sec, "线程与同步")

    if (
        n
        in {
            "sigaction",
            "sigprocmask",
            "sigpending",
            "sigaltstack",
            "sigsuspend",
            "sigreturn",
        }
        or "sig" in n
    ):
        return ("I-signal", "信号", "M", "信号投递与掩码")

    if n in {
        "select",
        "pselect",
        "poll",
        "kevent",
        "kevent64",
        "kevent_qos",
        "kevent_id",
        "kqueue",
        "kqueue_workloop_ctl",
    }:
        return ("J-event", "事件通知 / kqueue", "M", "事件与多路复用")

    if n in {
        "gettimeofday",
        "setitimer",
        "getitimer",
        "adjtime",
        "ntp_adjtime",
        "ntp_gettime",
    }:
        return ("K-time", "时间 / 定时器", "-", "时间")

    if (
        n.startswith("kdebug")
        or n
        in {
            "sysctl",
            "sys_sysctlbyname",
            "telemetry",
            "stack_snapshot_with_config",
            "microstackshot",
            "grab_pgo_data",
            "log_data",
            "oslog_coproc",
            "oslog_coproc_reg",
            "ptrace",
            "objc_bp_assist_cfg_np",
            "sys_record_system_event",
            "tracker_action",
        }
        or "trace" in n
        or "snapshot" in n
        or "debug" in n
    ):
        s = "H" if n == "ptrace" or "debug_syscall" in n else "M"
        return ("L-debug", "调试 / 追踪 / sysctl / 遥测", s, "可观测与调试")

    return ("Y-misc", "杂项 / 平台特殊", sec, "其它")


def classify_mach(name: str) -> tuple[str, str, str, str]:
    if any(
        x in name
        for x in (
            "task_for_pid",
            "task_name_for_pid",
            "debug_control",
            "pid_for_task",
        )
    ):
        return ("M-task", "Mach：Task↔PID 权能", "H", "跨进程 task port")
    if "mach_msg" in name:
        return ("M-msg", "Mach：消息 IPC", "H", "Mach IPC 主干")
    if "mach_port" in name or name in {
        "mach_reply_port",
        "thread_self_trap",
        "task_self_trap",
        "host_self_trap",
        "thread_get_special_reply_port",
    }:
        s = (
            "H"
            if any(x in name for x in ("insert_right", "guard", "mod_refs", "construct", "destruct"))
            else "M"
        )
        return ("M-port", "Mach：Port 权能", s, "port 权利模型")
    if "mach_vm" in name or "dyld_process" in name or "reclaim" in name:
        s = "H" if ("protect" in name or "map" in name or "allocate" in name) else "M"
        return ("M-vm", "Mach：VM", s, "Mach VM")
    if "semaphore" in name:
        return ("M-sem", "Mach：信号量", "M", "Mach semaphore")
    if "voucher" in name:
        return ("M-voucher", "Mach：Voucher", "H", "IPC 凭证")
    if "iokit" in name:
        return ("M-iokit", "Mach：IOKit", "H", "驱动 user client")
    if "exclaves" in name:
        return ("M-exclave", "Mach：Exclaves", "H", "隔离执行环境")
    if name.startswith("macx_"):
        return ("M-macx", "Mach：macx / swap", "M", "遗留 macx")
    if any(
        x in name
        for x in (
            "timer",
            "timebase",
            "wait_until",
            "clock_sleep",
            "swtch",
            "thread_switch",
            "pfz_exit",
            "activity_id",
        )
    ):
        return ("M-sched", "Mach：调度 / 时间 / Timer", "-", "调度与时间")
    return ("M-misc", "Mach：其它", "M", "其它 trap")


def sec_label(sec: str) -> str:
    return {"H": "**SEC-H**", "M": "SEC-M", "-": "—"}.get(sec, sec)


def main() -> None:
    bsd = load_bsd()
    mach = load_mach()

    rows_bsd = []
    for num, name in sorted(bsd.items()):
        ch, title, sec, default_blurb = classify_bsd(name)
        blurb = EXTRA.get(name, default_blurb)
        rows_bsd.append((ch, title, sec, num, name, blurb))

    rows_mach = []
    for num, name in sorted(mach.items()):
        ch, title, sec, default_blurb = classify_mach(name)
        blurb = EXTRA.get(name, default_blurb)
        rows_mach.append((ch, title, sec, num, name, blurb))

    out: list[str] = []
    out += [
        "# XNU 系统调用安全白皮书（BSD + Mach Trap）",
        "",
        f"> 版本基准：`xnu-12377.121.6`  ",
        f"> 覆盖：**全部有效 BSD syscall（{len(bsd)}）** + **全部有效 Mach trap（{len(mach)}，不含 `kern_invalid`）**  ",
        "> 生成脚本：[`scripts/gen_syscall_whitepaper.py`](../scripts/gen_syscall_whitepaper.py)  ",
        "> 配套 Demo：[`demos/whitepaper/`](../demos/whitepaper/)  ",
        "> 相关：[REMAINING_SYSCALLS.md](REMAINING_SYSCALLS.md) · [MACH_TRAPS.md](MACH_TRAPS.md)",
        "",
        "---",
        "",
        "## 0. 阅读指南",
        "",
        "| 标记 | 含义 |",
        "|------|------|",
        "| **SEC-H** | 安全核心：身份、MAC、审计、权能、跨进程、沙箱/策略 |",
        "| **SEC-M** | 安全相关：影响隔离/资源/同步边界 |",
        "| **—** | 常规功能 |",
        "",
        "```text",
        "用户态",
        " ├─ BSD syscall  → sysent            （xnu/bsd/kern/syscalls.master）",
        " └─ Mach trap    → mach_trap_table  （xnu/osfmk/kern/syscall_sw.c）",
        "```",
        "",
        "**安全主线：** 凭证/Audit → MAC/csops → Mach task/port → Guarded FD/fileport → 内存/共享区 → NECP → Jetsam/coalition → 其余。",
        "",
        "Demo 说明：能在 Linux CI 跑通的用可移植 POSIX；Darwin 专用 API 放在 `*_darwin.c`（`#ifdef __APPLE__`）。",
        "无法用户态直接调用的私有 syscall/trap，用「同族可移植包装」或注释说明对应关系。",
        "",
        "---",
        "",
        "## 1. 安全重点抽提（SEC-H）",
        "",
        "### 1.1 BSD SEC-H",
        "",
        "| # | 名字 | 分组 | 一句话 |",
        "|---|------|------|--------|",
    ]
    for ch, title, sec, num, name, blurb in rows_bsd:
        if sec == "H":
            out.append(f"| {num} | `{name}` | {title} | {blurb} |")

    out += [
        "",
        "### 1.2 Mach Trap SEC-H",
        "",
        "| # | 名字 | 分组 | 一句话 |",
        "|---|------|------|--------|",
    ]
    for ch, title, sec, num, name, blurb in rows_mach:
        if sec == "H":
            out.append(f"| {num} | `{name}` | {title} | {blurb} |")

    out += ["", "---", "", "## 2. BSD：按主题完整目录", ""]

    groups: OrderedDict[tuple[str, str], list] = OrderedDict()
    for row in rows_bsd:
        groups.setdefault((row[0], row[1]), []).append(row)

    for (ch, title), items in groups.items():
        h = sum(1 for i in items if i[2] == "H")
        m = sum(1 for i in items if i[2] == "M")
        out += [
            f"### {title}",
            "",
            f"共 **{len(items)}** · SEC-H **{h}** · SEC-M **{m}**",
            "",
            "| 安全 | # | 名字 | 一句话 |",
            "|------|---|------|--------|",
        ]
        for _, _, sec, num, name, blurb in items:
            out.append(f"| {sec_label(sec)} | {num} | `{name}` | {blurb} |")
        out.append("")

    out += ["---", "", "## 3. Mach Trap：按主题完整目录", ""]

    mgroups: OrderedDict[tuple[str, str], list] = OrderedDict()
    for row in rows_mach:
        mgroups.setdefault((row[0], row[1]), []).append(row)

    for (ch, title), items in mgroups.items():
        h = sum(1 for i in items if i[2] == "H")
        m = sum(1 for i in items if i[2] == "M")
        out += [
            f"### {title}",
            "",
            f"共 **{len(items)}** · SEC-H **{h}** · SEC-M **{m}**",
            "",
            "| 安全 | # | 名字 | 一句话 |",
            "|------|---|------|--------|",
        ]
        for _, _, sec, num, name, blurb in items:
            out.append(f"| {sec_label(sec)} | {num} | `{name}` | {blurb} |")
        out.append("")

    out += [
        "---",
        "",
        "## 4. Demo 索引",
        "",
        "| Demo | 覆盖主题 | 平台 |",
        "|------|----------|------|",
        "| [`01_process_ids.c`](../demos/whitepaper/01_process_ids.c) | 进程身份 getpid/ppid/uid/gid | 可移植 |",
        "| [`02_file_basic.c`](../demos/whitepaper/02_file_basic.c) | 文件 open/read/write/close/stat | 可移植 |",
        "| [`03_file_at.c`](../demos/whitepaper/03_file_at.c) | *at 族 openat/fstatat/unlinkat | 可移植 |",
        "| [`04_memory_mmap.c`](../demos/whitepaper/04_memory_mmap.c) | mmap/mprotect/munmap | 可移植 |",
        "| [`05_pipe_fcntl.c`](../demos/whitepaper/05_pipe_fcntl.c) | pipe/fcntl | 可移植 |",
        "| [`06_socket_udp.c`](../demos/whitepaper/06_socket_udp.c) | socket/bind/sendto/recvfrom | 可移植 |",
        "| [`07_signal_basic.c`](../demos/whitepaper/07_signal_basic.c) | sigaction/kill | 可移植 |",
        "| [`08_pthread_sync.c`](../demos/whitepaper/08_pthread_sync.c) | mutex/cond/rwlock（Darwin→psynch） | 可移植 |",
        "| [`09_pthread_cancel.c`](../demos/whitepaper/09_pthread_cancel.c) | pthread_cancel（→markcancel） | 可移植 |",
        "| [`10_time_rusage.c`](../demos/whitepaper/10_time_rusage.c) | gettimeofday/getrusage | 可移植 |",
        "| [`11_entropy.c`](../demos/whitepaper/11_entropy.c) | getentropy | 可移植* |",
        "| [`12_shm_posix.c`](../demos/whitepaper/12_shm_posix.c) | shm_open/mmap | 可移植 |",
        "| [`13_spawn_wait.c`](../demos/whitepaper/13_spawn_wait.c) | posix_spawn/wait | 可移植 |",
        "| [`14_event_poll.c`](../demos/whitepaper/14_event_poll.c) | poll | 可移植 |",
        "| [`20_mach_self_ports.c`](../demos/whitepaper/20_mach_self_ports.c) | task/thread/host self traps | Darwin |",
        "| [`21_mach_vm.c`](../demos/whitepaper/21_mach_vm.c) | mach_vm_allocate/protect/deallocate | Darwin |",
        "| [`22_mach_msg_bootstrap.c`](../demos/whitepaper/22_mach_msg_bootstrap.c) | mach_msg 探测 bootstrap | Darwin |",
        "| [`23_csops_darwin.c`](../demos/whitepaper/23_csops_darwin.c) | csops 状态位 | Darwin |",
        "",
        "```bash",
        "cd demos/whitepaper && make check          # 可移植 Demo",
        "cd demos/whitepaper && make check-darwin  # 仅 macOS",
        "```",
        "",
        "---",
        "",
        "## 5. 统计",
        "",
        f"- BSD 有效条目：**{len(bsd)}**",
        f"- Mach 有效 trap：**{len(mach)}**",
        f"- BSD SEC-H：**{sum(1 for r in rows_bsd if r[2]=='H')}**",
        f"- Mach SEC-H：**{sum(1 for r in rows_mach if r[2]=='H')}**",
        "",
        "重新生成：",
        "",
        "```bash",
        "python3 scripts/gen_syscall_whitepaper.py",
        "```",
        "",
    ]

    dest = ROOT / "docs/SYSCALL_SECURITY_WHITEPAPER.md"
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {dest} ({len(bsd)} bsd, {len(mach)} mach)")


if __name__ == "__main__":
    main()
