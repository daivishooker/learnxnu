package com.example.hardening

/**
 * JNI 桥接：把易被 smali NOP 的检测放到 native。
 * 库名需与 CMake 中 `native-guard` 一致。
 */
object NativeGuard {
    private var available: Boolean = false

    init {
        available = runCatching {
            System.loadLibrary("native-guard")
            true
        }.getOrDefault(false)
    }

    fun isAvailable(): Boolean = available

    /** native 侧 TracerPid；库不可用时返回 -1。 */
    fun nativeTracerPid(): Int {
        if (!available) return -1
        return runCatching { nativeTracerPidInternal() }.getOrDefault(-1)
    }

    private external fun nativeTracerPidInternal(): Int
}
