plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val pwaUrl: String = (project.findProperty("PWA_URL") as? String)
    ?: "https://h17401792.github.io/daejeon-cashback-oil/"

android {
    namespace = "kr.daejeon.cashbackoil"
    compileSdk = 34

    defaultConfig {
        applicationId = "kr.daejeon.cashbackoil"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        buildConfigField("String", "PWA_URL", "\"$pwaUrl\"")
    }

    buildFeatures {
        buildConfig = true
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
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.webkit:webkit:1.11.0")
}
