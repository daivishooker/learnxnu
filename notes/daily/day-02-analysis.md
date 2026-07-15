# 源码分析：Day 2（geteuid / getgid / getegid）

基于 `xnu-12377.121.6`。承接 Day 1：身份读凭证，不读 `proc` 缓存。

---

## 1. 四个「我是谁」在凭证里的位置

`posix_cred`（[`ucred.h`](../../xnu/bsd/sys/ucred.h)）：

```c
uid_t   cr_uid;    /* effective user id */
uid_t   cr_ruid;   /* real user id */
uid_t   cr_svuid;  /* saved user id */
...
gid_t   cr_groups[NGROUPS]; /* 补充组；egid 与首元素相关 */
gid_t   cr_rgid;   /* real group id */
gid_t   cr_svgid;  /* saved group id */
```

用户态日常最常碰的是 **real** 与 **effective**（saved 留给 setuid 故事）。

---

## 2. 三个 handler（全在 `kern_prot.c`）

```c
geteuid(...) { *retval = kauth_getuid();  return 0; }  // effective uid
getgid (...) { *retval = kauth_getrgid(); return 0; }  // real gid
getegid(...) { *retval = kauth_getgid();  return 0; }  // effective gid
```

加 Day 1：

```c
getuid (...) { *retval = kauth_getruid(); return 0; }  // real uid
```

---

## 3. kauth 助手如何落到字段

[`kern_credential.c`](../../xnu/bsd/kern/kern_credential.c)：

```c
kauth_getuid()  → kauth_cred_getuid(kauth_cred_get())  → cr_uid
kauth_getruid() → kauth_cred_getruid(...)              → cr_ruid
kauth_getgid()  → kauth_cred_getgid(...)               → cr_gid
kauth_getrgid() → kauth_cred_getrgid(...)              → cr_rgid

kauth_cred_get() → current_thread_ro()->tro_cred
```

**命名陷阱：**

- `getuid` syscall ↔ `kauth_get**r**uid`（real）  
- `geteuid` syscall ↔ `kauth_getuid`（effective，名字里没有 e）

记字段比记函数名更稳。

---

## 4. 为什么还是不读 `p->p_uid` / `p->p_gid`？

Day 1 已说过：`proc` 上的 `p_uid`/`p_ruid`/`p_gid`/`p_rgid` 是 `proc_update_creds_onproc()` 从 credential **抄的缓存**。

今天三个调用同样：

1. 权限真相在 `ucred`  
2. 可能按线程覆盖（`tro_cred`）  
3. 系统调用要当前上下文，不要可能滞后的进程快照

---

## 5. real vs effective（先建立直觉）

| | real | effective |
|--|------|-----------|
| uid | `getuid` / `cr_ruid` | `geteuid` / `cr_uid` |
| gid | `getgid` / `cr_rgid` | `getegid` / `cr_gid` |
| 粗浅含义 | 「你是谁」（登录身份） | 「此刻按谁的权限检查」 |

多数普通进程二者相同。不同起来通常和 **setuid 程序**有关（后面学 `setuid`/`exec` 再深挖）。今天只要能在源码里指到四个字段。

---

## 6. getegid 注释多说了一句

```c
 * Notes: As an implementation detail, the effective gid is stored as
 *        the first element of the supplementary group list.
```

实现细节：egid 与 `cr_groups[0]` 有绑定关系；对外仍通过 `kauth_getgid()` 读。不必今天追进 `setgroups`，知道「注释提醒了存储细节」即可。`ucred.h` 里也有 `#define cr_gid cr_groups[0]`，与注释一致。

---

## 7. 和 Day 1 串起来的调用链

```
用户态 geteuid/getgid/getegid
  → 陷阱 → unix_syscall → sysent[25|47|43]
  → handler（kern_prot.c）
  → kauth_get*( )
  → current_thread_ro()->tro_cred
  → posix_cred 对应字段
  → *retval；return 0
```

与 `getpid` 族对比：PID 看 `proc`；这一整组 UID/GID 看 **线程凭证**。

---

## 8. 建议点开的文件

1. `xnu/bsd/kern/syscalls.master` — 25 / 43 / 47  
2. `xnu/bsd/kern/kern_prot.c` — 三个 handler + 回头看 getuid  
3. `xnu/bsd/kern/kern_credential.c` — `kauth_getuid`/`getruid`/`getgid`/`getrgid`  
4. `xnu/bsd/sys/ucred.h` — `posix_cred` 字段布局  
