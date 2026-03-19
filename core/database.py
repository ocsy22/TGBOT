"""
数据库模块
"""
import os
import sqlite3
import json
from pathlib import Path


def get_db_path() -> str:
    """获取数据库路径"""
    # 优先放在用户数据目录
    if getattr(__import__('sys'), 'frozen', False):
        # 打包后的EXE，放在exe同目录
        import sys
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'tgpublisher.db')


def get_db() -> sqlite3.Connection:
    """获取数据库连接"""
    db = sqlite3.connect(get_db_path())
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """初始化数据库"""
    db = get_db()
    cursor = db.cursor()

    # 账号表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'bot',  -- bot / mtproto
            bot_token TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            api_id TEXT DEFAULT '',
            api_hash TEXT DEFAULT '',
            session_string TEXT DEFAULT '',
            proxy TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 频道表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            account_id INTEGER DEFAULT 0,
            type TEXT DEFAULT 'public',
            description TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 素材表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT DEFAULT 'video',  -- video / image / text
            thumbnail TEXT DEFAULT '',
            duration REAL DEFAULT 0,
            file_size INTEGER DEFAULT 0,
            caption TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            used_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 任务表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',  -- pending/running/done/failed/paused
            account_ids TEXT DEFAULT '[]',
            channel_ids TEXT DEFAULT '[]',
            media_ids TEXT DEFAULT '[]',
            caption TEXT DEFAULT '',
            schedule_type TEXT DEFAULT 'once',  -- once/interval/cron
            schedule_time TEXT DEFAULT '',
            interval_minutes INTEGER DEFAULT 60,
            cron_expr TEXT DEFAULT '',
            send_mode TEXT DEFAULT 'sequential',  -- sequential/random/all
            interval_seconds INTEGER DEFAULT 3,
            use_ai INTEGER DEFAULT 0,
            ai_config TEXT DEFAULT '{}',
            progress INTEGER DEFAULT 0,
            result TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_run TIMESTAMP
        )
    """)

    # 文案库
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS captions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT '',
            content TEXT NOT NULL,
            tags TEXT DEFAULT '[]',
            category TEXT DEFAULT '通用',
            used_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 设置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 初始化默认设置
    defaults = {
        'ffmpeg_path': '',
        'default_ai_provider': 'Grok (xAI)',
        'default_ai_key': '',
        'ai_config': '{}',
        'proxy_http': '',
        'proxy_socks5': '',
        'send_interval': '3',
        'max_retry': '3',
        'output_folder_name': '已裁剪',
        'screenshot_grid': '3x3',
    }
    for k, v in defaults.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v)
        )

    db.commit()
    db.close()


def get_settings() -> dict:
    """获取所有设置"""
    try:
        db = get_db()
        rows = db.execute("SELECT key, value FROM settings").fetchall()
        db.close()
        return {row['key']: row['value'] for row in rows}
    except Exception:
        return {}


def set_setting(key: str, value: str):
    """保存设置"""
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (key, value)
    )
    db.commit()
    db.close()


def get_accounts(enabled_only: bool = False) -> list:
    db = get_db()
    if enabled_only:
        rows = db.execute("SELECT * FROM accounts WHERE enabled=1").fetchall()
    else:
        rows = db.execute("SELECT * FROM accounts").fetchall()
    result = [dict(r) for r in rows]
    db.close()
    return result


def get_channels(enabled_only: bool = False) -> list:
    db = get_db()
    if enabled_only:
        rows = db.execute("SELECT * FROM channels WHERE enabled=1").fetchall()
    else:
        rows = db.execute("SELECT * FROM channels").fetchall()
    result = [dict(r) for r in rows]
    db.close()
    return result


def get_tasks(status: str = None) -> list:
    db = get_db()
    if status:
        rows = db.execute("SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    result = [dict(r) for r in rows]
    db.close()
    return result


def get_media(file_type: str = None) -> list:
    db = get_db()
    if file_type:
        rows = db.execute("SELECT * FROM media WHERE file_type=? ORDER BY created_at DESC", (file_type,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM media ORDER BY created_at DESC").fetchall()
    result = [dict(r) for r in rows]
    db.close()
    return result
