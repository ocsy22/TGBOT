"""
主窗口
"""
import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from ui.styles import MAIN_STYLE
from ui.pages.dashboard import DashboardPage
from ui.pages.channel_page import ChannelPage
from ui.pages.media_page import MediaLibraryPage
from ui.pages.task_page import TaskPage
from ui.pages.settings_page import SettingsPage
from ui.pages.other_pages import (
    AutoPublishPage, CopywritingPage, CopyTemplatePage,
    WritingDirectionPage, MediaCollectPage, BroadcastPage, PublishSettingsPage
)


class MainWindow(QMainWindow):
    NAV_ITEMS = [
        ('仪表盘', '🖥', 'dashboard'),
        ('素材库', '📁', 'media'),
        ('任务中心', '📋', 'tasks'),
        ('频道管理', '📡', 'channels'),
        ('自动发布', '🚀', 'auto_publish'),
        ('文案库', '📝', 'copywriting'),
        ('文案格式', '✏️', 'copy_template'),
        ('写作方向', '🧭', 'writing_direction'),
        ('素材采集', '⬇️', 'media_collect'),
        ('群发', '👥', 'broadcast'),
        ('发布设置', '⚙️', 'publish_settings'),
        ('设置', '🔧', 'settings'),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Telegram Auto Publisher')
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)
        self.setStyleSheet(MAIN_STYLE)

        # 设置自定义标题栏样式
        self._set_window_icon()
        self._build_ui()
        self._nav_to('dashboard')

    def _set_window_icon(self):
        # 创建简单图标
        pix = QPixmap(32, 32)
        pix.fill(Qt.GlobalColor.transparent)
        from PyQt6.QtGui import QPainter, QBrush, QColor, QPen
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor('#1f6feb')))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 32, 32)
        painter.setPen(QPen(QColor('white'), 2))
        painter.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, '▷')
        painter.end()
        self.setWindowIcon(QIcon(pix))

    def _build_ui(self):
        central = QWidget()
        central.setObjectName('central')
        main_lay = QHBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        self.setCentralWidget(central)

        # ===== 侧边栏 =====
        sidebar = QWidget()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(180)
        sidebar_lay = QVBoxLayout(sidebar)
        sidebar_lay.setContentsMargins(0, 0, 0, 0)
        sidebar_lay.setSpacing(0)

        # Logo区域
        logo_area = QWidget()
        logo_area.setObjectName('logo_area')
        logo_area.setStyleSheet('padding:16px 12px;border-bottom:1px solid #21262d;')
        logo_lay = QHBoxLayout(logo_area)
        logo_lay.setContentsMargins(8, 0, 8, 0)
        logo_lay.setSpacing(10)

        # TG图标
        icon_lbl = QLabel('✈️')
        icon_lbl.setStyleSheet('font-size:20px;')
        icon_lbl.setFixedWidth(28)

        title_lay = QVBoxLayout()
        title_lay.setSpacing(0)
        title = QLabel('Telegram Publisher')
        title.setStyleSheet('color:#e6edf3;font-size:13px;font-weight:bold;')
        subtitle = QLabel('Auto Video System')
        subtitle.setStyleSheet('color:#8b949e;font-size:9px;')
        title_lay.addWidget(title)
        title_lay.addWidget(subtitle)

        logo_lay.addWidget(icon_lbl)
        logo_lay.addLayout(title_lay, 1)
        sidebar_lay.addWidget(logo_area)

        # 导航按钮
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(4, 8, 4, 8)
        nav_layout.setSpacing(2)

        self._nav_btns = {}
        for label, icon, key in self.NAV_ITEMS:
            btn = QPushButton(f'  {icon}  {label}')
            btn.setObjectName('nav_btn')
            btn.setFixedHeight(36)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet('''
                QPushButton#nav_btn {
                    background: transparent;
                    border: none;
                    color: #8b949e;
                    text-align: left;
                    padding: 8px 12px 8px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                }
                QPushButton#nav_btn:hover {
                    background-color: #21262d;
                    color: #e6edf3;
                }
                QPushButton#nav_btn:checked {
                    background-color: #21262d;
                    color: #e6edf3;
                    border-left: 2px solid #1f6feb;
                }
            ''')
            btn.clicked.connect(lambda checked, k=key: self._nav_to(k))
            self._nav_btns[key] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        nav_scroll.setWidget(nav_widget)
        sidebar_lay.addWidget(nav_scroll, 1)

        # 版本号
        ver_lbl = QLabel('v1.2.0')
        ver_lbl.setObjectName('version_label')
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet('color:#484f58;font-size:10px;padding:8px;')
        sidebar_lay.addWidget(ver_lbl)

        main_lay.addWidget(sidebar)

        # ===== 内容区域 =====
        self._stack = QStackedWidget()
        self._stack.setObjectName('content_area')

        self._pages = {
            'dashboard': DashboardPage(),
            'media': MediaLibraryPage(),
            'tasks': TaskPage(),
            'channels': ChannelPage(),
            'auto_publish': AutoPublishPage(),
            'copywriting': CopywritingPage(),
            'copy_template': CopyTemplatePage(),
            'writing_direction': WritingDirectionPage(),
            'media_collect': MediaCollectPage(),
            'broadcast': BroadcastPage(),
            'publish_settings': PublishSettingsPage(),
            'settings': SettingsPage(),
        }

        for key, page in self._pages.items():
            self._stack.addWidget(page)

        main_lay.addWidget(self._stack, 1)

    def _nav_to(self, key):
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)

        page = self._pages.get(key)
        if page:
            self._stack.setCurrentWidget(page)
            if hasattr(page, 'refresh'):
                page.refresh()
