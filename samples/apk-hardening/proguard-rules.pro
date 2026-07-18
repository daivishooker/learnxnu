# ---------------------------------------------------------------------------
# APK 加固基线：R8 / ProGuard 规则模板
# 复制到 app/proguard-rules.pro 后按项目裁剪，勿盲目全盘 keep。
# ---------------------------------------------------------------------------

# --- 崩溃还原：保留行号（可选，体积略增） ---
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# --- 注解 / 泛型（Gson、Retrofit 等常需要） ---
-keepattributes Signature,InnerClasses,EnclosingMethod
-keepattributes *Annotation*

# --- JNI：保留 native 方法名 ---
-keepclasseswithmembernames class * {
    native <methods>;
}

# --- 枚举 ---
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# --- Parcelable ---
-keepclassmembers class * implements android.os.Parcelable {
    public static final ** CREATOR;
}

# --- Serializable ---
-keepclassmembers class * implements java.io.Serializable {
    static final long serialVersionUID;
    private static final java.io.ObjectStreamField[] serialPersistentFields;
    private void writeObject(java.io.ObjectOutputStream);
    private void readObject(java.io.ObjectInputStream);
    java.lang.Object writeReplace();
    java.lang.Object readResolve();
}

# --- 加固引导类：若需被反射调用可 keep；默认允许混淆 ---
# -keep class com.example.hardening.HardeningBootstrap { *; }

# --- 示例：Kotlin Metadata（若反射依赖） ---
# -keep class kotlin.Metadata { *; }

# 第三方 SDK：优先使用 AAR 自带的 consumer-rules.pro，再在此补充。
