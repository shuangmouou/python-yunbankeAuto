# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py', 'api_manager.py', 'auto_process.py', 'browser_manager.py', 'exam_assistant.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('msedgedriver.exe', '.'),
        ('shm.ico', '.'),  # 图标文件
    ],
    hiddenimports=[
        'selenium', 'webdriver_manager', 'socket', 'lxml', 'zipfile', 'shutil',
        'packaging', 'packaging.version', 'packaging.specifiers'
    ],
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
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='shm.ico',  # 关键参数
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)