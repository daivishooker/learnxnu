# 第三天（Day 3）正文

学这两个：**`issetugid` / `getdtablesize`**  
源码：`xnu/` = **xnu-12377.121.6**

Day 1–2 读身份字段；今天看两个「进程状态查询」：安全污染标志、FD 表上限。

---

## 今天目标

1. 找到编号 **327** / **89**  
2. 读懂 `P_SUGID` 何时为真  
3. 知道 `getdtablesize` 返回的是 **nofile 资源限制**，不是「当前已打开多少个 FD」

笔记：[`notes/daily/day-03.md`](../notes/daily/day-03.md)  
分析：[`notes/daily/day-03-analysis.md`](../notes/daily/day-03-analysis.md)

---

## 总表

[`syscalls.master`](../xnu/bsd/kern/syscalls.master)

| 名字 | # | 原型 |
|------|---|------|
| getdtablesize | **89** | `sys_getdtablesize(void)` |
| issetugid | **327** | `issetugid(void)` |

---

## 1. issetugid（#327）

[`kern_prot.c`](../xnu/bsd/kern/kern_prot.c)：

```c
int
proc_issetugid(proc_t p)
{
	return (p->p_flag & P_SUGID) ? 1 : 0;
}

int
issetugid(proc_t p, ..., int32_t *retval)
{
	*retval = proc_issetugid(p);
	return 0;
}
```

`P_SUGID` 定义（[`proc.h`](../xnu/bsd/sys/proc.h)）：

```c
#define P_SUGID  0x00000100  /* Has set privileges since last exec */
```

**返回值含义：**

| `*retval` | 含义 |
|-----------|------|
| 0 | 未「污染」 |
| 1 | 已污染（tainted） |

源码注释说：污染包括  
1）exec 了带 SUID/SGID 的镜像；或  
2）自启动后改过 real/effective/saved uid/gid。

用途直觉：库函数可用来决定「环境变量 / 路径是否还信得过」（例如不安全的 `$HOME` 处理）。

---

## 2. getdtablesize（#89）

[`kern_descrip.c`](../xnu/bsd/kern/kern_descrip.c)：

```c
int
sys_getdtablesize(proc_t p, ..., int32_t *retval)
{
	*retval = proc_limitgetcur_nofile(p);
	return 0;
}
```

读的是进程 **RLIMIT_NOFILE 当前软限制**（再经内核上限裁剪），即「FD 表最多能到多大」。

**不是：** 当前打开了多少个文件。

---

## 今日对比

| | issetugid | getdtablesize |
|--|-----------|---------------|
| # | 327 | 89 |
| 读什么 | `p->p_flag & P_SUGID` | nofile rlimit |
| 子系统 | 凭证/特权历史 | 资源限制 + FD |
| copyin | 无 | 无 |

---

## 做完打勾

- [ ] 找到 327 / 89  
- [ ] 能解释 `P_SUGID`  
- [ ] 能区分 getdtablesize vs 当前打开 FD 数  
- [ ] 填好 `notes/daily/day-03.md`

下一步：Day 4 → `open` / `close` / `access`
