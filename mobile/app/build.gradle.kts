import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

val appSettingsFile = rootProject.file("settings.properties")
val appSettings = Properties().apply {
    if (appSettingsFile.exists()) {
        appSettingsFile.inputStream().use { load(it) }
    }
}
val serverBase = appSettings.getProperty("server_base", "https://mybookwise.xyz")
    .trim()
    .removeSuffix("/")

android {
    namespace = "com.example.bookwiseapp"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.bookwiseapp"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "SERVER_BASE", "\"$serverBase\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    buildFeatures {
        buildConfig = true
        compose = true
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    // 网络
    implementation(libs.retrofit)
    implementation(libs.retrofit.gson)
    implementation(libs.okhttp.logging)
    // 导航
    implementation(libs.navigation.compose)
    // ViewModel
    implementation(libs.lifecycle.viewmodel.compose)
    // 图片加载
    implementation(libs.coil.compose)
    // Token 持久化
    implementation(libs.datastore.preferences)
    // 协程
    implementation(libs.kotlinx.coroutines.android)
    // Markdown 渲染 + 扩展图标
    implementation(libs.multiplatform.markdown.renderer.m3)
    implementation(libs.androidx.material.icons.extended)

    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
}
