"""
媒体库页面 - 支持视频导入、裁剪和截图
"""
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox,
    QProgressBar, QTextEdit, QSizePolicy, QSplitter,
    QScrollArea, QGridLayout, QTabWidget, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon


class VideoProcessThread(QThread):
    """视频处理线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, list)

    def __init__(self, files, ffmpeg_path, output_folder_name, action, params):
        super().__init__()
        self.files = files
        self.ffmpeg_path = ffmpeg_path
        self.output_folder_name = output_folder_name
        self.action = action  # 'crop' / 'screenshot' / 'both'
        self.params = params

    def run(self):
        try:
            from core.video_processor import VideoProcessor
            processor = VideoProcessor(self.ffmpeg_path)
            results = []

            for i, file_path in enumerate(self.files):
                self.progress.emit(
                    int((i / len(self.files)) * 100),
                    f"处理: {os.path.basename(file_path)}"
                )

                if self.action in ('crop', 'both'):
                    result = processor.crop_video(
                        file_path,
                        self.output_folder_name,
                        self.params.get('start_time', '00:00:00'),
                        self.params.get('end_time', ''),
                        self.params.get('duration', 0),
                    )
                    if result:
                        results.append(result)

                if self.action in ('screenshot', 'both'):
                    ss_results = processor.capture_screenshots(
                        file_path,
                        self.output_folder_name,
                        self.params.get('grid', '3x3'),
                        self.params.get('count', 9),
                    )
                    results.extend(ss_results)

            self.finished.emit(True, f"处理完成，共处理 {len(results)} 个文件", results)
        except Exception as e:
            self.finished.emit(False, f"处理失败: {str(e)}", [])


class MediaCard(QFrame):
    """媒体卡片"""

    def __init__(self, media_info: dict, parent=None):
        super().__init__(parent)
        self.media_info = media_info
        self.setObjectName("card")
        self.setFixedSize(180, 160)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 缩略图区域
        thumb_area = QFrame()
        thumb_area.setFixedHeight(90)
        thumb_area.setStyleSheet("""
            background-color: #21262d;
            border-radius: 6px;
        """)
        thumb_layout = QVBoxLayout(thumb_area)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        # 文件类型图标
        file_type = self.media_info.get('file_type', 'video')
        icons = {'video': '🎬', 'image': '🖼️', 'text': '📄'}
        icon_lbl = QLabel(icons.get(file_type, '📁'))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 28px; background: transparent;")
        thumb_layout.addWidget(icon_lbl)
        layout.addWidget(thumb_area)

        # 文件名
        name = os.path.basename(self.media_info.get('name', ''))
        name_lbl = QLabel(name[:22] + '...' if len(name) > 22 else name)
        name_lbl.setStyleSheet("font-size: 11px; color: #e6edf3; background: transparent;")
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        # 文件大小
        size = self.media_info.get('file_size', 0)
        size_str = f"{size / 1024 / 1024:.1f} MB" if size > 1024 * 1024 else f"{size / 1024:.0f} KB"
        size_lbl = QLabel(size_str)
        size_lbl.setStyleSheet("font-size: 10px; color: #8b949e; background: transparent;")
        layout.addWidget(size_lbl)


class MediaPage(QWidget):
    """媒体库页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_media()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        header = QHBoxLayout()
        title = QLabel("🎬 媒体库")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # === 媒体列表标签页 ===
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)
        list_layout.setContentsMargins(0, 12, 0, 0)
        list_layout.setSpacing(10)

        # 工具栏
        toolbar = QHBoxLayout()
        import_btn = QPushButton("📁 导入视频")
        import_btn.setObjectName("primaryBtn")
        import_btn.clicked.connect(self._import_video)

        import_img_btn = QPushButton("🖼️ 导入图片")
        import_img_btn.clicked.connect(self._import_image)

        import_dir_btn = QPushButton("📂 导入文件夹")
        import_dir_btn.clicked.connect(self._import_folder)

        del_btn = QPushButton("🗑 删除")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete_media)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._load_media)

        toolbar.addWidget(import_btn)
        toolbar.addWidget(import_img_btn)
        toolbar.addWidget(import_dir_btn)
        toolbar.addSpacing(8)
        toolbar.addWidget(del_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()

        self.media_count_lbl = QLabel("共 0 个素材")
        self.media_count_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        toolbar.addWidget(self.media_count_lbl)
        list_layout.addLayout(toolbar)

        # 筛选栏
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("筛选:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["全部", "视频", "图片", "文字"])
        self.type_filter.currentIndexChanged.connect(self._load_media)
        filter_bar.addWidget(self.type_filter)
        filter_bar.addStretch()
        list_layout.addLayout(filter_bar)

        # 媒体列表
        self.media_list = QListWidget()
        self.media_list.setViewMode(QListWidget.ViewMode.ListMode)
        self.media_list.setAlternatingRowColors(True)
        self.media_list.setSpacing(2)
        list_layout.addWidget(self.media_list)
        tabs.addTab(list_tab, "📋 素材列表")

        # === 视频处理标签页 ===
        process_tab = QWidget()
        proc_layout = QVBoxLayout(process_tab)
        proc_layout.setContentsMargins(0, 12, 0, 0)
        proc_layout.setSpacing(12)

        proc_header = QLabel("✂️ 视频处理工具")
        proc_header.setObjectName("sectionTitle")
        proc_layout.addWidget(proc_header)

        # 说明
        proc_note = QLabel(
            "📁 输出目录：在原视频同级位置自动创建「已裁剪」文件夹\n"
            "✂️  裁剪：截取视频片段，支持设置起止时间或持续时长\n"
            "📸 截图：自动从视频中均匀提取截图（3×3网格，共9张）\n"
            "⚡ 需要 FFmpeg：将 ffmpeg.exe 放在程序目录或在设置中配置路径"
        )
        proc_note.setStyleSheet("""
            font-size: 12px; color: #8b949e;
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 12px;
        """)
        proc_note.setWordWrap(True)
        proc_layout.addWidget(proc_note)

        # 文件选择
        file_sel_card = QFrame()
        file_sel_card.setObjectName("card")
        file_sel_layout = QVBoxLayout(file_sel_card)
        file_sel_layout.setSpacing(8)

        sel_title = QLabel("📂 选择要处理的视频文件")
        sel_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #e6edf3;")
        file_sel_layout.addWidget(sel_title)

        sel_row = QHBoxLayout()
        self.proc_file_input = QLineEdit()
        self.proc_file_input.setPlaceholderText("点击右侧按钮选择视频文件...")
        self.proc_file_input.setReadOnly(True)
        sel_row.addWidget(self.proc_file_input)

        browse_btn = QPushButton("📁 浏览")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_proc_file)

        browse_dir_btn = QPushButton("📂 选择文件夹")
        browse_dir_btn.setFixedWidth(110)
        browse_dir_btn.clicked.connect(self._browse_proc_dir)

        sel_row.addWidget(browse_btn)
        sel_row.addWidget(browse_dir_btn)
        file_sel_layout.addLayout(sel_row)

        self.selected_files_lbl = QLabel("未选择文件")
        self.selected_files_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        file_sel_layout.addWidget(self.selected_files_lbl)
        proc_layout.addWidget(file_sel_card)

        # 处理参数
        params_card = QFrame()
        params_card.setObjectName("card")
        params_layout = QVBoxLayout(params_card)
        params_layout.setSpacing(10)

        params_title = QLabel("⚙️ 处理参数")
        params_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #e6edf3;")
        params_layout.addWidget(params_title)

        # 操作类型
        action_row = QHBoxLayout()
        action_row.addWidget(QLabel("处理方式:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems([
            "仅截图（3x3网格，9张）",
            "仅裁剪视频片段",
            "截图 + 裁剪（同时执行）",
        ])
        action_row.addWidget(self.action_combo)
        action_row.addStretch()
        params_layout.addLayout(action_row)

        # 裁剪参数
        crop_row = QHBoxLayout()
        crop_row.addWidget(QLabel("裁剪起始:"))
        self.start_time_input = QLineEdit("00:00:00")
        self.start_time_input.setFixedWidth(100)
        crop_row.addWidget(self.start_time_input)
        crop_row.addSpacing(8)
        crop_row.addWidget(QLabel("结束时间:"))
        self.end_time_input = QLineEdit()
        self.end_time_input.setFixedWidth(100)
        self.end_time_input.setPlaceholderText("留空=到结尾")
        crop_row.addWidget(self.end_time_input)
        crop_row.addSpacing(8)
        crop_row.addWidget(QLabel("或持续时长(秒):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 7200)
        self.duration_spin.setFixedWidth(80)
        self.duration_spin.setSpecialValueText("不限")
        crop_row.addWidget(self.duration_spin)
        crop_row.addStretch()
        params_layout.addLayout(crop_row)

        # 输出文件夹名
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("输出文件夹名:"))
        self.output_folder_input = QLineEdit("已裁剪")
        self.output_folder_input.setFixedWidth(120)
        out_row.addWidget(self.output_folder_input)
        out_note = QLabel("（在原视频同级目录创建此文件夹）")
        out_note.setStyleSheet("color: #8b949e; font-size: 11px;")
        out_row.addWidget(out_note)
        out_row.addStretch()
        params_layout.addLayout(out_row)
        proc_layout.addWidget(params_card)

        # 进度和执行
        exec_card = QFrame()
        exec_card.setObjectName("card")
        exec_layout = QVBoxLayout(exec_card)
        exec_layout.setSpacing(8)

        exec_row = QHBoxLayout()
        self.process_btn = QPushButton("⚡ 开始处理")
        self.process_btn.setObjectName("successBtn")
        self.process_btn.setFixedHeight(40)
        self.process_btn.clicked.connect(self._start_processing)
        exec_row.addWidget(self.process_btn)

        stop_btn = QPushButton("⏹ 停止")
        stop_btn.setFixedHeight(40)
        stop_btn.setFixedWidth(80)
        exec_row.addWidget(stop_btn)
        exec_layout.addLayout(exec_row)

        self.proc_progress = QProgressBar()
        self.proc_progress.setValue(0)
        self.proc_progress.setFixedHeight(6)
        exec_layout.addWidget(self.proc_progress)

        self.proc_status = QLabel("就绪")
        self.proc_status.setStyleSheet("color: #8b949e; font-size: 12px;")
        exec_layout.addWidget(self.proc_status)
        proc_layout.addWidget(exec_card)

        proc_layout.addStretch()
        tabs.addTab(process_tab, "✂️ 视频处理")

        self._proc_files = []

    def _load_media(self):
        try:
            from core.database import get_media
            type_map = {'全部': None, '视频': 'video', '图片': 'image', '文字': 'text'}
            filter_text = self.type_filter.currentText() if hasattr(self, 'type_filter') else '全部'
            media_type = type_map.get(filter_text)
            medias = get_media(media_type)

            self.media_list.clear()
            for m in medias:
                name = os.path.basename(m.get('file_path', m.get('name', '')))
                file_type = m.get('file_type', 'video')
                type_icons = {'video': '🎬', 'image': '🖼️', 'text': '📄'}
                icon = type_icons.get(file_type, '📁')

                size = m.get('file_size', 0)
                size_str = f"{size / 1024 / 1024:.1f}MB" if size > 1024 * 1024 else f"{size / 1024:.0f}KB"

                item = QListWidgetItem(f"{icon}  {name}  ({size_str})")
                item.setData(Qt.ItemDataRole.UserRole, m.get('id'))
                self.media_list.addItem(item)

            if hasattr(self, 'media_count_lbl'):
                self.media_count_lbl.setText(f"共 {len(medias)} 个素材")
        except Exception as e:
            pass

    def _import_video(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.ts *.webm);;所有文件 (*.*)"
        )
        if files:
            self._add_files_to_db(files, 'video')

    def _import_image(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "",
            "图片文件 (*.jpg *.jpeg *.png *.gif *.webp *.bmp);;所有文件 (*.*)"
        )
        if files:
            self._add_files_to_db(files, 'image')

    def _import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择媒体文件夹")
        if folder:
            files = []
            video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.ts', '.webm'}
            image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

            for f in os.listdir(folder):
                ext = os.path.splitext(f)[1].lower()
                if ext in video_exts or ext in image_exts:
                    files.append(os.path.join(folder, f))

            if files:
                video_files = [f for f in files if os.path.splitext(f)[1].lower() in video_exts]
                image_files = [f for f in files if os.path.splitext(f)[1].lower() in image_exts]
                self._add_files_to_db(video_files, 'video')
                self._add_files_to_db(image_files, 'image')
                QMessageBox.information(
                    self, "导入成功",
                    f"已导入 {len(video_files)} 个视频，{len(image_files)} 个图片"
                )
            else:
                QMessageBox.information(self, "提示", "文件夹中未找到媒体文件")

    def _add_files_to_db(self, files: list, file_type: str):
        try:
            from core.database import get_db
            db = get_db()
            count = 0
            for file_path in files:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    name = os.path.basename(file_path)
                    db.execute("""
                        INSERT OR IGNORE INTO media (name, file_path, file_type, file_size)
                        VALUES (?, ?, ?, ?)
                    """, (name, file_path, file_type, file_size))
                    count += 1
            db.commit()
            db.close()
            self._load_media()
            if count > 0:
                QMessageBox.information(self, "导入成功", f"成功导入 {count} 个文件！")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", str(e))

    def _delete_media(self):
        item = self.media_list.currentItem()
        if not item:
            QMessageBox.information(self, "提示", "请先选择要删除的素材")
            return
        media_id = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "确认删除", "确定要从媒体库删除此素材吗？（不会删除原文件）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.database import get_db
                db = get_db()
                db.execute("DELETE FROM media WHERE id=?", (media_id,))
                db.commit()
                db.close()
                self._load_media()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _browse_proc_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.ts);;所有文件 (*.*)"
        )
        if files:
            self._proc_files = files
            self.proc_file_input.setText(files[0] if len(files) == 1 else f"{len(files)} 个文件")
            self.selected_files_lbl.setText(f"已选择 {len(files)} 个文件")

    def _browse_proc_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择包含视频的文件夹")
        if folder:
            video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.ts'}
            files = []
            for f in os.listdir(folder):
                if os.path.splitext(f)[1].lower() in video_exts:
                    files.append(os.path.join(folder, f))
            if files:
                self._proc_files = files
                self.proc_file_input.setText(folder)
                self.selected_files_lbl.setText(f"找到 {len(files)} 个视频文件")
            else:
                QMessageBox.information(self, "提示", "文件夹中未找到视频文件")

    def _start_processing(self):
        if not self._proc_files:
            QMessageBox.information(self, "提示", "请先选择要处理的视频文件")
            return

        # 查找FFmpeg
        from core.database import get_settings
        import shutil
        import sys

        settings = get_settings()
        ffmpeg_path = settings.get('ffmpeg_path', '') or shutil.which('ffmpeg') or ''
        if not ffmpeg_path:
            exe_dir = os.path.dirname(sys.executable)
            for name in ['ffmpeg.exe', 'ffmpeg']:
                p = os.path.join(exe_dir, name)
                if os.path.exists(p):
                    ffmpeg_path = p
                    break

        if not ffmpeg_path:
            QMessageBox.warning(
                self, "FFmpeg 未找到",
                "请将 ffmpeg.exe 放在程序所在目录，\n或在「设置 → 视频处理」中配置FFmpeg路径。\n\n"
                "下载地址：https://ffmpeg.org/download.html"
            )
            return

        action_map = {0: 'screenshot', 1: 'crop', 2: 'both'}
        action = action_map[self.action_combo.currentIndex()]

        params = {
            'start_time': self.start_time_input.text() or '00:00:00',
            'end_time': self.end_time_input.text(),
            'duration': self.duration_spin.value(),
            'grid': '3x3',
            'count': 9,
        }

        output_folder = self.output_folder_input.text() or '已裁剪'

        self.process_btn.setEnabled(False)
        self.proc_status.setText("处理中...")
        self.proc_progress.setValue(0)

        self._proc_thread = VideoProcessThread(
            self._proc_files, ffmpeg_path, output_folder, action, params
        )
        self._proc_thread.progress.connect(self._on_proc_progress)
        self._proc_thread.finished.connect(self._on_proc_finished)
        self._proc_thread.start()

    def _on_proc_progress(self, pct: int, msg: str):
        self.proc_progress.setValue(pct)
        self.proc_status.setText(msg)

    def _on_proc_finished(self, success: bool, msg: str, results: list):
        self.process_btn.setEnabled(True)
        self.proc_progress.setValue(100 if success else 0)
        self.proc_status.setText(msg)
        if success:
            QMessageBox.information(
                self, "处理完成",
                f"{msg}\n\n结果文件已保存至原视频同目录下的「{self.output_folder_input.text()}」文件夹。"
            )
        else:
            QMessageBox.warning(self, "处理失败", msg)
