# 06 · 在已有 APK 上加固

## 场景

- 只有 Release APK，没有完整工程  
- 外包/CI 已出包，要在发布前再套一层防护  
- 先用商业壳加密 DEX，再统一重签  

## 流水线心智模型

```text
输入 APK
  ├─ DIY：apktool → 注入 Application 壳 → 回编 → 签名
  └─ 商业壳：厂商处理 DEX/SO → （常需）再签名
输出 APK → 安装冒烟 → 上架/分发
```

本仓库入口：`samples/apk-hardening/pipeline/harden-existing-apk.sh`

## 注入壳如何挂上原 Application

1. 读取原 `AndroidManifest.xml` 的 `application@android:name`  
2. 改成 `com.hardening.shell.HardeningApp`  
3. 原类名写入 `meta-data`：`com.hardening.shell.ORIGINAL_APPLICATION`  
4. 壳在 `attachBaseContext` 里 `new` 原 Application，调用隐藏的 `attach()`，再写回 `ActivityThread`  

这样 `getApplication()` 仍尽量回到业务自定义 Application，降低 ClassCast 风险。

## 与源码期加固的分工

| 已出包可做 | 需回工程做 |
|------------|------------|
| 商业壳、注入运行时检测、重签 | R8 混淆、Play Integrity SDK、业务密钥下沉 |

## 验收

1. 用正式证书签名后可安装  
2. 篡改重签（错误证书）时 logcat 出现 `cert_mismatch`  
3. 主路径：启动、登录、支付相关页可用  
