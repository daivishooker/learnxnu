package com.example.hardening

import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import java.security.MessageDigest

/**
 * 安装包签名完整性：比对当前证书 SHA-256 与期望指纹。
 *
 * 期望指纹来自 BuildConfig（CI 注入），避免手写进业务逻辑散落各处。
 */
object IntegrityGuard {

    fun verifySigningCert(context: Context, expectedSha256Hex: String): GuardResult {
        if (expectedSha256Hex.isBlank()) {
            // 未配置期望指纹时跳过（本地 Debug 常见）
            return GuardResult.success()
        }

        val actual = runCatching { currentCertSha256(context) }
            .getOrElse { return GuardResult.failure("cert_read_failed:${it.javaClass.simpleName}") }

        val normalizedExpected = normalizeHex(expectedSha256Hex)
        return if (actual == normalizedExpected) {
            GuardResult.success()
        } else {
            GuardResult.failure("cert_mismatch")
        }
    }

    fun installSource(context: Context): String {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val info = context.packageManager.getInstallSourceInfo(context.packageName)
            info.installingPackageName ?: "unknown"
        } else {
            @Suppress("DEPRECATION")
            context.packageManager.getInstallerPackageName(context.packageName) ?: "unknown"
        }
    }

    @SuppressLint("PackageManagerGetSignatures")
    private fun currentCertSha256(context: Context): String {
        val pm = context.packageManager
        val packageName = context.packageName

        val signatures = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            val info = pm.getPackageInfo(packageName, PackageManager.GET_SIGNING_CERTIFICATES)
            val signingInfo = info.signingInfo
                ?: throw IllegalStateException("signingInfo_null")
            if (signingInfo.hasMultipleSigners()) {
                signingInfo.apkContentsSigners
            } else {
                signingInfo.signingCertificateHistory
            }
        } else {
            @Suppress("DEPRECATION")
            val info = pm.getPackageInfo(packageName, PackageManager.GET_SIGNATURES)
            @Suppress("DEPRECATION")
            info.signatures ?: emptyArray()
        }

        val first = signatures.firstOrNull()
            ?: throw IllegalStateException("no_signature")
        return sha256Hex(first.toByteArray())
    }

    private fun sha256Hex(bytes: ByteArray): String {
        val digest = MessageDigest.getInstance("SHA-256").digest(bytes)
        return digest.joinToString("") { b -> "%02X".format(b) }
    }

    private fun normalizeHex(value: String): String =
        value.trim().replace(":", "").replace(" ", "").uppercase()
}
