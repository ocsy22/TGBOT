"""
仪表盘页面
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from core.database import DB
import os


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(10000)  # 每10秒刷新

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # 页面标题
        title_w = QWidget()
        title_lay = QVBoxLayout(title_w)
        title_lay.setContentsMargins(0, 0, 0, 0)
        title_lay.setSpacing(2)
        t = QLabel('仪表盘')
        t.setObjectName('page_title')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('系统概览和运行状态')
        sub.setObjectName('page_subtitle')
        title_lay.addWidget(t)
        title_lay.addWidget(sub)
        layout.addWidget(title_w)

        # 统计卡片行
        self._stats_widget = QWidget()
        stats_layout = QGridLayout(self._stats_widget)
        stats_layout.setSpacing(12)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        self._stat_cards = {}
        cards_info = [
            ('活跃账号', '0/0', '#8b949e', 'accounts', '👤'),
            ('频道数量', '0', '#1f6feb', 'channels', '📡'),
            ('素材数量', '0', '#d29922', 'media', '📁'),
            ('总任务数', '0', '#da3633', 'tasks', '📋'),
            ('今日发布', '0', '#2ea043', 'today_pub', '✅'),
            ('今日失败', '0', '#da3633', 'today_fail', '❌'),
            ('今日任务', '0', '#1f6feb', 'today_tasks', '⚡'),
            ('存储占用', '0 MB', '#d29922', 'storage', '💾'),
        ]

        for i, (label, val, color, key, icon) in enumerate(cards_info):
            card = self._create_stat_card(label, val, color, icon)
            self._stat_cards[key] = card
            stats_layout.addWidget(card, i // 4, i % 4)

        layout.addWidget(self._stats_widget)

        # 快速操作
        quick_label = QLabel('快速操作')
        quick_label.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        layout.addWidget(quick_label)

        quick_w = QWidget()
        quick_lay = QHBoxLayout(quick_w)
        quick_lay.setContentsMargins(0, 0, 0, 0)
        quick_lay.setSpacing(12)

        actions = [
            ('📤 上传素材', '添加视频/图片/音频素材', '#2ea043'),
            ('📋 创建任务', '剪辑视频并发布', '#1f6feb'),
            ('📡 管理频道', '添加账号和频道', '#d29922'),
        ]

        for text, sub_text, color in actions:
            btn = self._create_quick_action(text, sub_text, color)
            quick_lay.addWidget(btn)

        layout.addWidget(quick_w)

        # 最近任务
        recent_label = QLabel('最近任务')
        recent_label.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        layout.addWidget(recent_label)

        self._task_table = QTableWidget()
        self._task_table.setColumnCount(5)
        self._task_table.setHorizontalHeaderLabels(['任务', '状态', '进度', '频道', '时间'])
        self._task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._task_table.setAlternatingRowColors(False)
        self._task_table.verticalHeader().setVisible(False)
        self._task_table.setShowGrid(False)
        self._task_table.setFixedHeight(200)
        layout.addWidget(self._task_table)

        layout.addStretch()
        self.refresh()

    def _create_stat_card(self, label, value, color, icon):
        frame = QFrame()
        frame.setObjectName('card')
        frame.setStyleSheet(f"""
            QFrame#card {{
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
            }}
        """)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(16, 14, 16, 14)

        left = QVBoxLayout()
        left.setSpacing(4)
        lbl = QLabel(label)
        lbl.setStyleSheet('color: #8b949e; font-size: 12px;')
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f'color: {color}; font-size: 22px; font-weight: bold;')
        val_lbl.setObjectName('val')
        left.addWidget(lbl)
        left.addWidget(val_lbl)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f'font-size: 28px;')
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        lay.addLayout(left, 1)
        lay.addWidget(icon_lbl)
        return frame

    def _create_quick_action(self, text, sub_text, color):
        frame = QFrame()
        frame.setCursor(Qt.CursorShape.PointingHandCursor)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {color};
                background-color: #1c2128;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 14, 16, 14)

        title = QLabel(text)
        title.setStyleSheet(f'color: {color}; font-size: 14px; font-weight: bold;')
        sub = QLabel(sub_text)
        sub.setStyleSheet('color: #8b949e; font-size: 12px;')

        lay.addWidget(title)
        lay.addWidget(sub)
        return frame

    def refresh(self):
        """刷新数据"""
        try:
            # 账号
            acc_total = DB.fetchone('SELECT COUNT(*) as cnt FROM accounts')['cnt']
            acc_online = DB.fetchone("SELECT COUNT(*) as cnt FROM accounts WHERE status='online'")['cnt']

            # 频道
            ch_count = DB.fetchone('SELECT COUNT(*) as cnt FROM channels')['cnt']

            # 素材
            media_count = DB.fetchone('SELECT COUNT(*) as cnt FROM media_files')['cnt']

            # 任务
            task_count = DB.fetchone('SELECT COUNT(*) as cnt FROM tasks')['cnt']

            # 今日统计
            today = __import__('datetime').date.today().strftime('%Y-%m-%d')
            today_logs = DB.fetchall("SELECT status FROM publish_logs WHERE created_at LIKE ?", (f'{today}%',))
            today_success = sum(1 for l in today_logs if l['status'] == 'success')
            today_fail = sum(1 for l in today_logs if l['status'] != 'success')
            today_tasks = DB.fetchone("SELECT COUNT(*) as cnt FROM tasks WHERE created_at LIKE ?", (f'{today}%',))['cnt']

            # 存储（粗略计算data目录）
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
            storage_mb = 0
            if os.path.exists(data_dir):
                for root, dirs, files in os.walk(data_dir):
                    for f in files:
                        try:
                            storage_mb += os.path.getsize(os.path.join(root, f))
                        except:
                            pass
            storage_mb = storage_mb / (1024 * 1024)

            # 更新卡片
            def update_card(card, value):
                val_lbl = card.findChild(QLabel, 'val')
                if val_lbl:
                    val_lbl.setText(str(value))

            update_card(self._stat_cards['accounts'], f'{acc_online}/{acc_total}')
            update_card(self._stat_cards['channels'], str(ch_count))
            update_card(self._stat_cards['media'], str(media_count))
            update_card(self._stat_cards['tasks'], str(task_count))
            update_card(self._stat_cards['today_pub'], str(today_success))
            update_card(self._stat_cards['today_fail'], str(today_fail))
            update_card(self._stat_cards['today_tasks'], str(today_tasks))
            update_card(self._stat_cards['storage'], f'{storage_mb:.2f} MB')

            # 更新最近任务
            tasks = DB.fetchall('SELECT * FROM tasks ORDER BY id DESC LIMIT 10')
            self._task_table.setRowCount(len(tasks))

            status_map = {
                'pending': ('待处理', '#d29922'),
                'processing': ('处理中', '#1f6feb'),
                'completed': ('已完成', '#2ea043'),
                'failed': ('失败', '#da3633'),
                'partial': ('部分成功', '#d29922'),
            }

            for row, task in enumerate(tasks):
                self._task_table.setItem(row, 0, QTableWidgetItem(task.get('title') or f"任务 #{task['id']}"))
                status, color = status_map.get(task.get('status', 'pending'), ('未知', '#8b949e'))
                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor(color))
                self._task_table.setItem(row, 1, status_item)

                progress = task.get('progress', 0)
                self._task_table.setItem(row, 2, QTableWidgetItem(f'{progress}%'))
                self._task_table.setItem(row, 3, QTableWidgetItem(''))
                self._task_table.setItem(row, 4, QTableWidgetItem(task.get('created_at', '')[:16]))

                self._task_table.setRowHeight(row, 36)

        except Exception as e:
            pass
