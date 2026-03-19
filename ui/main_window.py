"""
主窗口 - 现代深色UI设计
"""
import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QStatusBar, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor

from ui.styles import DARK_THEME


class SidebarButton(QPushButton):
    """侧边栏导航按钮"""

    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.icon_text = icon_text
        self.label_text = label
        self.setObjectName("navBtn")
        self.setCheckable(True)
        self.setFixedHeight(46)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        # 图标
        icon_lbl = QLabel(self.icon_text)
        icon_lbl.setFixedWidth(22)
        icon_lbl.setStyleSheet("font-size: 16px; background: transparent; color: inherit;")
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # 文字
        text_lbl = QLabel(self.label_text)
        text_lbl.setStyleSheet("font-size: 13px; background: transparent; color: inherit; font-weight: 500;")
        text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        layout.addStretch()


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TG Auto Publisher v1.3.0")
        self.setMinimumSize(1200, 750)
        self.resize(1380, 860)
        self.setStyleSheet(DARK_THEME)

        # 延迟导入页面，避免循环导入
        self._pages = {}
        self._current_page = None

        self._setup_ui()
        self._setup_status_bar()
        self._nav_buttons = []
        self._setup_navigation()
        self._navigate_to(0)

        # 定时刷新状态栏
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(5000)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # 右侧内容区
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentArea")
        main_layout.addWidget(self.content_stack, 1)

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 0, 8, 12)
        layout.setSpacing(2)

        # Logo区域
        logo_widget = QWidget()
        logo_widget.setFixedHeight(70)
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(14, 16, 14, 8)
        logo_layout.setSpacing(2)

        title_label = QLabel("✈️ TG Publisher")
        title_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 700;
            color: #e6edf3;
            background: transparent;
        """)
        version_label = QLabel("v1.3.0  多账号发布系统")
        version_label.setStyleSheet("""
            font-size: 10px;
            color: #484f58;
            background: transparent;
        """)
        logo_layout.addWidget(title_label)
        logo_layout.addWidget(version_label)

        layout.addWidget(logo_widget)

        # 分割线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #21262d; max-height: 1px; margin: 0 6px;")
        layout.addWidget(sep)
        layout.addSpacing(6)

        # 导航项定义
        self._nav_items = [
            ("📊", "仪表板"),
            ("📢", "频道管理"),
            ("🎬", "媒体库"),
            ("📅", "任务中心"),
            ("🤖", "AI文案"),
            ("⚙️", "系统设置"),
            ("📖", "操作指南"),
        ]

        # 创建导航按钮容器（后续在_setup_navigation中填充）
        self._nav_container = QWidget()
        self._nav_layout = QVBoxLayout(self._nav_container)
        self._nav_layout.setContentsMargins(0, 0, 0, 0)
        self._nav_layout.setSpacing(2)
        layout.addWidget(self._nav_container)

        layout.addStretch()

        # 底部信息
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(14, 8, 14, 4)
        bottom_layout.setSpacing(4)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: #21262d; max-height: 1px;")
        bottom_layout.addWidget(sep2)

        github_label = QLabel("📦 github.com/ocsy22/TGBOT")
        github_label.setStyleSheet("font-size: 10px; color: #484f58; background: transparent;")
        github_label.setWordWrap(True)
        bottom_layout.addWidget(github_label)

        layout.addWidget(bottom_widget)
        return sidebar

    def _setup_navigation(self):
        """设置导航按钮"""
        from PyQt6.QtWidgets import QButtonGroup
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        self._nav_buttons = []
        for i, (icon, label) in enumerate(self._nav_items):
            btn = SidebarButton(icon, label)
            self._nav_layout.addWidget(btn)
            self._btn_group.addButton(btn, i)
            self._nav_buttons.append(btn)
            btn.clicked.connect(lambda checked, idx=i: self._navigate_to(idx))

    def _get_page(self, index: int) -> QWidget:
        """懒加载页面"""
        if index not in self._pages:
            page = self._create_page(index)
            self._pages[index] = page
            self.content_stack.addWidget(page)
        return self._pages[index]

    def _create_page(self, index: int) -> QWidget:
        """创建对应索引的页面"""
        if index == 0:
            from ui.pages.dashboard import DashboardPage
            return DashboardPage()
        elif index == 1:
            from ui.pages.channel_page import ChannelPage
            return ChannelPage()
        elif index == 2:
            from ui.pages.media_page import MediaPage
            return MediaPage()
        elif index == 3:
            from ui.pages.task_page import TaskPage
            return TaskPage()
        elif index == 4:
            from ui.pages.other_pages import AIPage
            return AIPage()
        elif index == 5:
            from ui.pages.settings_page import SettingsPage
            return SettingsPage()
        elif index == 6:
            from ui.pages.other_pages import HelpPage
            return HelpPage()
        else:
            placeholder = QWidget()
            lbl = QLabel(f"页面 {index} 开发中...")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #484f58; font-size: 16px;")
            layout = QVBoxLayout(placeholder)
            layout.addWidget(lbl)
            return placeholder

    def _navigate_to(self, index: int):
        """导航到指定页面"""
        page = self._get_page(index)
        self.content_stack.setCurrentWidget(page)
        self._current_page = index

        # 更新按钮状态
        if index < len(self._nav_buttons):
            self._nav_buttons[index].setChecked(True)

    def _setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setFixedHeight(24)

        self._status_left = QLabel("就绪")
        self._status_right = QLabel("FFmpeg: 检测中...")
        self._status_right.setStyleSheet("color: #484f58; font-size: 11px;")

        self.status_bar.addWidget(self._status_left)
        self.status_bar.addPermanentWidget(self._status_right)

        QTimer.singleShot(500, self._update_status)

    def _update_status(self):
        """更新状态栏"""
        import shutil
        from core.database import get_db

        try:
            db = get_db()
            accounts = db.execute("SELECT COUNT(*) FROM accounts WHERE enabled=1").fetchone()[0]
            channels = db.execute("SELECT COUNT(*) FROM channels WHERE enabled=1").fetchone()[0]
            tasks = db.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0]
            db.close()
            self._status_left.setText(
                f"活跃账号: {accounts}  |  监听频道: {channels}  |  待发任务: {tasks}"
            )
        except Exception:
            pass

        # 检查FFmpeg
        ffmpeg_path = self._find_ffmpeg()
        if ffmpeg_path:
            self._status_right.setText(f"✅ FFmpeg: {ffmpeg_path}")
            self._status_right.setStyleSheet("color: #3fb950; font-size: 11px;")
        else:
            self._status_right.setText("⚠️ FFmpeg 未找到（需手动配置）")
            self._status_right.setStyleSheet("color: #d29922; font-size: 11px;")

    def _find_ffmpeg(self) -> str:
        """查找FFmpeg"""
        import shutil
        from core.database import get_settings

        try:
            settings = get_settings()
            custom_path = settings.get('ffmpeg_path', '')
            if custom_path and os.path.exists(custom_path):
                return custom_path
        except Exception:
            pass

        # 自动查找
        import shutil
        found = shutil.which('ffmpeg')
        if found:
            return found

        # 查找当前目录
        exe_dir = os.path.dirname(sys.executable)
        for name in ['ffmpeg.exe', 'ffmpeg']:
            path = os.path.join(exe_dir, name)
            if os.path.exists(path):
                return path

        return ''

    def show_message(self, msg: str, timeout: int = 3000):
        """在状态栏显示临时消息"""
        self.status_bar.showMessage(msg, timeout)

    def closeEvent(self, event):
        """关闭事件"""
        try:
            from core.scheduler import get_scheduler
            scheduler = get_scheduler()
            scheduler.shutdown()
        except Exception:
            pass
        event.accept()
