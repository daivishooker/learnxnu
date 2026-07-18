# 已有 APK 加固流水线

输入一份**已经编好的 APK**，注入轻量 Application 壳后重签输出。

```text
app-release.apk  →  apktool 反编译  →  注入 HardeningApp  →  回编  →  zipalign  →  签名
                         ↑
              或商业壳加固后再 --resign-only
```

## 依赖

- `java`、`python3`、`curl`
- 首次运行自动下载：`apktool`、`uber-apk-signer` → `../tools/`
- 可选：`ANDROID_HOME` 下的 `zipalign`（更佳）

## 快速用

```bash
chmod +x harden-existing-apk.sh

./harden-existing-apk.sh \
  --apk ~/releases/app-release.apk \
  --keystore ~/keys/release.jks \
  --alias myalias \
  --storepass 'store-pass' \
  --keypass 'key-pass' \
  --cert-sha256 "$(keytool -list -v -keystore ~/keys/release.jks -alias myalias -storepass 'store-pass' \
      | awk -F'SHA256: ' '/SHA256:/{print $2}' | tr -d ':' | tr 'a-f' 'A-F')" \
  --out ~/releases/app-hardened.apk
```

### 商业壳之后只重签

```bash
./harden-existing-apk.sh \
  --resign-only \
  --apk ~/releases/app-legu.apk \
  --keystore ~/keys/release.jks \
  --alias myalias \
  --storepass 'store-pass' \
  --out ~/releases/app-legu-signed.apk
```

## 壳做了什么

| 项 | 行为 |
|----|------|
| Manifest | `android:name` 改为 `com.hardening.shell.HardeningApp` |
| 原 Application | 写入 meta-data，启动时反射创建并替换进 `ActivityThread` |
| 签名校验 | 比对 meta-data / 常量中的证书 SHA-256 |
| 反调试信号 | `Debug.isDebuggerConnected`、`TracerPid`（默认只打日志） |

这是**轻量运行时防护**，不是 DEX 全加密商业壳。深度对抗请接厂商加固后再用本脚本重签。

## 排错

| 现象 | 处理 |
|------|------|
| apktool 回编失败 | 加 `--keep-work` 看 `decoded/`；复杂资源包可能需更高版本 apktool |
| 启动 ClassCastException | 原 Application 替换失败；保留 `--keep-work` 查 logcat `HardeningShell` |
| 安装解析失败 | 确认已重签；尽量提供 `zipalign` |
| 签名校验总失败 | `--cert-sha256` 必须与**最终签名证书**一致（含 Play 重签场景） |

## 目录

```
harden-existing-apk.sh     # 入口
lib/inject_hardening.py    # Manifest + smali 注入
template/java/             # 壳的 Java 参考源码
template/smali/            # 实际注入的 smali
```
