# Day 62 — getpgrp / setpgid / setsid / getpgid / getsid

> **正文：** [docs/day-62.md](../../docs/day-62.md)  
> **分析：** [day-62-analysis.md](day-62-analysis.md)

## 读侧（#81 / #151 / #310）
- `getpgrp` → `p_pgrpid`；`getpgid`/`getsid` 可查任意 pid（0=自己）
- 一句话：读进程组与会话 ID

## setpgid (#82)
- 入口：`enterpgrp(..., mksess=0)`；同 session、非会话首领
- 一句话：作业控制调班组

## setsid (#147)
- 入口：`setsid_internal` → `enterpgrp(..., mksess=1)`
- 一句话：新建会话并当首领；解绑控制终端

## 今日对比
- 共同点：都围绕 pgrp/session 拓扑
- 最大差异：只读 vs 调组 vs 开新会话
