# Day 12 — execve / exit

> **正文：** [docs/day-12.md](../../docs/day-12.md)  
> **分析：** [day-12-analysis.md](day-12-analysis.md)

## execve (#59)
- 入口：`kern_exec.c` → `execve` → `__mac_execve` → `exec_activate_image`
- master：`59 AUE_EXECVE … execve(char *fname, char **argp, char **envp)`
- 一句话：用新可执行映像替换当前进程；成功不回到旧代码；本树经 `CLONEPROC_EXEC` 再切换

## exit (#1)
- 入口：`kern_exit.c` → `exit` → `exit1` → `exit_with_reason` →（末线程）`proc_exit`
- master：`1 AUE_EXIT … void exit(int rval)`
- 一句话：收资源、变僵尸、通知父进程；不返回用户态

## 今日对比
- 共同点：都是进程生命周期的「换轨/收尾」，成功路径都不像普通 syscall 那样回到原用户代码
- 最大差异：`execve` 换程序继续活；`exit` 结束并留下僵尸等 `wait*`
