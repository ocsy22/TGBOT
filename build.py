#!/usr/bin/env python3
"""
构建脚本 - 生成Windows可执行文件
"""
import os
import sys
import subprocess
import shutil


def build():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    print("=" * 60)
    print("TG Auto Publisher - 构建 Windows EXE")
    print("=" * 60)

    # 清理旧的构建
    for dir_name in ['dist', 'build', '__pycache__']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"清理: {dir_name}")

    # 构建命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name', 'TGAutoPublisher',
        '--add-data', 'data:data',
        '--hidden-import', 'PyQt6',
        '--hidden-import', 'PyQt6.QtWidgets',
        '--hidden-import', 'PyQt6.QtCore',
        '--hidden-import', 'PyQt6.QtGui',
        '--hidden-import', 'PyQt6.sip',
        '--hidden-import', 'telethon',
        '--hidden-import', 'telethon.sessions',
        '--hidden-import', 'telethon.sessions.string',
        '--hidden-import', 'aiohttp',
        '--hidden-import', 'aiofiles',
        '--hidden-import', 'cryptg',
        '--hidden-import', 'apscheduler',
        '--hidden-import', 'apscheduler.schedulers.background',
        '--hidden-import', 'socks',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.Image',
        '--hidden-import', 'core.database',
        '--hidden-import', 'core.ai_generator',
        '--hidden-import', 'core.video_processor',
        '--hidden-import', 'core.telegram_sender',
        '--hidden-import', 'core.task_engine',
        '--hidden-import', 'core.scheduler',
        '--hidden-import', 'ui.styles',
        '--hidden-import', 'ui.main_window',
        '--hidden-import', 'ui.pages.dashboard',
        '--hidden-import', 'ui.pages.channel_page',
        '--hidden-import', 'ui.pages.media_page',
        '--hidden-import', 'ui.pages.task_page',
        '--hidden-import', 'ui.pages.settings_page',
        '--hidden-import', 'ui.pages.other_pages',
        '--exclude-module', 'tkinter',
        '--exclude-module', 'matplotlib',
        '--noconfirm',
        '--clean',
        'main.py'
    ]

    print(f"\n运行: {' '.join(cmd[:5])} ...\n")
    result = subprocess.run(cmd, cwd=project_dir)

    if result.returncode == 0:
        exe_path = os.path.join(project_dir, 'dist', 'TGAutoPublisher')
        exe_win = exe_path + '.exe' if sys.platform == 'win32' else exe_path
        if os.path.exists(exe_win):
            size = os.path.getsize(exe_win) / (1024 * 1024)
            print(f"\n✅ 构建成功!")
            print(f"📦 输出文件: {exe_win}")
            print(f"📊 文件大小: {size:.1f} MB")
            return True
        elif os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n✅ 构建成功!")
            print(f"📦 输出文件: {exe_path}")
            print(f"📊 文件大小: {size:.1f} MB")
            return True
    else:
        print(f"\n❌ 构建失败，返回码: {result.returncode}")
        return False


if __name__ == '__main__':
    build()
