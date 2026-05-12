# TomatoCare ProGuard rules.

# kotlinx.serialization — keep @Serializable generated companions.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.SerializationKt
-keep,includedescriptorclasses class com.tomatocare.**$$serializer { *; }
-keepclassmembers class com.tomatocare.** {
    *** Companion;
}
-keepclasseswithmembers class com.tomatocare.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# TensorFlow Lite — preserve all interpreter classes; the support library
# reflects into these at runtime for delegate registration.
-keep class org.tensorflow.lite.** { *; }
-keep class org.tensorflow.lite.support.** { *; }
-dontwarn org.tensorflow.lite.**
