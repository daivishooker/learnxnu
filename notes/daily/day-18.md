# Day 18 — sigaltstack / __pthread_kill

> **正文：** [docs/day-18.md](../../docs/day-18.md)  
> **分析：** [day-18-analysis.md](day-18-analysis.md)

## sigaltstack (#53)
- 入口：`kern_sig.c` → 写当前线程 `uu_sigstk`
- 一句话：登记备用信号栈；配合 `SA_ONSTACK` 让 handler 不在普通栈上跑

## __pthread_kill (#328)
- 入口：`port_name_to_thread` → `psignal_uthread`
- 一句话：按线程 Mach port 定向发信号；比 `kill(进程)` 更细

## 今日对比
- 共同点：都是信号路径的细化（栈在哪跑 / 投给谁）
- 最大差异：一个配置接收环境，一个指定投递目标线程
