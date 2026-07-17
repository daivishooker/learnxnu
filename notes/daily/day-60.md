# Day 60 — setuid / setgid / seteuid / setegid / setreuid / setregid

> **正文：** [docs/day-60.md](../../docs/day-60.md)  
> **分析：** [day-60-analysis.md](day-60-analysis.md)

## uid 侧（#23 / #183 / #126）
- 入口：`kauth_cred_proc_update` → `kauth_cred_model_setresuid`
- 一句话：改 real/effective/saved uid；非特权只能在已有集合切换

## gid 侧（#181 / #182 / #127）
- 入口：对称走 `kauth_cred_model_setresgid`
- 一句话：组版 setuid 族

## 今日对比
- 共同点：都改 `kauth_cred`；成功常打 SETUGID 标记
- 最大差异：只改 effective vs 特权下连带 real/saved；`-1` 表示不动（re*）
