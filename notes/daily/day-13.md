# Day 13 — posix_spawn / kill

> **正文：** [docs/day-13.md](../../docs/day-13.md)  
> **分析：** [day-13-analysis.md](day-13-analysis.md)

## posix_spawn (#244)
- 入口：`kern_exec.c` → `posix_spawn`
- master：`244 … posix_spawn(pid_t *pid, const char *path, … argv, envp)`
- 一句话：一步创建子进程并装映像；默认 `fork1(SPAWN)` + `exec_activate_image`；`SETEXEC` 则像带选项的 exec

## kill (#37)
- 入口：`kern_sig.c` → `kill` → `cansignal` → `psignal`（或 `killpg1`）
- master：`37 … kill(int pid, int signum, int posix)`
- 一句话：按 pid/进程组找目标，过权限后投递信号

## 今日对比
- 共同点：都是进程间协作入口（一个造进程，一个发信号）
- 最大差异：spawn 改生命周期；kill 只投递事件，不换映像
