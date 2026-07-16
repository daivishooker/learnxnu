# 源码分析：Day 18（sigaltstack / __pthread_kill）

基于 `xnu-12377.121.6`。信号栈与线程定向投递。

---

## 1. 心智模型（尽量不抽象）

```text
Day 17：规矩（action）+ 勿扰牌（mask）+ 门外名单（pending）

Day 18：
  sigaltstack     → 开门时站在玄关，不站在已经塌了一半的书桌前
  __pthread_kill  → 不朝整栋楼喊，只敲 3 楼那一户
```

---

## 2. sigaltstack 主路径

[`kern_sig.c`](../../xnu/bsd/kern/kern_sig.c)：

```
sigaltstack(nss, oss)
  uth = current_uthread()
  oss → copyout(uth->uu_sigstk)
  nss → copyin → 校验 flags/大小
       SA_DISABLE：关掉 UT_ALTSTACK
       否则：uth->uu_flag |= UT_ALTSTACK；保存 ss
```

真正递送时：若该信号 `SA_ONSTACK` 且线程有 altstack，handler 帧建在备用栈上。

经典动机：**SIGSEGV 因栈溢出触发时，不能再在原栈上跑 handler。**

---

## 3. __pthread_kill 主路径

```
__pthread_kill(thread_port, sig)
  thread = port_name_to_thread(thread_port)
  校验 signum、线程是否允许收（workq 等可能 ENOTSUP）
  psignal_uthread(thread, sig)
```

和 `kill`：

| | kill | __pthread_kill |
|--|------|----------------|
| 参数 | pid | thread_port |
| 解析 | `proc_find` | Mach port → `thread_t` |
| 投递 | 进程级 `psignal` | 线程级 `psignal_uthread` |

用户态 `pthread_kill` 通常拿到目标 pthread 对应的 Mach 口，再进这个 syscall。

---

## 4. 和前几天串起来

```
sigaction(SIGUSR1, handler + 可选 SA_ONSTACK)
sigaltstack(准备一块栈)          // 可选
__pthread_kill(某线程, SIGUSR1) // 或 kill(进程)
  → 该线程（或进程内某线程）递送
  → 若 ONSTACK：handler 在备用栈跑
```

---

## 5. 建议点开的文件

1. `syscalls.master` — 53 / 328  
2. `kern_sig.c` — `sigaltstack` 写 `uu_sigstk`  
3. `kern_sig.c` — `__pthread_kill` → `psignal_uthread`  
4. （对照）同文件 `kill`  

验收：能用一句话说清「备用栈」和「杀线程 vs 杀进程」。
