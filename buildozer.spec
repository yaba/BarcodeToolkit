[app]
title = BarcodeToolkit
package.name = barcodetoolkit
package.domain = pt.filipe
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 0.1
requirements = python3,kivy==2.3.1,pillow,python-barcode
orientation = landscape
fullscreen = 0
android.permissions = INTERNET, CAMERA
android.api = 34
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.release_artifact = apk
android.debug_artifact = apk

# Forçar uma versão do python-for-android que usa Python 3.11 (o master do p4a
# usa 3.14 e rebenta com wheels cp314). Esta tag alinha host(3.11)=target(3.11).
p4a.fork = kivy
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
