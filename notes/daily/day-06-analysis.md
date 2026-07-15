# 源码分析：Day 6（dup / dup2）

基于 `xnu-12377.121.6`。把 Day 5 的「共享偏移」钉死在代码上。

---

## 1. 对象关系（dup 之后）

```
fd_old ──► fileproc_old ──┐
                           ├──► 同一个 fileglob
fd_new ──► fileproc_new ──┘         ├─ fg_offset
                                    ├─ fg_cred
                                    └─ 底层对象（vnode…）
```

- **fileproc**：每个 fd 一个表项（可有各自的 `fp_flags`，如 CLOEXEC）  
- **fileglob**：打开文件的真正状态；**引用计数** `fg_count`；dup 时 `fg_ref`

---

## 2. dup

[`kern_descrip.c`](../../xnu/bsd/kern/kern_descrip.c) `sys_dup`：

1. `fp_lookup` 源 fd  
2. 可选 `GUARD_DUP`（guarded fd 禁止随意 dup）  
3. `fdalloc(p, 0, &new)` — 从 0 起找空槽（受 Day 3 nofile 限制）  
4. `finishdup(old, new)`

### `finishdup` 精华

```c
fg_ref(p, ofp->fp_glob);        // 共享对象引用 +1
nfp = fileproc_alloc_init();
nfp->fp_glob = ofp->fp_glob;    // 不拷贝文件状态，直接共用
// 把 nfp 安进 fd 表的 new 槽
*retval = new;
```

**没有**新开 vnode，也**没有**独立偏移副本。

---

## 3. dup2

`sys_dup2` → `dup2(from, to)`：

| 情况 | 行为 |
|------|------|
| `to` 越界（≥ nofile） | `EBADF` |
| `old == new` | 直接成功，`*retval = new` |
| `to` 槽已有打开文件 | 先 close（注意 `GUARD_CLOSE`），再 finishdup |
| `to` 空闲 / 需扩表 | `fdalloc` / reserve 后 finishdup |

与 `dup` 最终汇合到同一个 `finishdup`，所以共享语义完全一样。

经典用途：把文件/管道接到 stdin/stdout/stderr（`dup2(pipefd, 1)` 等）。

---

## 4. 和 close / lseek 的交互

- **close 一个 dup 出来的 fd**：只拆掉该 `fileproc`，`fg_count--`；另一个 fd 仍可用，直到引用归零才真正关底层对象。  
- **lseek**：改 `fg_offset`，所有指向该 `fileglob` 的 fd 一起变。  
- **若要独立偏移**：不能靠 `dup`；通常要再 `open` 一次同一路径（各有各的 fileglob）。

---

## 5. 建议点开的文件

1. `syscalls.master` — 41 / 90  
2. `kern_descrip.c` — `sys_dup`  
3. `kern_descrip.c` — `dup2`（含 old==new、先 close）  
4. `kern_descrip.c` — `finishdup`（`fg_ref` + 共享 `fp_glob`）  

今天验收：能画「两 fd → 两 fileproc → 一 fileglob」图，并说明为何 dup 后 seek 互相影响。
