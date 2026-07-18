#!/usr/bin/env python3
"""将加固 Application 壳注入 apktool 反编译目录，并改写 AndroidManifest.xml。"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

NS_ANDROID = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", NS_ANDROID)

HARDENING_APP = "com.hardening.shell.HardeningApp"
META_ORIGINAL_APP = "com.hardening.shell.ORIGINAL_APPLICATION"
META_EXPECTED_CERT = "com.hardening.shell.EXPECTED_CERT_SHA256"


def android_attr(name: str) -> str:
    return f"{{{NS_ANDROID}}}{name}"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_cert(hex_str: str) -> str:
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", hex_str or "")
    if cleaned and len(cleaned) != 64:
        raise SystemExit(f"EXPECTED_CERT_SHA256 应为 64 位十六进制，当前长度={len(cleaned)}")
    return cleaned.upper()


def patch_manifest(decoded_dir: Path, expected_cert: str) -> str | None:
    manifest_path = decoded_dir / "AndroidManifest.xml"
    if not manifest_path.is_file():
        raise SystemExit(f"找不到 AndroidManifest.xml: {manifest_path}")

    # apktool 输出通常带命名空间；用 ElementTree 解析
    tree = ET.parse(manifest_path)
    root = tree.getroot()
    app = root.find("application")
    if app is None:
        raise SystemExit("AndroidManifest.xml 中没有 <application>")

    original = app.get(android_attr("name"))
    # 已注入过则保留原 meta，只更新证书
    if original == HARDENING_APP:
        original_meta = None
        for meta in app.findall("meta-data"):
            if meta.get(android_attr("name")) == META_ORIGINAL_APP:
                original_meta = meta.get(android_attr("value"))
                break
        original = original_meta
    else:
        app.set(android_attr("name"), HARDENING_APP)

    def upsert_meta(name: str, value: str) -> None:
        for meta in app.findall("meta-data"):
            if meta.get(android_attr("name")) == name:
                meta.set(android_attr("value"), value)
                return
        meta = ET.SubElement(app, "meta-data")
        meta.set(android_attr("name"), name)
        meta.set(android_attr("value"), value)

    if original:
        # 去掉前导点：相对 applicationId 的短名留给壳去解析
        upsert_meta(META_ORIGINAL_APP, original)
    upsert_meta(META_EXPECTED_CERT, expected_cert)

    # 保持较可读的声明顺序：先写回
    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)
    return original


def inject_smali(decoded_dir: Path, template_smali: Path, expected_cert: str) -> None:
    if not template_smali.is_file():
        raise SystemExit(f"缺少 smali 模板: {template_smali}")

    # 选择已有 smali 根（优先 smali/，否则 smali_classesN）
    smali_roots = sorted(decoded_dir.glob("smali*"))
    if not smali_roots:
        smali_root = decoded_dir / "smali"
        smali_root.mkdir(parents=True, exist_ok=True)
    else:
        # 放到主 dex（smali）以尽早加载
        preferred = decoded_dir / "smali"
        smali_root = preferred if preferred in smali_roots else smali_roots[0]

    target = smali_root / "com" / "hardening" / "shell" / "HardeningApp.smali"
    content = read_text(template_smali)
    # 模板内也可被 meta-data 覆盖；此处写入默认常量作后备
    content = content.replace("__EXPECTED_CERT_SHA256__", expected_cert)
    write_text(target, content)
    print(f"[inject] smali -> {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description="注入 APK 加固壳")
    parser.add_argument("--decoded-dir", required=True, type=Path)
    parser.add_argument("--template-smali", required=True, type=Path)
    parser.add_argument("--cert-sha256", default="", help="期望签名证书 SHA-256（可空=仅采集不校验）")
    args = parser.parse_args()

    decoded = args.decoded_dir.resolve()
    if not decoded.is_dir():
        raise SystemExit(f"反编译目录不存在: {decoded}")

    expected = normalize_cert(args.cert_sha256)
    original = patch_manifest(decoded, expected)
    inject_smali(decoded, args.template_smali.resolve(), expected)

    print(f"[inject] application -> {HARDENING_APP}")
    print(f"[inject] original application -> {original or '(none)'}")
    print(f"[inject] expected cert -> {expected or '(empty, skip hard check)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
