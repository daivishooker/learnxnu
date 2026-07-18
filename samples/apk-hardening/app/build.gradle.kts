/**
 * 片段示例：合并进真实 app 模块的 build.gradle.kts。
 * 非完整工程文件。
 */
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.hardening"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.hardening"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"

        // CI 注入：64 位大写十六进制，无冒号。Debug 可留空以跳过硬失败。
        val expectedCert = (project.findProperty("EXPECTED_CERT_SHA256") as String?)
            ?.trim()
            .orEmpty()
        buildConfigField("String", "EXPECTED_CERT_SHA256", "\"$expectedCert\"")

        externalNativeBuild {
            cmake {
                cppFlags += "-std=c++17"
            }
        }
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
            buildConfigField("boolean", "HARDENING_STRICT", "false")
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            buildConfigField("boolean", "HARDENING_STRICT", "true")
            // signingConfig = signingConfigs.getByName("release")
        }
    }

    buildFeatures {
        buildConfig = true
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
        }
    }
}
