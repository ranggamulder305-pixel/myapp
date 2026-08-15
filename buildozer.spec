[app]

# (str) Title of your application
title = Garang305

# (str) Package name
package.name = garang305

# (str) Package domain (needed for android/ios packaging)
package.domain = org.garang305

# (source.dir) Source code where the main.py live
source.dir = .

# (list) Source include patterns (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
requirements = python3,kivy==2.3.1,pillow,srt,edge-tts,google-genai

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash of the application
presplash.filename = %(source.dir)s/data/presplash.png

# (string) Icon of the application
icon.filename = %(source.dir)s/icon.png

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (bool) Enable AndroidX support
android.enable_androidx = True