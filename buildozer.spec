[app]

title = CONTROLE DE FRETE

package.name = controledefrete

package.domain = org.almir

source.dir = .

source.include_exts = py,png,jpg,kv,atlas

icon.filename = %(source.dir)s/icone.png

version = 0.1

requirements = python3,kivy,charset-normalizer==2.1.1

orientation = portrait

fullscreen = 0

android.permissions =

android.api = 35

android.minapi = 24

android.archs = arm64-v8a

android.accept_sdk_license = True

p4a.branch = develop

[buildozer]

log_level = 2

warn_on_root = 1
