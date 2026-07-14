# Vendored XNU source

| Field | Value |
|-------|-------|
| Version | `xnu-12377.121.6` |
| Upstream | https://github.com/apple-oss-distributions/xnu |
| Tag | `xnu-12377.121.6` |
| Upstream commit | `ac9718fb1af618d5ce8678d0dc6e8a58f252216f` |
| Imported from | https://github.com/apple-oss-distributions/xnu/archive/refs/tags/xnu-12377.121.6.tar.gz |
| License | Apple Public Source License (see `APPLE_LICENSE`) |
| Imported date | 2026-07-14 |

This tree is an unmodified first copy of the latest published XNU tag at import time, for local study (system calls, Mach, BSD, etc.).

## Syscall study entry points

- `bsd/kern/syscalls.master` — BSD syscall table source
- `libsyscall/` — userland syscall stubs
- `osfmk/` — Mach kernel / traps / VM / IPC
- `bsd/` — BSD subsystem (process, VFS, networking, …)
