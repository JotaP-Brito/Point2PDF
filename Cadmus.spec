# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['cadmus.py'],
    pathex=[],
    binaries=[('gtk\\*.dll', 'gtk')],
    datas=[('index.html', '.'), ('CadmusLogo.png', '.'), ('Cadmus.ico', '.'), ('gifs', 'gifs')],
    hiddenimports=['pypdf', 'pytesseract', 'weasyprint', 'mammoth', 'pandas', 'PIL', 'fpdf'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Cadmus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version.txt',
    icon=['Cadmus.ico'],
)
