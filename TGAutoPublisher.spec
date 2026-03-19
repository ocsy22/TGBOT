# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data')],
    hiddenimports=['PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.sip', 'telethon', 'telethon.sessions', 'telethon.sessions.string', 'aiohttp', 'aiofiles', 'cryptg', 'apscheduler', 'apscheduler.schedulers.background', 'socks', 'PIL', 'PIL.Image', 'core.database', 'core.ai_generator', 'core.video_processor', 'core.telegram_sender', 'core.task_engine', 'core.scheduler', 'ui.styles', 'ui.main_window', 'ui.pages.dashboard', 'ui.pages.channel_page', 'ui.pages.media_page', 'ui.pages.task_page', 'ui.pages.settings_page', 'ui.pages.other_pages'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],
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
    name='TGAutoPublisher',
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
)
