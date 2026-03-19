"""
频道和账号管理页面
"""
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QMessageBox, QTabWidget, QSizePolicy, QTextEdit, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class AccountDialog(QDialog):
    """账号添加/编辑对话框"""

    def __init__(self, account=None, parent=None):
        super().__init__(parent)
        self.account = account
        self.setWindowTitle("添加账号" if not account else "编辑账号")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()
        if account:
            self._load_account(account)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("📱 账号信息")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # 账号类型
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("账号类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Bot API (普通机器人)", "MTProto (真实账号，支持2GB文件)"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self.type_combo)
        layout.addLayout(type_row)

        # 账号名称
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("账号名称:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("给账号起个名字，如：主账号Bot")
        name_row.addWidget(self.name_input)
        layout.addLayout(name_row)

        # Bot配置区域
        self.bot_group = QFrame()
        self.bot_group.setObjectName("card")
        bot_layout = QFormLayout(self.bot_group)
        bot_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        bot_layout.setSpacing(10)

        bot_title = QLabel("🤖 Bot Token配置")
        bot_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #58a6ff;")
        bot_layout.addRow("", bot_title)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("从 @BotFather 获取的Token，如：123456789:AABcd...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        bot_layout.addRow("Bot Token:", self.token_input)

        show_token_btn = QPushButton("👁 显示/隐藏")
        show_token_btn.setFixedWidth(100)
        show_token_btn.clicked.connect(
            lambda: self.token_input.setEchoMode(
                QLineEdit.EchoMode.Normal if self.token_input.echoMode() == QLineEdit.EchoMode.Password
                else QLineEdit.EchoMode.Password
            )
        )
        bot_layout.addRow("", show_token_btn)
        layout.addWidget(self.bot_group)

        # MTProto配置区域
        self.mtproto_group = QFrame()
        self.mtproto_group.setObjectName("card")
        mt_layout = QFormLayout(self.mtproto_group)
        mt_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        mt_layout.setSpacing(10)

        mt_title = QLabel("📱 MTProto配置（可发送2GB超大文件）")
        mt_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #3fb950;")
        mt_layout.addRow("", mt_title)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+86 13800138000")
        mt_layout.addRow("手机号:", self.phone_input)

        self.api_id_input = QLineEdit()
        self.api_id_input.setPlaceholderText("从 my.telegram.org 获取")
        mt_layout.addRow("API ID:", self.api_id_input)

        self.api_hash_input = QLineEdit()
        self.api_hash_input.setPlaceholderText("从 my.telegram.org 获取")
        self.api_hash_input.setEchoMode(QLineEdit.EchoMode.Password)
        mt_layout.addRow("API Hash:", self.api_hash_input)

        self.session_input = QTextEdit()
        self.session_input.setPlaceholderText("Session字符串（可选，已登录后自动填充）")
        self.session_input.setMaximumHeight(80)
        mt_layout.addRow("Session:", self.session_input)

        api_note = QLabel(
            "💡 获取API ID/Hash: 访问 https://my.telegram.org\n"
            "   登录 → App configuration → 创建应用"
        )
        api_note.setStyleSheet("color: #8b949e; font-size: 11px;")
        api_note.setWordWrap(True)
        mt_layout.addRow("", api_note)
        layout.addWidget(self.mtproto_group)

        # 代理设置
        proxy_group = QFrame()
        proxy_group.setObjectName("card")
        proxy_layout = QFormLayout(proxy_group)
        proxy_layout.setSpacing(8)

        proxy_title = QLabel("🌐 代理设置（可选）")
        proxy_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #8b949e;")
        proxy_layout.addRow("", proxy_title)

        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("socks5://127.0.0.1:1080 或 http://127.0.0.1:7890")
        proxy_layout.addRow("代理地址:", self.proxy_input)
        layout.addWidget(proxy_group)

        # 备注
        note_row = QHBoxLayout()
        note_row.addWidget(QLabel("备注:"))
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("可选备注信息")
        note_row.addWidget(self.note_input)
        layout.addLayout(note_row)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("保存账号")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setFixedWidth(120)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        self._on_type_changed(0)

    def _on_type_changed(self, idx):
        is_bot = (idx == 0)
        self.bot_group.setVisible(is_bot)
        self.mtproto_group.setVisible(not is_bot)

    def _load_account(self, account):
        self.name_input.setText(account.get('name', ''))
        acc_type = account.get('type', 'bot')
        self.type_combo.setCurrentIndex(0 if acc_type == 'bot' else 1)
        self.token_input.setText(account.get('bot_token', ''))
        self.phone_input.setText(account.get('phone', ''))
        self.api_id_input.setText(account.get('api_id', ''))
        self.api_hash_input.setText(account.get('api_hash', ''))
        self.session_input.setPlainText(account.get('session_string', ''))
        self.proxy_input.setText(account.get('proxy', ''))
        self.note_input.setText(account.get('note', ''))
        self._on_type_changed(0 if acc_type == 'bot' else 1)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "验证失败", "请填写账号名称")
            return

        is_bot = (self.type_combo.currentIndex() == 0)

        if is_bot and not self.token_input.text().strip():
            QMessageBox.warning(self, "验证失败", "Bot模式需要填写Bot Token")
            return

        self.result_data = {
            'name': name,
            'type': 'bot' if is_bot else 'mtproto',
            'bot_token': self.token_input.text().strip(),
            'phone': self.phone_input.text().strip(),
            'api_id': self.api_id_input.text().strip(),
            'api_hash': self.api_hash_input.text().strip(),
            'session_string': self.session_input.toPlainText().strip(),
            'proxy': self.proxy_input.text().strip(),
            'note': self.note_input.text().strip(),
            'enabled': 1,
        }
        self.accept()


class ChannelDialog(QDialog):
    """频道添加对话框"""

    def __init__(self, channel=None, accounts=None, parent=None):
        super().__init__(parent)
        self.channel = channel
        self.accounts = accounts or []
        self.setWindowTitle("添加频道" if not channel else "编辑频道")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._setup_ui()
        if channel:
            self._load_channel(channel)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("📢 频道信息")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        form_group = QFrame()
        form_group.setObjectName("card")
        form = QFormLayout(form_group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("如：主要发布频道")
        form.addRow("频道名称:", self.name_input)

        self.channel_id_input = QLineEdit()
        self.channel_id_input.setPlaceholderText("@username 或 -100xxxxxxxxxx")
        form.addRow("频道ID:", self.channel_id_input)

        self.account_combo = QComboBox()
        self.account_combo.addItem("-- 选择发布账号 --", None)
        for acc in self.accounts:
            self.account_combo.addItem(f"{acc['name']} ({acc['type']})", acc['id'])
        form.addRow("绑定账号:", self.account_combo)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("可选描述")
        form.addRow("描述:", self.desc_input)

        layout.addWidget(form_group)

        id_note = QLabel(
            "💡 如何获取频道ID：\n"
            "   • 公开频道: 直接使用 @频道用户名\n"
            "   • 私有频道: 通过 @userinfobot 获取数字ID，格式 -100XXXXXXXXX\n"
            "   • 群组: 使用群组ID（负数）"
        )
        id_note.setStyleSheet("""
            color: #8b949e;
            font-size: 11px;
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px;
        """)
        id_note.setWordWrap(True)
        layout.addWidget(id_note)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("保存频道")
        save_btn.setObjectName("primaryBtn")
        save_btn.setFixedWidth(120)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _load_channel(self, channel):
        self.name_input.setText(channel.get('name', ''))
        self.channel_id_input.setText(channel.get('channel_id', ''))
        self.desc_input.setText(channel.get('description', ''))
        for i in range(self.account_combo.count()):
            if self.account_combo.itemData(i) == channel.get('account_id'):
                self.account_combo.setCurrentIndex(i)
                break

    def _save(self):
        name = self.name_input.text().strip()
        channel_id = self.channel_id_input.text().strip()
        if not name or not channel_id:
            QMessageBox.warning(self, "验证失败", "请填写频道名称和频道ID")
            return

        self.result_data = {
            'name': name,
            'channel_id': channel_id,
            'account_id': self.account_combo.currentData() or 0,
            'description': self.desc_input.text().strip(),
            'enabled': 1,
        }
        self.accept()


class ChannelPage(QWidget):
    """账号和频道管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        header = QHBoxLayout()
        title = QLabel("📢 账号与频道管理")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # 使用标签页
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # === 账号标签页 ===
        account_tab = QWidget()
        acc_layout = QVBoxLayout(account_tab)
        acc_layout.setContentsMargins(0, 12, 0, 0)
        acc_layout.setSpacing(10)

        # 账号工具栏
        acc_toolbar = QHBoxLayout()
        add_acc_btn = QPushButton("➕ 添加Bot账号")
        add_acc_btn.setObjectName("primaryBtn")
        add_acc_btn.clicked.connect(self._add_account)

        add_mt_btn = QPushButton("📱 添加真实账号")
        add_mt_btn.setObjectName("successBtn")
        add_mt_btn.clicked.connect(self._add_mtproto_account)

        del_acc_btn = QPushButton("🗑 删除")
        del_acc_btn.setObjectName("dangerBtn")
        del_acc_btn.clicked.connect(self._delete_account)

        test_acc_btn = QPushButton("🔗 测试连接")
        test_acc_btn.clicked.connect(self._test_account)

        acc_toolbar.addWidget(add_acc_btn)
        acc_toolbar.addWidget(add_mt_btn)
        acc_toolbar.addSpacing(8)
        acc_toolbar.addWidget(test_acc_btn)
        acc_toolbar.addWidget(del_acc_btn)
        acc_toolbar.addStretch()

        self.acc_count_lbl = QLabel("共 0 个账号")
        self.acc_count_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        acc_toolbar.addWidget(self.acc_count_lbl)
        acc_layout.addLayout(acc_toolbar)

        # 账号表格
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(7)
        self.accounts_table.setHorizontalHeaderLabels(
            ["#", "账号名称", "类型", "标识/手机号", "代理", "状态", "备注"]
        )
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.accounts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.accounts_table.setColumnWidth(0, 50)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.accounts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.accounts_table.setAlternatingRowColors(True)
        acc_layout.addWidget(self.accounts_table)

        # Bot使用说明
        bot_note = QLabel(
            "📖 Bot API: 最大发送50MB文件，无需手机号，操作简单。\n"
            "📱 MTProto (真实账号): 支持最大2GB文件，需手机号+API ID/Hash。\n"
            "   获取API: https://my.telegram.org → Apps → 创建App"
        )
        bot_note.setStyleSheet("""
            font-size: 11px; color: #8b949e;
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px 12px;
        """)
        bot_note.setWordWrap(True)
        acc_layout.addWidget(bot_note)
        tabs.addTab(account_tab, "👤 发布账号")

        # === 频道标签页 ===
        channel_tab = QWidget()
        ch_layout = QVBoxLayout(channel_tab)
        ch_layout.setContentsMargins(0, 12, 0, 0)
        ch_layout.setSpacing(10)

        ch_toolbar = QHBoxLayout()
        add_ch_btn = QPushButton("➕ 添加频道")
        add_ch_btn.setObjectName("primaryBtn")
        add_ch_btn.clicked.connect(self._add_channel)

        del_ch_btn = QPushButton("🗑 删除")
        del_ch_btn.setObjectName("dangerBtn")
        del_ch_btn.clicked.connect(self._delete_channel)

        import_ch_btn = QPushButton("📂 批量导入")
        import_ch_btn.clicked.connect(self._import_channels)

        ch_toolbar.addWidget(add_ch_btn)
        ch_toolbar.addWidget(import_ch_btn)
        ch_toolbar.addSpacing(8)
        ch_toolbar.addWidget(del_ch_btn)
        ch_toolbar.addStretch()

        self.ch_count_lbl = QLabel("共 0 个频道")
        self.ch_count_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        ch_toolbar.addWidget(self.ch_count_lbl)
        ch_layout.addLayout(ch_toolbar)

        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(6)
        self.channels_table.setHorizontalHeaderLabels(
            ["#", "频道名称", "频道ID", "绑定账号", "状态", "描述"]
        )
        self.channels_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.channels_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.channels_table.setColumnWidth(0, 50)
        self.channels_table.verticalHeader().setVisible(False)
        self.channels_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.channels_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.channels_table.setAlternatingRowColors(True)
        ch_layout.addWidget(self.channels_table)

        batch_note = QLabel(
            "💡 批量导入格式：每行一个频道ID，格式：\n"
            "   频道名称,@username 或 频道名称,-100xxxxxxxxxx"
        )
        batch_note.setStyleSheet("""
            font-size: 11px; color: #8b949e;
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px 12px;
        """)
        ch_layout.addWidget(batch_note)
        tabs.addTab(channel_tab, "📺 发布频道")

    def _load_data(self):
        """加载数据"""
        try:
            from core.database import get_accounts, get_channels
            self._accounts = get_accounts()
            self._channels = get_channels()
            self._populate_accounts_table()
            self._populate_channels_table()
        except Exception as e:
            pass

    def _populate_accounts_table(self):
        self.accounts_table.setRowCount(0)
        for i, acc in enumerate(self._accounts):
            self.accounts_table.insertRow(i)
            items = [
                str(acc.get('id', i + 1)),
                acc.get('name', ''),
                'Bot API' if acc.get('type') == 'bot' else '📱 MTProto',
                acc.get('bot_token', '')[:20] + '...' if acc.get('bot_token') else acc.get('phone', ''),
                acc.get('proxy', '') or '无',
                '✅ 启用' if acc.get('enabled') else '❌ 禁用',
                acc.get('note', ''),
            ]
            for j, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, acc.get('id'))
                self.accounts_table.setItem(i, j, item)

        self.acc_count_lbl.setText(f"共 {len(self._accounts)} 个账号")

    def _populate_channels_table(self):
        self.channels_table.setRowCount(0)
        acc_map = {acc['id']: acc['name'] for acc in self._accounts}

        for i, ch in enumerate(self._channels):
            self.channels_table.insertRow(i)
            items = [
                str(ch.get('id', i + 1)),
                ch.get('name', ''),
                ch.get('channel_id', ''),
                acc_map.get(ch.get('account_id', 0), '未绑定'),
                '✅ 启用' if ch.get('enabled') else '❌ 禁用',
                ch.get('description', ''),
            ]
            for j, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, ch.get('id'))
                self.channels_table.setItem(i, j, item)

        self.ch_count_lbl.setText(f"共 {len(self._channels)} 个频道")

    def _add_account(self):
        dlg = AccountDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data
            try:
                from core.database import get_db
                db = get_db()
                db.execute("""
                    INSERT INTO accounts (name, type, bot_token, phone, api_id, api_hash,
                        session_string, proxy, note, enabled)
                    VALUES (:name, :type, :bot_token, :phone, :api_id, :api_hash,
                        :session_string, :proxy, :note, :enabled)
                """, data)
                db.commit()
                db.close()
                self._load_data()
                QMessageBox.information(self, "成功", f"账号 '{data['name']}' 添加成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")

    def _add_mtproto_account(self):
        dlg = AccountDialog(parent=self)
        dlg.type_combo.setCurrentIndex(1)
        dlg._on_type_changed(1)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data
            try:
                from core.database import get_db
                db = get_db()
                db.execute("""
                    INSERT INTO accounts (name, type, bot_token, phone, api_id, api_hash,
                        session_string, proxy, note, enabled)
                    VALUES (:name, :type, :bot_token, :phone, :api_id, :api_hash,
                        :session_string, :proxy, :note, :enabled)
                """, data)
                db.commit()
                db.close()
                self._load_data()
                QMessageBox.information(self, "成功", f"MTProto账号 '{data['name']}' 添加成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")

    def _delete_account(self):
        row = self.accounts_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择要删除的账号")
            return
        acc_id = self.accounts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        name = self.accounts_table.item(row, 1).text()
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除账号 '{name}'？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.database import get_db
                db = get_db()
                db.execute("DELETE FROM accounts WHERE id=?", (acc_id,))
                db.commit()
                db.close()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")

    def _test_account(self):
        row = self.accounts_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择要测试的账号")
            return
        QMessageBox.information(self, "测试", "连接测试功能需要运行环境支持，请在实际Windows环境中测试。")

    def _add_channel(self):
        dlg = ChannelDialog(accounts=self._accounts, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data
            try:
                from core.database import get_db
                db = get_db()
                db.execute("""
                    INSERT INTO channels (name, channel_id, account_id, description, enabled)
                    VALUES (:name, :channel_id, :account_id, :description, :enabled)
                """, data)
                db.commit()
                db.close()
                self._load_data()
                QMessageBox.information(self, "成功", f"频道 '{data['name']}' 添加成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")

    def _delete_channel(self):
        row = self.channels_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择要删除的频道")
            return
        ch_id = self.channels_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        name = self.channels_table.item(row, 1).text()
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除频道 '{name}'？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.database import get_db
                db = get_db()
                db.execute("DELETE FROM channels WHERE id=?", (ch_id,))
                db.commit()
                db.close()
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")

    def _import_channels(self):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getMultiLineText(
            self, "批量导入频道",
            "格式：频道名称,@username 或 频道名称,-100xxxxxxxxxx\n（每行一条）：",
            ""
        )
        if ok and text.strip():
            count = 0
            errors = []
            try:
                from core.database import get_db
                db = get_db()
                for line in text.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        name, ch_id = parts[0].strip(), parts[1].strip()
                        db.execute(
                            "INSERT OR IGNORE INTO channels (name, channel_id, enabled) VALUES (?,?,1)",
                            (name, ch_id)
                        )
                        count += 1
                    else:
                        errors.append(line)
                db.commit()
                db.close()
                self._load_data()
                msg = f"成功导入 {count} 个频道"
                if errors:
                    msg += f"\n格式错误 {len(errors)} 条"
                QMessageBox.information(self, "导入结果", msg)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {e}")
