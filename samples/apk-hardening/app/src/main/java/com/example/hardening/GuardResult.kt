package com.example.hardening

/**
 * 加固检测结果。由产品层决定：上报、降级或阻断。
 */
data class GuardResult(
    val ok: Boolean,
    val reasons: List<String> = emptyList(),
) {
    companion object {
        fun success() = GuardResult(ok = true)

        fun failure(vararg reason: String) =
            GuardResult(ok = false, reasons = reason.toList())
    }
}
