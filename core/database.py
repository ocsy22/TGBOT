"""
数据库管理模块 - SQLite本地存储
"""
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'tgpublisher.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    c = conn.cursor()

    # Telegram API配置
    c.execute('''CREATE TABLE IF NOT EXISTS telegram_apis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_id TEXT NOT NULL,
        api_hash TEXT NOT NULL,
        label TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Bot管理
    c.execute('''CREATE TABLE IF NOT EXISTS bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL,
        token TEXT NOT NULL,
        status TEXT DEFAULT 'unknown',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 账号管理（MTProto真实账号）
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL UNIQUE,
        api_id INTEGER,
        label TEXT DEFAULT '',
        session_string TEXT DEFAULT '',
        status TEXT DEFAULT 'offline',
        proxy TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 频道管理
    c.execute('''CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT DEFAULT '',
        chat_id TEXT DEFAULT '',
        account_id INTEGER DEFAULT 0,
        bot_id INTEGER DEFAULT 0,
        send_mode TEXT DEFAULT 'bot',
        auto_like TEXT DEFAULT '',
        proxy TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 素材库 - 文件夹
    c.execute('''CREATE TABLE IF NOT EXISTS media_folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        path TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 素材库 - 文件
    c.execute('''CREATE TABLE IF NOT EXISTS media_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_id INTEGER,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        file_type TEXT DEFAULT 'video',
        size INTEGER DEFAULT 0,
        duration INTEGER DEFAULT 0,
        width INTEGER DEFAULT 0,
        height INTEGER DEFAULT 0,
        thumbnail TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (folder_id) REFERENCES media_folders(id)
    )''')

    # 文案库
    c.execute('''CREATE TABLE IF NOT EXISTS copywriting (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT '',
        content TEXT NOT NULL,
        media_path TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 文案格式模板
    c.execute('''CREATE TABLE IF NOT EXISTS copy_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        template TEXT NOT NULL,
        is_builtin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 写作方向预设
    c.execute('''CREATE TABLE IF NOT EXISTS writing_directions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        style TEXT DEFAULT '',
        keywords TEXT DEFAULT '',
        extra_prompt TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 任务中心
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT '',
        channel_ids TEXT DEFAULT '[]',
        media_folder_id INTEGER DEFAULT 0,
        media_file_id INTEGER DEFAULT 0,
        copy_template_id INTEGER DEFAULT 0,
        writing_direction_id INTEGER DEFAULT 0,
        ai_generate INTEGER DEFAULT 1,
        send_mode TEXT DEFAULT 'video',
        clip_enabled INTEGER DEFAULT 0,
        clip_start INTEGER DEFAULT 0,
        clip_duration INTEGER DEFAULT 60,
        clip_resolution TEXT DEFAULT '1920x1080',
        clip_bitrate TEXT DEFAULT '4M',
        screenshot_enabled INTEGER DEFAULT 1,
        screenshot_grid TEXT DEFAULT '3x3',
        status TEXT DEFAULT 'pending',
        progress INTEGER DEFAULT 0,
        result_text TEXT DEFAULT '',
        error_msg TEXT DEFAULT '',
        scheduled_time TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        finished_at TEXT DEFAULT ''
    )''')

    # 自动发布规则
    c.execute('''CREATE TABLE IF NOT EXISTS auto_publish_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        channel_ids TEXT DEFAULT '[]',
        media_folder_id INTEGER DEFAULT 0,
        copy_template_id INTEGER DEFAULT 0,
        writing_direction_id INTEGER DEFAULT 0,
        schedule_type TEXT DEFAULT 'daily',
        schedule_time TEXT DEFAULT '20:55',
        schedule_interval INTEGER DEFAULT 1,
        random_order INTEGER DEFAULT 1,
        send_after_done TEXT DEFAULT 'stop',
        send_mode TEXT DEFAULT 'original',
        enabled INTEGER DEFAULT 1,
        published_count INTEGER DEFAULT 0,
        total_count INTEGER DEFAULT 0,
        last_publish TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 群发规则
    c.execute('''CREATE TABLE IF NOT EXISTS broadcast_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        channel_ids TEXT DEFAULT '[]',
        media_folder_id INTEGER DEFAULT 0,
        copy_template_id INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 发布设置
    c.execute('''CREATE TABLE IF NOT EXISTS publish_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        footer_links TEXT DEFAULT '[]',
        sticker_paths TEXT DEFAULT '[]',
        tag_library TEXT DEFAULT '[]',
        mtproto_proxy TEXT DEFAULT '',
        local_bot_api TEXT DEFAULT '',
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # AI API配置
    c.execute('''CREATE TABLE IF NOT EXISTS ai_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_url TEXT DEFAULT 'https://api.x.ai/v1',
        api_key TEXT DEFAULT '',
        text_model TEXT DEFAULT 'grok-3-mini',
        vision_model TEXT DEFAULT 'grok-2-vision-1212',
        max_tokens INTEGER DEFAULT 1024,
        http_proxy TEXT DEFAULT '',
        title_min INTEGER DEFAULT 15,
        title_max INTEGER DEFAULT 25,
        content_min INTEGER DEFAULT 30,
        content_max INTEGER DEFAULT 60,
        cover_title_min INTEGER DEFAULT 10,
        cover_title_max INTEGER DEFAULT 20,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 视频处理设置
    c.execute('''CREATE TABLE IF NOT EXISTS video_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ffmpeg_path TEXT DEFAULT 'ffmpeg',
        default_resolution TEXT DEFAULT '1920x1080',
        default_bitrate TEXT DEFAULT '4M',
        encoder TEXT DEFAULT 'libx264',
        cover_grid TEXT DEFAULT '3x3',
        cover_size INTEGER DEFAULT 1080,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # 发布日志
    c.execute('''CREATE TABLE IF NOT EXISTS publish_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER DEFAULT 0,
        channel_id INTEGER DEFAULT 0,
        channel_name TEXT DEFAULT '',
        status TEXT DEFAULT 'success',
        message TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()

    # 初始化默认数据
    _init_defaults(c, conn)
    conn.close()


def _init_defaults(c, conn):
    """初始化默认配置"""
    # 默认AI设置
    c.execute('SELECT COUNT(*) FROM ai_settings')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO ai_settings DEFAULT VALUES')

    # 默认视频设置
    c.execute('SELECT COUNT(*) FROM video_settings')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO video_settings DEFAULT VALUES')

    # 默认发布设置
    c.execute('SELECT COUNT(*) FROM publish_settings')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO publish_settings DEFAULT VALUES')

    # 默认文案模板
    c.execute('SELECT COUNT(*) FROM copy_templates')
    if c.fetchone()[0] == 0:
        templates = [
            ('默认（加粗标题 + ⏱时长）', '<b>{title}</b>\n{content}\n⏱ 时长: {duration}', 1),
            ('引用风格（"内容"+ 🔥时长🔥）', '{emoji} {title}\n\n<blockquote>" {content} "</blockquote>\n\n<blockquote>🔥 纯享完整版{duration} 🔥</blockquote>', 1),
        ]
        c.executemany('INSERT INTO copy_templates (name, template, is_builtin) VALUES (?,?,?)', templates)

    conn.commit()


# =================== CRUD操作 ===================

class DB:
    """数据库操作封装"""

    @staticmethod
    def fetchall(sql, params=()):
        conn = get_connection()
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def fetchone(sql, params=()):
        conn = get_connection()
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def execute(sql, params=()):
        conn = get_connection()
        c = conn.execute(sql, params)
        conn.commit()
        last_id = c.lastrowid
        conn.close()
        return last_id

    @staticmethod
    def executemany(sql, params_list):
        conn = get_connection()
        conn.executemany(sql, params_list)
        conn.commit()
        conn.close()
