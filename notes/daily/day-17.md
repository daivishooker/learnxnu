# Day 17 — sigaction / sigprocmask / sigpending

> **正文：** [docs/day-17.md](../../docs/day-17.md)  
> **分析：** [day-17-analysis.md](day-17-analysis.md)

## sigaction (#46)
- 入口：`kern_sig.c` → `sigaction` → `setsigvec`
- 一句话：设置/查询某信号的处理（DFL / IGN / handler）；KILL/STOP 除外

## sigprocmask (#48)
- 入口：`sigprocmask` 改当前线程 `uu_sigmask`
- 一句话：BLOCK/UNBLOCK/SETMASK；被挡的信号可挂起稍后递送

## sigpending (#52)
- 入口：读 `uu_siglist` 并 copyout
- 一句话：查看当前未决信号集

## 今日对比
- 共同点：都是信号接收侧控制/查询
- 最大差异：action 定“怎么处理”，mask 定“现在能不能递送”，pending 看“堆着什么”
