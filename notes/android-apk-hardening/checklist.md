# APK 加固发布检查清单

## 已有 APK 流水线（主）

- [ ] 输入包已是最终业务包（有工程则已开 R8）
- [ ] 已跑 `pipeline/harden-existing-apk.sh` 或商业壳
- [ ] `--cert-sha256` 与**最终分发证书**一致
- [ ] 输出包可安装；冷启动 / 登录 / 关键页冒烟通过
- [ ] logcat 无意外的 `HardeningShell` / `cert_mismatch`
- [ ] 工作密钥库不在 git；CI 用密钥保管服务

## 商业壳（如有）

- [ ] 厂商工具版本锁定
- [ ] 加固后按厂商要求重签（可用 `--resign-only`）
- [ ] 多进程 / 热修复 / 推送兼容已验证

## 有工程时的构建补充

- [ ] `release` 开启 `minifyEnabled` + `shrinkResources`
- [ ] `mapping.txt` 已按版本归档
- [ ] 敏感 API 有服务端二次鉴权

## 合规

- [ ] 隐私政策与实际采集一致（含完整性/设备信号）
- [ ] 无多余高危权限
