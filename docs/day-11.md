# 第十一天（Day 11）正文

学这三个：**`fork` / `vfork` / `wait4`**  
源码：`xnu/` = **xnu-12377.121.6**

离开「文件/目录」，进入**进程生命周期**：创建子进程、等待子进程结束。

---

## 今天目标

1. 找到编号 **2 / 66 / 7**  
2. 理解 `fork`：复制出新 `proc` + Mach `task`，父子各返回一次  
3. 理解 `wait4`：等僵尸子进程并回收  
4. 知道 `vfork` 的经典语义，以及本树里可能受 `CONFIG_VFORK` 影响

笔记：[`notes/daily/day-11.md`](../notes/daily/day-11.md)  
分析：[`notes/daily/day-11-analysis.md`](../notes/daily/day-11-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| fork | **2** | 创建子进程（复制） |
| wait4 | **7** | 等待并回收子进程 |
| vfork | **66** | 经典「轻量 fork，共享地址空间直到 exec」；本树可能 `#if CONFIG_VFORK` |

---

## 1. fork（#2）

[`kern_fork.c`](../xnu/bsd/kern/kern_fork.c)：

```c
fork(parent, ...) {
    retval[1] = 0;  // 标记：用户态区分父子
    fork1(..., PROC_CREATE_FORK)
      → cloneproc(...)   // 新 task + 新 proc，继承/复制特征
      → thread_dup      // 拷当前线程状态到子线程
    父：retval[0] = 子 pid
    子：被调度起来后，从「fork 返回点」继续（返回 0）
}
```

要点：

- 一次调用，**两个执行流**（父拿到子 pid，子拿到 0）  
- 地址空间：通常 **写时复制（COW）**，不是立刻整本拷内存  
- XNU 里 BSD `proc` 与 Mach `task`/`thread` 一起出现

---

## 2. wait4（#7）

[`kern_exit.c`](../xnu/bsd/kern/kern_exit.c)：

```c
wait4 → wait4_nocancel
  在子进程列表里找匹配 pid/进程组
  若子进程已是僵尸 SZOMB → 取退出状态、可选 rusage，回收
  否则按 options 阻塞等待（或 WNOHANG 立即返回）
```

`exit` 的子进程先变成僵尸；父不 `wait*` 会留下僵尸。  
`*retval` 常为被回收的子 pid；状态经用户指针 `status` copyout。

---

## 3. vfork（#66）——先记经典语义

经典 Unix：

- 子进程**暂借**父地址空间  
- 父阻塞，直到子 `exec` 或 `_exit`  
- 为少拷地址空间而存在；规则很脆

在本 XNU 树：

```c
#if CONFIG_VFORK
66  vfork(...)
#else
66  nosys   // old vfork
#endif
```

源码树里未必还能看到完整独立的 `vfork()` C 实现；现代更推荐 **`posix_spawn`**（Day 13）。  
今天：知道历史上为什么有 vfork，以及和 fork 的差别即可。

---

## 今日对比

| | fork | vfork（经典） | wait4 |
|--|------|---------------|-------|
| 新进程 | 是 | 是（受限） | 否 |
| 地址空间 | COW 副本 | 暂共享 | — |
| 返回 | 父子都从 fork 返回 | 特殊约定 | 父拿子 pid/状态 |

---

## 做完打勾

- [ ] 找到 2 / 7 / 66  
- [ ] 能说 fork 双返回与 cloneproc  
- [ ] 能说 wait4 收僵尸  
- [ ] 填好 `notes/daily/day-11.md`

下一步：Day 12 → `execve` / `exit`
