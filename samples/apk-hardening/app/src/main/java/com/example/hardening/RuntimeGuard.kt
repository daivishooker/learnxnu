package com.example.hardening

import android.content.Context
import android.os.Debug
import java.io.BufferedReader
import java.io.FileReader

/**
 * 运行时环境信号采集。结果宜上报服务端，谨慎在客户端直接杀进程。
 */
object RuntimeGuard {

    fun evaluate(context: Context): GuardResult {
        val reasons = mutableListOf<String>()

        if (Debug.isDebuggerConnected() || Debug.waitingForDebugger()) {
            reasons += "debugger_connected"
        }

        if (tracerPid() != 0) {
            reasons += "tracer_pid"
        }

        if (isLikelyEmulator()) {
            reasons += "emulator_heuristic"
        }

        val installer = IntegrityGuard.installSource(context)
        if (installer == "unknown" || installer.isBlank()) {
            reasons += "sideload_or_unknown_installer"
        }

        return if (reasons.isEmpty()) {
            GuardResult.success()
        } else {
            GuardResult(ok = false, reasons = reasons)
        }
    }

    /** 读取 /proc/self/status 中的 TracerPid；非 0 表示可能被 ptrace。 */
    fun tracerPid(): Int {
        return runCatching {
            BufferedReader(FileReader("/proc/self/status")).use { reader ->
                reader.lineSequence()
                    .firstOrNull { it.startsWith("TracerPid:") }
                    ?.substringAfter(":")
                    ?.trim()
                    ?.toIntOrNull()
                    ?: 0
            }
        }.getOrDefault(0)
    }

    /**
     * 极简模拟器启发式，误报可能存在；仅作风险分，勿单独作为封禁依据。
     */
    fun isLikelyEmulator(): Boolean {
        val fingerprint = listOf(
            android.os.Build.FINGERPRINT,
            android.os.Build.MODEL,
            android.os.Build.MANUFACTURER,
            android.os.Build.BRAND,
            android.os.Build.DEVICE,
            android.os.Build.PRODUCT,
        ).joinToString("|").lowercase()

        val markers = listOf(
            "generic",
            "emulator",
            "android sdk built for",
            "genymotion",
            "sdk_gphone",
            "goldfish",
            "ranchu",
        )
        return markers.any { fingerprint.contains(it) }
    }
}
