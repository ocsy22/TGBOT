"""
设置页面 + AI文案页面 + 帮助页面
"""
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QComboBox, QSpinBox, QFormLayout,
    QMessageBox, QTabWidget, QTextEdit, QCheckBox, QGroupBox,
    QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class AIGenerateThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, config, prompt):
        super().__init__()
        self.config = config
        self.prompt = prompt

    def run(self):
        try:
            from core.ai_generator import AIGenerator
            import asyncio
            gen = AIGenerator(self.config)
            result = asyncio.run(gen.generate_text(self.prompt))
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AIPage(QWidget):
    """AI文案生成页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("🤖 AI文案生成")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # AI配置
        config_card = QFrame()
        config_card.setObjectName("card")
        config_layout = QFormLayout(config_card)
        config_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        config_layout.setSpacing(10)

        cfg_title = QLabel("⚙️ AI接口配置")
        cfg_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #58a6ff;")
        config_layout.addRow("", cfg_title)

        self.provider_combo = QComboBox()
        from core.ai_generator import AI_PRESETS
        self.provider_combo.addItems(list(AI_PRESETS.keys()))
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        config_layout.addRow("AI服务商:", self.provider_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        config_layout.addRow("API Key:", self.api_key_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("模型名称（自动填充）")
        config_layout.addRow("模型:", self.model_input)

        self.provider_note = QLabel("")
        self.provider_note.setStyleSheet("color: #8b949e; font-size: 11px;")
        config_layout.addRow("说明:", self.provider_note)

        layout.addWidget(config_card)

        # 文案生成
        gen_card = QFrame()
        gen_card.setObjectName("card")
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setSpacing(10)

        gen_title = QLabel("✍️ 生成文案")
        gen_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #e6edf3;")
        gen_layout.addWidget(gen_title)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "输入生成提示词，例如：\n"
            "为成人内容频道写一条吸引眼球的推广文案，风格活泼，包含emoji，100字以内"
        )
        self.prompt_input.setFixedHeight(100)
        gen_layout.addWidget(self.prompt_input)

        # 快速提示词
        quick_row = QHBoxLayout()
        quick_row.addWidget(QLabel("快速模板:"))
        templates = [
            ("🔥 热门推广", "为成人内容频道写一条吸引眼球的推广文案，活泼风格，含emoji，100字以内"),
            ("📺 视频介绍", "为一个视频写简短吸引人的介绍文案，包含互动引导，80字以内"),
            ("📢 频道推广", "写一条Telegram频道推广文案，突出频道特色和价值，含emoji，120字以内"),
        ]
        for tpl_name, tpl_text in templates:
            btn = QPushButton(tpl_name)
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda checked, t=tpl_text: self.prompt_input.setPlainText(t))
            quick_row.addWidget(btn)
        quick_row.addStretch()
        gen_layout.addLayout(quick_row)

        btn_row = QHBoxLayout()
        self.gen_btn = QPushButton("🚀 生成文案")
        self.gen_btn.setObjectName("primaryBtn")
        self.gen_btn.setFixedHeight(38)
        self.gen_btn.clicked.connect(self._generate)
        btn_row.addWidget(self.gen_btn)
        btn_row.addStretch()
        gen_layout.addLayout(btn_row)

        self.result_output = QTextEdit()
        self.result_output.setPlaceholderText("AI生成的文案将显示在这里...")
        self.result_output.setMinimumHeight(150)
        gen_layout.addWidget(self.result_output)

        save_btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 保存到文案库")
        save_btn.clicked.connect(self._save_caption)
        copy_btn = QPushButton("📋 复制")
        copy_btn.clicked.connect(self._copy_result)
        save_btn_row.addWidget(save_btn)
        save_btn_row.addWidget(copy_btn)
        save_btn_row.addStretch()
        gen_layout.addLayout(save_btn_row)

        layout.addWidget(gen_card)
        layout.addStretch()

        self._on_provider_changed(self.provider_combo.currentText())

    def _on_provider_changed(self, provider: str):
        try:
            from core.ai_generator import AI_PRESETS
            preset = AI_PRESETS.get(provider, {})
            self.model_input.setText(preset.get('text_model', ''))
            self.provider_note.setText(preset.get('note', ''))
        except Exception:
            pass

    def _generate(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请先输入API Key")
            return

        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "提示", "请输入提示词")
            return

        try:
            from core.ai_generator import AI_PRESETS
            provider = self.provider_combo.currentText()
            preset = AI_PRESETS.get(provider, {})
            config = {
                'api_url': preset.get('api_url', ''),
                'api_key': api_key,
                'text_model': self.model_input.text() or preset.get('text_model', ''),
            }
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            return

        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("生成中...")
        self.result_output.setPlainText("正在生成，请稍候...")

        self._gen_thread = AIGenerateThread(config, prompt)
        self._gen_thread.finished.connect(self._on_gen_finished)
        self._gen_thread.error.connect(self._on_gen_error)
        self._gen_thread.start()

    def _on_gen_finished(self, text: str):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("🚀 生成文案")
        self.result_output.setPlainText(text)

    def _on_gen_error(self, err: str):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("🚀 生成文案")
        self.result_output.setPlainText(f"生成失败: {err}")
        QMessageBox.warning(self, "生成失败", f"AI接口返回错误：\n{err}")

    def _save_caption(self):
        text = self.result_output.toPlainText().strip()
        if not text:
            return
        try:
            from core.database import get_db
            db = get_db()
            db.execute("INSERT INTO captions (content, category) VALUES (?, '自动生成')", (text,))
            db.commit()
            db.close()
            QMessageBox.information(self, "成功", "文案已保存到文案库！")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def _copy_result(self):
        from PyQt6.QtWidgets import QApplication
        text = self.result_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "已复制", "文案已复制到剪贴板")


class SettingsPage(QWidget):
    """系统设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        title = QLabel("⚙️ 系统设置")
        title.setObjectName("titleLabel")
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # FFmpeg设置
        ffmpeg_card = QFrame()
        ffmpeg_card.setObjectName("card")
        ffmpeg_layout = QVBoxLayout(ffmpeg_card)
        ffmpeg_layout.setSpacing(10)

        ffmpeg_title = QLabel("🎬 FFmpeg 配置")
        ffmpeg_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #e6edf3;")
        ffmpeg_layout.addWidget(ffmpeg_title)

        ffmpeg_note = QLabel(
            "📌 FFmpeg 必须配置才能使用视频裁剪和截图功能。\n"
            "   将 ffmpeg.exe 放在程序同目录（推荐），或手动指定路径。"
        )
        ffmpeg_note.setStyleSheet("""
            color: #8b949e; font-size: 12px;
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px;
        """)
        ffmpeg_note.setWordWrap(True)
        ffmpeg_layout.addWidget(ffmpeg_note)

        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("FFmpeg路径:"))
        self.ffmpeg_path_input = QLineEdit()
        self.ffmpeg_path_input.setPlaceholderText("留空=自动检测（程序目录或系统PATH）")
        path_row.addWidget(self.ffmpeg_path_input)
        browse_btn = QPushButton("📂 浏览")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_ffmpeg)
        path_row.addWidget(browse_btn)
        test_btn = QPushButton("🔍 测试")
        test_btn.setFixedWidth(70)
        test_btn.clicked.connect(self._test_ffmpeg)
        path_row.addWidget(test_btn)
        ffmpeg_layout.addLayout(path_row)

        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("输出文件夹名:"))
        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("已裁剪")
        self.output_folder_input.setFixedWidth(150)
        out_row.addWidget(self.output_folder_input)
        out_note = QLabel("（在原视频目录下创建此文件夹存放处理结果）")
        out_note.setStyleSheet("color: #8b949e; font-size: 11px;")
        out_row.addWidget(out_note)
        out_row.addStretch()
        ffmpeg_layout.addLayout(out_row)

        layout.addWidget(ffmpeg_card)

        # 发布设置
        pub_card = QFrame()
        pub_card.setObjectName("card")
        pub_layout = QFormLayout(pub_card)
        pub_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        pub_layout.setSpacing(10)

        pub_title = QLabel("📤 发布设置")
        pub_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #e6edf3;")
        pub_layout.addRow("", pub_title)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(3)
        self.interval_spin.setSuffix(" 秒")
        pub_layout.addRow("频道间发送间隔:", self.interval_spin)

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setValue(3)
        pub_layout.addRow("失败重试次数:", self.retry_spin)

        layout.addWidget(pub_card)

        # 代理设置
        proxy_card = QFrame()
        proxy_card.setObjectName("card")
        proxy_layout = QFormLayout(proxy_card)
        proxy_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        proxy_layout.setSpacing(10)

        proxy_title = QLabel("🌐 代理设置（全局）")
        proxy_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #e6edf3;")
        proxy_layout.addRow("", proxy_title)

        self.http_proxy_input = QLineEdit()
        self.http_proxy_input.setPlaceholderText("http://127.0.0.1:7890")
        proxy_layout.addRow("HTTP代理:", self.http_proxy_input)

        self.socks_proxy_input = QLineEdit()
        self.socks_proxy_input.setPlaceholderText("socks5://127.0.0.1:1080")
        proxy_layout.addRow("SOCKS5代理:", self.socks_proxy_input)

        layout.addWidget(proxy_card)
        layout.addStretch()

        # 保存按钮
        save_btn = QPushButton("💾 保存所有设置")
        save_btn.setObjectName("primaryBtn")
        save_btn.setFixedHeight(40)
        save_btn.setFixedWidth(180)
        save_btn.clicked.connect(self._save_settings)
        main_layout.addWidget(save_btn)

    def _browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择FFmpeg可执行文件", "",
            "可执行文件 (ffmpeg.exe ffmpeg);;所有文件 (*.*)"
        )
        if path:
            self.ffmpeg_path_input.setText(path)

    def _test_ffmpeg(self):
        import subprocess
        path = self.ffmpeg_path_input.text().strip() or 'ffmpeg'
        try:
            result = subprocess.run(
                [path, '-version'], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                QMessageBox.information(self, "FFmpeg 正常", f"检测成功！\n{version_line}")
            else:
                QMessageBox.warning(self, "FFmpeg 错误", "FFmpeg 返回错误，请检查路径")
        except FileNotFoundError:
            QMessageBox.warning(
                self, "FFmpeg 未找到",
                "未找到 FFmpeg！\n\n请将 ffmpeg.exe 放在程序目录，\n"
                "或手动指定路径。\n\n下载：https://ffmpeg.org/download.html"
            )
        except Exception as e:
            QMessageBox.critical(self, "测试失败", str(e))

    def _load_settings(self):
        try:
            from core.database import get_settings
            s = get_settings()
            self.ffmpeg_path_input.setText(s.get('ffmpeg_path', ''))
            self.output_folder_input.setText(s.get('output_folder_name', '已裁剪'))
            self.interval_spin.setValue(int(s.get('send_interval', '3')))
            self.retry_spin.setValue(int(s.get('max_retry', '3')))
            self.http_proxy_input.setText(s.get('proxy_http', ''))
            self.socks_proxy_input.setText(s.get('proxy_socks5', ''))
        except Exception:
            pass

    def _save_settings(self):
        try:
            from core.database import set_setting
            set_setting('ffmpeg_path', self.ffmpeg_path_input.text().strip())
            set_setting('output_folder_name', self.output_folder_input.text().strip() or '已裁剪')
            set_setting('send_interval', str(self.interval_spin.value()))
            set_setting('max_retry', str(self.retry_spin.value()))
            set_setting('proxy_http', self.http_proxy_input.text().strip())
            set_setting('proxy_socks5', self.socks_proxy_input.text().strip())
            QMessageBox.information(self, "成功", "✅ 设置已保存！")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))


class HelpPage(QWidget):
    """操作指南页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("📖 使用指南")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)
        scroll.setWidget(content)

        sections = [
            ("🚀 快速开始", """
1. 添加发布账号（「账号与频道」→「发布账号」→「添加Bot账号」）
   - Bot API：从 @BotFather 获取 Token，最大支持50MB文件
   - MTProto真实账号：需要手机号 + API ID/Hash，支持2GB超大文件

2. 添加目标频道（「账号与频道」→「发布频道」→「添加频道」）
   - 公开频道：@频道用户名
   - 私有频道：-100XXXXXXXXX（通过 @userinfobot 获取）

3. 导入媒体素材（「媒体库」→「导入视频/图片」）

4. 创建发布任务（「任务中心」→「创建任务」）
   - 选择账号、频道、素材、文案
   - 设置调度：立即/定时/循环

5. 点击「立即发布」开始执行
"""),
            ("🎬 视频处理 (FFmpeg)", """
FFmpeg 配置：
• 将 ffmpeg.exe 放在 TGAutoPublisher.exe 同一文件夹（推荐）
• 或在「系统设置」→「FFmpeg路径」中手动指定
• 下载FFmpeg：https://ffmpeg.org/download.html → Windows builds

视频处理功能：
• ✂️ 裁剪：截取视频片段，设置起止时间
• 📸 截图：均匀提取9张截图（3×3网格，生成封面图）
• 输出位置：原视频同目录下自动创建「已裁剪」文件夹

使用步骤：
1. 进入「媒体库」→「视频处理」标签
2. 选择视频文件或文件夹
3. 选择处理方式（截图/裁剪/同时执行）
4. 点击「开始处理」
"""),
            ("🤖 AI文案生成", """
支持的AI服务商（含无内容限制）：
• Grok (xAI) - 支持成人内容，免费额度充足
• Together AI - 开源模型，无内容审查
• Mistral - 欧洲模型，政策宽松
• DeepSeek - 中文优化，性价比高
• Groq - 极速推理
• Gemini - Google，免费额度
• OpenAI - GPT系列
• 小悟SaaS - 国内无限制API
• 等共12家

使用步骤：
1. 进入「AI文案」页面
2. 选择服务商，填入API Key
3. 输入生成提示词
4. 点击「生成文案」
5. 可保存到文案库供复用
"""),
            ("📅 定时发布", """
调度类型：
• 立即发布：创建任务后立即开始
• 指定时间：在设定时间自动触发
• 定时循环：每隔N分钟重复发布

多频道发布模式：
• 顺序发布：按频道列表顺序逐一发布
• 随机发布：随机选择频道发布
• 全部发布：同时向所有频道发布

频道间隔：可设置每个频道之间的发送间隔（防刷屏）
"""),
            ("📱 MTProto真实账号", """
MTProto账号支持发送最大2GB的文件，突破Bot API的50MB限制。

获取 API ID / API Hash：
1. 访问 https://my.telegram.org
2. 用手机号登录
3. 点击「API development tools」
4. 创建一个App（填写任意名称）
5. 复制 App api_id 和 App api_hash

注意事项：
• 首次使用需要手机验证码确认
• Session字符串会自动保存，下次无需重复验证
• 建议使用专用的小号账号，不要用主账号
"""),
        ]

        for section_title, section_content in sections:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(8)

            sec_title = QLabel(section_title)
            sec_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #58a6ff;")
            card_layout.addWidget(sec_title)

            sec_content = QLabel(section_content.strip())
            sec_content.setStyleSheet("""
                font-size: 12px;
                color: #c9d1d9;
                line-height: 1.6;
            """)
            sec_content.setWordWrap(True)
            sec_content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            card_layout.addWidget(sec_content)

            content_layout.addWidget(card)

        content_layout.addStretch()
        layout.addWidget(scroll)
