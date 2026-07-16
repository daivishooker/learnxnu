# 源码分析：Day 32（setrlimit / getrlimit）

基于 `xnu-12377.121.6`。资源上限读写。

---

## 1. 心智模型

```text
proc → plimit → pl_rlimit[which] = { rlim_cur, rlim_max }

getrlimit: 读出 copyout
setrlimit: copyin → 校验 soft/hard/特权 → 按资源类型生效 → 写回
```

---

## 2. getrlimit

[`kern_resource.c`](../../xnu/bsd/kern/kern_resource.c)：

```
which 合法？
proc_limitget(p, which)
copyout sizeof(rlimit)
```

---

## 3. setrlimit → dosetrlimit

```
copyin new rlimit
soft > hard → EINVAL
抬高 hard → suser，否则 EPERM
switch(which): CPU 计时器 / DATA→vm_map / STACK / NOFILE…
写回 plimit
```

细节因 which 而异；今天跟到「分发 + 权限规则」即可。

---

## 4. 和 rusage / nice

| | rlimit | rusage | nice |
|--|--------|--------|------|
| 含义 | 上限 | 已用统计 | 调度优先级 |
| 天 | 21/32 | 30 | 31 |

---

## 5. 建议点开

1. `syscalls.master` — 195 / 194  
2. `kern_resource.c` — `getrlimit` / `setrlimit` / `dosetrlimit`  

验收：能说 soft/hard；能说谁能抬 hard；能对比 rusage。
