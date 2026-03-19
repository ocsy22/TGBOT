"""
频道管理页面
"""
import asyncio
import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from core.database import DB


class ChannelPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        hdr = QHBoxLayout()
        t_v = QVBoxLayout()
        t = QLabel('频道 & 账号管理')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('管理 Telegram 账号、代理和频道')
        sub.setStyleSheet('color: #8b949e;')
        t_v.addWidget(t)
        t_v.addWidget(sub)
        hdr.addLayout(t_v, 1)
        layout.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setSpacing(16)
        content_lay.setContentsMargins(0, 0, 0, 0)

        # ===== Telegram API配置 =====
        api_card = QFrame()
        api_card.setObjectName('card')
        api_card.setStyleSheet('QFrame#card{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        api_lay = QVBoxLayout(api_card)
        api_hdr = QHBoxLayout()
        api_title = QLabel('🔑  Telegram API 配置')
        api_title.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        api_note = QLabel('管理多组 Telegram API 凭据，不同账号可使用不同 API 避免关联。前往 my.telegram.org 获取。')
        api_note.setStyleSheet('color:#8b949e; font-size:12px;')
        api_note.setWordWrap(True)
        add_api_btn = QPushButton('+ 添加 API')
        add_api_btn.setObjectName('primary_btn')
        add_api_btn.clicked.connect(self._add_api)
        api_hdr.addWidget(api_title, 1)
        api_hdr.addWidget(add_api_btn)
        api_lay.addLayout(api_hdr)
        api_lay.addWidget(api_note)
        self._api_list = QVBoxLayout()
        self._api_list.setSpacing(6)
        api_lay.addLayout(self._api_list)
        content_lay.addWidget(api_card)

        # ===== Bot管理 =====
        bot_card = QFrame()
        bot_card.setObjectName('card')
        bot_card.setStyleSheet('QFrame#card{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        bot_lay = QVBoxLayout(bot_card)
        bot_hdr = QHBoxLayout()
        bot_title_w = QHBoxLayout()
        bot_title = QLabel('🤖  Bot 管理')
        bot_title.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        bot_badge = QLabel('推荐')
        bot_badge.setStyleSheet('color:#2ea043;background:#1a3a2a;border-radius:8px;padding:2px 8px;font-size:11px;')
        bot_title_w.addWidget(bot_title)
        bot_title_w.addWidget(bot_badge)
        bot_title_w.addStretch()
        add_bot_btn = QPushButton('+ 添加 Bot')
        add_bot_btn.setObjectName('primary_btn')
        add_bot_btn.clicked.connect(self._add_bot)
        bot_note = QLabel('使用 Bot 发布内容到频道，无封号风险。前往 @BotFather 创建 Bot 并获取 Token，然后将 Bot 添加为频道管理员。')
        bot_note.setStyleSheet('color:#8b949e; font-size:12px;')
        bot_note.setWordWrap(True)
        bot_hdr.addLayout(bot_title_w, 1)
        bot_hdr.addWidget(add_bot_btn)
        bot_lay.addLayout(bot_hdr)
        bot_lay.addWidget(bot_note)
        self._bot_list = QVBoxLayout()
        self._bot_list.setSpacing(6)
        bot_lay.addLayout(self._bot_list)
        content_lay.addWidget(bot_card)

        # ===== 账号管理 =====
        acc_card = QFrame()
        acc_card.setObjectName('card')
        acc_card.setStyleSheet('QFrame#card{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        acc_lay = QVBoxLayout(acc_card)
        acc_hdr = QHBoxLayout()
        acc_title = QLabel('👤  账号管理 (MTProto)')
        acc_title.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        add_acc_btn = QPushButton('+ 添加账号')
        add_acc_btn.setObjectName('primary_btn')
        add_acc_btn.clicked.connect(self._add_account)
        acc_hdr.addWidget(acc_title, 1)
        acc_hdr.addWidget(add_acc_btn)
        acc_lay.addLayout(acc_hdr)
        acc_note = QLabel('真实账号登录，支持发送大文件（最大2GB）。首次登录需要手机验证码。')
        acc_note.setStyleSheet('color:#8b949e;font-size:12px;')
        acc_note.setWordWrap(True)
        acc_lay.addWidget(acc_note)
        self._acc_list = QVBoxLayout()
        self._acc_list.setSpacing(6)
        acc_lay.addLayout(self._acc_list)
        content_lay.addWidget(acc_card)

        # ===== 频道管理 =====
        ch_card = QFrame()
        ch_card.setObjectName('card')
        ch_card.setStyleSheet('QFrame#card{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        ch_lay = QVBoxLayout(ch_card)
        ch_hdr = QHBoxLayout()
        ch_title = QLabel('📡  频道管理')
        ch_title.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        add_ch_btn = QPushButton('+ 添加频道')
        add_ch_btn.setObjectName('primary_btn')
        add_ch_btn.clicked.connect(self._add_channel)
        ch_hdr.addWidget(ch_title, 1)
        ch_hdr.addWidget(add_ch_btn)
        ch_lay.addLayout(ch_hdr)
        self._ch_list = QVBoxLayout()
        self._ch_list.setSpacing(8)
        ch_lay.addLayout(self._ch_list)
        content_lay.addWidget(ch_card)

        content_lay.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def refresh(self):
        self._refresh_apis()
        self._refresh_bots()
        self._refresh_accounts()
        self._refresh_channels()

    def _clear_layout(self, lay):
        while lay.count():
            item = lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _refresh_apis(self):
        self._clear_layout(self._api_list)
        apis = DB.fetchall('SELECT * FROM telegram_apis ORDER BY id')
        for api in apis:
            row = self._create_api_row(api)
            self._api_list.addWidget(row)

    def _create_api_row(self, api):
        row = QFrame()
        row.setStyleSheet('QFrame{background:#0d1117;border:1px solid #21262d;border-radius:6px;}')
        lay = QHBoxLayout(row)
        lay.setContentsMargins(12, 10, 12, 10)
        lbl = QLabel(f"{api['id']}   ID: {api['api_id']}   Hash: {api['api_hash'][:8]}...")
        lbl.setStyleSheet('color:#e6edf3;')
        edit_btn = QPushButton('✏️')
        edit_btn.setObjectName('icon_btn')
        edit_btn.setFixedSize(28, 28)
        del_btn = QPushButton('🗑️')
        del_btn.setObjectName('icon_btn')
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet('color:#da3633;')
        del_btn.clicked.connect(lambda: self._delete_api(api['id']))
        edit_btn.clicked.connect(lambda: self._edit_api(api))
        lay.addWidget(lbl, 1)
        lay.addWidget(edit_btn)
        lay.addWidget(del_btn)
        return row

    def _refresh_bots(self):
        self._clear_layout(self._bot_list)
        bots = DB.fetchall('SELECT * FROM bots ORDER BY id')
        for bot in bots:
            row = self._create_bot_row(bot)
            self._bot_list.addWidget(row)

    def _create_bot_row(self, bot):
        row = QFrame()
        row.setStyleSheet('QFrame{background:#0d1117;border:1px solid #21262d;border-radius:6px;}')
        lay = QVBoxLayout(row)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)

        hdr_lay = QHBoxLayout()
        name = QLabel(f'🤖 {bot["label"]}')
        name.setStyleSheet('font-weight:bold;color:#e6edf3;')
        status_lbl = QLabel('正常')
        status_lbl.setStyleSheet('color:#2ea043;background:#1a3a2a;border-radius:8px;padding:2px 8px;font-size:11px;')

        get_ch_btn = QPushButton('📡 获取频道')
        get_ch_btn.setObjectName('icon_btn')
        get_ch_btn.clicked.connect(lambda: self._get_bot_channels(bot))
        del_btn = QPushButton('🗑️')
        del_btn.setObjectName('icon_btn')
        del_btn.setStyleSheet('color:#da3633;')
        del_btn.clicked.connect(lambda: self._delete_bot(bot['id']))

        hdr_lay.addWidget(name)
        hdr_lay.addWidget(status_lbl)
        hdr_lay.addStretch()
        hdr_lay.addWidget(get_ch_btn)
        hdr_lay.addWidget(del_btn)

        token_lbl = QLabel(f'@{bot.get("label", "")}bot\nToken: {bot["token"][:20]}...')
        token_lbl.setStyleSheet('color:#8b949e;font-size:11px;')

        lay.addLayout(hdr_lay)
        lay.addWidget(token_lbl)
        return row

    def _refresh_accounts(self):
        self._clear_layout(self._acc_list)
        accounts = DB.fetchall('SELECT * FROM accounts ORDER BY id')
        for acc in accounts:
            row = self._create_account_row(acc)
            self._acc_list.addWidget(row)

    def _create_account_row(self, acc):
        row = QFrame()
        row.setStyleSheet('QFrame{background:#0d1117;border:1px solid #21262d;border-radius:6px;}')
        lay = QHBoxLayout(row)
        lay.setContentsMargins(12, 10, 12, 10)

        icon = '🟢' if acc.get('status') == 'online' else '⚪'
        lbl = QLabel(f'{icon} {acc["phone"]} ({acc.get("label", "")})')
        lbl.setStyleSheet('color:#e6edf3;')

        login_btn = QPushButton('登录')
        login_btn.setObjectName('icon_btn')
        login_btn.clicked.connect(lambda: self._login_account(acc))
        del_btn = QPushButton('🗑️')
        del_btn.setObjectName('icon_btn')
        del_btn.setStyleSheet('color:#da3633;')
        del_btn.clicked.connect(lambda: self._delete_account(acc['id']))

        lay.addWidget(lbl, 1)
        lay.addWidget(login_btn)
        lay.addWidget(del_btn)
        return row

    def _refresh_channels(self):
        self._clear_layout(self._ch_list)
        channels = DB.fetchall('SELECT * FROM channels ORDER BY id')
        for ch in channels:
            row = self._create_channel_row(ch)
            self._ch_list.addWidget(row)

    def _create_channel_row(self, ch):
        row = QFrame()
        row.setStyleSheet('QFrame{background:#0d1117;border:1px solid #21262d;border-radius:8px;}')
        lay = QVBoxLayout(row)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        hdr = QHBoxLayout()
        name = QLabel(f'📡 {ch["name"]}')
        name.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
        del_btn = QPushButton('🗑️')
        del_btn.setObjectName('icon_btn')
        del_btn.setStyleSheet('color:#da3633;font-size:14px;')
        del_btn.clicked.connect(lambda: self._delete_channel(ch['id']))
        hdr.addWidget(name, 1)
        hdr.addWidget(del_btn)

        info = QHBoxLayout()
        if ch.get('username'):
            user_lbl = QLabel(f'@{ch["username"]}')
            user_lbl.setStyleSheet('color:#8b949e;font-size:11px;')
            info.addWidget(user_lbl)
        if ch.get('chat_id'):
            id_lbl = QLabel(f'Chat ID: {ch["chat_id"]}')
            id_lbl.setStyleSheet('color:#8b949e;font-size:11px;')
            info.addWidget(id_lbl)
        info.addStretch()

        mode_labels = QHBoxLayout()
        mode_text = 'Bot' if ch.get('send_mode') == 'bot' else 'AI'
        for tag in [mode_text, 'AI']:
            tl = QLabel(tag)
            tl.setStyleSheet('color:#1f6feb;background:#1f3a5f;border-radius:8px;padding:2px 8px;font-size:11px;margin-right:4px;')
            mode_labels.addWidget(tl)

        if ch.get('auto_like'):
            likes_lbl = QLabel(f'♡ 自动点赞')
            likes_lbl.setStyleSheet('color:#8b949e;font-size:11px;')
            info.addWidget(likes_lbl)

        lay.addLayout(hdr)
        lay.addLayout(info)
        return row

    # ===== 对话框方法 =====

    def _add_api(self):
        dlg = APIDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute('INSERT INTO telegram_apis (api_id, api_hash, label) VALUES (?,?,?)',
                       (data['api_id'], data['api_hash'], data.get('label', '')))
            self._refresh_apis()

    def _edit_api(self, api):
        dlg = APIDialog(self, api)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute('UPDATE telegram_apis SET api_id=?, api_hash=?, label=? WHERE id=?',
                       (data['api_id'], data['api_hash'], data.get('label', ''), api['id']))
            self._refresh_apis()

    def _delete_api(self, api_id):
        if QMessageBox.question(self, '确认', '确定删除此API配置？') == QMessageBox.StandardButton.Yes:
            DB.execute('DELETE FROM telegram_apis WHERE id=?', (api_id,))
            self._refresh_apis()

    def _add_bot(self):
        dlg = BotDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute('INSERT INTO bots (label, token) VALUES (?,?)',
                       (data['label'], data['token']))
            self._refresh_bots()

    def _delete_bot(self, bot_id):
        if QMessageBox.question(self, '确认', '确定删除此Bot？') == QMessageBox.StandardButton.Yes:
            DB.execute('DELETE FROM bots WHERE id=?', (bot_id,))
            self._refresh_bots()

    def _get_bot_channels(self, bot):
        QMessageBox.information(self, '提示', f'请将 Bot @{bot["label"]}bot 添加为频道管理员后，手动在频道管理中添加频道信息。\n\nChat ID获取方式：将Bot添加到频道，然后发送一条消息，访问 https://api.telegram.org/bot{bot["token"]}/getUpdates 查看chat.id')

    def _add_account(self):
        dlg = AccountDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute(
                'INSERT OR REPLACE INTO accounts (phone, api_id, label, proxy) VALUES (?,?,?,?)',
                (data['phone'], data.get('api_id', 0), data.get('label', ''), data.get('proxy', ''))
            )
            self._refresh_accounts()

    def _login_account(self, acc):
        QMessageBox.information(self, '登录账号', f'请在任务中使用此账号时，系统会提示输入验证码进行登录。\n\n手机号: {acc["phone"]}')

    def _delete_account(self, acc_id):
        if QMessageBox.question(self, '确认', '确定删除此账号？') == QMessageBox.StandardButton.Yes:
            DB.execute('DELETE FROM accounts WHERE id=?', (acc_id,))
            self._refresh_accounts()

    def _add_channel(self):
        dlg = ChannelDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute(
                'INSERT INTO channels (name, username, chat_id, bot_id, account_id, send_mode) VALUES (?,?,?,?,?,?)',
                (data['name'], data.get('username', ''), data.get('chat_id', ''),
                 data.get('bot_id', 0), data.get('account_id', 0), data.get('send_mode', 'bot'))
            )
            self._refresh_channels()

    def _delete_channel(self, ch_id):
        if QMessageBox.question(self, '确认', '确定删除此频道？') == QMessageBox.StandardButton.Yes:
            DB.execute('DELETE FROM channels WHERE id=?', (ch_id,))
            self._refresh_channels()


# ===== 对话框 =====

class APIDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('Telegram API 配置')
        self.setFixedWidth(460)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        lay.addWidget(QLabel('API ID:'))
        self._api_id = QLineEdit(data['api_id'] if data else '')
        self._api_id.setPlaceholderText('如: 12345678')
        lay.addWidget(self._api_id)

        lay.addWidget(QLabel('API Hash:'))
        self._api_hash = QLineEdit(data['api_hash'] if data else '')
        self._api_hash.setPlaceholderText('32位十六进制字符串')
        lay.addWidget(self._api_hash)

        lay.addWidget(QLabel('备注 (可选):'))
        self._label = QLineEdit(data.get('label', '') if data else '')
        lay.addWidget(self._label)

        note = QLabel('前往 https://my.telegram.org 登录后，在 API Development Tools 获取')
        note.setStyleSheet('color:#8b949e;font-size:11px;')
        note.setWordWrap(True)
        lay.addWidget(note)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self):
        return {'api_id': self._api_id.text().strip(), 'api_hash': self._api_hash.text().strip(), 'label': self._label.text().strip()}


class BotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加 Bot')
        self.setFixedWidth(460)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        lay.addWidget(QLabel('Bot 名称/备注:'))
        self._label = QLineEdit()
        self._label.setPlaceholderText('如: 内容1')
        lay.addWidget(self._label)

        lay.addWidget(QLabel('Bot Token:'))
        self._token = QLineEdit()
        self._token.setPlaceholderText('如: 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi')
        lay.addWidget(self._token)

        note = QLabel('前往 @BotFather 创建 Bot 并获取 Token')
        note.setStyleSheet('color:#8b949e;font-size:11px;')
        lay.addWidget(note)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self):
        return {'label': self._label.text().strip(), 'token': self._token.text().strip()}


class AccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加账号')
        self.setFixedWidth(460)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        lay.addWidget(QLabel('手机号 (含国际区号):'))
        self._phone = QLineEdit()
        self._phone.setPlaceholderText('+8613812345678')
        lay.addWidget(self._phone)

        lay.addWidget(QLabel('关联 API 配置:'))
        self._api_combo = QComboBox()
        apis = DB.fetchall('SELECT * FROM telegram_apis')
        for api in apis:
            self._api_combo.addItem(f'ID:{api["api_id"]} ({api.get("label", "")})', api['id'])
        lay.addWidget(self._api_combo)

        lay.addWidget(QLabel('备注:'))
        self._label = QLineEdit()
        lay.addWidget(self._label)

        lay.addWidget(QLabel('代理 (可选, socks5://ip:port):'))
        self._proxy = QLineEdit()
        self._proxy.setPlaceholderText('socks5://127.0.0.1:1080')
        lay.addWidget(self._proxy)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self):
        api_id = self._api_combo.currentData() or 0
        return {'phone': self._phone.text().strip(), 'api_id': api_id,
                'label': self._label.text().strip(), 'proxy': self._proxy.text().strip()}


class ChannelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加频道')
        self.setFixedWidth(480)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        lay.addWidget(QLabel('频道名称:'))
        self._name = QLineEdit()
        self._name.setPlaceholderText('如: 爱拼才会赢')
        lay.addWidget(self._name)

        lay.addWidget(QLabel('频道用户名 (@xxxx):'))
        self._username = QLineEdit()
        self._username.setPlaceholderText('aipindddddddd')
        lay.addWidget(self._username)

        lay.addWidget(QLabel('Chat ID (如 -1001234567890):'))
        self._chat_id = QLineEdit()
        self._chat_id.setPlaceholderText('-1003431224285')
        lay.addWidget(self._chat_id)

        lay.addWidget(QLabel('发送方式:'))
        self._send_mode = QComboBox()
        self._send_mode.addItem('Bot 发送 (推荐，无封号风险)', 'bot')
        self._send_mode.addItem('账号 MTProto (支持大文件)', 'account')
        lay.addWidget(self._send_mode)

        self._bot_area = QWidget()
        bot_lay = QVBoxLayout(self._bot_area)
        bot_lay.setContentsMargins(0, 0, 0, 0)
        bot_lay.addWidget(QLabel('选择 Bot:'))
        self._bot_combo = QComboBox()
        bots = DB.fetchall('SELECT * FROM bots')
        for bot in bots:
            self._bot_combo.addItem(f'{bot["label"]} ({bot["token"][:15]}...)', bot['id'])
        bot_lay.addWidget(self._bot_combo)
        lay.addWidget(self._bot_area)

        self._acc_area = QWidget()
        self._acc_area.setVisible(False)
        acc_lay = QVBoxLayout(self._acc_area)
        acc_lay.setContentsMargins(0, 0, 0, 0)
        acc_lay.addWidget(QLabel('选择账号:'))
        self._acc_combo = QComboBox()
        accs = DB.fetchall('SELECT * FROM accounts')
        for acc in accs:
            self._acc_combo.addItem(f'{acc["phone"]} ({acc.get("label", "")})', acc['id'])
        acc_lay.addWidget(self._acc_combo)
        lay.addWidget(self._acc_area)

        self._send_mode.currentIndexChanged.connect(self._on_mode_changed)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _on_mode_changed(self, idx):
        mode = self._send_mode.currentData()
        self._bot_area.setVisible(mode == 'bot')
        self._acc_area.setVisible(mode == 'account')

    def get_data(self):
        mode = self._send_mode.currentData()
        return {
            'name': self._name.text().strip(),
            'username': self._username.text().strip().lstrip('@'),
            'chat_id': self._chat_id.text().strip(),
            'send_mode': mode,
            'bot_id': self._bot_combo.currentData() or 0 if mode == 'bot' else 0,
            'account_id': self._acc_combo.currentData() or 0 if mode == 'account' else 0,
        }
