plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}
// Resolve the real API 35 simulation runtime through Gradle. Robolectric's
// own Maven staging directory creation fails in the Windows sandbox.
val robolectricRuntime by configurations.creating
android {
    namespace = "com.praxis.caller"
    compileSdk = 37
    buildToolsVersion = "37.0.0"
    defaultConfig {
        applicationId = "com.praxis.caller"
        minSdk = 29
        targetSdk = 37
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures { compose = true }
    testOptions {
        unitTests.isIncludeAndroidResources = true
        unitTests.all {
            it.systemProperty("praxis.render.dir", rootProject.file("evidence/ui-host").absolutePath)
            it.systemProperty("user.home", rootProject.file(".local/test-home").absolutePath)
            it.systemProperty("java.io.tmpdir", rootProject.file(".local/test-temp").absolutePath)
            it.systemProperty("robolectric.offline", "true")
            it.doFirst {
                rootProject.file(".local/test-home").mkdirs()
                rootProject.file(".local/test-temp").mkdirs()
                it.systemProperty("robolectric.dependency.dir", robolectricRuntime.singleFile.parent)
            }
        }
    }
    sourceSets["test"].resources.srcDir("../contracts/examples")
    lint { abortOnError = true }
}
dependencies {
    implementation(files("../artifacts/praxis-runtime-release.aar"))
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.1")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    testImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
    robolectricRuntime("org.robolectric:android-all-instrumented:15-robolectric-13954326-i7")
    implementation(platform("androidx.compose:compose-bom:2025.08.01"))
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.1")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-core")
    debugImplementation("androidx.compose.ui:ui-tooling")
    testImplementation(platform("androidx.compose:compose-bom:2025.08.01"))
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.robolectric:robolectric:4.16.1")
    testImplementation("androidx.test:core:1.6.1")
    testImplementation("androidx.compose.ui:ui-test-junit4")
}
