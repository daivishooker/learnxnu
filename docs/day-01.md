# 第一天（Day 1）正文

学这三个：**`getpid` / `getppid` / `getuid`**  
源码版本：`xnu/` = **xnu-12377.121.6**

> 若你在 GitHub 默认的 `main` 分支看不到本文件：内容在分支  
> `cursor/daily-syscall-plan-a8ed`（PR #3）。  
> 直接打开：  
> https://github.com/daivishooker/learnxnu/blob/cursor/daily-syscall-plan-a8ed/docs/day-01.md

---

## 今天目标

1. 在 `syscalls.master` 里找到三个编号  
2. 读到三个 handler 实现（都很短）  
3. 理解：返回值写在 `*retval`，成功返回 `0`  
4. 对比：PID 来自 `proc`，UID 来自凭证 API

预计 1–2 小时。笔记可填：[`notes/daily/day-01.md`](../notes/daily/day-01.md)

---

## 步骤 0：打开总表

文件：[`xnu/bsd/kern/syscalls.master`](../xnu/bsd/kern/syscalls.master)

| 名字 | 编号 | master 里大致长这样 |
|------|------|---------------------|
| getpid | **20** | `{ int getpid(void); }` |
| getuid | **24** | `{ int getuid(void); }` |
| getppid | **39** | `{ int getppid(void); }` |

编号就是进内核后查 `sysent[]` 用的下标。

---

## 1. getpid（#20）

### 用户态（可选看一眼）

[`xnu/libsyscall/custom/__getpid.s`](../xnu/libsyscall/custom/__getpid.s)

要点：用户态可能缓存 `__current_pid`；缓存无效时才真正 `UNIX_SYSCALL` / `SYSCALL` 进内核。

### 内核 handler（必读）

[`xnu/bsd/kern/kern_prot.c`](../xnu/bsd/kern/kern_prot.c) 约 157–162 行：

```c
int
getpid(proc_t p, __unused struct getpid_args *uap, int32_t *retval)
{
	*retval = proc_getpid(p);
	return 0;
}
```

### 调用链（最短版）

```
用户态 getpid / ___getpid
  → 陷阱进入内核
  → 按编号 20 查 sysent
  → getpid(proc, uap, retval)
  → *retval = proc_getpid(p); return 0
  → 返回用户态（PID 在返回值寄存器）
```

### 你要记住的

- 第一个参数 `proc_t p`：当前进程，分发层已经帮你准备好  
- 无 `copyin`：没有用户指针参数  
- `return 0` = 成功；真正给用户的 PID 在 `*retval`

---

## 2. getppid（#39）

同一文件 [`kern_prot.c`](../xnu/bsd/kern/kern_prot.c) 约 176–181 行：

```c
int
getppid(proc_t p, __unused struct getppid_args *uap, int32_t *retval)
{
	*retval = p->p_ppid;
	return 0;
}
```

### 和 getpid 比

| | getpid | getppid |
|--|--------|---------|
| 数据来源 | `proc_getpid(p)` | 直接读 `p->p_ppid` |
| 复杂度 | 极简 | 极简 |
| copyin | 无 | 无 |

一句话：父进程 ID 就存在当前 `proc` 结构体字段里。

---

## 3. getuid（#24）

同一文件约 288–293 行：

```c
int
getuid(__unused proc_t p, __unused struct getuid_args *uap, int32_t *retval)
{
	*retval = kauth_getruid();
	return 0;
}
```

### 和前两个比

- 这里读的是 **real uid**（真实用户 ID），走 `kauth_getruid()`  
- `proc_t p` 标了 `__unused`：UID 不从 `p` 字段直接取，而从当前线程/进程的 **凭证（credential）** 取  
- 仍然无用户指针、无 `copyin`

明天 Day 2 会继续看 `geteuid` / `getgid` / `getegid`，同一文件往后翻即可。

---

## 今日对比（写进笔记）

| 项目 | getpid | getppid | getuid |
|------|--------|---------|--------|
| # | 20 | 39 | 24 |
| handler | `kern_prot.c` | 同左 | 同左 |
| 读什么 | 当前 PID | 父 PID | real UID |
| 对象 | `proc` | `proc` | kauth 凭证 |
| copyin | 否 | 否 | 否 |

**共同点：** 无参数、只读、成功一律 `return 0`，结果放 `*retval`。  
**最大差异：** PID 族看 `proc`；`getuid` 看凭证子系统。

---

## 做完打勾

- [ ] 在 `syscalls.master` 找到 20 / 39 / 24  
- [ ] 读完 `kern_prot.c` 里三个函数  
- [ ] 能口头复述上面三条调用链  
- [ ] 填好 [`notes/daily/day-01.md`](../notes/daily/day-01.md)  
- [ ] （可选）macOS 上写个 `printf("%d\n", getpid());` 用 `dtruss` 看一眼

下一步：Day 2 → `geteuid` / `getgid` / `getegid`（见 [`DAILY_SYSCALL_PLAN.md`](DAILY_SYSCALL_PLAN.md)）。
