package com.example.hardening

import android.content.Context
import android.util.Log

/**
 * 应用启动时调用一次。根据 BuildConfig.HARDENING_STRICT 决定是否硬失败。
 *
 * 接入示例：
 * ```
 * class App : Application() {
 *   override fun onCreate() {
 *     super.onCreate()
 *     HardeningBootstrap.init(this)
 *   }
 * }
 * ```
 */
object HardeningBootstrap {
    private const val TAG = "Hardening"

    data class Report(
        val integrity: GuardResult,
        val runtime: GuardResult,
        val nativeTracerPid: Int,
        val installer: String,
    ) {
        val ok: Boolean get() = integrity.ok && runtime.ok
        val allReasons: List<String>
            get() = integrity.reasons + runtime.reasons
    }

    fun init(context: Context): Report {
        val app = context.applicationContext
        val expected = BuildConfig.EXPECTED_CERT_SHA256
        val integrity = IntegrityGuard.verifySigningCert(app, expected)
        val runtime = RuntimeGuard.evaluate(app)
        val nativePid = NativeGuard.nativeTracerPid()
        val installer = IntegrityGuard.installSource(app)

        val report = Report(
            integrity = integrity,
            runtime = runtime,
            nativeTracerPid = nativePid,
            installer = installer,
        )

        if (!report.ok) {
            Log.w(TAG, "guard_failed reasons=${report.allReasons} installer=$installer nativeTracer=$nativePid")
            // TODO: 上报到你的风控/遥测管道
            if (BuildConfig.HARDENING_STRICT) {
                // 严格模式：由宿主决定是否结束进程或进入受限模式。
                // 默认只记录，避免样例误杀开发机。
                Log.e(TAG, "HARDENING_STRICT=true but sample refuses to kill; wire your own policy.")
            }
        } else {
            Log.i(TAG, "guard_ok installer=$installer")
        }

        return report
    }
}
