"""
素材库页面
"""
import os
import json
import threading
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from core.database import DB
from core.video_processor import VideoProcessor


class MediaLibraryPage(QWidget):
    thumbnail_loaded = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self._current_folder = None
        self._init_ui()
        self.thumbnail_loaded.connect(self._on_thumbnail_loaded)
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        hdr = QHBoxLayout()
        t_v = QVBoxLayout()
        t = QLabel('素材库')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('通过文件夹管理视频、图片和音频素材')
        sub.setStyleSheet('color: #8b949e;')
        t_v.addWidget(t)
        t_v.addWidget(sub)
        hdr.addLayout(t_v, 1)

        rescan_btn = QPushButton('🔄 全部重新扫描')
        rescan_btn.clicked.connect(self._rescan_all)
        add_folder_btn = QPushButton('📁 添加文件夹')
        add_folder_btn.clicked.connect(self._add_folder)
        upload_btn = QPushButton('⬆️ 上传素材')
        upload_btn.setObjectName('primary_btn')
        upload_btn.clicked.connect(self._upload_media)

        hdr.addWidget(rescan_btn)
        hdr.addWidget(add_folder_btn)
        hdr.addWidget(upload_btn)
        layout.addLayout(hdr)

        # 主体：左侧文件夹 + 右侧内容
        main_h = QHBoxLayout()
        main_h.setSpacing(16)

        # 左侧文件夹列表
        left_w = QFrame()
        left_w.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        left_lay = QVBoxLayout(left_w)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)
        left_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_w.setFixedWidth(220)

        folder_hdr = QLabel('  素材文件夹')
        folder_hdr.setStyleSheet('color:#8b949e;font-size:12px;padding:10px;border-bottom:1px solid #30363d;')
        left_lay.addWidget(folder_hdr)

        self._folder_list = QListWidget()
        self._folder_list.setStyleSheet('QListWidget{background:transparent;border:none;}QListWidget::item{padding:10px 12px;border-bottom:1px solid #21262d;}QListWidget::item:selected{background:#1f3a5f;}QListWidget::item:hover{background:#21262d;}')
        self._folder_list.currentRowChanged.connect(self._on_folder_selected)
        left_lay.addWidget(self._folder_list)

        main_h.addWidget(left_w)

        # 右侧内容
        right_w = QWidget()
        right_lay = QVBoxLayout(right_w)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(12)

        # 搜索和过滤
        filter_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText('🔍 搜索素材...')
        self._search_input.textChanged.connect(self._filter_media)

        self._type_filter = QTabBar()
        self._type_filter.addTab('全部')
        self._type_filter.addTab('视频')
        self._type_filter.addTab('图片')
        self._type_filter.addTab('音频')
        self._type_filter.setStyleSheet('QTabBar::tab{background:transparent;color:#8b949e;padding:6px 16px;border:none;}QTabBar::tab:selected{color:#e6edf3;border-bottom:2px solid #1f6feb;}')
        self._type_filter.currentChanged.connect(self._filter_media)

        filter_row.addWidget(self._search_input, 1)
        filter_row.addWidget(self._type_filter)
        right_lay.addLayout(filter_row)

        # 全选和标签
        self._folder_tag_bar = QHBoxLayout()
        self._select_all_cb = QCheckBox('全选')
        self._folder_tag_bar.addWidget(self._select_all_cb)
        self._folder_tag_bar.addStretch()
        right_lay.addLayout(self._folder_tag_bar)

        # 媒体网格
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(10)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._scroll.setWidget(self._grid_widget)
        right_lay.addWidget(self._scroll)

        main_h.addWidget(right_w, 1)
        layout.addLayout(main_h)

    def refresh(self):
        self._refresh_folders()

    def _refresh_folders(self):
        self._folder_list.clear()
        folders = DB.fetchall('SELECT * FROM media_folders ORDER BY id')
        for folder in folders:
            count = DB.fetchone('SELECT COUNT(*) as c FROM media_files WHERE folder_id=?', (folder['id'],))['c']
            item = QListWidgetItem(f'📁 {folder["name"]}')
            item.setData(Qt.ItemDataRole.UserRole, folder)
            size_info = DB.fetchone('SELECT SUM(size) as total FROM media_files WHERE folder_id=?', (folder['id'],))
            total_mb = (size_info['total'] or 0) / (1024 * 1024)
            item.setToolTip(f'{count} 个素材 · {total_mb:.1f} MB · {folder["path"]}')
            self._folder_list.addItem(item)
        if self._folder_list.count() > 0 and self._current_folder is None:
            self._folder_list.setCurrentRow(0)

    def _on_folder_selected(self, row):
        if row < 0:
            return
        item = self._folder_list.item(row)
        if item:
            self._current_folder = item.data(Qt.ItemDataRole.UserRole)
            self._load_media_grid()

    def _load_media_grid(self):
        if not self._current_folder:
            return
        # 清除网格
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        files = DB.fetchall('SELECT * FROM media_files WHERE folder_id=? ORDER BY id DESC',
                            (self._current_folder['id'],))

        cols = 5
        for idx, f in enumerate(files):
            card = self._create_media_card(f)
            self._grid_layout.addWidget(card, idx // cols, idx % cols)

    def _create_media_card(self, f: dict) -> QWidget:
        card = QFrame()
        card.setFixedSize(170, 180)
        card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}QFrame:hover{border-color:#1f6feb;}')
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(4)

        # 缩略图区域
        thumb_area = QLabel()
        thumb_area.setFixedHeight(110)
        thumb_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_area.setStyleSheet('background:#0d1117;border-radius:6px 6px 0 0;')

        if f.get('thumbnail') and os.path.exists(f['thumbnail']):
            pix = QPixmap(f['thumbnail'])
            if not pix.isNull():
                thumb_area.setPixmap(pix.scaled(170, 110, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                Qt.TransformationMode.SmoothTransformation))
        else:
            icon_map = {'video': '🎬', 'image': '🖼️', 'audio': '🎵'}
            thumb_area.setText(icon_map.get(f.get('file_type', 'video'), '📄'))
            thumb_area.setFont(QFont('Segoe UI', 30))

            # 异步加载缩略图
            file_id = f['id']
            file_path = f['filepath']
            if f.get('file_type') == 'video' and os.path.exists(file_path):
                def load_thumb(fid, fpath, lbl):
                    try:
                        vp = VideoProcessor()
                        thumb_dir = os.path.join(os.path.dirname(fpath), '.thumbs')
                        os.makedirs(thumb_dir, exist_ok=True)
                        thumb_path = os.path.join(thumb_dir, f'{os.path.basename(fpath)}.jpg')
                        if not os.path.exists(thumb_path):
                            vp.extract_thumbnail(fpath, thumb_path)
                        if os.path.exists(thumb_path):
                            DB.execute('UPDATE media_files SET thumbnail=? WHERE id=?', (thumb_path, fid))
                            self.thumbnail_loaded.emit(fid, thumb_path)
                    except:
                        pass
                threading.Thread(target=load_thumb, args=(file_id, file_path, thumb_area), daemon=True).start()

        # 标签
        file_type = f.get('file_type', 'video')
        type_badge = QLabel({'video': '视频', 'image': '图片', 'audio': '音频'}.get(file_type, file_type))
        type_badge.setStyleSheet('color:#1f6feb;background:#1f3a5f;border-radius:4px;padding:1px 5px;font-size:10px;')

        # 文件名
        name_lbl = QLabel(f['filename'][:20] + ('...' if len(f['filename']) > 20 else ''))
        name_lbl.setStyleSheet('color:#e6edf3;font-size:11px;padding:0 6px;')
        name_lbl.setToolTip(f['filename'])

        # 信息
        size_mb = f.get('size', 0) / (1024 * 1024)
        info_parts = [f'{size_mb:.1f}MB']
        if f.get('duration'):
            m, s = divmod(int(f['duration']), 60)
            info_parts.append(f'{m}:{s:02d}')
        if f.get('width') and f.get('height'):
            info_parts.append(f'{f["width"]}x{f["height"]}')
        info_lbl = QLabel(' · '.join(info_parts))
        info_lbl.setStyleSheet('color:#8b949e;font-size:10px;padding:0 6px;')

        lay.addWidget(thumb_area)
        lay.addWidget(name_lbl)
        lay.addWidget(info_lbl)

        # 右键菜单
        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda pos, fdata=f: self._show_context_menu(pos, fdata, card))

        return card

    def _on_thumbnail_loaded(self, file_id, thumb_path):
        self._load_media_grid()

    def _show_context_menu(self, pos, file_data, widget):
        menu = QMenu(self)
        menu.addAction('▶️ 播放', lambda: self._play_file(file_data))
        menu.addAction('✂️ 裁剪视频', lambda: self._clip_video(file_data))
        menu.addAction('📸 提取截图', lambda: self._extract_screenshots(file_data))
        menu.addSeparator()
        menu.addAction('🗑️ 删除', lambda: self._delete_file(file_data))
        menu.exec(widget.mapToGlobal(pos))

    def _play_file(self, f):
        import subprocess, platform
        path = f['filepath']
        if not os.path.exists(path):
            QMessageBox.warning(self, '文件不存在', f'文件不存在:\n{path}')
            return
        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        except Exception as e:
            QMessageBox.warning(self, '错误', str(e))

    def _clip_video(self, f):
        from .task_page import ClipDialog
        dlg = ClipDialog(self, f)
        dlg.exec()

    def _extract_screenshots(self, f):
        vcfg = DB.fetchone('SELECT * FROM video_settings WHERE id=1') or {}
        vp = VideoProcessor(vcfg.get('ffmpeg_path', 'ffmpeg'))
        thumb_dir = os.path.join(os.path.dirname(f['filepath']), 'thumbnails')
        result = vp.extract_screenshots(
            f['filepath'], thumb_dir,
            grid=vcfg.get('cover_grid', '3x3'),
            size=vcfg.get('cover_size', 1080)
        )
        if result:
            QMessageBox.information(self, '截图完成', f'截图已保存到:\n{result}')
        else:
            QMessageBox.warning(self, '失败', '截图提取失败，请检查FFmpeg是否安装')

    def _delete_file(self, f):
        if QMessageBox.question(self, '确认', f'确定从素材库删除 "{f["filename"]}"？\n（不会删除实际文件）') == QMessageBox.StandardButton.Yes:
            DB.execute('DELETE FROM media_files WHERE id=?', (f['id'],))
            self._load_media_grid()

    def _add_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, '选择素材文件夹')
        if not folder_path:
            return
        folder_name = os.path.basename(folder_path)
        existing = DB.fetchone('SELECT id FROM media_folders WHERE path=?', (folder_path,))
        if existing:
            QMessageBox.information(self, '提示', '该文件夹已添加')
            return
        folder_id = DB.execute('INSERT INTO media_folders (name, path) VALUES (?,?)', (folder_name, folder_path))
        self._scan_folder(folder_id, folder_path)
        self._refresh_folders()

    def _scan_folder(self, folder_id, folder_path):
        """扫描文件夹中的媒体文件"""
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.ts'}
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        audio_exts = {'.mp3', '.aac', '.wav', '.flac', '.ogg', '.m4a'}

        vcfg = DB.fetchone('SELECT * FROM video_settings WHERE id=1') or {}
        vp = VideoProcessor(vcfg.get('ffmpeg_path', 'ffmpeg'))

        for fname in os.listdir(folder_path):
            fpath = os.path.join(folder_path, fname)
            if not os.path.isfile(fpath):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext in video_exts:
                ftype = 'video'
            elif ext in image_exts:
                ftype = 'image'
            elif ext in audio_exts:
                ftype = 'audio'
            else:
                continue

            size = os.path.getsize(fpath)
            width = height = duration = 0

            if ftype == 'video':
                try:
                    info = vp.get_video_info(fpath)
                    width = info.get('width', 0)
                    height = info.get('height', 0)
                    duration = int(info.get('duration', 0))
                except:
                    pass

            DB.execute(
                'INSERT OR IGNORE INTO media_files (folder_id, filename, filepath, file_type, size, duration, width, height) VALUES (?,?,?,?,?,?,?,?)',
                (folder_id, fname, fpath, ftype, size, duration, width, height)
            )

    def _upload_media(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, '选择素材文件', '',
            'Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.gif *.mp3 *.aac *.wav);;All Files (*)'
        )
        if not files:
            return

        if not self._current_folder:
            # 创建默认文件夹
            default_dir = os.path.expanduser('~/Documents/TGPublisher/media')
            os.makedirs(default_dir, exist_ok=True)
            folder_id = DB.execute('INSERT INTO media_folders (name, path) VALUES (?,?)', ('默认素材库', default_dir))
        else:
            folder_id = self._current_folder['id']
            default_dir = self._current_folder['path']

        import shutil
        vcfg = DB.fetchone('SELECT * FROM video_settings WHERE id=1') or {}
        vp = VideoProcessor(vcfg.get('ffmpeg_path', 'ffmpeg'))

        for src in files:
            fname = os.path.basename(src)
            dst = os.path.join(default_dir, fname)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)

            ext = os.path.splitext(fname)[1].lower()
            video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
            ftype = 'video' if ext in video_exts else 'image'
            size = os.path.getsize(dst)
            width = height = duration = 0

            if ftype == 'video':
                try:
                    info = vp.get_video_info(dst)
                    width = info.get('width', 0)
                    height = info.get('height', 0)
                    duration = int(info.get('duration', 0))
                except:
                    pass

            DB.execute(
                'INSERT OR IGNORE INTO media_files (folder_id, filename, filepath, file_type, size, duration, width, height) VALUES (?,?,?,?,?,?,?,?)',
                (folder_id, fname, dst, ftype, size, duration, width, height)
            )

        self._refresh_folders()
        self._load_media_grid()

    def _filter_media(self):
        self._load_media_grid()

    def _rescan_all(self):
        folders = DB.fetchall('SELECT * FROM media_folders')
        for folder in folders:
            if os.path.exists(folder['path']):
                self._scan_folder(folder['id'], folder['path'])
        self._refresh_folders()
        self._load_media_grid()
        QMessageBox.information(self, '完成', '素材库已重新扫描')
