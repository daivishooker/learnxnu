# 05 · Native 与商业加固

## Native 能保护什么

把高价值逻辑放到 `.so`：

- 协议签名、本地许可证校验片段
- 反调试辅助（读 `TracerPid`、检测内存断点等）

构建时务必：

```bash
# CMake / ndk-build 默认 Release 会 strip；确认 .so 无多余符号
llvm-strip --strip-unneeded libxxx.so
```

注意：Native **不是**保险箱——IDA/Ghidra 仍可读；只是成本更高。

## SO 加固方向（概念）

1. 符号剥离 + 控制流平坦化（OLLVM 等，兼容性自负）
2. 关键字符串运行时解密
3. 与 Java 层交叉校验（双向，防单边被 nop）

本仓库 `native-guard.cpp` 仅示范轻量检测，不作对抗级壳。

## 商业加固选型清单

上壳前确认：

- [ ] 支持当前 AGP / targetSdk / 16KB page（新设备）
- [ ] 与多进程、热修复、插件化兼容
- [ ] 能导出映射 / 崩溃还原方案
- [ ] 过应用商店审核（加固标记、敏感权限）
- [ ] CI 可自动化（命令行加固 + 重签）

常见厂商（名字供检索，非背书）：乐固、梆梆、爱加密、360 加固保、网易易盾等。

## DIY vs 商业：决策

```text
有强对抗（外挂/盗版）且预算充足 → 商业壳 + Play Integrity + 服务端
普通工具/内容 App → R8 + 签名校验 + Keystore 足够
```
