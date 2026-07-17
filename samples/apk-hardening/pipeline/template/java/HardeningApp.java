package com.hardening.shell;

import android.app.Application;
import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.content.pm.SigningInfo;
import android.os.Build;
import android.os.Debug;
import android.util.Log;

import java.io.BufferedReader;
import java.io.FileReader;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;

/**
 * 已有 APK 注入用 Application 壳（Java 参考实现）。
 * 流水线实际注入的是同逻辑的 smali：template/smali/.../HardeningApp.smali
 *
 * 能力：
 * 1. 签名证书 SHA-256 校验（meta-data / 常量）
 * 2. 调试器 / TracerPid 信号
 * 3. 委托并替换原 Application（ActivityThread）
 */
public class HardeningApp extends Application {
    private static final String TAG = "HardeningShell";
    private static final String META_ORIGINAL = "com.hardening.shell.ORIGINAL_APPLICATION";
    private static final String META_CERT = "com.hardening.shell.EXPECTED_CERT_SHA256";
    /** apktool 注入时可由脚本替换；运行时优先读 meta-data */
    private static final String DEFAULT_EXPECTED_CERT = "__EXPECTED_CERT_SHA256__";

    private Application realApplication;

    @Override
    protected void attachBaseContext(Context base) {
        super.attachBaseContext(base);
        String originalName = readMeta(base, META_ORIGINAL);
        if (originalName != null && originalName.length() > 0) {
            realApplication = createOriginalApplication(base, originalName);
            if (realApplication != null) {
                replaceApplication(realApplication);
            }
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        GuardReport report = evaluate(this);
        if (!report.ok) {
            Log.e(TAG, "guard_failed: " + report.reasons);
            // 默认不直接杀进程，避免误伤；需要硬失败可改为 android.os.Process.killProcess(...)
        } else {
            Log.i(TAG, "guard_ok");
        }
        if (realApplication != null) {
            realApplication.onCreate();
        }
    }

    private static Application createOriginalApplication(Context base, String name) {
        try {
            if (name.startsWith(".")) {
                name = base.getPackageName() + name;
            }
            Class<?> cls = Class.forName(name, false, base.getClassLoader());
            Application app = (Application) cls.newInstance();
            Method attach = Application.class.getDeclaredMethod("attach", Context.class);
            attach.setAccessible(true);
            attach.invoke(app, base);
            return app;
        } catch (Throwable t) {
            Log.e(TAG, "create_original_failed: " + name, t);
            return null;
        }
    }

    @SuppressWarnings("unchecked")
    private void replaceApplication(Application real) {
        try {
            Class<?> atClass = Class.forName("android.app.ActivityThread");
            Method current = atClass.getMethod("currentActivityThread");
            Object at = current.invoke(null);

            Field mInitial = atClass.getDeclaredField("mInitialApplication");
            mInitial.setAccessible(true);
            mInitial.set(at, real);

            Field mAll = atClass.getDeclaredField("mAllApplications");
            mAll.setAccessible(true);
            List<Application> list = (List<Application>) mAll.get(at);
            if (list != null) {
                list.remove(this);
                if (!list.contains(real)) {
                    list.add(real);
                }
            }

            // LoadedApk.mApplication
            Field mBound = atClass.getDeclaredField("mBoundApplication");
            mBound.setAccessible(true);
            Object loadedApk = mBound.get(at);
            if (loadedApk != null) {
                Field mApp = loadedApk.getClass().getDeclaredField("mApplication");
                mApp.setAccessible(true);
                mApp.set(loadedApk, real);

                Field mInfo = loadedApk.getClass().getDeclaredField("mApplicationInfo");
                mInfo.setAccessible(true);
                ApplicationInfo ai = (ApplicationInfo) mInfo.get(loadedApk);
                if (ai != null) {
                    ai.className = real.getClass().getName();
                }
            }
        } catch (Throwable t) {
            Log.w(TAG, "replace_application_partial_failed", t);
        }
    }

    private static String readMeta(Context context, String key) {
        try {
            ApplicationInfo ai = context.getPackageManager().getApplicationInfo(
                    context.getPackageName(), PackageManager.GET_META_DATA);
            if (ai.metaData == null) {
                return null;
            }
            Object v = ai.metaData.get(key);
            return v == null ? null : String.valueOf(v);
        } catch (Throwable t) {
            return null;
        }
    }

    static final class GuardReport {
        final boolean ok;
        final String reasons;

        GuardReport(boolean ok, String reasons) {
            this.ok = ok;
            this.reasons = reasons;
        }
    }

    static GuardReport evaluate(Context context) {
        List<String> reasons = new ArrayList<>();
        String expected = readMeta(context, META_CERT);
        if (expected == null || expected.length() == 0 || expected.contains("__EXPECTED")) {
            expected = DEFAULT_EXPECTED_CERT;
        }
        expected = expected.replace(":", "").replace(" ", "").toUpperCase();
        if (expected.length() == 64 && !expected.contains("__")) {
            String actual = currentCertSha256(context);
            if (actual == null) {
                reasons.add("cert_read_failed");
            } else if (!expected.equals(actual)) {
                reasons.add("cert_mismatch");
            }
        }
        if (Debug.isDebuggerConnected() || Debug.waitingForDebugger()) {
            reasons.add("debugger_connected");
        }
        if (tracerPid() > 0) {
            reasons.add("tracer_pid");
        }
        if (reasons.isEmpty()) {
            return new GuardReport(true, "");
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < reasons.size(); i++) {
            if (i > 0) sb.append(',');
            sb.append(reasons.get(i));
        }
        return new GuardReport(false, sb.toString());
    }

    private static int tracerPid() {
        try {
            BufferedReader r = new BufferedReader(new FileReader("/proc/self/status"));
            String line;
            while ((line = r.readLine()) != null) {
                if (line.startsWith("TracerPid:")) {
                    r.close();
                    return Integer.parseInt(line.substring(10).trim());
                }
            }
            r.close();
        } catch (Throwable ignored) {
        }
        return 0;
    }

    private static String currentCertSha256(Context context) {
        try {
            PackageManager pm = context.getPackageManager();
            String pkg = context.getPackageName();
            Signature[] signatures;
            if (Build.VERSION.SDK_INT >= 28) {
                PackageInfo pi = pm.getPackageInfo(pkg, PackageManager.GET_SIGNING_CERTIFICATES);
                SigningInfo si = pi.signingInfo;
                if (si == null) return null;
                signatures = si.hasMultipleSigners()
                        ? si.getApkContentsSigners()
                        : si.getSigningCertificateHistory();
            } else {
                PackageInfo pi = pm.getPackageInfo(pkg, PackageManager.GET_SIGNATURES);
                signatures = pi.signatures;
            }
            if (signatures == null || signatures.length == 0) return null;
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] dig = md.digest(signatures[0].toByteArray());
            StringBuilder sb = new StringBuilder(dig.length * 2);
            for (byte b : dig) {
                sb.append(String.format("%02X", b));
            }
            return sb.toString();
        } catch (Throwable t) {
            return null;
        }
    }
}
