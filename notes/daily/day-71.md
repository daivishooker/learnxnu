# Day 71 — __semwait_signal / iopolicysys / process_policy / settid / gettid

> **正文：** [docs/day-71.md](../../docs/day-71.md)  
> **分析：** [day-71-analysis.md](day-71-analysis.md)

## 归属
- `__semwait_signal`：**BSD→Mach**（Mach semaphore）  
- `iopolicysys`：**BSD**  
- `process_policy`：**BSD→Mach**  
- `sys_settid` / `gettid`：**BSD**（线程凭证覆盖，不是线程 ID）

## 一句话
- semwait：POSIX/旧同步对 Mach 信号量的等待包装  
- iopolicysys / process_policy：I/O 与进程/线程策略 MUX  
- settid/gettid：线程级假身份；**别当成 Linux tid**
