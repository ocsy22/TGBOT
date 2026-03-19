"""
设置页面
"""
import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from core.database import DB
from core.ai_generator import AI_PRESETS, AIGenerator


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(0)

        # 标题
        t = QLabel('设置')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        layout.addWidget(t)
        layout.addSpacing(20)

        # 选项卡
        tabs = QTabWidget()
        tabs.setStyleSheet('QTabWidget::pane{border:none;}')

        tabs.addTab(self._build_ai_tab(), '🤖 AI接口管理')
        tabs.addTab(self._build_video_tab(), '🎬 视频处理')
        tabs.addTab(self._build_tg_tab(), '🌐 Telegram网络')

        layout.addWidget(tabs)

    def _build_ai_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(16)
        lay.setContentsMargins(0, 16, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setSpacing(16)

        # 快速预设
        preset_card = QFrame()
        preset_card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        preset_lay = QVBoxLayout(preset_card)
        preset_hdr = QLabel('🚀  AI接口管理')
        preset_hdr.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        preset_lay.addWidget(preset_hdr)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel('快速预设: '))
        for name in ['小悟SaaS', 'OpenAI', 'Grok (xAI)', 'DeepSeek', 'Together AI', 'Groq', 'Gemini', 'Mistral']:
            btn = QPushButton(f'⚡ {name}')
            btn.setStyleSheet('QPushButton{background:#21262d;border:1px solid #30363d;border-radius:4px;padding:4px 10px;font-size:11px;}QPushButton:hover{background:#30363d;}')
            btn.clicked.connect(lambda _, n=name: self._apply_preset(n))
            preset_row.addWidget(btn)
        preset_row.addStretch()
        preset_lay.addLayout(preset_row)

        # API地址和Key
        form_grid = QGridLayout()
        form_grid.setSpacing(12)
        form_grid.addWidget(QLabel('API 地址:'), 0, 0)
        self._api_url = QLineEdit()
        self._api_url.setPlaceholderText('https://api.x.ai/v1')
        form_grid.addWidget(self._api_url, 0, 1)

        form_grid.addWidget(QLabel('API Key:'), 0, 2)
        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setPlaceholderText('sk-...')
        form_grid.addWidget(self._api_key, 0, 3)

        form_grid.addWidget(QLabel('文本模型:'), 1, 0)
        self._text_model = QLineEdit()
        self._text_model.setPlaceholderText('grok-3-mini')
        form_grid.addWidget(self._text_model, 1, 1)

        form_grid.addWidget(QLabel('视觉模型:'), 1, 2)
        self._vision_model = QLineEdit()
        self._vision_model.setPlaceholderText('grok-2-vision-1212')
        form_grid.addWidget(self._vision_model, 1, 3)

        form_grid.addWidget(QLabel('最大 Token:'), 2, 0)
        self._max_tokens = QSpinBox()
        self._max_tokens.setRange(100, 8000)
        self._max_tokens.setValue(1024)
        form_grid.addWidget(self._max_tokens, 2, 1)

        form_grid.addWidget(QLabel('HTTP 代理:'), 2, 2)
        self._http_proxy = QLineEdit()
        self._http_proxy.setPlaceholderText('留空则直连（如 http://127.0.0.1:7890）')
        form_grid.addWidget(self._http_proxy, 2, 3)

        preset_lay.addLayout(form_grid)

        # AI生成字数控制
        gen_ctrl_lbl = QLabel('AI 生成字数控制')
        gen_ctrl_lbl.setStyleSheet('font-weight:bold;margin-top:8px;')
        preset_lay.addWidget(gen_ctrl_lbl)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(12)

        def add_range(lay, label, attr_min, attr_max, default_min, default_max):
            lay.addWidget(QLabel(label))
            w_min = QSpinBox()
            w_min.setRange(1, 500)
            w_min.setValue(default_min)
            setattr(self, attr_min, w_min)
            lay.addWidget(w_min)
            lay.addWidget(QLabel('—'))
            w_max = QSpinBox()
            w_max.setRange(1, 500)
            w_max.setValue(default_max)
            setattr(self, attr_max, w_max)
            lay.addWidget(w_max)
            lay.addWidget(QLabel('字'))
            lay.addSpacing(16)

        add_range(ctrl_row, '标题字数', '_title_min', '_title_max', 15, 25)
        add_range(ctrl_row, '文案内容字数', '_content_min', '_content_max', 30, 60)
        add_range(ctrl_row, '封面标题字数', '_cover_min', '_cover_max', 10, 20)
        ctrl_row.addStretch()
        preset_lay.addLayout(ctrl_row)

        # 按钮
        btn_row = QHBoxLayout()
        save_btn = QPushButton('💾 保存')
        save_btn.setObjectName('primary_btn')
        save_btn.clicked.connect(self._save_ai_settings)
        test_btn = QPushButton('🔌 测试连接')
        test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(test_btn)
        btn_row.addStretch()
        preset_lay.addLayout(btn_row)

        content_lay.addWidget(preset_card)
        content_lay.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)
        return w

    def _build_video_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(16)
        lay.setContentsMargins(0, 16, 0, 0)

        card = QFrame()
        card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        card_lay = QVBoxLayout(card)

        lbl = QLabel('🎬  视频处理')
        lbl.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        card_lay.addWidget(lbl)

        form = QGridLayout()
        form.setSpacing(12)

        form.addWidget(QLabel('FFmpeg 路径:'), 0, 0)
        ffmpeg_row = QHBoxLayout()
        self._ffmpeg_path = QLineEdit()
        self._ffmpeg_path.setPlaceholderText('ffmpeg（已在系统PATH中）或完整路径')
        ffmpeg_row.addWidget(self._ffmpeg_path)
        ffmpeg_browse = QPushButton('浏览...')
        ffmpeg_browse.clicked.connect(self._browse_ffmpeg)
        ffmpeg_row.addWidget(ffmpeg_browse)
        check_btn = QPushButton('检查')
        check_btn.clicked.connect(self._check_ffmpeg)
        ffmpeg_row.addWidget(check_btn)
        form.addLayout(ffmpeg_row, 0, 1, 1, 3)

        ffmpeg_hint = QLabel('📌 FFmpeg请放在程序同目录下（如 ffmpeg.exe），或填写完整路径，或将ffmpeg加入系统PATH')
        ffmpeg_hint.setStyleSheet('color:#d29922;font-size:11px;')
        ffmpeg_hint.setWordWrap(True)
        form.addWidget(ffmpeg_hint, 1, 0, 1, 4)

        form.addWidget(QLabel('默认分辨率:'), 2, 0)
        self._def_res = QComboBox()
        for r in ['1920x1080 (1080p)', '1280x720 (720p)', '854x480 (480p)', '1080x1920 (竖屏1080p)', '720x1280 (竖屏720p)']:
            self._def_res.addItem(r)
        form.addWidget(self._def_res, 2, 1)

        form.addWidget(QLabel('默认码率:'), 2, 2)
        self._def_bitrate = QComboBox()
        for br in ['4 Mbps', '2 Mbps', '6 Mbps', '8 Mbps', '1 Mbps']:
            self._def_bitrate.addItem(br)
        form.addWidget(self._def_bitrate, 2, 3)

        form.addWidget(QLabel('编码器:'), 3, 0)
        self._encoder = QComboBox()
        for enc in ['H.264 (推荐)', 'H.265/HEVC', 'VP9', '复制原始编码']:
            self._encoder.addItem(enc)
        form.addWidget(self._encoder, 3, 1)

        form.addWidget(QLabel('封面网格:'), 3, 2)
        self._cover_grid = QComboBox()
        for g in ['3x3 (9格)', '2x2 (4格)', '4x4 (16格)', '2x3 (6格)', '3x4 (12格)']:
            self._cover_grid.addItem(g)
        form.addWidget(self._cover_grid, 3, 3)

        form.addWidget(QLabel('封面尺寸:'), 4, 0)
        self._cover_size = QSpinBox()
        self._cover_size.setRange(360, 4096)
        self._cover_size.setValue(1080)
        self._cover_size.setSuffix(' px')
        form.addWidget(self._cover_size, 4, 1)

        card_lay.addLayout(form)

        save_btn = QPushButton('💾 保存')
        save_btn.setObjectName('primary_btn')
        save_btn.clicked.connect(self._save_video_settings)
        card_lay.addWidget(save_btn)

        lay.addWidget(card)
        lay.addStretch()
        return w

    def _build_tg_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(16)
        lay.setContentsMargins(0, 16, 0, 0)

        # Telegram API 多组配置说明
        api_card = QFrame()
        api_card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        api_lay = QVBoxLayout(api_card)
        lbl = QLabel('🌐  Telegram 网络 & 大文件')
        lbl.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        api_lay.addWidget(lbl)

        note = QLabel('大文件（>50MB）自动通过 MTProto 协议以 Bot 身份发送（最大 2GB）。国内服务器需配置代理才能使用 MTProto。')
        note.setStyleSheet('color:#8b949e;font-size:12px;')
        note.setWordWrap(True)
        api_lay.addWidget(note)

        form = QGridLayout()
        form.setSpacing(12)

        form.addWidget(QLabel('MTProto 代理:'), 0, 0)
        self._mtproto_proxy = QLineEdit()
        self._mtproto_proxy.setPlaceholderText('socks5://127.0.0.1:1080')
        mtproto_row = QHBoxLayout()
        mtproto_row.addWidget(self._mtproto_proxy)
        test_proxy_btn = QPushButton('检测代理')
        test_proxy_btn.clicked.connect(self._test_proxy)
        mtproto_row.addWidget(test_proxy_btn)
        form.addLayout(mtproto_row, 0, 1)

        form.addWidget(QLabel(''), 1, 0)
        proxy_note = QLabel('格式 socks5://IP:端口 或 http://IP:端口，用于 Bot 大文件 MTProto 上传')
        proxy_note.setStyleSheet('color:#8b949e;font-size:11px;')
        form.addWidget(proxy_note, 1, 1)

        form.addWidget(QLabel('Local Bot API Server (可选):'), 2, 0)
        self._local_bot_api = QLineEdit()
        self._local_bot_api.setPlaceholderText('http://localhost:8081')
        form.addWidget(self._local_bot_api, 2, 1)

        local_api_note = QLabel('高级选项：如已自建 Local Bot API Server 可填入地址，留空则使用 MTProto 自动切换')
        local_api_note.setStyleSheet('color:#8b949e;font-size:11px;')
        local_api_note.setWordWrap(True)
        form.addWidget(local_api_note, 3, 0, 1, 2)

        api_lay.addLayout(form)

        save_btn = QPushButton('💾 保存')
        save_btn.setObjectName('primary_btn')
        save_btn.clicked.connect(self._save_tg_settings)
        api_lay.addWidget(save_btn)

        lay.addWidget(api_card)
        lay.addStretch()
        return w

    def _apply_preset(self, name):
        preset = AI_PRESETS.get(name, {})
        if preset.get('api_url'):
            self._api_url.setText(preset['api_url'])
        if preset.get('text_model'):
            self._text_model.setText(preset['text_model'])
        if preset.get('vision_model'):
            self._vision_model.setText(preset['vision_model'])

    def _load_settings(self):
        ai = DB.fetchone('SELECT * FROM ai_settings WHERE id=1')
        if ai:
            self._api_url.setText(ai.get('api_url', ''))
            self._api_key.setText(ai.get('api_key', ''))
            self._text_model.setText(ai.get('text_model', ''))
            self._vision_model.setText(ai.get('vision_model', ''))
            self._max_tokens.setValue(ai.get('max_tokens', 1024))
            self._http_proxy.setText(ai.get('http_proxy', ''))
            self._title_min.setValue(ai.get('title_min', 15))
            self._title_max.setValue(ai.get('title_max', 25))
            self._content_min.setValue(ai.get('content_min', 30))
            self._content_max.setValue(ai.get('content_max', 60))
            self._cover_min.setValue(ai.get('cover_title_min', 10))
            self._cover_max.setValue(ai.get('cover_title_max', 20))

        vcfg = DB.fetchone('SELECT * FROM video_settings WHERE id=1')
        if vcfg:
            self._ffmpeg_path.setText(vcfg.get('ffmpeg_path', 'ffmpeg'))

        pub = DB.fetchone('SELECT * FROM publish_settings WHERE id=1')
        if pub:
            self._mtproto_proxy.setText(pub.get('mtproto_proxy', ''))
            self._local_bot_api.setText(pub.get('local_bot_api', ''))

    def _save_ai_settings(self):
        DB.execute('''UPDATE ai_settings SET 
            api_url=?, api_key=?, text_model=?, vision_model=?, max_tokens=?,
            http_proxy=?, title_min=?, title_max=?, content_min=?, content_max=?,
            cover_title_min=?, cover_title_max=? WHERE id=1''',
            (self._api_url.text().strip(), self._api_key.text().strip(),
             self._text_model.text().strip(), self._vision_model.text().strip(),
             self._max_tokens.value(), self._http_proxy.text().strip(),
             self._title_min.value(), self._title_max.value(),
             self._content_min.value(), self._content_max.value(),
             self._cover_min.value(), self._cover_max.value()))
        QMessageBox.information(self, '已保存', 'AI接口设置已保存')

    def _test_connection(self):
        ai_cfg = {
            'api_url': self._api_url.text().strip(),
            'api_key': self._api_key.text().strip(),
            'text_model': self._text_model.text().strip(),
            'vision_model': self._vision_model.text().strip(),
            'max_tokens': self._max_tokens.value(),
            'http_proxy': self._http_proxy.text().strip(),
        }
        ai = AIGenerator(ai_cfg)
        btn = self.sender()
        if btn:
            btn.setText('测试中...')
            btn.setEnabled(False)

        def do_test():
            ok, msg = ai.test_connection()
            btn.setText('🔌 测试连接')
            btn.setEnabled(True)
            if ok:
                QMessageBox.information(self, '连接成功', f'✅ {msg}')
            else:
                QMessageBox.warning(self, '连接失败', f'❌ {msg}')

        import threading
        threading.Thread(target=do_test, daemon=True).start()

    def _save_video_settings(self):
        enc_map = {'H.264 (推荐)': 'libx264', 'H.265/HEVC': 'libx265', 'VP9': 'libvpx-vp9', '复制原始编码': 'copy'}
        res_map = {'1920x1080 (1080p)': '1920x1080', '1280x720 (720p)': '1280x720',
                   '854x480 (480p)': '854x480', '1080x1920 (竖屏1080p)': '1080x1920', '720x1280 (竖屏720p)': '720x1280'}
        bitrate_map = {'4 Mbps': '4M', '2 Mbps': '2M', '6 Mbps': '6M', '8 Mbps': '8M', '1 Mbps': '1M'}
        grid_map = {'3x3 (9格)': '3x3', '2x2 (4格)': '2x2', '4x4 (16格)': '4x4', '2x3 (6格)': '2x3', '3x4 (12格)': '3x4'}

        DB.execute('''UPDATE video_settings SET ffmpeg_path=?, default_resolution=?,
            default_bitrate=?, encoder=?, cover_grid=?, cover_size=? WHERE id=1''',
            (self._ffmpeg_path.text().strip(),
             res_map.get(self._def_res.currentText(), '1920x1080'),
             bitrate_map.get(self._def_bitrate.currentText(), '4M'),
             enc_map.get(self._encoder.currentText(), 'libx264'),
             grid_map.get(self._cover_grid.currentText(), '3x3'),
             self._cover_size.value()))
        QMessageBox.information(self, '已保存', '视频处理设置已保存')

    def _save_tg_settings(self):
        DB.execute('UPDATE publish_settings SET mtproto_proxy=?, local_bot_api=? WHERE id=1',
                   (self._mtproto_proxy.text().strip(), self._local_bot_api.text().strip()))
        QMessageBox.information(self, '已保存', 'Telegram网络设置已保存')

    def _browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择FFmpeg', '', 'FFmpeg (ffmpeg ffmpeg.exe);;All Files (*)')
        if path:
            self._ffmpeg_path.setText(path)

    def _check_ffmpeg(self):
        from core.video_processor import VideoProcessor
        vp = VideoProcessor(self._ffmpeg_path.text().strip() or 'ffmpeg')
        if vp.check_ffmpeg():
            QMessageBox.information(self, 'FFmpeg', '✅ FFmpeg 可用')
        else:
            QMessageBox.warning(self, 'FFmpeg', '❌ FFmpeg 不可用\n\n请下载ffmpeg.exe并放在程序同目录，或填写完整路径。\n下载地址: https://ffmpeg.org/download.html')

    def _test_proxy(self):
        proxy = self._mtproto_proxy.text().strip()
        if not proxy:
            QMessageBox.warning(self, '提示', '请先填写代理地址')
            return
        QMessageBox.information(self, '代理检测', f'代理: {proxy}\n\n请确保代理地址格式正确: socks5://host:port')
