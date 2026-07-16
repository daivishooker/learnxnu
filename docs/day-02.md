# 第二天（Day 2）正文

学这三个：**`geteuid` / `getgid` / `getegid`**  
源码版本：`xnu/` = **xnu-12377.121.6**

承接 Day 1 的 `getuid`（real uid）。今天把 **real vs effective**、**uid vs gid** 在凭证里的位置看清楚。

---

## 今天目标

1. 在 `syscalls.master` 找到 25 / 47 / 43  
2. 读 `kern_prot.c` 三个 handler（仍然极短）  
3. 对照 `kauth_getuid` / `kauth_getrgid` / `kauth_getgid`  
4. 能说出：real 与 effective 各读哪个字段

笔记：[`notes/daily/day-02.md`](../notes/daily/day-02.md)  
分析：[`notes/daily/day-02-analysis.md`](../notes/daily/day-02-analysis.md)

---

## 步骤 0：总表编号

[`xnu/bsd/kern/syscalls.master`](../xnu/bsd/kern/syscalls.master)

| 名字 | # | 语义 |
|------|---|------|
| geteuid | **25** | effective user id |
| getegid | **43** | effective group id |
| getgid | **47** | real group id |

（Day 1 的 `getuid` #24 = real user id，今天要和 `geteuid` 对照。）

---

## 1. geteuid（#25）

[`kern_prot.c`](../xnu/bsd/kern/kern_prot.c)：

```c
int
geteuid(__unused proc_t p, __unused struct geteuid_args *uap, int32_t *retval)
{
	*retval = kauth_getuid();
	return 0;
}
```

对比 Day 1：

| | getuid (#24) | geteuid (#25) |
|--|--------------|---------------|
| 助手 | `kauth_getruid()` | `kauth_getuid()` |
| 字段 | `cr_ruid`（real） | `cr_uid`（effective） |

命名容易混：`kauth_getuid()` 取的是 **effective**，不是 real。

---

## 2. getgid（#47）

```c
int
getgid(__unused proc_t p, __unused struct getgid_args *uap, int32_t *retval)
{
	*retval = kauth_getrgid();
	return 0;
}
```

- real group id → `kauth_getrgid()` → `cr_rgid`  
- 和 `getuid` 对称：名字是 get**g**id，助手却是 get**r**gid（强调 real）

---

## 3. getegid（#43）

```c
int
getegid(__unused proc_t p, __unused struct getegid_args *uap, int32_t *retval)
{
	*retval = kauth_getgid();
	return 0;
}
```

源码注释要点：effective gid 在实现上与补充组列表首元素相关；对你今天只需记住：**读的是 effective gid（`kauth_getgid` → `cr_gid`）**。

---

## 今日对照表（务必背下）

| syscall | # | kauth 助手 | posix_cred 字段 | 含义 |
|---------|---|------------|-----------------|------|
| getuid | 24 | `kauth_getruid` | `cr_ruid` | real uid |
| geteuid | 25 | `kauth_getuid` | `cr_uid` | effective uid |
| getgid | 47 | `kauth_getrgid` | `cr_rgid` | real gid |
| getegid | 43 | `kauth_getgid` | `cr_gid` | effective gid |

共同点：都走 `kauth_cred_get()` → 当前线程 `tro_cred`；无 `copyin`；不读 `proc->p_*` 缓存。

---

## 用户层 Demo

对比 real / effective 身份与组 ID；在 macOS 上通常 euid==uid，setuid 程序才会分叉。

```c
#include <stdio.h>
#include <unistd.h>

int main(void) {
    printf("euid=%d gid=%d egid=%d\n",
           geteuid(), getgid(), getegid());
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 master 里 25 / 47 / 43  
- [ ] 读完三个 handler  
- [ ] 能说清 getuid vs geteuid、getgid vs getegid  
- [ ] 填好 `notes/daily/day-02.md`

下一步：Day 3 → `issetugid` / `getdtablesize`
