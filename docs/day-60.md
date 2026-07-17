# 第六十天（Day 60）正文

学这六个：**`setuid` / `setgid` / `seteuid` / `setegid` / `setreuid` / `setregid`**  
源码：`xnu/` = **xnu-12377.121.6**

Day 1–2 学的是**读**凭证；今天学**改**。六个调用都在 [`kern_prot.c`](../xnu/bsd/kern/kern_prot.c)，最后多半进 `kauth_cred_proc_update` + `kauth_cred_model_setresuid/gid`。

生活类比：

1. **real**：户口本上的名字  
2. **effective**：此刻办事出示的工牌（权限检查多看它）  
3. **saved**：口袋里那张「还能变回去」的备用工牌（setuid 程序常用）  

---

## 今天目标

1. 找到编号 **23 / 181 / 183 / 182 / 126 / 127**  
2. 分清：只改 euid vs 特权下连带改 real/saved  
3. 理解普通用户只能在「自己已有的 ruid/euid/svuid 集合」里切换  
4. 能说：改凭证会打「曾 setugid」标记（与 Day 3 `issetugid` 相关）  

笔记：[`notes/daily/day-60.md`](../notes/daily/day-60.md)  
分析：[`notes/daily/day-60-analysis.md`](../notes/daily/day-60-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| setuid | **23** | 设 uid（特权可连带 real/saved） |
| seteuid | **183** | 只设 effective uid |
| setreuid | **126** | 分别设 real / effective（`-1` 表示不动） |
| setgid | **181** | 设 gid（对称于 setuid） |
| setegid | **182** | 只设 effective gid |
| setregid | **127** | 分别设 real / effective gid |

---

## 1. 共同骨架

```c
set*(...) {
    // 可选 MAC 检查
    // 非特权：目标须落在当前 ruid/euid/svuid（或 rgid/...）允许集
    // 否则 suser → EPERM
    kauth_cred_proc_update(p, PROC_SETTOKEN_SETUGID, ^{
        return kauth_cred_model_setresuid/gid(model, ...);
    });
}
```

要点：

- **汇合点**：换进程的 `kauth_cred` 模型，不是各写各的散逻辑  
- `PROC_SETTOKEN_SETUGID`：标记「自上次 exec 后动过特权相关凭证」→ `issetugid()` 可能变 1  
- 读侧回顾：`getuid`→real，`geteuid`→effective（Day 1–2）  

---

## 2. setuid / seteuid / setreuid

| 调用 | 非特权大致能做什么 | 特权（root） |
|------|-------------------|--------------|
| `seteuid(e)` | e 等于当前 ruid 或 svuid | 只改 euid |
| `setuid(u)` | u 等于 ruid 或 svuid 时改 euid；特权才改齐 | 常同时改 real/effective/saved |
| `setreuid(r,e)` | r/e 须落在已有 uid 集合；`-1` 不动 | 可设任意组合 |

典型 setuid-root 程序模式：先以 euid=0 做事，再 `seteuid(getuid())` 丢掉有效特权，必要时再切回 saved。

---

## 3. setgid / setegid / setregid

与 uid 侧**对称**：

```
setgid  ↔ setuid
setegid ↔ seteuid
setregid ↔ setreuid
```

字段：`cr_rgid` / `cr_gid`（effective）/ `cr_svgid`。  
实现细节：effective gid 常放在补充组列表首元素，改 egid 可能重排组列表。

---

## 4. 和「读」对照

| 读 | 写 |
|----|----|
| getuid / geteuid | setuid / seteuid / setreuid |
| getgid / getegid | setgid / setegid / setregid |
| issetugid | 上述成功变更后可能置位 |

权限检查日常看 **effective**；`access`/`faccessat` 默认看 **real**（Day 4/55）——所以「工牌」和「户口本」不是一回事。

---

## 用户层 Demo

> 无特权环境不能随意改成别人的 uid。Demo 用「设成当前自己」验证调用可通，并打印 `issetugid`。

```c
#include <stdio.h>
#include <unistd.h>
#if defined(__APPLE__) || defined(__FreeBSD__)
#include <unistd.h> /* issetugid */
#define HAS_ISSETUGID 1
#endif

int main(void) {
    uid_t r = getuid();
    uid_t e = geteuid();
    gid_t rg = getgid();
    gid_t eg = getegid();

    printf("before uid r/e=%d/%d gid r/e=%d/%d",
           (int)r, (int)e, (int)rg, (int)eg);
#if defined(HAS_ISSETUGID)
    printf(" issetugid=%d", issetugid());
#endif
    printf("\n");

    /* 设成自己：非特权通常应成功 */
    if (seteuid(e) != 0) { perror("seteuid"); return 1; }
    if (setuid(r) != 0) { perror("setuid"); return 1; }
    if (setegid(eg) != 0) { perror("setegid"); return 1; }
    if (setgid(rg) != 0) { perror("setgid"); return 1; }
    if (setreuid(r, e) != 0) { perror("setreuid"); return 1; }
    if (setregid(rg, eg) != 0) { perror("setregid"); return 1; }

    printf("after  uid r/e=%d/%d gid r/e=%d/%d",
           (int)getuid(), (int)geteuid(),
           (int)getgid(), (int)getegid());
#if defined(HAS_ISSETUGID)
    printf(" issetugid=%d", issetugid());
#endif
    printf("\ncred setters ok (no-op to self)\n");
    return 0;
}
```

```bash
cc -o day60_demo day60_demo.c && ./day60_demo
```

---

## 做完打勾

- [ ] 找到六个编号  
- [ ] 能说 real / effective / saved 三角  
- [ ] 能说非特权只能在已有集合里切换  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-60.md`

下一步：Day 61 → `getgroups` / `setgroups` / `initgroups`（若有）/ `getlogin` / `setlogin` / `chroot`
