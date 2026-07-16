# 第三十三天（Day 33）正文

学这个：**`sys_flock`（用户层 `flock`）**；对照 `fcntl` 文件锁略提。  
源码：`xnu/` = **xnu-12377.121.6**

今天看**文件劝告锁**：进程之间约定「谁占用这个文件」，内核帮忙排队/互斥，但**不强制**所有读写都检查锁（劝告 = advisory）。

生活类比：图书馆座位上放一块「有人」牌子——守规矩的人会看；硬坐上去也能坐（除非文件系统另有强制策略）。

---

## 今天目标

1. 找到编号 **131**（`sys_flock`）  
2. 理解 `LOCK_SH` / `LOCK_EX` / `LOCK_UN` / `LOCK_NB`  
3. 理解主路径：FD → vnode → `VNOP_ADVLOCK`（`F_FLOCK` 语义，整文件）  
4. 知道与 `fcntl(F_SETLK…)` POSIX 字节锁是同一 VNOP、不同语义标志  

笔记：[`notes/daily/day-33.md`](../notes/daily/day-33.md)  
分析：[`notes/daily/day-33-analysis.md`](../notes/daily/day-33-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| sys_flock | **131** | 对打开文件加/解劝告锁（整文件） |

`how`：

| 标志 | 含义 |
|------|------|
| `LOCK_SH` | 共享锁（读锁） |
| `LOCK_EX` | 排他锁（写锁） |
| `LOCK_UN` | 解锁 |
| `LOCK_NB` | 非阻塞；冲突立刻失败，不睡等 |

---

## 1. flock 主路径

[`kern_descrip.c`](../xnu/bsd/kern/kern_descrip.c) `sys_flock`：

```c
sys_flock(fd, how) {
    fp_getfvp → fp, vp          // FD 必须落到 vnode
    填 flock：整文件（start=0, len=0）
    if LOCK_UN → VNOP_ADVLOCK(..., F_UNLCK, F_FLOCK)
    if LOCK_EX → F_WRLCK；LOCK_SH → F_RDLCK
    VNOP_ADVLOCK(vp, fileglob 作 id, F_SETLK, &lf,
                 F_FLOCK [| F_WAIT])
    成功则 fg_flag |= FWASLOCKED
}
```

要点：

- **锁在 vnode / 文件系统劝告锁层**，id 常用 **fileglob**（这个打开实例）  
- `F_FLOCK`：flock(2) 语义 = **整文件**  
- 无 `LOCK_NB` 时带 `F_WAIT`：冲突可睡眠等待  
- 不是所有文件系统都完整支持  

---

## 2. 和 fcntl 锁对照（略）

| | flock | fcntl `F_SETLK` / `F_SETLKW` |
|--|-------|------------------------------|
| 范围 | 通常整文件 | 可字节区间 |
| 入口 | `sys_flock` | `fcntl`（Day 14 见过骨架） |
| 底层 | 都常进 `VNOP_ADVLOCK` | 标志 `F_POSIX` 等 |

今天验收：能说 flock 走 `VNOP_ADVLOCK` + `F_FLOCK`；fcntl 锁是亲戚，不是另一套宇宙。

---

## 3. 「劝告」是什么意思

- 锁住后，**别的也用 flock/fcntl 守规矩的进程**会阻塞或失败  
- 普通的 `read`/`write` **不一定**因你没拿锁就被内核拒绝  
- 用途：多进程协作（如单实例守护、简单文件互斥）

---

## 做完打勾

- [ ] 找到 131  
- [ ] 能说 SH/EX/UN/NB  
- [ ] 能说 FD → vnode → VNOP_ADVLOCK  
- [ ] 能说劝告锁 ≠ 强制所有 IO 检查  
- [ ] 填好 `notes/daily/day-33.md`

下一步：Day 34 → `sync` / `fsync`（回顾刷盘；`fsync` Day 14 已见）
