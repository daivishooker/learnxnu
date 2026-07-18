#!/usr/bin/env bash
# 对「已经有的 APK」做轻量加固：注入 Application 壳 → 回编 → 对齐 → 重签
# 仅用于自有 APK。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="${ROOT}/tools"
TEMPLATE_SMALI="${PIPELINE}/template/smali/com/hardening/shell/HardeningApp.smali"
INJECT_PY="${PIPELINE}/lib/inject_hardening.py"

APKTOOL_VER="2.11.1"
APKTOOL_URL="https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VER}/apktool_${APKTOOL_VER}.jar"
SIGNER_URL="https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar"

APK=""
KEYSTORE=""
ALIAS=""
STOREPASS=""
KEYPASS=""
CERT_SHA256=""
OUT_APK=""
WORK_DIR=""
RESIGN_ONLY=0
KEEP_WORK=0
STRICT_TOOLS=0

usage() {
  cat <<'EOF'
用法:
  harden-existing-apk.sh --apk <input.apk> --keystore <jks/keystore> --alias <alias> \
      --storepass <pass> [--keypass <pass>] [--cert-sha256 <HEX64>] --out <out.apk>

  harden-existing-apk.sh --resign-only --apk <protected.apk> --keystore ... --alias ... \
      --storepass ... --out <out.apk>

选项:
  --apk            输入 APK（已有包 / 商业壳输出包）
  --keystore       签名密钥库
  --alias          密钥别名
  --storepass      密钥库密码
  --keypass        密钥密码（默认同 storepass）
  --cert-sha256    期望证书 SHA-256（64位十六进制，可带冒号）；空则只注入不强制校验
  --out            输出 APK 路径
  --work-dir       工作目录（默认临时目录）
  --resign-only    跳过注入，只做 zipalign + 重签（商业壳后常用）
  --keep-work      保留反编译目录，便于排错
  -h, --help       帮助
EOF
}

log() { printf '[harden] %s\n' "$*"; }
die() { printf '[harden] ERROR: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apk) APK="${2:-}"; shift 2 ;;
    --keystore) KEYSTORE="${2:-}"; shift 2 ;;
    --alias) ALIAS="${2:-}"; shift 2 ;;
    --storepass) STOREPASS="${2:-}"; shift 2 ;;
    --keypass) KEYPASS="${2:-}"; shift 2 ;;
    --cert-sha256) CERT_SHA256="${2:-}"; shift 2 ;;
    --out) OUT_APK="${2:-}"; shift 2 ;;
    --work-dir) WORK_DIR="${2:-}"; shift 2 ;;
    --resign-only) RESIGN_ONLY=1; shift ;;
    --keep-work) KEEP_WORK=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "未知参数: $1" ;;
  esac
done

[[ -n "$APK" && -f "$APK" ]] || die "需要有效 --apk"
[[ -n "$KEYSTORE" && -f "$KEYSTORE" ]] || die "需要有效 --keystore"
[[ -n "$ALIAS" ]] || die "需要 --alias"
[[ -n "$STOREPASS" ]] || die "需要 --storepass"
[[ -n "$OUT_APK" ]] || die "需要 --out"
KEYPASS="${KEYPASS:-$STOREPASS}"

mkdir -p "$TOOLS_DIR"
APKTOOL_JAR="${TOOLS_DIR}/apktool.jar"
SIGNER_JAR="${TOOLS_DIR}/uber-apk-signer.jar"

ensure_tool() {
  local dest="$1" url="$2" label="$3"
  if [[ -f "$dest" ]]; then
    return 0
  fi
  log "下载 ${label} ..."
  curl -fsSL -o "${dest}.partial" "$url"
  mv "${dest}.partial" "$dest"
}

find_build_tool() {
  local name="$1"
  if [[ -n "${ANDROID_HOME:-}" && -x "${ANDROID_HOME}/build-tools" ]]; then
    local hit
    hit="$(ls -1d "${ANDROID_HOME}/build-tools"/*/"${name}" 2>/dev/null | sort -V | tail -1 || true)"
    if [[ -n "$hit" && -x "$hit" ]]; then
      echo "$hit"
      return 0
    fi
  fi
  local bundled
  bundled="$(ls -1d "${TOOLS_DIR}/build-tools-unpack"/*/"${name}" 2>/dev/null | sort -V | tail -1 || true)"
  if [[ -n "$bundled" && -x "$bundled" ]]; then
    echo "$bundled"
    return 0
  fi
  if command -v "$name" >/dev/null 2>&1; then
    command -v "$name"
    return 0
  fi
  return 1
}

ensure_tool "$APKTOOL_JAR" "$APKTOOL_URL" "apktool ${APKTOOL_VER}"
ensure_tool "$SIGNER_JAR" "$SIGNER_URL" "uber-apk-signer"

command -v java >/dev/null || die "需要 java"
command -v python3 >/dev/null || die "需要 python3"
[[ -f "$INJECT_PY" ]] || die "缺少 ${INJECT_PY}"
[[ -f "$TEMPLATE_SMALI" ]] || die "缺少 smali 模板: ${TEMPLATE_SMALI}"

APK="$(cd "$(dirname "$APK")" && pwd)/$(basename "$APK")"
KEYSTORE="$(cd "$(dirname "$KEYSTORE")" && pwd)/$(basename "$KEYSTORE")"
mkdir -p "$(dirname "$OUT_APK")"
OUT_APK="$(cd "$(dirname "$OUT_APK")" && pwd)/$(basename "$OUT_APK")"

CLEANUP_DIR=""
if [[ -z "$WORK_DIR" ]]; then
  WORK_DIR="$(mktemp -d -t apk-harden-XXXXXX)"
  CLEANUP_DIR="$WORK_DIR"
fi
mkdir -p "$WORK_DIR"
DECODED="${WORK_DIR}/decoded"
BUILT_UNSIGNED="${WORK_DIR}/built-unsigned.apk"
ALIGNED="${WORK_DIR}/aligned.apk"

cleanup() {
  if [[ "$KEEP_WORK" -eq 0 && -n "$CLEANUP_DIR" && -d "$CLEANUP_DIR" ]]; then
    rm -rf "$CLEANUP_DIR"
  fi
}
trap cleanup EXIT

apktool() { java -jar "$APKTOOL_JAR" "$@"; }

if [[ "$RESIGN_ONLY" -eq 0 ]]; then
  log "反编译: $APK"
  rm -rf "$DECODED"
  apktool d -f -o "$DECODED" "$APK"

  log "注入加固壳"
  # 同步注入内部类
  SHELL_DIR="${DECODED}/smali/com/hardening/shell"
  mkdir -p "$SHELL_DIR"
  python3 "$INJECT_PY" \
    --decoded-dir "$DECODED" \
    --template-smali "$TEMPLATE_SMALI" \
    --cert-sha256 "$CERT_SHA256"

  TEMPLATE_DIR="${PIPELINE}/template/smali/com/hardening/shell"
  for f in "$TEMPLATE_DIR"/*.smali; do
    base="$(basename "$f")"
    if [[ "$base" == "HardeningApp.smali" ]]; then
      continue
    fi
    cp "$f" "${SHELL_DIR}/${base}"
  done

  log "回编 APK"
  apktool b -o "$BUILT_UNSIGNED" "$DECODED"
  SIGN_INPUT="$BUILT_UNSIGNED"
else
  log "仅重签模式"
  SIGN_INPUT="$APK"
fi

ZIPALIGN_BIN=""
if ZIPALIGN_BIN="$(find_build_tool zipalign)"; then
  log "zipalign: $ZIPALIGN_BIN"
  "$ZIPALIGN_BIN" -f -p 4 "$SIGN_INPUT" "$ALIGNED"
  SIGN_INPUT="$ALIGNED"
else
  log "未找到 zipalign，跳过对齐（建议安装 Android build-tools）"
fi

log "签名 -> $OUT_APK"
# uber-apk-signer 会写出 *-aligned-debugSigned 等名字；用 --out 目录再搬运
SIGN_OUT_DIR="${WORK_DIR}/signed"
rm -rf "$SIGN_OUT_DIR"
mkdir -p "$SIGN_OUT_DIR"
java -jar "$SIGNER_JAR" \
  -a "$SIGN_INPUT" \
  --ks "$KEYSTORE" \
  --ksAlias "$ALIAS" \
  --ksPass "$STOREPASS" \
  --ksKeyPass "$KEYPASS" \
  -o "$SIGN_OUT_DIR" \
  --allowResign

SIGNED_FILE="$(find "$SIGN_OUT_DIR" -type f -name '*.apk' | head -1 || true)"
[[ -n "$SIGNED_FILE" ]] || die "签名后未找到 APK"
cp -f "$SIGNED_FILE" "$OUT_APK"

log "完成: $OUT_APK"
log "安装前请真机冒烟；若原包有自定义 Application，请确认业务启动正常。"
if [[ "$KEEP_WORK" -eq 1 ]]; then
  log "工作目录保留: $WORK_DIR"
fi
