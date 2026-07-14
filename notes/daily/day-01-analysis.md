# 源码分析：Day 1 三个系统调用（基于 xnu-12377.121.6）

对着仓库里的 `xnu/` 实读结论，不是空泛概述。

---

## 1. 总览：一次 BSD syscall 怎么跑完

```
用户态 stub (libsyscall)
    │  把「类 + 编号」放进寄存器，执行 syscall / svc
    ▼
架构陷阱入口 (osfmk)
    │
    ▼
unix_syscall / unix_syscall64   ← BSD 分发器
    │  code = 编号 & mask
    │  callp = &sysent[code]
    │  准备 uu_arg[] / uu_rval[]
    │  error = callp->sy_call(proc, args, &rval)
    ▼
具体 handler（如 getpid）
    │  *retval = ...; return 0;
    ▼
分发器写回用户寄存器 / 设进位标志表示 errno
```

关键类型在 [`xnu/bsd/sys/sysent.h`](../xnu/bsd/sys/sysent.h)：

```c
typedef int32_t sy_call_t(struct proc *, void *, int *);

struct sysent {
    sy_call_t *sy_call;   /* 真正的实现函数 */
    int32_t    sy_return_type;
    int16_t    sy_narg;   /* 参数个数 */
    uint16_t   sy_arg_bytes;
};
```

**约定：**

- 第一个参数永远是当前 `proc_t`
- 第二个是打包好的用户参数（`uap`）
- 第三个是返回值槽 `retval`（可视为 `int32_t`/`int` 数组）
- 函数 **返回值** = 0 成功，或 errno；**给用户看的数据** 放在 `*retval`

Day 1 三个调用 `sy_narg == 0`，所以几乎不碰参数拷贝。

---

## 2. 编号从哪来

[`xnu/bsd/kern/syscalls.master`](../xnu/bsd/kern/syscalls.master)：

| 名字 | # | 行意 |
|------|---|------|
| getpid | 20 | `{ int getpid(void); }` |
| getuid | 24 | `{ int getuid(void); }` |
| getppid | 39 | `{ int getppid(void); }` |

这张表经脚本生成 `sysent[]`。你在源码树里读 master 即可；生成物是构建时产物。

x86_64 用户态还会把编号和「Unix 类」拼进 `%eax`（见 `SYSCALL_CONSTRUCT_UNIX`，[`osfmk/mach/i386/syscall_sw.h`](../xnu/osfmk/mach/i386/syscall_sw.h)）。进内核后用 `SYSCALL_NUMBER_MASK` 取出真正的 20/24/39。

---

## 3. 用户态：`getpid` 并不总是进内核

[`xnu/libsyscall/custom/__getpid.s`](../xnu/libsyscall/custom/__getpid.s)：

- 维护私有变量 `__current_pid`
- 若缓存 `> 0`：直接 `ret`，**不陷阱**
- 否则：`UNIX_SYSCALL_NONAME(getpid, …)` / `SYSCALL_NONAME(getpid, …)`，成功后再 `cmpxchg` 写回缓存

**分析要点：** `getpid` 在用户态被特化过；`fork`/`exec` 等会让缓存失效（否则子进程会读到错 PID）。学系统调用时，要以「最终会进内核的那条路径」为准，同时知道 libsyscall 可能短路。

宏定义在 [`xnu/libsyscall/custom/SYS.h`](../xnu/libsyscall/custom/SYS.h)：

- x86_64：`movl $SYSCALL_CONSTRUCT_UNIX(SYS_getpid), %eax` → `syscall`
- 失败时进位标志置位，跳到 `cerror` 填 `errno`

---

## 4. 内核分发：真正调用 `sy_call` 的那一行

### ARM（逻辑最清晰）

[`xnu/bsd/dev/arm/systemcalls.c`](../xnu/bsd/dev/arm/systemcalls.c)：

```c
syscode = (code < nsysent) ? code : SYS_invalid;
callp   = &sysent[syscode];
/* ... 参数、MACF 过滤、audit ... */
error = (*(callp->sy_call))(proc, &uthread->uu_arg[0], &(uthread->uu_rval[0]));
```

### x86_64

[`xnu/bsd/dev/i386/systemcalls.c`](../xnu/bsd/dev/i386/systemcalls.c) 的 `unix_syscall64`：

```c
code    = regs->rax & SYSCALL_NUMBER_MASK;
syscode = (code < nsysent) ? code : SYS_invalid;
callp   = &sysent[syscode];
/* sy_narg==0 时几乎不 memcpy 参数 */
error = (*(callp->sy_call))((void *) p, vt, &(uthread->uu_rval[0]));
```

成功时把 `uu_rval[0]` 写进 `%rax` 返回用户态；失败则 `%rax = errno` 且置 `EFL_CF`。

**分析要点：**

1. 越界编号 → `SYS_invalid`，不会乱跳函数指针  
2. 分发前可能过 MACF syscall filter、audit、debug rejection  
3. Day 1 三个调用 `sy_narg == 0`，分发路径上几乎没有 `copyin`

---

## 5. 三个 handler 逐行分析

全部在 [`xnu/bsd/kern/kern_prot.c`](../xnu/bsd/kern/kern_prot.c)。

### 5.1 `getpid`

```c
int
getpid(proc_t p, __unused struct getpid_args *uap, int32_t *retval)
{
	*retval = proc_getpid(p);
	return 0;
}
```

`proc_getpid` 在 [`kern_proc.c`](../xnu/bsd/kern/kern_proc.c)：

```c
pid_t
proc_getpid(proc_t p)
{
	if (p == kernproc) {
		return 0;
	}
	return p->p_pid;
}
```

- 当前进程由分发器传入，handler 不再查「我是谁」  
- 内核进程 `kernproc` 特判返回 0  
- 恒 `return 0`：对用户态而言几乎不会失败

### 5.2 `getppid`

```c
int
getppid(proc_t p, __unused struct getppid_args *uap, int32_t *retval)
{
	*retval = p->p_ppid;
	return 0;
}
```

- 直接读 `proc` 字段 `p_ppid`  
- 比 `getpid` 少一层封装；语义一样简单  
- 注意：这是「记录中的父 PID」，进程成为孤儿后可能指向 init/launchd 一类，字段仍可读

### 5.3 `getuid`

```c
int
getuid(__unused proc_t p, __unused struct getuid_args *uap, int32_t *retval)
{
	*retval = kauth_getruid();
	return 0;
}
```

凭证路径 [`kern_credential.c`](../xnu/bsd/kern/kern_credential.c)：

```c
uid_t
kauth_getruid(void)
{
	return kauth_cred_getruid(kauth_cred_get());
}

kauth_cred_t
kauth_cred_get(void)
{
	return current_thread_ro()->tro_cred;
}
```

- **不读 `p->…` 的 uid 字段**，而读当前线程只读区里的 credential  
- `getuid` = **real uid**（`getruid`）；`geteuid` 会走另一条 `kauth_getuid` / effective  
- `proc_t p` 标 `__unused`：身份在凭证子系统，不在这次传入的 proc 参数里直接取

---

## 6. 对比结论（学完 Day 1 应能复述）

| | getpid | getppid | getuid |
|--|--------|---------|--------|
| # | 20 | 39 | 24 |
| 用户参数 | 无 | 无 | 无 |
| copyin | 无 | 无 | 无 |
| 数据源 | `p->p_pid`（经 `proc_getpid`） | `p->p_ppid` | `tro_cred` → real uid |
| 子系统 | BSD `proc` | BSD `proc` | kauth 凭证 |
| 失败可能 | 实际无 | 实际无 | 实际无 |

**设计味道：**

1. BSD syscall ABI 统一成 `(proc, uap, retval)`，极简调用也遵守  
2. 「给用户的值」和「errno」分开通道，避免和负数 PID/UID 混淆  
3. 身份信息拆成 **进程标识（proc）** 与 **权限主体（cred）** 两套对象——后面学 `setuid`/`fork` 会反复碰到

---

## 7. 建议你接着在源码里点开的 4 个文件

1. `xnu/bsd/kern/syscalls.master` — 找 20/24/39  
2. `xnu/bsd/kern/kern_prot.c` — 三个 handler  
3. `xnu/bsd/dev/arm/systemcalls.c` — `unix_syscall` 里 `sy_call` 那一行  
4. `xnu/libsyscall/custom/__getpid.s` — 用户态缓存捷径  

读完这四个，Day 1 就算真正「对着源码懂了」。
