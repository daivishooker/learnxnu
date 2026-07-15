# 第六天（Day 6）正文

学这两个：**`dup` / `dup2`**  
源码：`xnu/` = **xnu-12377.121.6**

Day 5 说过：偏移在 `fileglob.fg_offset`。今天看清楚——**dup 出来的两个 fd 共享同一个 `fileglob`**。

---

## 今天目标

1. 找到编号 **41 / 90**  
2. 能说出 `dup`：分配新 fd，指向同一 `fileglob`  
3. 能说出 `dup2`：指定目标 fd；若已被占用则先 close  
4. 理解为何一个 fd 上 `lseek` 会影响另一个 dup 出来的 fd

笔记：[`notes/daily/day-06.md`](../notes/daily/day-06.md)  
分析：[`notes/daily/day-06-analysis.md`](../notes/daily/day-06-analysis.md)

---

## 总表

| 名字 | # | 原型 |
|------|---|------|
| dup | **41** | `sys_dup(fd)` → 新 fd |
| dup2 | **90** | `sys_dup2(from, to)` → to |

---

## 1. dup（#41）

[`kern_descrip.c`](../xnu/bsd/kern/kern_descrip.c)：

```c
sys_dup(...) {
    proc_fdlock(p);
    fp_lookup(p, old, &fp, ...);   // 源 fd
    // GUARD_DUP 检查
    fdalloc(p, 0, &new);           // 分配最小可用新 fd
    finishdup(p, ..., old, new, ..., retval);
}
```

`finishdup` 关键一行：

```c
fg_ref(p, ofp->fp_glob);     // fileglob 引用 +1
nfp->fp_glob = ofp->fp_glob; // 新 fileproc 指向同一个 fileglob
```

最短链：

```
dup → 查旧 fd → fdalloc 新槽 → finishdup
    → 新 fileproc 共享旧 fileglob → *retval = 新 fd
```

---

## 2. dup2（#90）

```c
sys_dup2 → dup2(p, cred, from, to, retval)
```

`dup2` 额外逻辑：

1. `to` 必须在 nofile 限制内，否则 `EBADF`  
2. `from == to`：直接成功，返回 `to`（POSIX）  
3. 若 `to` 已打开：先 `fp_close_and_unlock` 关掉目标，再 `finishdup`  
4. 同样走 `finishdup` → **共享 `fileglob`**

---

## 今日对比

| | dup | dup2 |
|--|-----|------|
| 新 fd 谁定 | 内核挑最小空闲 | 调用者指定 `to` |
| 目标已占用 | 不涉及 | 先 close 再占 |
| `from == to` | — | 空操作成功 |
| 是否共享偏移 | 是（同一 `fileglob`） | 是 |

回扣 Day 5：`lseek(fd_a)` 改的是 `fg_offset`；`fd_b = dup(fd_a)` 后，`fd_b` 看到的是同一个偏移。

---

## 做完打勾

- [ ] 找到 41 / 90  
- [ ] 读过 `finishdup` 里 `nfp->fp_glob = ofp->fp_glob`  
- [ ] 能解释 dup 后共享 `fg_offset`  
- [ ] 填好 `notes/daily/day-06.md`

下一步：Day 7 → `stat64` / `fstat64` / `lstat64`
