"""
仪表板页面
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class StatCard(QFrame):
    """统计卡片"""

    def __init__(self, icon: str, title: str, value: str, color: str = "#58a6ff", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        # 顶部行：图标 + 标题
        top_row = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 22px; color: {color}; background: transparent;")
        title_lbl = QLabel(title)
        title_lbl.setObjectName("statLabel")
        top_row.addWidget(icon_lbl)
        top_row.addWidget(title_lbl)
        top_row.addStretch()
        layout.addLayout(top_row)

        # 数值
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {color}; background: transparent;")
        layout.addWidget(self.value_lbl)

    def set_value(self, value: str):
        self.value_lbl.setText(value)


class QuickActionBtn(QPushButton):
    """快速操作按钮"""

    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}  {label}")
        self.setMinimumHeight(42)
        self.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 8px;
                font-size: 13px;
                text-align: left;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #21262d;
                border-color: #1f6feb;
                color: #58a6ff;
            }
            QPushButton:pressed {
                background-color: #1f6feb22;
            }
        """)


class DashboardPage(QWidget):
    """仪表板主页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_stats()

        # 定时刷新
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._load_stats)
        self._timer.start(10000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # 标题区域
        header = QHBoxLayout()
        title = QLabel("📊 控制台")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Telegram Auto Publisher — 多账号多频道自动发布系统")
        subtitle.setObjectName("subtitleLabel")
        header.addWidget(title)
        header.addSpacing(12)
        header.addWidget(subtitle)
        header.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedWidth(90)
        refresh_btn.clicked.connect(self._load_stats)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # 统计卡片区域
        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)

        self.stat_accounts = StatCard("👤", "活跃账号", "0", "#58a6ff")
        self.stat_channels = StatCard("📢", "发布频道", "0", "#3fb950")
        self.stat_tasks = StatCard("📅", "待发任务", "0", "#d29922")
        self.stat_media = StatCard("🎬", "素材数量", "0", "#a371f7")
        self.stat_done = StatCard("✅", "已完成任务", "0", "#3fb950")
        self.stat_captions = StatCard("📝", "文案数量", "0", "#58a6ff")

        stats_grid.addWidget(self.stat_accounts, 0, 0)
        stats_grid.addWidget(self.stat_channels, 0, 1)
        stats_grid.addWidget(self.stat_tasks, 0, 2)
        stats_grid.addWidget(self.stat_media, 1, 0)
        stats_grid.addWidget(self.stat_done, 1, 1)
        stats_grid.addWidget(self.stat_captions, 1, 2)
        layout.addLayout(stats_grid)

        # 快速操作 + 最近任务
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # 快速操作
        quick_card = QFrame()
        quick_card.setObjectName("card")
        quick_layout = QVBoxLayout(quick_card)
        quick_layout.setContentsMargins(16, 14, 16, 16)
        quick_layout.setSpacing(10)

        quick_title = QLabel("⚡ 快速操作")
        quick_title.setObjectName("sectionTitle")
        quick_layout.addWidget(quick_title)
        quick_layout.addSpacing(4)

        actions = [
            ("📢", "添加发布账号"),
            ("📺", "添加目标频道"),
            ("📁", "导入视频素材"),
            ("🚀", "创建发布任务"),
            ("🤖", "AI生成文案"),
            ("✂️", "视频裁剪处理"),
        ]
        for icon, label in actions:
            btn = QuickActionBtn(icon, label)
            quick_layout.addWidget(btn)

        quick_layout.addStretch()
        bottom_row.addWidget(quick_card, 1)

        # 最近活动
        activity_card = QFrame()
        activity_card.setObjectName("card")
        activity_layout = QVBoxLayout(activity_card)
        activity_layout.setContentsMargins(16, 14, 16, 16)
        activity_layout.setSpacing(8)

        activity_title = QLabel("📋 最近活动")
        activity_title.setObjectName("sectionTitle")
        activity_layout.addWidget(activity_title)
        activity_layout.addSpacing(4)

        self.activity_container = QVBoxLayout()
        self.activity_container.setSpacing(4)
        activity_layout.addLayout(self.activity_container)
        activity_layout.addStretch()
        bottom_row.addWidget(activity_card, 2)

        # 系统状态
        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(16, 14, 16, 16)
        status_layout.setSpacing(10)

        status_title = QLabel("🔧 系统状态")
        status_title.setObjectName("sectionTitle")
        status_layout.addWidget(status_title)
        status_layout.addSpacing(4)

        self._status_items = {}
        for key, label in [
            ("ffmpeg", "FFmpeg"),
            ("db", "数据库"),
            ("scheduler", "调度器"),
            ("network", "网络连接"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #8b949e; background: transparent;")
            val = QLabel("检测中...")
            val.setObjectName("badge")
            self._status_items[key] = val
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            status_layout.addLayout(row)

        status_layout.addStretch()

        # FFmpeg说明
        ffmpeg_note = QLabel(
            "💡 请将 ffmpeg.exe 放在程序所在目录\n"
            "   或在「设置 → 视频处理」中配置路径"
        )
        ffmpeg_note.setStyleSheet("""
            font-size: 11px;
            color: #8b949e;
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 10px;
        """)
        ffmpeg_note.setWordWrap(True)
        status_layout.addWidget(ffmpeg_note)
        bottom_row.addWidget(status_card, 1)

        layout.addLayout(bottom_row, 1)

    def _load_stats(self):
        """加载统计数据"""
        try:
            from core.database import get_db
            db = get_db()

            accounts = db.execute("SELECT COUNT(*) FROM accounts WHERE enabled=1").fetchone()[0]
            channels = db.execute("SELECT COUNT(*) FROM channels WHERE enabled=1").fetchone()[0]
            tasks_pending = db.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0]
            media_count = db.execute("SELECT COUNT(*) FROM media").fetchone()[0]
            tasks_done = db.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
            captions = db.execute("SELECT COUNT(*) FROM captions").fetchone()[0]

            # 最近任务
            recent_tasks = db.execute(
                "SELECT name, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 8"
            ).fetchall()
            db.close()

            self.stat_accounts.set_value(str(accounts))
            self.stat_channels.set_value(str(channels))
            self.stat_tasks.set_value(str(tasks_pending))
            self.stat_media.set_value(str(media_count))
            self.stat_done.set_value(str(tasks_done))
            self.stat_captions.set_value(str(captions))

            # 刷新活动列表
            while self.activity_container.count():
                item = self.activity_container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if recent_tasks:
                for task in recent_tasks:
                    item_widget = self._make_activity_item(
                        task['name'], task['status'], task['created_at']
                    )
                    self.activity_container.addWidget(item_widget)
            else:
                empty = QLabel("暂无任务记录")
                empty.setStyleSheet("color: #484f58; font-size: 12px; padding: 20px; background: transparent;")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.activity_container.addWidget(empty)

            # 更新系统状态
            self._update_system_status()

        except Exception as e:
            pass

    def _make_activity_item(self, name: str, status: str, time_str: str) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("""
            background-color: #1c2128;
            border-radius: 6px;
        """)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        status_icons = {
            'pending': ('⏳', '#d29922'),
            'running': ('▶️', '#58a6ff'),
            'done': ('✅', '#3fb950'),
            'failed': ('❌', '#f85149'),
            'paused': ('⏸️', '#8b949e'),
        }
        icon, color = status_icons.get(status, ('•', '#8b949e'))

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 13px; color: {color}; background: transparent;")
        icon_lbl.setFixedWidth(20)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("color: #e6edf3; font-size: 12px; background: transparent;")
        name_lbl.setMaximumWidth(180)

        status_labels = {
            'pending': '等待', 'running': '运行中',
            'done': '完成', 'failed': '失败', 'paused': '暂停'
        }
        status_lbl = QLabel(status_labels.get(status, status))
        obj = "badgeSuccess" if status == 'done' else \
              "badgeDanger" if status == 'failed' else \
              "badge"
        status_lbl.setObjectName(obj)

        layout.addWidget(icon_lbl)
        layout.addWidget(name_lbl, 1)
        layout.addWidget(status_lbl)
        return widget

    def _update_system_status(self):
        """更新系统状态显示"""
        import shutil
        import os
        import sys

        # FFmpeg
        ffmpeg_ok = False
        from core.database import get_settings
        try:
            settings = get_settings()
            ffmpeg_path = settings.get('ffmpeg_path', '')
            if ffmpeg_path and os.path.exists(ffmpeg_path):
                ffmpeg_ok = True
        except Exception:
            pass

        if not ffmpeg_ok:
            ffmpeg_ok = bool(shutil.which('ffmpeg'))
        if not ffmpeg_ok:
            exe_dir = os.path.dirname(sys.executable)
            ffmpeg_ok = os.path.exists(os.path.join(exe_dir, 'ffmpeg.exe'))

        self._set_status("ffmpeg", ffmpeg_ok, "已配置", "未找到")
        self._set_status("db", True, "正常", "错误")
        self._set_status("scheduler", True, "运行中", "停止")
        self._set_status("network", True, "在线", "离线")

    def _set_status(self, key: str, ok: bool, ok_text: str, fail_text: str):
        if key not in self._status_items:
            return
        lbl = self._status_items[key]
        if ok:
            lbl.setText(ok_text)
            lbl.setObjectName("badgeSuccess")
        else:
            lbl.setText(fail_text)
            lbl.setObjectName("badgeWarning")
        lbl.style().unpolish(lbl)
        lbl.style().polish(lbl)
