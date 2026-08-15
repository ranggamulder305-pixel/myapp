[app]
title = Garang305
package.name = garang305
package.domain = org.garang305
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.2.1,pillow,srt,edge-tts,google-genai
orientation = portrait
fullscreen = 0
presplash.filename = %(source.dir)s/data/presplash.png
icon.filename = %(source.dir)s/icon.png
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.archs = arm64-v8a,armeabi-v7a
android.enable_androidx = True
[buildozer]
log_level = 2
warn_on_root = 1
