# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# 收集所有源码目录
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('core', 'core'),
        ('ui', 'ui'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',
        'PyQt6.QtNetwork', 'PyQt6.sip',
        # 项目模块
        'core', 'core.database', 'core.ai_generator', 'core.video_processor',
        'core.telegram_sender', 'core.task_engine', 'core.scheduler',
        'ui', 'ui.styles', 'ui.main_window',
        'ui.pages', 'ui.pages.dashboard', 'ui.pages.channel_page',
        'ui.pages.media_page', 'ui.pages.task_page',
        'ui.pages.settings_page', 'ui.pages.other_pages',
        # 第三方
        'telethon', 'telethon.sessions', 'telethon.sessions.string',
        'telethon.network', 'telethon.tl',
        'aiohttp', 'aiofiles', 'aiohttp.connector',
        'cryptg', 'apscheduler', 'apscheduler.schedulers',
        'apscheduler.schedulers.background',
        'socks', 'PIL', 'PIL.Image', 'PIL.ImageDraw',
        'requests', 'mutagen', 'openai',
        'sqlite3', 'asyncio', 'json', 'threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TGAutoPublisher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
