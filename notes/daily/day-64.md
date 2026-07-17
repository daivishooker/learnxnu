# Day 64 — revoke / acct / gethostuuid / minherit / swapon

> **正文：** [docs/day-64.md](../../docs/day-64.md)  
> **分析：** [day-64-analysis.md](day-64-analysis.md)

## revoke (#56)
- 入口：设备 vnode → 属主/root → `VNOP_REVOKE`
- 一句话：吊销字符/块设备访问

## acct (#51)
- 入口：root 打开记账文件或 path=NULL 关闭
- 一句话：进程会计开关

## gethostuuid (#142)
- 入口：`IOBSDGetPlatformUUID` + copyout
- 一句话：读平台 UUID（常需 entitlement）

## minherit (#250)
- 入口：`mach_vm_inherit`
- 一句话：映射区 fork 继承策略

## swapon (#85)
- 本树 `ENOTSUP`
- 一句话：BSD 包装未实现

## 今日对比
- 共同点：杂项收尾；多个要特权或平台特性
- 最大差异：VFS 吊销/记账 vs VM 继承 vs 平台 UUID
