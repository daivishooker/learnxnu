# 源码分析：Day 4（open / close / access）

基于 `xnu-12377.121.6`。这是进入 VFS + FD 表的第一天。

---

## 1. 为什么今天突然变难？

| Day 1–3 | Day 4 |
|---------|-------|
| 多半无用户指针 | `path` 要进内核 |
| 几乎总成功 | 大量 errno（不存在、无权限、FD 用尽） |
| 读字段/标志 | 要创建/销毁内核对象 |

学习策略：**先跟主路径，别一次钻进整个 namei/ACL。**

---

## 2. open：先占坑，再打开文件

### 入口分层

```
open (#5)
  → open_nocancel          // 可取消点已测过
  → openat_internal(..., AT_FDCWD, ...)
  → open1at / open1
```

`AT_FDCWD`：相对路径相对「当前工作目录」，不是某个目录 fd（那是 `openat`）。

### `open1` 里两件大事

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c) 的 `open1`：

1. **`falloc_withinit(p, …, &fp, &indx, …)`**  
   - 在本进程描述符表分配 `fileproc`  
   - 失败常见：`EMFILE`（本进程到 nofile 上限，回扣 Day 3）、`ENFILE`（系统级）

2. **`vn_open_auth(ndp, &flags, vap, …)`**  
   - 路径查找（namei 族）→ `vnode`  
   - 权限 / 创建 / 截断等  
   - 失败则 `fp_free` 把已占 FD 退掉

成功：`*retval = indx`（新 fd）。

**顺序很重要：** 先 falloc 再打开。这样打开过程中已有稳定 fd 槽；失败必须配对释放，否则漏描述符。

### 和前几天的衔接

- FD 上限：`proc_limitgetcur_nofile`（Day 3）  
- 权限检查用的身份：走 `vfs_context` 里的 credential（Day 2 的 effective 世界；具体授权在 `vn_open_auth` / kauth）

---

## 3. close：按 fd 拆掉 fileproc

[`kern_descrip.c`](../../xnu/bsd/kern/kern_descrip.c)：

```
sys_close
  → close_nocancel(p, cred, fd)
      → proc_fdlock
      → fp_get_noref_locked  // 无此 fd → EBADF
      → 可选 guard 检查
      → fp_close_and_unlock // 真正关：减引用、可能回收 vnode/socket…
```

要点：

- **不再碰路径**；句柄就是整数 fd  
- `fileproc` 是用户 fd 与内核对象（vnode/socket/…）之间的中间层  
- 关闭可能触发底层 `fo_close`；今天只需知道「表项被拆掉」

---

## 4. access：只检查，不打开

```
access (#33)
  → faccessat_internal(ctx, AT_FDCWD, path, amode, 0, …)
      → 默认 kauth_cred_copy_real(...)   // 用 real 身份！
      → nameiat → vnode
      → access1(vp, dvp, amode, &context)
      → vnode_put / nameidone
```

### 和 open 的关键差别

| | open | access |
|--|------|--------|
| 目的 | 得到可用 fd | 问「以某身份能否」 |
| 占 FD | 是 | 否 |
| 默认身份 | 通常按有效凭证/上下文操作 | **real**（无 `AT_EACCESS` 时） |

源码写得很直白：access 传统语义是对 **real** identity 检查，即使进程 effective uid 不同。这能解释 setuid 程序里 `access` 与真正 `open` 结果不一致的经典坑。

---

## 5. 三条链一张图

```
用户 path ──namei──► vnode
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       access1     vn_open_auth   (close 不走这里)
       (只检查)     + falloc
                      │
                      ▼
                   fileproc / fd
                      │
                      ▼
                    close 按 fd 拆除
```

---

## 6. 建议点开的文件（控制深度）

1. `syscalls.master` — 5 / 6 / 33  
2. `vfs_syscalls.c` — `open` / `open_nocancel` / `open1` 开头 80 行  
3. `vfs_syscalls.c` — `access` / `faccessat_internal` 里 real cred 那段  
4. `kern_descrip.c` — `sys_close` / `close_nocancel`  
5. （可选扫一眼）`vn_open_auth` 声明/定义位置，先不深挖  

**今天验收：** 能讲清 open 与 access 都解析路径，但一个分配 FD、一个默认用 real 身份只做检查；close 只认 fd。
