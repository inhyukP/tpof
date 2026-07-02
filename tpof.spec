# -*- mode: python ; coding: utf-8 -*-

import sys

from PyInstaller.utils.hooks import collect_submodules


block_cipher = None

datas = [
    ("assets", "assets"),
    ("fonts", "fonts"),
    ("static", "static"),
    ("templates", "templates"),
]

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "app",
        "flask",
        "jinja2",
        "werkzeug",
        "click",
        "itsdangerous",
        "markupsafe",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "PIL.ImageOps",
        "waitress",
    ]
    + collect_submodules("flask")
    + collect_submodules("jinja2")
    + collect_submodules("werkzeug")
    + collect_submodules("waitress"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_options = {
    "name": "TPOF",
    "debug": False,
    "bootloader_ignore_signals": False,
    "strip": False,
    "upx": True,
    "console": False,
    "disable_windowed_traceback": False,
    "argv_emulation": False,
    "target_arch": None,
    "codesign_identity": None,
    "entitlements_file": None,
}

if sys.platform == "win32":
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        **exe_options,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        **exe_options,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="TPOF",
    )

    if sys.platform == "darwin":
        app = BUNDLE(
            coll,
            name="TPOF.app",
            icon=None,
            bundle_identifier="com.inhyukp.tpof",
        )
