"""
任务中心页面
"""
import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QMessageBox, QTabWidget, QListWidget, QListWidgetItem,
    QTextEdit, QSpinBox, QProgressBar, QSplitter, QScrollArea,
    QDateTimeEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QDateTime, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont


class TaskPublishThread(QThread):
    """任务发布线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            from core.database import get_db
            db = get_db()
            task = dict(db.execute("SELECT * FROM tasks WHERE id=?", (self.task_id,)).fetchone())

            channel_ids = json.loads(task.get('channel_ids', '[]'))
            account_ids = json.loads(task.get('account_ids', '[]'))
            media_ids = json.loads(task.get('media_ids', '[]'))
            caption = task.get('caption', '')

            total = len(channel_ids)
            if total == 0:
                self.finished.emit(False, "没有设置目标频道")
                db.close()
                return

            # 更新状态为运行中
            db.execute("UPDATE tasks SET status='running' WHERE id=?", (self.task_id,))
            db.commit()

            import asyncio
            from core.telegram_sender import TelegramSender

            success_count = 0
            fail_count = 0
            sender = TelegramSender({})

            for i, ch_id in enumerate(channel_ids):
                if self._stop:
                    break

                self.progress.emit(
                    int((i / total) * 100),
                    f"发布到频道 {i + 1}/{total}..."
                )

                # 获取频道信息
                ch_row = db.execute("SELECT * FROM channels WHERE id=?", (ch_id,)).fetchone()
                if not ch_row:
                    fail_count += 1
                    continue

                ch_info = dict(ch_row)
                channel_tg_id = ch_info.get('channel_id', '')
                account_id = ch_info.get('account_id', 0)

                if not account_id:
                    # 用任务绑定的第一个账号
                    if account_ids:
                        account_id = account_ids[0]

                if not account_id:
                    fail_count += 1
                    continue

                acc_row = db.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
                if not acc_row:
                    fail_count += 1
                    continue

                acc_info = dict(acc_row)

                # 获取媒体文件
                media_file = ''
                photo_files = []
                if media_ids:
                    for mid in media_ids[:1]:  # 先发第一个
                        m_row = db.execute("SELECT * FROM media WHERE id=?", (mid,)).fetchone()
                        if m_row:
                            m_info = dict(m_row)
                            fp = m_info.get('file_path', '')
                            if os.path.exists(fp):
                                if m_info.get('file_type') == 'video':
                                    media_file = fp
                                elif m_info.get('file_type') == 'image':
                                    photo_files.append(fp)

                # 发送
                try:
                    result = asyncio.run(
                        sender.send_via_bot(
                            token=acc_info.get('bot_token', ''),
                            chat_id=channel_tg_id,
                            text=caption if not media_file and not photo_files else '',
                            video_path=media_file,
                            photo_paths=photo_files if photo_files else None,
                            caption=caption if (media_file or photo_files) else '',
                        )
                    )
                    if result.get('success'):
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    fail_count += 1

                # 发送间隔
                if i < total - 1:
                    import time
                    interval = int(task.get('interval_seconds', 3))
                    time.sleep(max(1, interval))

            db.close()

            status = 'done' if not self._stop else 'paused'
            result_msg = f"成功: {success_count}, 失败: {fail_count}"

            from core.database import get_db as _get_db
            db2 = _get_db()
            db2.execute(
                "UPDATE tasks SET status=?, result=?, progress=100, last_run=CURRENT_TIMESTAMP WHERE id=?",
                (status, result_msg, self.task_id)
            )
            db2.commit()
            db2.close()

            self.finished.emit(True, f"发布完成！{result_msg}")

        except Exception as e:
            self.finished.emit(False, f"发布失败: {str(e)}")


class CreateTaskDialog(QDialog):
    """创建发布任务对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建发布任务")
        self.setMinimumWidth(620)
        self.setMinimumHeight(680)
        self.setModal(True)
        self._setup_ui()
        self._load_accounts_channels()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("📅 新建发布任务")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # === 基本信息 ===
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        basic_layout.setContentsMargins(12, 12, 12, 12)
        basic_layout.setSpacing(10)

        form = QFrame()
        form.setObjectName("card")
        form_layout = QFormLayout(form)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        self.task_name = QLineEdit()
        self.task_name.setPlaceholderText("如：每日早报发布")
        form_layout.addRow("任务名称:", self.task_name)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(3)
        self.interval_spin.setSuffix(" 秒")
        form_layout.addRow("频道间隔:", self.interval_spin)

        self.send_mode_combo = QComboBox()
        self.send_mode_combo.addItems(["顺序发布（按列表顺序）", "随机发布（随机选择频道）", "全部发布（所有频道）"])
        form_layout.addRow("发布模式:", self.send_mode_combo)

        basic_layout.addWidget(form)

        # 目标账号
        acc_group = QGroupBox("👤 选择发布账号（可多选）")
        acc_layout = QVBoxLayout(acc_group)
        self.acc_list = QListWidget()
        self.acc_list.setFixedHeight(120)
        self.acc_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        acc_layout.addWidget(self.acc_list)
        basic_layout.addWidget(acc_group)

        # 目标频道
        ch_group = QGroupBox("📺 选择目标频道（可多选）")
        ch_layout = QVBoxLayout(ch_group)
        self.ch_list = QListWidget()
        self.ch_list.setFixedHeight(150)
        self.ch_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        ch_btn_row = QHBoxLayout()
        sel_all_btn = QPushButton("全选")
        sel_all_btn.setFixedWidth(60)
        sel_all_btn.clicked.connect(lambda: self.ch_list.selectAll())
        clr_btn = QPushButton("清除")
        clr_btn.setFixedWidth(60)
        clr_btn.clicked.connect(lambda: self.ch_list.clearSelection())
        ch_btn_row.addWidget(sel_all_btn)
        ch_btn_row.addWidget(clr_btn)
        ch_btn_row.addStretch()
        ch_layout.addWidget(self.ch_list)
        ch_layout.addLayout(ch_btn_row)
        basic_layout.addWidget(ch_group)

        # 素材
        media_group = QGroupBox("🎬 选择素材（可多选）")
        media_layout = QVBoxLayout(media_group)
        self.media_list = QListWidget()
        self.media_list.setFixedHeight(120)
        self.media_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        media_layout.addWidget(self.media_list)
        basic_layout.addWidget(media_group)

        tabs.addTab(basic_tab, "📋 基本设置")

        # === 文案 ===
        caption_tab = QWidget()
        cap_layout = QVBoxLayout(caption_tab)
        cap_layout.setContentsMargins(12, 12, 12, 12)
        cap_layout.setSpacing(10)

        cap_title = QLabel("✍️ 发布文案")
        cap_title.setObjectName("sectionTitle")
        cap_layout.addWidget(cap_title)

        self.use_ai_check = QCheckBox("🤖 使用AI自动生成文案")
        cap_layout.addWidget(self.use_ai_check)

        self.caption_input = QTextEdit()
        self.caption_input.setPlaceholderText(
            "输入发布文案（支持HTML格式标签，如 <b>粗体</b> <i>斜体</i> <a href='url'>链接</a>）\n\n"
            "发布效果参考: https://t.me/guofuAD/10784"
        )
        self.caption_input.setMinimumHeight(200)
        cap_layout.addWidget(self.caption_input)

        # 文案模板
        tpl_row = QHBoxLayout()
        tpl_row.addWidget(QLabel("快速模板:"))
        for tpl_name, tpl_text in [
            ("🔥 热门推荐", "🔥 最新发布！\n\n{content}\n\n👆 点击查看详情"),
            ("📢 通知", "📢 重要通知\n\n{content}"),
            ("🎬 视频", "🎬 精彩视频\n\n{content}\n\n🔔 关注频道获取更多"),
        ]:
            btn = QPushButton(tpl_name)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, t=tpl_text: self.caption_input.setPlainText(t))
            tpl_row.addWidget(btn)
        tpl_row.addStretch()
        cap_layout.addLayout(tpl_row)
        cap_layout.addStretch()
        tabs.addTab(caption_tab, "✍️ 文案设置")

        # === 调度 ===
        schedule_tab = QWidget()
        sch_layout = QVBoxLayout(schedule_tab)
        sch_layout.setContentsMargins(12, 12, 12, 12)
        sch_layout.setSpacing(12)

        sch_title = QLabel("📅 调度设置")
        sch_title.setObjectName("sectionTitle")
        sch_layout.addWidget(sch_title)

        sch_card = QFrame()
        sch_card.setObjectName("card")
        sch_card_layout = QFormLayout(sch_card)
        sch_card_layout.setSpacing(12)

        self.schedule_type = QComboBox()
        self.schedule_type.addItems(["立即发布", "指定时间发布", "定时循环（每N分钟）"])
        self.schedule_type.currentIndexChanged.connect(self._on_schedule_type_changed)
        sch_card_layout.addRow("调度类型:", self.schedule_type)

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(300))
        self.datetime_edit.setCalendarPopup(True)
        sch_card_layout.addRow("发布时间:", self.datetime_edit)

        self.interval_minutes = QSpinBox()
        self.interval_minutes.setRange(1, 10080)
        self.interval_minutes.setValue(60)
        self.interval_minutes.setSuffix(" 分钟")
        sch_card_layout.addRow("循环间隔:", self.interval_minutes)

        sch_layout.addWidget(sch_card)

        sch_note = QLabel(
            "💡 调度说明：\n"
            "• 立即发布：保存后立即开始发布\n"
            "• 指定时间：在指定时间自动开始发布\n"
            "• 定时循环：每隔N分钟重复发布一次"
        )
        sch_note.setStyleSheet("""
            font-size: 12px; color: #8b949e;
            background-color: #1c2128;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px;
        """)
        sch_layout.addWidget(sch_note)
        sch_layout.addStretch()
        tabs.addTab(schedule_tab, "📅 调度计划")

        # 按钮区域
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.reject)
        self.create_btn = QPushButton("🚀 创建任务")
        self.create_btn.setObjectName("primaryBtn")
        self.create_btn.setFixedWidth(130)
        self.create_btn.clicked.connect(self._create)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.create_btn)
        layout.addLayout(btn_row)

        self._on_schedule_type_changed(0)

    def _on_schedule_type_changed(self, idx):
        self.datetime_edit.setVisible(idx == 1)
        self.interval_minutes.setVisible(idx == 2)

    def _load_accounts_channels(self):
        try:
            from core.database import get_accounts, get_channels, get_media
            for acc in get_accounts():
                item = QListWidgetItem(f"{'Bot' if acc['type'] == 'bot' else '📱'} {acc['name']}")
                item.setData(Qt.ItemDataRole.UserRole, acc['id'])
                self.acc_list.addItem(item)

            for ch in get_channels():
                item = QListWidgetItem(f"📢 {ch['name']} ({ch['channel_id']})")
                item.setData(Qt.ItemDataRole.UserRole, ch['id'])
                self.ch_list.addItem(item)

            for m in get_media():
                icon = '🎬' if m['file_type'] == 'video' else '🖼️'
                item = QListWidgetItem(f"{icon} {m['name']}")
                item.setData(Qt.ItemDataRole.UserRole, m['id'])
                self.media_list.addItem(item)
        except Exception:
            pass

    def _create(self):
        name = self.task_name.text().strip()
        if not name:
            QMessageBox.warning(self, "验证失败", "请填写任务名称")
            return

        selected_channels = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.ch_list.selectedItems()
        ]
        if not selected_channels:
            QMessageBox.warning(self, "验证失败", "请选择至少一个目标频道")
            return

        selected_accounts = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.acc_list.selectedItems()
        ]
        selected_media = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.media_list.selectedItems()
        ]

        sch_type_map = {0: 'once', 1: 'scheduled', 2: 'interval'}
        sch_type = sch_type_map[self.schedule_type.currentIndex()]
        sch_time = self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss") if sch_type == 'scheduled' else ''

        self.result_data = {
            'name': name,
            'account_ids': json.dumps(selected_accounts),
            'channel_ids': json.dumps(selected_channels),
            'media_ids': json.dumps(selected_media),
            'caption': self.caption_input.toPlainText().strip(),
            'schedule_type': sch_type,
            'schedule_time': sch_time,
            'interval_minutes': self.interval_minutes.value(),
            'send_mode': ['sequential', 'random', 'all'][self.send_mode_combo.currentIndex()],
            'interval_seconds': self.interval_spin.value(),
            'use_ai': 1 if self.use_ai_check.isChecked() else 0,
            'status': 'pending',
        }
        self.accept()


class TaskPage(QWidget):
    """任务中心页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._publish_threads = {}
        self._setup_ui()
        self._load_tasks()

        # 定时刷新
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_tasks)
        self._refresh_timer.start(8000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        header = QHBoxLayout()
        title = QLabel("📅 任务中心")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # 工具栏
        toolbar = QHBoxLayout()
        create_btn = QPushButton("➕ 创建任务")
        create_btn.setObjectName("primaryBtn")
        create_btn.clicked.connect(self._create_task)

        run_btn = QPushButton("▶️ 立即发布")
        run_btn.setObjectName("successBtn")
        run_btn.clicked.connect(self._run_task)

        pause_btn = QPushButton("⏸ 暂停")
        pause_btn.clicked.connect(self._pause_task)

        del_btn = QPushButton("🗑 删除")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete_task)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._load_tasks)

        toolbar.addWidget(create_btn)
        toolbar.addWidget(run_btn)
        toolbar.addWidget(pause_btn)
        toolbar.addSpacing(8)
        toolbar.addWidget(del_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()

        self.task_count_lbl = QLabel("共 0 个任务")
        self.task_count_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        toolbar.addWidget(self.task_count_lbl)
        layout.addLayout(toolbar)

        # 状态筛选
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("状态筛选:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "等待中", "运行中", "已完成", "失败", "已暂停"])
        self.status_filter.currentIndexChanged.connect(self._load_tasks)
        filter_row.addWidget(self.status_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # 任务表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(8)
        self.tasks_table.setHorizontalHeaderLabels(
            ["#", "任务名称", "状态", "频道数", "调度类型", "上次运行", "结果", "进度"]
        )
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tasks_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tasks_table.setColumnWidth(0, 50)
        self.tasks_table.setColumnWidth(7, 100)
        self.tasks_table.verticalHeader().setVisible(False)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tasks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tasks_table.setAlternatingRowColors(True)
        layout.addWidget(self.tasks_table)

        # 进度区域
        progress_card = QFrame()
        progress_card.setObjectName("card")
        prog_layout = QVBoxLayout(progress_card)
        prog_layout.setContentsMargins(14, 10, 14, 10)
        prog_layout.setSpacing(6)

        prog_title = QLabel("📡 发布进度")
        prog_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        prog_layout.addWidget(prog_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        prog_layout.addWidget(self.progress_bar)

        self.progress_status = QLabel("等待任务...")
        self.progress_status.setStyleSheet("color: #8b949e; font-size: 12px;")
        prog_layout.addWidget(self.progress_status)

        layout.addWidget(progress_card)

    def _load_tasks(self):
        try:
            from core.database import get_tasks
            status_map = {
                '全部': None, '等待中': 'pending', '运行中': 'running',
                '已完成': 'done', '失败': 'failed', '已暂停': 'paused'
            }
            status_filter = status_map.get(self.status_filter.currentText())
            tasks = get_tasks(status_filter)

            self.tasks_table.setRowCount(0)
            for i, task in enumerate(tasks):
                self.tasks_table.insertRow(i)

                status_icons = {
                    'pending': '⏳ 等待中', 'running': '▶️ 运行中',
                    'done': '✅ 已完成', 'failed': '❌ 失败', 'paused': '⏸️ 已暂停'
                }
                sch_types = {'once': '单次', 'scheduled': '定时', 'interval': '循环'}

                channels = json.loads(task.get('channel_ids', '[]'))

                items = [
                    str(task.get('id', '')),
                    task.get('name', ''),
                    status_icons.get(task.get('status', ''), task.get('status', '')),
                    str(len(channels)) + ' 个频道',
                    sch_types.get(task.get('schedule_type', ''), 'once'),
                    str(task.get('last_run', '') or '从未'),
                    task.get('result', '') or '-',
                ]

                for j, text in enumerate(items):
                    item = QTableWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, task.get('id'))
                    self.tasks_table.setItem(i, j, item)

                # 进度条
                progress = task.get('progress', 0)
                bar = QProgressBar()
                bar.setValue(progress)
                bar.setFixedHeight(6)
                self.tasks_table.setCellWidget(i, 7, bar)

            self.task_count_lbl.setText(f"共 {len(tasks)} 个任务")
        except Exception:
            pass

    def _create_task(self):
        dlg = CreateTaskDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data
            try:
                from core.database import get_db
                db = get_db()
                db.execute("""
                    INSERT INTO tasks (name, account_ids, channel_ids, media_ids, caption,
                        schedule_type, schedule_time, interval_minutes, send_mode,
                        interval_seconds, use_ai, status)
                    VALUES (:name, :account_ids, :channel_ids, :media_ids, :caption,
                        :schedule_type, :schedule_time, :interval_minutes, :send_mode,
                        :interval_seconds, :use_ai, :status)
                """, data)
                db.commit()
                db.close()
                self._load_tasks()
                QMessageBox.information(self, "成功", f"任务 '{data['name']}' 创建成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建失败: {e}")

    def _get_selected_task_id(self):
        row = self.tasks_table.currentRow()
        if row < 0:
            return None
        item = self.tasks_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _run_task(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            QMessageBox.information(self, "提示", "请先选择要发布的任务")
            return

        if task_id in self._publish_threads and self._publish_threads[task_id].isRunning():
            QMessageBox.information(self, "提示", "该任务正在运行中")
            return

        thread = TaskPublishThread(task_id)
        thread.progress.connect(self._on_publish_progress)
        thread.finished.connect(lambda ok, msg: self._on_publish_finished(task_id, ok, msg))
        self._publish_threads[task_id] = thread
        thread.start()

        self.progress_status.setText(f"任务 #{task_id} 开始发布...")
        self._load_tasks()

    def _on_publish_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.progress_status.setText(msg)

    def _on_publish_finished(self, task_id, ok: bool, msg: str):
        self.progress_bar.setValue(100 if ok else 0)
        self.progress_status.setText(msg)
        self._load_tasks()
        if ok:
            QMessageBox.information(self, "发布完成", msg)
        else:
            QMessageBox.warning(self, "发布失败", msg)

    def _pause_task(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            QMessageBox.information(self, "提示", "请先选择任务")
            return
        if task_id in self._publish_threads:
            self._publish_threads[task_id].stop()
        try:
            from core.database import get_db
            db = get_db()
            db.execute("UPDATE tasks SET status='paused' WHERE id=?", (task_id,))
            db.commit()
            db.close()
            self._load_tasks()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def _delete_task(self):
        task_id = self._get_selected_task_id()
        if not task_id:
            QMessageBox.information(self, "提示", "请先选择要删除的任务")
            return
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除此任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.database import get_db
                db = get_db()
                db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
                db.commit()
                db.close()
                self._load_tasks()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))
