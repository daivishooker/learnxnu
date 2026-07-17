# 04 · 运行时防护

## 反调试（常见信号）

| 信号 | 含义 |
|------|------|
| `Debug.isDebuggerConnected()` | JDWP 调试器已连 |
| `/proc/self/status` 的 `TracerPid` | 被 ptrace |
| 可疑进程/端口 | Frida server 等（误报高，慎用） |

策略建议：

1. 检测到风险 → **上报 + 降敏感功能**，不必立即 `killProcess`
2. 检测放在 native 更难被 smali 一键 nop（仍可被绕过）
3. 与业务票据绑定：服务端看到风险分则拒发敏感数据

## Root / 模拟器

启发式检测（文件路径、`su`、已知模拟器属性）只作参考：

- 误报：部分定制 ROM、模拟器合法测试
- 漏报：隐藏 Root、Magisk DenyList

金融类可结合 Play Integrity 的设备完整性档位。

## 资产保护

- **不要**把长期密钥、对称加密主密钥写进 APK
- 短期会话密钥用 Android Keystore / StrongBox
- URL/开关可用简单 XOR/AES 混淆抬静态成本，但**不是密钥管理**

## 与 Frida 的对抗现实

公开的「反 Frida」清单很快失效。可持续做法是：

1. 缩小客户端信任边界
2. 关键操作服务端二次校验
3. 异常行为风控，而非单点检测
