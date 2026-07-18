# 02 · R8 混淆与收缩

## 做什么

R8 在 Release 构建中：

- **shrink**：删未引用代码/资源
- **obfuscate**：类/方法/字段改短名
- **optimize**：内联、去死代码

这是成本最低、收益最稳的一层。

## Gradle 要点

```kotlin
android {
    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

## 规则编写原则

1. **Keep 宁少勿滥**：反射、JNI、序列化、SPI 才 keep
2. **第三方 SDK**：优先用官方 consumer ProGuard 规则
3. **验证**：每次改规则后跑一次完整 Release + 冒烟
4. **mapping.txt**：归档到 CI 产物，否则线上堆栈无法还原

## 常见坑

| 现象 | 原因 | 处理 |
|------|------|------|
| Gson/Moshi 字段变 null | 字段被混淆/删除 | `@Keep` 或 `-keepclassmembers` |
| JNI `UnsatisfiedLinkError` | native 方法名被改 | `-keepclasseswithmembernames class * { native <methods>; }` |
| 反射找不到类 | 类名被改 | keep 被反射的类 |
| 资源 shrink 误删 | 仅动态拼接资源名 | `tools:keep` 或 `-keep` 资源 |

## 验收

- Release APK 用 jadx 打开：业务包名下大量 `a/b/c` 短名
- `mapping.txt` 已备份
- 核心用户路径冒烟通过
