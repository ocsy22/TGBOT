"""
任务中心页面
"""
import os
import json
import threading
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from core.database import DB
from core.task_engine import TaskEngine


class TaskPage(QWidget):
    task_log_signal = pyqtSignal(int, str)
    task_progress_signal = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self._engine = TaskEngine()
        self._init_ui()
        self.task_log_signal.connect(self._on_task_log)
        self.task_progress_signal.connect(self._on_task_progress)
        self.refresh()

        self._timer = QTimer()
        self._timer.timeout.connect(self.refresh)
        self._timer.start(5000)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题行
        hdr = QHBoxLayout()
        t_v = QVBoxLayout()
        t = QLabel('任务中心')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('创建、管理和发布视频任务')
        sub.setStyleSheet('color: #8b949e;')
        t_v.addWidget(t)
        t_v.addWidget(sub)
        hdr.addLayout(t_v, 1)

        batch_btn = QPushButton('⚡ 批量发布')
        batch_btn.clicked.connect(self._batch_publish)
        new_btn = QPushButton('+ 新建任务')
        new_btn.setObjectName('primary_btn')
        new_btn.clicked.connect(self._new_task)
        hdr.addWidget(batch_btn)
        hdr.addWidget(new_btn)
        layout.addLayout(hdr)

        # 状态标签
        tab_row = QHBoxLayout()
        self._status_tabs = []
        for label, key in [('全部', ''), ('处理中', 'processing'), ('待预览', 'pending'), ('已完成', 'completed'), ('失败', 'failed')]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName('tab_btn')
            btn.setStyleSheet('''
                QPushButton#tab_btn{background:transparent;border:none;color:#8b949e;padding:6px 12px;border-bottom:2px solid transparent;}
                QPushButton#tab_btn:checked{color:#e6edf3;border-bottom:2px solid #1f6feb;}
                QPushButton#tab_btn:hover{color:#e6edf3;}
            ''')
            btn.clicked.connect(lambda checked, k=key: self._filter_tasks(k))
            self._status_tabs.append(btn)
            tab_row.addWidget(btn)
        self._status_tabs[0].setChecked(True)

        self._count_label = QLabel('共 0 个任务')
        self._count_label.setStyleSheet('color:#8b949e;font-size:12px;')
        tab_row.addStretch()
        tab_row.addWidget(self._count_label)
        layout.addLayout(tab_row)

        # 任务列表
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._task_container = QWidget()
        self._task_layout = QVBoxLayout(self._task_container)
        self._task_layout.setSpacing(8)
        self._task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._task_container)
        layout.addWidget(self._scroll)

        self._current_filter = ''

    def _filter_tasks(self, status_key):
        for btn in self._status_tabs:
            btn.setChecked(False)
        self._current_filter = status_key
        self.refresh()

    def refresh(self):
        while self._task_layout.count():
            item = self._task_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._current_filter:
            tasks = DB.fetchall('SELECT * FROM tasks WHERE status=? ORDER BY id DESC', (self._current_filter,))
        else:
            tasks = DB.fetchall('SELECT * FROM tasks ORDER BY id DESC')

        self._count_label.setText(f'共 {len(tasks)} 个任务')

        for task in tasks:
            card = self._create_task_card(task)
            self._task_layout.addWidget(card)

    def _create_task_card(self, task: dict) -> QFrame:
        card = QFrame()
        card.setObjectName('card')
        card.setStyleSheet('QFrame#card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;}')

        lay = QVBoxLayout(card)
        lay.setSpacing(8)
        lay.setContentsMargins(14, 12, 14, 12)

        # 顶部行
        top = QHBoxLayout()
        title_text = task.get('title') or f'任务 #{task["id"]}'
        title = QLabel(f'任务 #{task["id"]} — {title_text}')
        title.setFont(QFont('Segoe UI', 13))
        title.setStyleSheet('color:#e6edf3;')

        status = task.get('status', 'pending')
        status_map = {
            'pending': ('待处理', 'color:#d29922;background:#2d2000;'),
            'processing': ('处理中', 'color:#1f6feb;background:#1f3a5f;'),
            'completed': ('已完成', 'color:#2ea043;background:#1a3a2a;'),
            'failed': ('失败', 'color:#da3633;background:#3d1a1a;'),
            'partial': ('部分成功', 'color:#d29922;background:#2d2000;'),
        }
        s_text, s_style = status_map.get(status, ('未知', ''))
        status_lbl = QLabel(s_text)
        status_lbl.setStyleSheet(f'{s_style}border-radius:10px;padding:2px 10px;font-size:11px;')

        top.addWidget(title, 1)
        top.addWidget(status_lbl)
        lay.addLayout(top)

        # 进度和信息
        info_text_parts = []
        created = task.get('created_at', '')[:16]
        info_text_parts.append(f'⏰ {created}')

        # 频道信息
        ch_ids = json.loads(task.get('channel_ids', '[]'))
        if ch_ids:
            channels = [DB.fetchone('SELECT name FROM channels WHERE id=?', (cid,)) for cid in ch_ids]
            ch_names = [c['name'] for c in channels if c]
            info_text_parts.append(f'📡 {", ".join(ch_names)}')

        if task.get('scheduled_time'):
            info_text_parts.append(f'⏱ 定时: {task["scheduled_time"]}')

        info_lbl = QLabel('  '.join(info_text_parts))
        info_lbl.setStyleSheet('color:#8b949e;font-size:12px;')
        lay.addWidget(info_lbl)

        # 进度条（处理中显示）
        if status == 'processing':
            prog = QProgressBar()
            prog.setValue(task.get('progress', 0))
            prog.setFixedHeight(4)
            lay.addWidget(prog)

        # AI文案预览
        result_text = task.get('result_text', '')
        if result_text:
            # 截取前100字
            preview = result_text[:120] + ('...' if len(result_text) > 120 else '')
            preview_lbl = QLabel(f'AI文案: {preview}')
            preview_lbl.setStyleSheet('color:#8b949e;font-size:11px;')
            preview_lbl.setWordWrap(True)
            lay.addWidget(preview_lbl)

        # 错误信息
        if task.get('error_msg') and status == 'failed':
            err_lbl = QLabel(f'❌ {task["error_msg"][:100]}')
            err_lbl.setStyleSheet('color:#da3633;font-size:11px;')
            err_lbl.setWordWrap(True)
            lay.addWidget(err_lbl)

        # 操作按钮
        actions = QHBoxLayout()
        actions.setSpacing(6)

        view_btn = QPushButton('👁')
        view_btn.setObjectName('icon_btn')
        view_btn.setFixedSize(28, 28)
        view_btn.setToolTip('查看详情')
        view_btn.clicked.connect(lambda: self._view_task(task))

        run_btn = QPushButton('▶')
        run_btn.setObjectName('icon_btn')
        run_btn.setFixedSize(28, 28)
        run_btn.setToolTip('立即执行')
        run_btn.clicked.connect(lambda: self._run_task(task['id']))

        if status in ('processing',):
            run_btn.setEnabled(False)

        sched_btn = QPushButton('⏱')
        sched_btn.setObjectName('icon_btn')
        sched_btn.setFixedSize(28, 28)
        sched_btn.setToolTip('定时发布')
        sched_btn.clicked.connect(lambda: self._schedule_task(task))

        del_btn = QPushButton('🗑️')
        del_btn.setObjectName('icon_btn')
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet('color:#da3633;background:transparent;border:none;')
        del_btn.setToolTip('删除')
        del_btn.clicked.connect(lambda: self._delete_task(task['id']))

        retry_btn = QPushButton('🔄')
        retry_btn.setObjectName('icon_btn')
        retry_btn.setFixedSize(28, 28)
        retry_btn.setToolTip('重试')
        retry_btn.clicked.connect(lambda: self._retry_task(task))

        actions.addStretch()
        actions.addWidget(view_btn)
        actions.addWidget(run_btn)
        actions.addWidget(sched_btn)
        actions.addWidget(retry_btn)
        actions.addWidget(del_btn)
        lay.addLayout(actions)

        return card

    def _new_task(self):
        dlg = NewTaskDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            task_id = DB.execute(
                '''INSERT INTO tasks (title, channel_ids, media_file_id, media_folder_id,
                   copy_template_id, writing_direction_id, ai_generate, send_mode,
                   clip_enabled, clip_start, clip_duration, clip_resolution, clip_bitrate,
                   screenshot_enabled, scheduled_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (data['title'], json.dumps(data['channel_ids']), data.get('media_file_id', 0),
                 data.get('media_folder_id', 0), data.get('copy_template_id', 0),
                 data.get('writing_direction_id', 0), data.get('ai_generate', 1),
                 data.get('send_mode', 'video'), data.get('clip_enabled', 0),
                 data.get('clip_start', 0), data.get('clip_duration', 60),
                 data.get('clip_resolution', '1920x1080'), data.get('clip_bitrate', '4M'),
                 data.get('screenshot_enabled', 1), data.get('scheduled_time', ''))
            )
            self.refresh()
            if not data.get('scheduled_time'):
                reply = QMessageBox.question(self, '立即执行', '任务已创建，是否立即执行？')
                if reply == QMessageBox.StandardButton.Yes:
                    self._run_task(task_id)

    def _run_task(self, task_id):
        def on_log(msg):
            self.task_log_signal.emit(task_id, msg)

        def on_progress(pct):
            self.task_progress_signal.emit(task_id, pct)

        self._engine.execute_task_async(task_id, on_progress, on_log)
        self.refresh()

    def _view_task(self, task):
        dlg = TaskDetailDialog(self, task)
        dlg.exec()

    def _schedule_task(self, task):
        time_str, ok = QInputDialog.getText(self, '定时发布', '输入发布时间 (格式: 2026-03-19 20:55):')
        if ok and time_str:
            DB.execute('UPDATE tasks SET scheduled_time=? WHERE id=?', (time_str, task['id']))
            self.refresh()

    def _delete_task(self, task_id):
        if QMessageBox.question(self, '确认', '确定删除此任务？') == QMessageBox.StandardButton.Yes:
            DB.execute('DELETE FROM tasks WHERE id=?', (task_id,))
            self.refresh()

    def _retry_task(self, task):
        DB.execute("UPDATE tasks SET status='pending', progress=0, error_msg='' WHERE id=?", (task['id'],))
        self._run_task(task['id'])

    def _batch_publish(self):
        dlg = BatchPublishDialog(self)
        dlg.exec()

    def _on_task_log(self, task_id, msg):
        pass  # 可以显示在状态栏

    def _on_task_progress(self, task_id, pct):
        self.refresh()


class NewTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('新建任务')
        self.setFixedSize(600, 700)
        self.setStyleSheet('QDialog{background:#161b22;}')
        self._init_ui()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        form = QVBoxLayout(content)
        form.setSpacing(12)

        # 任务标题
        form.addWidget(QLabel('任务标题 (可选):'))
        self._title = QLineEdit()
        self._title.setPlaceholderText('留空将自动使用文件名')
        form.addWidget(self._title)

        # 发布频道
        form.addWidget(QLabel('发布频道 (多选):'))
        self._ch_list = QListWidget()
        self._ch_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._ch_list.setFixedHeight(120)
        channels = DB.fetchall('SELECT * FROM channels ORDER BY name')
        for ch in channels:
            item = QListWidgetItem(f'📡 {ch["name"]}')
            item.setData(Qt.ItemDataRole.UserRole, ch['id'])
            self._ch_list.addItem(item)
        form.addWidget(self._ch_list)

        # 媒体文件
        form.addWidget(QLabel('选择媒体文件:'))
        media_row = QHBoxLayout()
        self._media_combo = QComboBox()
        self._media_combo.addItem('-- 不选择 --', 0)
        folders = DB.fetchall('SELECT * FROM media_folders')
        for folder in folders:
            files = DB.fetchall('SELECT * FROM media_files WHERE folder_id=?', (folder['id'],))
            for f in files:
                self._media_combo.addItem(f'[{folder["name"]}] {f["filename"]}', f['id'])
        media_row.addWidget(self._media_combo, 1)
        browse_btn = QPushButton('浏览...')
        browse_btn.clicked.connect(self._browse_file)
        media_row.addWidget(browse_btn)
        form.addLayout(media_row)

        # 视频裁剪设置
        clip_group = QGroupBox('视频裁剪')
        clip_group.setStyleSheet('QGroupBox{color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding-top:10px;}QGroupBox::title{color:#8b949e;}')
        clip_lay = QVBoxLayout(clip_group)

        self._clip_enabled = QCheckBox('启用视频裁剪')
        self._clip_enabled.stateChanged.connect(self._on_clip_changed)
        clip_lay.addWidget(self._clip_enabled)

        self._clip_settings = QWidget()
        cs_lay = QGridLayout(self._clip_settings)
        cs_lay.addWidget(QLabel('开始时间(秒):'), 0, 0)
        self._clip_start = QSpinBox()
        self._clip_start.setRange(0, 36000)
        cs_lay.addWidget(self._clip_start, 0, 1)

        cs_lay.addWidget(QLabel('裁剪时长(秒):'), 0, 2)
        self._clip_dur = QSpinBox()
        self._clip_dur.setRange(1, 36000)
        self._clip_dur.setValue(60)
        cs_lay.addWidget(self._clip_dur, 0, 3)

        cs_lay.addWidget(QLabel('分辨率:'), 1, 0)
        self._clip_res = QComboBox()
        for res in ['1920x1080', '1280x720', '854x480', '1080x1920', '720x1280']:
            self._clip_res.addItem(res)
        cs_lay.addWidget(self._clip_res, 1, 1)

        cs_lay.addWidget(QLabel('码率:'), 1, 2)
        self._clip_bitrate = QComboBox()
        for br in ['4M', '2M', '6M', '8M', '1M']:
            self._clip_bitrate.addItem(br)
        cs_lay.addWidget(self._clip_bitrate, 1, 3)

        self._clip_settings.setVisible(False)
        clip_lay.addWidget(self._clip_settings)
        form.addWidget(clip_group)

        # 截图设置
        self._screenshot_enabled = QCheckBox('提取视频截图（封面图）')
        self._screenshot_enabled.setChecked(True)
        form.addWidget(self._screenshot_enabled)

        # AI文案
        ai_group = QGroupBox('AI文案生成')
        ai_group.setStyleSheet('QGroupBox{color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding-top:10px;}QGroupBox::title{color:#8b949e;}')
        ai_lay = QVBoxLayout(ai_group)
        self._ai_generate = QCheckBox('AI自动生成文案')
        self._ai_generate.setChecked(True)
        ai_lay.addWidget(self._ai_generate)

        tmpl_row = QHBoxLayout()
        tmpl_row.addWidget(QLabel('文案模板:'))
        self._tmpl_combo = QComboBox()
        templates = DB.fetchall('SELECT * FROM copy_templates')
        for t in templates:
            self._tmpl_combo.addItem(t['name'], t['id'])
        tmpl_row.addWidget(self._tmpl_combo, 1)
        ai_lay.addLayout(tmpl_row)

        wd_row = QHBoxLayout()
        wd_row.addWidget(QLabel('写作方向:'))
        self._wd_combo = QComboBox()
        self._wd_combo.addItem('-- 默认 --', 0)
        wds = DB.fetchall('SELECT * FROM writing_directions')
        for wd in wds:
            self._wd_combo.addItem(wd['name'], wd['id'])
        wd_row.addWidget(self._wd_combo, 1)
        ai_lay.addLayout(wd_row)
        form.addWidget(ai_group)

        # 定时发布
        form.addWidget(QLabel('定时发布时间 (可选):'))
        self._sched_time = QLineEdit()
        self._sched_time.setPlaceholderText('如: 2026-03-19 20:55 (留空立即发布)')
        form.addWidget(self._sched_time)

        form.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText('创建任务')
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _on_clip_changed(self, state):
        self._clip_settings.setVisible(state == Qt.CheckState.Checked.value)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择视频文件', '',
                                               'Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)')
        if path:
            fname = os.path.basename(path)
            # 添加到临时
            self._media_combo.addItem(f'[文件] {fname}', -1)
            self._media_combo.setCurrentIndex(self._media_combo.count() - 1)
            self._browse_path = path

    def get_data(self):
        ch_ids = []
        for item in self._ch_list.selectedItems():
            ch_ids.append(item.data(Qt.ItemDataRole.UserRole))

        return {
            'title': self._title.text().strip(),
            'channel_ids': ch_ids,
            'media_file_id': self._media_combo.currentData() or 0,
            'clip_enabled': 1 if self._clip_enabled.isChecked() else 0,
            'clip_start': self._clip_start.value(),
            'clip_duration': self._clip_dur.value(),
            'clip_resolution': self._clip_res.currentText(),
            'clip_bitrate': self._clip_bitrate.currentText(),
            'screenshot_enabled': 1 if self._screenshot_enabled.isChecked() else 0,
            'ai_generate': 1 if self._ai_generate.isChecked() else 0,
            'copy_template_id': self._tmpl_combo.currentData() or 0,
            'writing_direction_id': self._wd_combo.currentData() or 0,
            'scheduled_time': self._sched_time.text().strip(),
        }


class TaskDetailDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle(f'任务详情 #{task["id"]}')
        self.setFixedSize(600, 500)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_lay = QVBoxLayout(content)

        if task.get('result_text'):
            lbl = QLabel('AI生成文案:')
            lbl.setStyleSheet('font-weight:bold;')
            content_lay.addWidget(lbl)
            txt = QTextEdit()
            txt.setPlainText(task['result_text'])
            txt.setReadOnly(True)
            txt.setFixedHeight(200)
            content_lay.addWidget(txt)

        if task.get('error_msg'):
            err_lbl = QLabel(f'错误信息:\n{task["error_msg"]}')
            err_lbl.setStyleSheet('color:#da3633;')
            err_lbl.setWordWrap(True)
            content_lay.addWidget(err_lbl)

        # 发布日志
        logs = DB.fetchall('SELECT * FROM publish_logs WHERE task_id=? ORDER BY id', (task['id'],))
        if logs:
            log_lbl = QLabel('发布日志:')
            log_lbl.setStyleSheet('font-weight:bold;')
            content_lay.addWidget(log_lbl)
            for log in logs:
                color = '#2ea043' if log['status'] == 'success' else '#da3633'
                icon = '✅' if log['status'] == 'success' else '❌'
                ll = QLabel(f'{icon} {log["channel_name"]}: {log["message"]}')
                ll.setStyleSheet(f'color:{color};font-size:12px;')
                content_lay.addWidget(ll)

        content_lay.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)

        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)


class ClipDialog(QDialog):
    """视频裁剪对话框"""
    def __init__(self, parent=None, file_data=None):
        super().__init__(parent)
        self.setWindowTitle('视频裁剪')
        self.setFixedSize(480, 360)
        self.setStyleSheet('QDialog{background:#161b22;}')
        self._file_data = file_data
        self._init_ui()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        if self._file_data:
            lbl = QLabel(f'文件: {self._file_data["filename"]}')
            lbl.setStyleSheet('color:#e6edf3;font-weight:bold;')
            lay.addWidget(lbl)

        lay.addWidget(QLabel('开始时间(秒):'))
        self._start = QSpinBox()
        self._start.setRange(0, 36000)
        lay.addWidget(self._start)

        lay.addWidget(QLabel('裁剪时长(秒):'))
        self._dur = QSpinBox()
        self._dur.setRange(1, 36000)
        self._dur.setValue(60)
        lay.addWidget(self._dur)

        lay.addWidget(QLabel('输出分辨率:'))
        self._res = QComboBox()
        for r in ['1920x1080', '1280x720', '854x480', '1080x1920', '720x1280']:
            self._res.addItem(r)
        lay.addWidget(self._res)

        lay.addWidget(QLabel('码率:'))
        self._br = QComboBox()
        for br in ['4M', '2M', '6M']:
            self._br.addItem(br)
        lay.addWidget(self._br)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        lay.addWidget(self._progress)

        self._log_lbl = QLabel('')
        self._log_lbl.setStyleSheet('color:#8b949e;font-size:11px;')
        lay.addWidget(self._log_lbl)

        btn_row = QHBoxLayout()
        clip_btn = QPushButton('开始裁剪')
        clip_btn.setObjectName('primary_btn')
        clip_btn.clicked.connect(self._do_clip)
        cancel_btn = QPushButton('关闭')
        cancel_btn.clicked.connect(self.accept)
        btn_row.addWidget(clip_btn)
        btn_row.addWidget(cancel_btn)
        lay.addLayout(btn_row)

    def _do_clip(self):
        if not self._file_data:
            return
        vcfg = DB.fetchone('SELECT * FROM video_settings WHERE id=1') or {}
        from core.video_processor import VideoProcessor
        vp = VideoProcessor(vcfg.get('ffmpeg_path', 'ffmpeg'))

        input_path = self._file_data['filepath']
        if not os.path.exists(input_path):
            QMessageBox.warning(self, '错误', '文件不存在')
            return

        output_dir = os.path.join(os.path.dirname(input_path), '已裁剪')
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.splitext(self._file_data['filename'])[0]
        output_path = os.path.join(output_dir, f'{base}_clipped.mp4')

        self._progress.setVisible(True)
        self._progress.setValue(0)

        def do_work():
            def on_progress(pct):
                self._progress.setValue(pct)
            success = vp.clip_video(
                input_path, output_path,
                start=self._start.value(),
                duration=self._dur.value(),
                resolution=self._res.currentText(),
                bitrate=self._br.currentText(),
                progress_callback=on_progress
            )
            if success:
                self._log_lbl.setText(f'✅ 裁剪完成: {output_path}')
            else:
                self._log_lbl.setText('❌ 裁剪失败，请检查FFmpeg配置')

        t = threading.Thread(target=do_work, daemon=True)
        t.start()


class BatchPublishDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('批量发布')
        self.setFixedSize(560, 480)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)
        lbl = QLabel('批量创建并发布多个视频任务')
        lbl.setStyleSheet('color:#8b949e;')
        lay.addWidget(lbl)

        lay.addWidget(QLabel('选择素材文件夹:'))
        self._folder_combo = QComboBox()
        folders = DB.fetchall('SELECT * FROM media_folders')
        for f in folders:
            self._folder_combo.addItem(f'📁 {f["name"]}', f['id'])
        lay.addWidget(self._folder_combo)

        lay.addWidget(QLabel('发布频道 (多选):'))
        self._ch_list = QListWidget()
        self._ch_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._ch_list.setFixedHeight(120)
        channels = DB.fetchall('SELECT * FROM channels')
        for ch in channels:
            item = QListWidgetItem(f'📡 {ch["name"]}')
            item.setData(Qt.ItemDataRole.UserRole, ch['id'])
            self._ch_list.addItem(item)
        lay.addWidget(self._ch_list)

        self._ai_cb = QCheckBox('AI自动生成文案')
        self._ai_cb.setChecked(True)
        lay.addWidget(self._ai_cb)

        self._screenshot_cb = QCheckBox('自动提取截图')
        self._screenshot_cb.setChecked(True)
        lay.addWidget(self._screenshot_cb)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText('批量创建任务')
        btns.accepted.connect(self._create_batch)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _create_batch(self):
        folder_id = self._folder_combo.currentData()
        if not folder_id:
            QMessageBox.warning(self, '错误', '请选择素材文件夹')
            return

        ch_ids = [item.data(Qt.ItemDataRole.UserRole) for item in self._ch_list.selectedItems()]
        if not ch_ids:
            QMessageBox.warning(self, '错误', '请选择频道')
            return

        files = DB.fetchall('SELECT * FROM media_files WHERE folder_id=? AND file_type="video"', (folder_id,))
        if not files:
            QMessageBox.warning(self, '错误', '该文件夹没有视频文件')
            return

        for f in files:
            DB.execute(
                '''INSERT INTO tasks (title, channel_ids, media_file_id, ai_generate, screenshot_enabled)
                   VALUES (?,?,?,?,?)''',
                (f['filename'], json.dumps(ch_ids), f['id'],
                 1 if self._ai_cb.isChecked() else 0,
                 1 if self._screenshot_cb.isChecked() else 0)
            )

        QMessageBox.information(self, '完成', f'已创建 {len(files)} 个任务')
        self.accept()
