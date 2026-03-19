"""
其他页面：自动发布、文案库、文案格式、写作方向、群发、发布设置
"""
import json
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from core.database import DB


# =================== 自动发布页面 ===================
class AutoPublishPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        hdr = QHBoxLayout()
        tv = QVBoxLayout()
        t = QLabel('自动发布')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('配置定时自动发布规则，从素材库自动选材并发布到频道')
        sub.setStyleSheet('color:#8b949e;')
        tv.addWidget(t)
        tv.addWidget(sub)
        hdr.addLayout(tv, 1)
        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(self.refresh)
        new_btn = QPushButton('+ 新建规则')
        new_btn.setObjectName('primary_btn')
        new_btn.clicked.connect(self._new_rule)
        hdr.addWidget(refresh_btn)
        hdr.addWidget(new_btn)
        lay.addLayout(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._list_lay = QVBoxLayout(self._container)
        self._list_lay.setSpacing(10)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._container)
        lay.addWidget(self._scroll)

    def refresh(self):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rules = DB.fetchall('SELECT * FROM auto_publish_rules ORDER BY id DESC')
        if not rules:
            empty = QLabel('暂无自动发布规则\n点击「新建规则」创建')
            empty.setStyleSheet('color:#8b949e;')
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(200)
            self._list_lay.addWidget(empty)
            return

        for rule in rules:
            card = self._create_rule_card(rule)
            self._list_lay.addWidget(card)

    def _create_rule_card(self, rule):
        card = QFrame()
        card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        name = QLabel(f'cs{rule["id"]}   {rule["name"]}')
        name.setFont(QFont('Segoe UI', 13))

        enabled = rule.get('enabled', 1)
        status_lbl = QLabel('运行中' if enabled else '已停止')
        status_style = 'color:#2ea043;background:#1a3a2a;' if enabled else 'color:#8b949e;background:#21262d;'
        status_lbl.setStyleSheet(f'{status_style}border-radius:10px;padding:2px 10px;font-size:11px;')

        mode_lbl = QLabel(rule.get('schedule_type', 'daily').replace('daily', '每天').replace('interval', '间隔'))
        mode_lbl.setStyleSheet('color:#8b949e;background:#21262d;border-radius:10px;padding:2px 8px;font-size:11px;')

        top.addWidget(name, 1)
        top.addWidget(status_lbl)
        top.addWidget(mode_lbl)

        info = QHBoxLayout()
        sched_icon = '📅 每天 1 条' if rule.get('schedule_type') == 'daily' else '⏱ 间隔'
        info_parts = [
            sched_icon,
            f'⏰ 固定时间 {rule.get("schedule_time", "20:00")}',
            '🔀 随机' if rule.get('random_order') else '📋 顺序',
            f'📡 {rule.get("send_mode", "原视频")}',
            f'已发: {rule.get("published_count", 0)} 条',
        ]
        if rule.get('last_publish'):
            info_parts.append(f'上次: {rule["last_publish"][:16]}')

        folder = DB.fetchone('SELECT name FROM media_folders WHERE id=?', (rule.get('media_folder_id', 0),))
        if folder:
            info_parts.append(f'素材: {folder["name"]}')

        info_lbl = QLabel('    '.join(info_parts))
        info_lbl.setStyleSheet('color:#8b949e;font-size:11px;')
        info.addWidget(info_lbl, 1)

        actions = QHBoxLayout()
        btns_data = [
            ('👁', '查看', lambda: self._view_rule(rule)),
            ('▶', '立即执行', lambda: self._run_rule(rule)),
            ('⏱', '定时', None),
            ('🗑️', '删除', lambda: self._delete_rule(rule['id'])),
            ('🔄', '重置', lambda: self._reset_rule(rule['id'])),
            ('❌', '停止/启动', lambda: self._toggle_rule(rule)),
        ]
        for icon, tip, handler in btns_data:
            btn = QPushButton(icon)
            btn.setObjectName('icon_btn')
            btn.setFixedSize(28, 28)
            btn.setToolTip(tip)
            if handler:
                btn.clicked.connect(handler)
            if icon == '🗑️':
                btn.setStyleSheet('color:#da3633;background:transparent;border:none;')
            actions.addWidget(btn)
        actions.addStretch()

        lay.addLayout(top)
        lay.addLayout(info)
        lay.addLayout(actions)
        return card

    def _new_rule(self):
        dlg = AutoPublishRuleDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute('''INSERT INTO auto_publish_rules 
                (name, channel_ids, media_folder_id, copy_template_id, writing_direction_id,
                schedule_type, schedule_time, random_order, send_after_done, send_mode, enabled)
                VALUES (?,?,?,?,?,?,?,?,?,?,1)''',
                (data['name'], json.dumps(data['channel_ids']), data.get('folder_id', 0),
                 data.get('tmpl_id', 0), data.get('wd_id', 0),
                 data.get('schedule_type', 'daily'), data.get('schedule_time', '20:00'),
                 1 if data.get('random_order') else 0,
                 data.get('send_after_done', 'stop'), data.get('send_mode', 'original')))
            self.refresh()

    def _toggle_rule(self, rule):
        new_enabled = 0 if rule.get('enabled') else 1
        DB.execute('UPDATE auto_publish_rules SET enabled=? WHERE id=?', (new_enabled, rule['id']))
        self.refresh()

    def _delete_rule(self, rule_id):
        if QMessageBox.question(self, '确认', '确定删除此规则？') == QMessageBox.StandardButton.Yes:
            DB.execute('DELETE FROM auto_publish_rules WHERE id=?', (rule_id,))
            self.refresh()

    def _reset_rule(self, rule_id):
        DB.execute('UPDATE auto_publish_rules SET published_count=0, last_publish="" WHERE id=?', (rule_id,))
        self.refresh()

    def _view_rule(self, rule):
        QMessageBox.information(self, '规则详情', json.dumps(rule, ensure_ascii=False, indent=2))

    def _run_rule(self, rule):
        QMessageBox.information(self, '立即执行', f'将立即执行规则: {rule["name"]}')


class AutoPublishRuleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('新建自动发布规则')
        self.setFixedSize(520, 600)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        lay.addWidget(QLabel('规则名称:'))
        self._name = QLineEdit()
        self._name.setPlaceholderText('如: 每日推送')
        lay.addWidget(self._name)

        lay.addWidget(QLabel('素材文件夹:'))
        self._folder = QComboBox()
        folders = DB.fetchall('SELECT * FROM media_folders')
        for f in folders:
            self._folder.addItem(f'📁 {f["name"]}', f['id'])
        lay.addWidget(self._folder)

        lay.addWidget(QLabel('发布频道 (多选):'))
        self._ch_list = QListWidget()
        self._ch_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._ch_list.setFixedHeight(100)
        for ch in DB.fetchall('SELECT * FROM channels'):
            item = QListWidgetItem(f'📡 {ch["name"]}')
            item.setData(Qt.ItemDataRole.UserRole, ch['id'])
            self._ch_list.addItem(item)
        lay.addWidget(self._ch_list)

        sched_row = QHBoxLayout()
        sched_row.addWidget(QLabel('发布时间:'))
        self._sched_time = QTimeEdit()
        self._sched_time.setDisplayFormat('HH:mm')
        self._sched_time.setTime(QTime(20, 55))
        sched_row.addWidget(self._sched_time)
        sched_row.addStretch()
        lay.addLayout(sched_row)

        self._random_order = QCheckBox('随机顺序发布')
        self._random_order.setChecked(True)
        lay.addWidget(self._random_order)

        lay.addWidget(QLabel('发送完所有素材后:'))
        self._done_action = QComboBox()
        self._done_action.addItem('停止发布', 'stop')
        self._done_action.addItem('循环重新发布', 'loop')
        lay.addWidget(self._done_action)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self):
        ch_ids = [item.data(Qt.ItemDataRole.UserRole) for item in self._ch_list.selectedItems()]
        return {
            'name': self._name.text().strip(),
            'folder_id': self._folder.currentData(),
            'channel_ids': ch_ids,
            'schedule_type': 'daily',
            'schedule_time': self._sched_time.time().toString('HH:mm'),
            'random_order': self._random_order.isChecked(),
            'send_after_done': self._done_action.currentData(),
        }


# =================== 文案库页面 ===================
class CopywritingPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        hdr = QHBoxLayout()
        tv = QVBoxLayout()
        t = QLabel('文案库')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('管理预设文案，可附带视频或图片，用于自动发布')
        sub.setStyleSheet('color:#8b949e;')
        tv.addWidget(t)
        tv.addWidget(sub)
        hdr.addLayout(tv, 1)
        new_btn = QPushButton('+ 新建文案')
        new_btn.setObjectName('primary_btn')
        new_btn.clicked.connect(self._new_copy)
        hdr.addWidget(new_btn)
        lay.addLayout(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._list_lay = QVBoxLayout(self._container)
        self._list_lay.setSpacing(8)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._container)
        lay.addWidget(self._scroll)

    def refresh(self):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        copies = DB.fetchall('SELECT * FROM copywriting ORDER BY id DESC')
        if not copies:
            empty = QLabel('还没有文案，点击「新建文案」开始创建')
            empty.setStyleSheet('color:#8b949e;')
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(200)
            self._list_lay.addWidget(empty)
            return

        for copy in copies:
            card = self._create_copy_card(copy)
            self._list_lay.addWidget(card)

    def _create_copy_card(self, copy):
        card = QFrame()
        card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        lay = QHBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)

        content_lay = QVBoxLayout()
        title = QLabel(copy.get('title') or f'文案 #{copy["id"]}')
        title.setFont(QFont('Segoe UI', 13))
        content_preview = QLabel(copy['content'][:80] + '...' if len(copy['content']) > 80 else copy['content'])
        content_preview.setStyleSheet('color:#8b949e;font-size:12px;')
        content_preview.setWordWrap(True)
        content_lay.addWidget(title)
        content_lay.addWidget(content_preview)

        edit_btn = QPushButton('✏️')
        edit_btn.setObjectName('icon_btn')
        del_btn = QPushButton('🗑️')
        del_btn.setObjectName('icon_btn')
        del_btn.setStyleSheet('color:#da3633;')
        del_btn.clicked.connect(lambda: self._delete_copy(copy['id']))

        lay.addLayout(content_lay, 1)
        lay.addWidget(edit_btn)
        lay.addWidget(del_btn)
        return card

    def _new_copy(self):
        dlg = CopyDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute('INSERT INTO copywriting (title, content, tags) VALUES (?,?,?)',
                       (data['title'], data['content'], data.get('tags', '')))
            self.refresh()

    def _delete_copy(self, copy_id):
        if QMessageBox.question(self, '确认', '删除此文案？') == QMessageBox.StandardButton.Yes:
            DB.execute('DELETE FROM copywriting WHERE id=?', (copy_id,))
            self.refresh()


class CopyDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('新建文案')
        self.setFixedSize(560, 460)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel('标题:'))
        self._title = QLineEdit(data.get('title', '') if data else '')
        lay.addWidget(self._title)
        lay.addWidget(QLabel('正文内容:'))
        self._content = QTextEdit()
        self._content.setPlainText(data.get('content', '') if data else '')
        self._content.setFixedHeight(200)
        lay.addWidget(self._content)
        lay.addWidget(QLabel('标签 (用空格分隔):'))
        self._tags = QLineEdit(data.get('tags', '') if data else '')
        lay.addWidget(self._tags)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self):
        return {'title': self._title.text().strip(), 'content': self._content.toPlainText().strip(), 'tags': self._tags.text().strip()}


# =================== 文案格式页面 ===================
class CopyTemplatePage(QWidget):
    EMOJIS = ['🔥', '❤️', '👋', '😍', '🤤', '🍑', '🍒', '💦', '⭐', '💎', '🎬', '🎥', '🎞️', '❤️‍🔥', '💋', '🌶️', '🍓', '👅', '💥', '🚀', '✅', '⏱️', '🔞']

    def __init__(self):
        super().__init__()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        hdr = QHBoxLayout()
        tv = QVBoxLayout()
        t = QLabel('文案格式')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('管理视频发布时的文案排版模板，支持自定义占位符和 HTML 标签')
        sub.setStyleSheet('color:#8b949e;')
        tv.addWidget(t)
        tv.addWidget(sub)
        hdr.addLayout(tv, 1)
        new_btn = QPushButton('+ 新增格式')
        new_btn.setObjectName('primary_btn')
        new_btn.clicked.connect(self._new_template)
        hdr.addWidget(new_btn)
        lay.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setSpacing(12)

        # 占位符说明
        info_card = QFrame()
        info_card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        info_lay = QVBoxLayout(info_card)
        info_lay.setSpacing(8)

        placeholders = QLabel(
            '可用占位符：<b style="color:#1f6feb">{title}</b> AI标题、'
            '<b style="color:#1f6feb">{content}</b> AI内容、'
            '<b style="color:#1f6feb">{duration}</b> 时长（如3分20秒）、'
            '<b style="color:#1f6feb">{emoji}</b> 标题表情，'
            '支持 Telegram HTML 标签: <b>&lt;b&gt;</b> 加粗, <b>&lt;i&gt;</b> 斜体, <b>&lt;blockquote&gt;</b> 引用块。'
        )
        placeholders.setStyleSheet('color:#e6edf3;font-size:12px;')
        placeholders.setWordWrap(True)
        info_lay.addWidget(placeholders)

        emoji_row_lbl = QLabel('Emoji 使用：直接在模板中输入 emoji 即可，点击下方复制常用表情：')
        emoji_row_lbl.setStyleSheet('color:#8b949e;font-size:11px;')
        info_lay.addWidget(emoji_row_lbl)

        emoji_row = QHBoxLayout()
        emoji_row.setSpacing(4)
        for e in self.EMOJIS:
            btn = QPushButton(e)
            btn.setFixedSize(32, 32)
            btn.setStyleSheet('QPushButton{background:#21262d;border:none;border-radius:4px;font-size:14px;}QPushButton:hover{background:#30363d;}')
            btn.clicked.connect(lambda _, em=e: QApplication.clipboard().setText(em))
            btn.setToolTip('点击复制')
            emoji_row.addWidget(btn)
        emoji_row.addStretch()
        info_lay.addLayout(emoji_row)
        content_lay.addWidget(info_card)

        self._tmpl_container = QWidget()
        self._tmpl_lay = QVBoxLayout(self._tmpl_container)
        self._tmpl_lay.setSpacing(8)
        self._tmpl_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_lay.addWidget(self._tmpl_container)

        content_lay.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)

    def refresh(self):
        while self._tmpl_lay.count():
            item = self._tmpl_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        templates = DB.fetchall('SELECT * FROM copy_templates ORDER BY id')
        for tmpl in templates:
            card = self._create_template_card(tmpl)
            self._tmpl_lay.addWidget(card)

    def _create_template_card(self, tmpl):
        card = QFrame()
        card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        lay = QHBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)

        left = QVBoxLayout()
        name_row = QHBoxLayout()
        name_lbl = QLabel(f'📝 {tmpl["name"]}')
        name_lbl.setFont(QFont('Segoe UI', 13))
        builtin_badge = QLabel('内置') if tmpl.get('is_builtin') else QLabel()
        builtin_badge.setStyleSheet('color:#1f6feb;background:#1f3a5f;border-radius:8px;padding:2px 8px;font-size:11px;')
        name_row.addWidget(name_lbl)
        if tmpl.get('is_builtin'):
            name_row.addWidget(builtin_badge)
        name_row.addStretch()
        left.addLayout(name_row)

        code_lbl = QLabel(tmpl.get('template', '')[:100])
        code_lbl.setStyleSheet('color:#8b949e;font-size:11px;font-family:Consolas,monospace;')
        code_lbl.setWordWrap(True)
        left.addWidget(code_lbl)

        preview_btn = QPushButton('👁')
        preview_btn.setObjectName('icon_btn')
        preview_btn.setFixedSize(28, 28)
        preview_btn.setToolTip('预览')
        preview_btn.clicked.connect(lambda: self._preview_template(tmpl))

        edit_btn = QPushButton('✏️')
        edit_btn.setObjectName('icon_btn')
        edit_btn.setFixedSize(28, 28)
        edit_btn.clicked.connect(lambda: self._edit_template(tmpl))

        lay.addLayout(left, 1)
        lay.addWidget(preview_btn)
        lay.addWidget(edit_btn)
        return card

    def _new_template(self):
        dlg = TemplateDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute('INSERT INTO copy_templates (name, template) VALUES (?,?)', (data['name'], data['template']))
            self.refresh()

    def _edit_template(self, tmpl):
        dlg = TemplateDialog(self, tmpl)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute('UPDATE copy_templates SET name=?, template=? WHERE id=?', (data['name'], data['template'], tmpl['id']))
            self.refresh()

    def _preview_template(self, tmpl):
        template = tmpl.get('template', '')
        preview = template.replace('{title}', '这是一个示例标题').replace('{content}', '这是AI生成的文案内容示例').replace('{duration}', '3:20').replace('{emoji}', '🔥')
        QMessageBox.information(self, f'预览: {tmpl["name"]}', preview)


class TemplateDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('文案模板')
        self.setFixedSize(520, 400)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel('模板名称:'))
        self._name = QLineEdit(data['name'] if data else '')
        lay.addWidget(self._name)
        lay.addWidget(QLabel('模板内容 (支持 {title} {content} {duration} {emoji} 占位符及HTML标签):'))
        self._template = QTextEdit()
        self._template.setPlainText(data['template'] if data else '')
        self._template.setFixedHeight(200)
        self._template.setFont(QFont('Consolas', 11))
        lay.addWidget(self._template)
        hint = QLabel('HTML标签: <b></b> 加粗  <i></i> 斜体  <blockquote></blockquote> 引用')
        hint.setStyleSheet('color:#8b949e;font-size:11px;')
        lay.addWidget(hint)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self):
        return {'name': self._name.text().strip(), 'template': self._template.toPlainText()}


# =================== 写作方向页面 ===================
class WritingDirectionPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        hdr = QHBoxLayout()
        tv = QVBoxLayout()
        t = QLabel('写作方向')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('管理 AI 生成文案时的写作风格预设，可在自动发布规则中选择使用')
        sub.setStyleSheet('color:#8b949e;')
        tv.addWidget(t)
        tv.addWidget(sub)
        hdr.addLayout(tv, 1)
        new_btn = QPushButton('+ 新增预设')
        new_btn.setObjectName('primary_btn')
        new_btn.clicked.connect(self._new_direction)
        hdr.addWidget(new_btn)
        lay.addLayout(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._list_lay = QVBoxLayout(self._container)
        self._list_lay.setSpacing(8)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._container)
        lay.addWidget(self._scroll)

    def refresh(self):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        wds = DB.fetchall('SELECT * FROM writing_directions ORDER BY id DESC')
        if not wds:
            empty = QLabel('暂无写作方向预设')
            empty.setStyleSheet('color:#8b949e;')
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(200)
            self._list_lay.addWidget(empty)
            return

        for wd in wds:
            card = QFrame()
            card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
            lay2 = QHBoxLayout(card)
            lay2.setContentsMargins(14, 12, 14, 12)
            left = QVBoxLayout()
            name = QLabel(f'🎯 {wd["name"]}')
            name.setFont(QFont('Segoe UI', 13))
            desc = QLabel(wd.get('description', ''))
            desc.setStyleSheet('color:#8b949e;font-size:12px;')
            left.addWidget(name)
            left.addWidget(desc)
            edit_btn = QPushButton('✏️')
            edit_btn.setObjectName('icon_btn')
            edit_btn.clicked.connect(lambda _, w=wd: self._edit_direction(w))
            del_btn = QPushButton('🗑️')
            del_btn.setObjectName('icon_btn')
            del_btn.setStyleSheet('color:#da3633;')
            del_btn.clicked.connect(lambda _, wid=wd['id']: self._delete_direction(wid))
            lay2.addLayout(left, 1)
            lay2.addWidget(edit_btn)
            lay2.addWidget(del_btn)
            self._list_lay.addWidget(card)

    def _new_direction(self):
        dlg = WritingDirectionDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute('INSERT INTO writing_directions (name, description, style, keywords, extra_prompt) VALUES (?,?,?,?,?)',
                       (data['name'], data['description'], data['style'], data['keywords'], data['extra_prompt']))
            self.refresh()

    def _edit_direction(self, wd):
        dlg = WritingDirectionDialog(self, wd)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            DB.execute('UPDATE writing_directions SET name=?, description=?, style=?, keywords=?, extra_prompt=? WHERE id=?',
                       (data['name'], data['description'], data['style'], data['keywords'], data['extra_prompt'], wd['id']))
            self.refresh()

    def _delete_direction(self, wd_id):
        if QMessageBox.question(self, '确认', '删除此写作方向？') == QMessageBox.StandardButton.Yes:
            DB.execute('DELETE FROM writing_directions WHERE id=?', (wd_id,))
            self.refresh()


class WritingDirectionDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('写作方向')
        self.setFixedSize(520, 500)
        self.setStyleSheet('QDialog{background:#161b22;}')
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel('预设名称:'))
        self._name = QLineEdit(data['name'] if data else '')
        lay.addWidget(self._name)
        lay.addWidget(QLabel('描述:'))
        self._desc = QLineEdit(data.get('description', '') if data else '')
        lay.addWidget(self._desc)
        lay.addWidget(QLabel('写作风格:'))
        self._style = QLineEdit(data.get('style', '') if data else '')
        self._style.setPlaceholderText('如: 暗示性、大胆、引人入胜')
        lay.addWidget(self._style)
        lay.addWidget(QLabel('关键词 (空格分隔):'))
        self._keywords = QLineEdit(data.get('keywords', '') if data else '')
        self._keywords.setPlaceholderText('如: 福利 成人 私密')
        lay.addWidget(self._keywords)
        lay.addWidget(QLabel('额外提示词:'))
        self._extra = QTextEdit()
        self._extra.setPlainText(data.get('extra_prompt', '') if data else '')
        self._extra.setFixedHeight(120)
        self._extra.setPlaceholderText('给AI的额外写作指导...')
        lay.addWidget(self._extra)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self):
        return {'name': self._name.text().strip(), 'description': self._desc.text().strip(),
                'style': self._style.text().strip(), 'keywords': self._keywords.text().strip(),
                'extra_prompt': self._extra.toPlainText().strip()}


# =================== 素材采集页面 ===================
class MediaCollectPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        hdr = QHBoxLayout()
        tv = QVBoxLayout()
        t = QLabel('素材采集')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('从网站、Telegram 频道、RSS 订阅自动采集素材到素材库')
        sub.setStyleSheet('color:#8b949e;')
        tv.addWidget(t)
        tv.addWidget(sub)
        hdr.addLayout(tv, 1)
        log_btn = QPushButton('📋 采集日志')
        new_btn = QPushButton('+ 新建规则')
        new_btn.setObjectName('primary_btn')
        new_btn.clicked.connect(self._new_collect_rule)
        hdr.addWidget(log_btn)
        hdr.addWidget(new_btn)
        lay.addLayout(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._list_lay = QVBoxLayout(self._container)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._container)
        lay.addWidget(self._scroll)

    def refresh(self):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        empty = QLabel('暂无采集规则，点击「新建规则」开始')
        empty.setStyleSheet('color:#8b949e;')
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setMinimumHeight(200)
        self._list_lay.addWidget(empty)

    def _new_collect_rule(self):
        QMessageBox.information(self, '素材采集', '支持从以下来源采集:\n\n• Telegram 频道/群组\n• RSS 订阅链接\n• 自定义网页 URL\n\n(此功能开发中...)')


# =================== 群发页面 ===================
class BroadcastPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        hdr = QHBoxLayout()
        tv = QVBoxLayout()
        t = QLabel('群发')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('向多个群组批量发送素材')
        sub.setStyleSheet('color:#8b949e;')
        tv.addWidget(t)
        tv.addWidget(sub)
        hdr.addLayout(tv, 1)
        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(self.refresh)
        new_btn = QPushButton('+ 新建规则')
        new_btn.setObjectName('primary_btn')
        new_btn.clicked.connect(self._new_rule)
        hdr.addWidget(refresh_btn)
        hdr.addWidget(new_btn)
        lay.addLayout(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._list_lay = QVBoxLayout(self._container)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._container)
        lay.addWidget(self._scroll)

    def refresh(self):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rules = DB.fetchall('SELECT * FROM broadcast_rules')
        if not rules:
            empty = QLabel('暂无群发规则\n点击「新建规则」创建你的第一个群发任务')
            empty.setStyleSheet('color:#8b949e;')
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(200)
            self._list_lay.addWidget(empty)

    def _new_rule(self):
        QMessageBox.information(self, '群发规则', '群发功能：\n一次性向多个频道/群组发送相同内容。\n可选择素材文件夹中的文件批量发送。')


# =================== 发布设置页面 ===================
class PublishSettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        t = QLabel('发布设置')
        t.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        sub = QLabel('管理文案尾部链接、封面贴图和标签库')
        sub.setStyleSheet('color:#8b949e;')
        lay.addWidget(t)
        lay.addWidget(sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setSpacing(16)

        # 文案尾部链接
        links_card = QFrame()
        links_card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        links_lay = QVBoxLayout(links_card)
        links_hdr = QHBoxLayout()
        links_title = QLabel('🔗  文案尾部链接')
        links_title.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
        links_sub = QLabel('发布时自动添加到文案末尾')
        links_sub.setStyleSheet('color:#8b949e;font-size:12px;')
        self._links_count = QLabel('0 个链接')
        self._links_count.setStyleSheet('color:#d29922;background:#2d2000;border-radius:10px;padding:2px 8px;font-size:11px;')
        links_hdr.addWidget(links_title)
        links_hdr.addWidget(links_sub)
        links_hdr.addStretch()
        links_hdr.addWidget(self._links_count)
        links_lay.addLayout(links_hdr)

        self._links_container = QVBoxLayout()
        links_lay.addLayout(self._links_container)

        links_btns = QHBoxLayout()
        add_link_btn = QPushButton('+ 添加链接')
        add_link_btn.clicked.connect(self._add_link)
        save_links_btn = QPushButton('💾 保存')
        save_links_btn.setObjectName('primary_btn')
        save_links_btn.clicked.connect(self._save_links)
        links_btns.addWidget(add_link_btn)
        links_btns.addWidget(save_links_btn)
        links_btns.addStretch()
        links_lay.addLayout(links_btns)
        content_lay.addWidget(links_card)

        # 封面贴图 + 标签库
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # 封面贴图
        sticker_card = QFrame()
        sticker_card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        sticker_lay = QVBoxLayout(sticker_card)
        sticker_hdr = QHBoxLayout()
        sticker_title = QLabel('🖼️  封面贴图')
        sticker_title.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
        self._sticker_count = QLabel('0 个')
        self._sticker_count.setStyleSheet('color:#d29922;background:#2d2000;border-radius:10px;padding:2px 8px;font-size:11px;')
        sticker_hdr.addWidget(sticker_title)
        sticker_hdr.addStretch()
        sticker_hdr.addWidget(self._sticker_count)
        sticker_lay.addLayout(sticker_hdr)

        sticker_sub = QLabel('封面随机叠加贴图素材')
        sticker_sub.setStyleSheet('color:#8b949e;font-size:12px;')
        sticker_lay.addWidget(sticker_sub)

        add_sticker_btn = QPushButton('+ 添加')
        add_sticker_btn.clicked.connect(self._add_sticker)
        sticker_lay.addWidget(add_sticker_btn)
        sticker_lay.addStretch()

        hint = QLabel('PNG/WebP 支持透明背景，在任务配置中设置叠加数量')
        hint.setStyleSheet('color:#8b949e;font-size:11px;')
        hint.setWordWrap(True)
        sticker_lay.addWidget(hint)
        bottom_row.addWidget(sticker_card)

        # 标签库
        tag_card = QFrame()
        tag_card.setStyleSheet('QFrame{background:#161b22;border:1px solid #30363d;border-radius:8px;}')
        tag_lay = QVBoxLayout(tag_card)
        tag_hdr = QHBoxLayout()
        tag_title = QLabel('🏷️  标签库')
        tag_title.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
        self._tag_count = QLabel('0 个')
        self._tag_count.setStyleSheet('color:#d29922;background:#2d2000;border-radius:10px;padding:2px 8px;font-size:11px;')
        tag_hdr.addWidget(tag_title)
        tag_hdr.addStretch()
        tag_hdr.addWidget(self._tag_count)
        tag_lay.addLayout(tag_hdr)

        tag_sub = QLabel('发布时随机选取5个标签')
        tag_sub.setStyleSheet('color:#8b949e;font-size:12px;')
        tag_lay.addWidget(tag_sub)

        tag_row = QHBoxLayout()
        self._tag_input = QLineEdit()
        self._tag_input.setPlaceholderText('输入标签，空格分隔可批量添加（如 #驾货 #极品 #巨卖）')
        tag_row.addWidget(self._tag_input, 1)
        add_tag_btn = QPushButton('+ 添加')
        add_tag_btn.setObjectName('primary_btn')
        add_tag_btn.clicked.connect(self._add_tags)
        tag_row.addWidget(add_tag_btn)
        tag_lay.addLayout(tag_row)

        self._tag_list = QListWidget()
        self._tag_list.setFixedHeight(120)
        tag_lay.addWidget(self._tag_list)

        tag_ai_hint = QLabel('标签库为空，将使用AI生成的标签')
        tag_ai_hint.setStyleSheet('color:#d29922;font-size:11px;')
        tag_lay.addWidget(tag_ai_hint)

        save_tags_btn = QPushButton('💾 保存标签库')
        save_tags_btn.setObjectName('primary_btn')
        save_tags_btn.clicked.connect(self._save_tags)
        tag_lay.addWidget(save_tags_btn)

        bottom_row.addWidget(tag_card)
        content_lay.addLayout(bottom_row)
        content_lay.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)

        self._link_items = []

    def _load_settings(self):
        pub = DB.fetchone('SELECT * FROM publish_settings WHERE id=1')
        if not pub:
            return

        links = json.loads(pub.get('footer_links', '[]'))
        for link in links:
            self._add_link_item(link.get('text', ''), link.get('url', ''))
        self._links_count.setText(f'{len(links)} 个链接')

        tags = json.loads(pub.get('tag_library', '[]'))
        for tag in tags:
            self._tag_list.addItem(tag)
        self._tag_count.setText(f'{len(tags)} 个')

    def _add_link(self):
        self._add_link_item('', '')

    def _add_link_item(self, text, url):
        row = QHBoxLayout()
        text_input = QLineEdit(text)
        text_input.setPlaceholderText('显示文字')
        url_input = QLineEdit(url)
        url_input.setPlaceholderText('https://t.me/...')
        del_btn = QPushButton('🗑️')
        del_btn.setObjectName('icon_btn')
        del_btn.setStyleSheet('color:#da3633;')

        item = (text_input, url_input)
        self._link_items.append(item)

        def remove():
            self._link_items.remove(item)
            widget_to_remove = text_input.parent()
            for i in range(row.count()):
                w = row.itemAt(i).widget()
                if w:
                    w.deleteLater()

        del_btn.clicked.connect(remove)
        row.addWidget(text_input, 1)
        row.addWidget(url_input, 2)
        row.addWidget(del_btn)
        self._links_container.addLayout(row)

    def _save_links(self):
        links = []
        for text_input, url_input in self._link_items:
            t = text_input.text().strip()
            u = url_input.text().strip()
            if t or u:
                links.append({'text': t, 'url': u})
        DB.execute('UPDATE publish_settings SET footer_links=? WHERE id=1', (json.dumps(links),))
        self._links_count.setText(f'{len(links)} 个链接')
        QMessageBox.information(self, '已保存', '尾部链接已保存')

    def _add_sticker(self):
        files, _ = QFileDialog.getOpenFileNames(self, '选择贴图文件', '', 'Images (*.png *.webp *.jpg)')
        if files:
            pub = DB.fetchone('SELECT sticker_paths FROM publish_settings WHERE id=1')
            existing = json.loads(pub.get('sticker_paths', '[]')) if pub else []
            existing.extend(files)
            DB.execute('UPDATE publish_settings SET sticker_paths=? WHERE id=1', (json.dumps(existing),))
            self._sticker_count.setText(f'{len(existing)} 个')

    def _add_tags(self):
        text = self._tag_input.text().strip()
        if not text:
            return
        tags = [t.strip().lstrip('#') for t in text.split() if t.strip()]
        for tag in tags:
            if tag:
                self._tag_list.addItem(f'#{tag}')
        self._tag_input.clear()
        self._tag_count.setText(f'{self._tag_list.count()} 个')

    def _save_tags(self):
        tags = [self._tag_list.item(i).text() for i in range(self._tag_list.count())]
        DB.execute('UPDATE publish_settings SET tag_library=? WHERE id=1', (json.dumps(tags),))
        self._tag_count.setText(f'{len(tags)} 个')
        QMessageBox.information(self, '已保存', '标签库已保存')
