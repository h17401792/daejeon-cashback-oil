# Keep WebView JS bridge methods
-keepclassmembers class kr.daejeon.cashbackoil.MainActivity$AndroidBridge {
    @android.webkit.JavascriptInterface <methods>;
}
