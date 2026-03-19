"""
现代深色主题样式
"""

DARK_THEME = """
/* 全局样式 */
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
    font-size: 13px;
}

/* 左侧导航栏 */
QWidget#sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}

/* 导航按钮 */
QPushButton#navBtn {
    background-color: transparent;
    color: #8b949e;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
}
QPushButton#navBtn:hover {
    background-color: #21262d;
    color: #e6edf3;
}
QPushButton#navBtn:checked {
    background-color: #1f6feb22;
    color: #58a6ff;
    border-left: 3px solid #1f6feb;
}

/* 内容区域 */
QWidget#contentArea {
    background-color: #0d1117;
}

/* 卡片样式 */
QFrame#card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px;
}

/* 按钮样式 */
QPushButton {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 13px;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}
QPushButton:pressed {
    background-color: #1f2937;
}
QPushButton:disabled {
    color: #484f58;
    background-color: #161b22;
    border-color: #21262d;
}

/* 主要操作按钮 */
QPushButton#primaryBtn {
    background-color: #1f6feb;
    color: #ffffff;
    border: 1px solid #1f6feb;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #388bfd;
    border-color: #388bfd;
}
QPushButton#primaryBtn:pressed {
    background-color: #1158c7;
}

/* 成功按钮 */
QPushButton#successBtn {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
    font-weight: 600;
}
QPushButton#successBtn:hover {
    background-color: #2ea043;
}

/* 危险按钮 */
QPushButton#dangerBtn {
    background-color: #da3633;
    color: #ffffff;
    border: 1px solid #f85149;
}
QPushButton#dangerBtn:hover {
    background-color: #f85149;
}

/* 输入框 */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #1f6feb44;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #1f6feb;
    outline: none;
}
QLineEdit::placeholder {
    color: #484f58;
}

/* 下拉框 */
QComboBox {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    min-width: 120px;
}
QComboBox:hover {
    border-color: #8b949e;
}
QComboBox:focus {
    border-color: #1f6feb;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8b949e;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #1c2128;
    border: 1px solid #30363d;
    border-radius: 6px;
    selection-background-color: #1f6feb44;
    color: #e6edf3;
    padding: 4px;
}

/* 数字输入框 */
QSpinBox, QDoubleSpinBox {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #1f6feb;
}

/* 时间选择框 */
QTimeEdit, QDateEdit, QDateTimeEdit {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
}

/* 复选框 */
QCheckBox {
    color: #e6edf3;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #30363d;
    border-radius: 3px;
    background-color: #161b22;
}
QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #1f6feb;
}
QCheckBox::indicator:hover {
    border-color: #8b949e;
}

/* 单选按钮 */
QRadioButton {
    color: #e6edf3;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #30363d;
    border-radius: 8px;
    background-color: #161b22;
}
QRadioButton::indicator:checked {
    background-color: #1f6feb;
    border-color: #1f6feb;
}

/* 列表控件 */
QListWidget {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    alternate-background-color: #1c2128;
    outline: none;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    margin: 1px 4px;
    color: #e6edf3;
}
QListWidget::item:selected {
    background-color: #1f6feb33;
    color: #58a6ff;
}
QListWidget::item:hover {
    background-color: #21262d;
}

/* 表格 */
QTableWidget {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    gridline-color: #21262d;
    alternate-background-color: #1c2128;
    outline: none;
}
QTableWidget::item {
    padding: 8px 12px;
    color: #e6edf3;
}
QTableWidget::item:selected {
    background-color: #1f6feb33;
    color: #58a6ff;
}
QHeaderView::section {
    background-color: #21262d;
    color: #8b949e;
    border: none;
    border-bottom: 1px solid #30363d;
    padding: 8px 12px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}
QHeaderView::section:first {
    border-top-left-radius: 8px;
}

/* 分组框 */
QGroupBox {
    background-color: transparent;
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-top: 20px;
    padding-top: 12px;
    font-weight: 600;
    color: #8b949e;
    font-size: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    left: 12px;
    background-color: #0d1117;
    color: #8b949e;
}

/* 标签页 */
QTabWidget::pane {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    border-top-left-radius: 0;
}
QTabBar::tab {
    background-color: #161b22;
    color: #8b949e;
    border: 1px solid #30363d;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 2px;
    font-size: 13px;
}
QTabBar::tab:selected {
    background-color: #0d1117;
    color: #e6edf3;
    border-bottom: 1px solid #0d1117;
}
QTabBar::tab:hover:!selected {
    background-color: #21262d;
    color: #e6edf3;
}

/* 滚动条 */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #30363d;
    border-radius: 4px;
    min-height: 40px;
}
QScrollBar::handle:vertical:hover {
    background-color: #484f58;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background-color: #30363d;
    border-radius: 4px;
    min-width: 40px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #484f58;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* 进度条 */
QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #e6edf3;
    font-size: 11px;
    min-height: 8px;
    max-height: 8px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1f6feb, stop:1 #388bfd);
    border-radius: 4px;
}

/* 工具提示 */
QToolTip {
    background-color: #1c2128;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

/* 菜单 */
QMenu {
    background-color: #1c2128;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 16px;
    border-radius: 4px;
    color: #e6edf3;
}
QMenu::item:selected {
    background-color: #21262d;
}
QMenu::separator {
    height: 1px;
    background-color: #30363d;
    margin: 4px 0;
}

/* 状态栏 */
QStatusBar {
    background-color: #161b22;
    color: #8b949e;
    border-top: 1px solid #30363d;
    font-size: 12px;
    padding: 2px 8px;
}

/* 标签 */
QLabel {
    color: #e6edf3;
    background: transparent;
}
QLabel#titleLabel {
    font-size: 20px;
    font-weight: 700;
    color: #e6edf3;
}
QLabel#subtitleLabel {
    font-size: 12px;
    color: #8b949e;
}
QLabel#sectionTitle {
    font-size: 14px;
    font-weight: 600;
    color: #e6edf3;
    padding-bottom: 4px;
    border-bottom: 1px solid #21262d;
}
QLabel#statValue {
    font-size: 28px;
    font-weight: 700;
    color: #58a6ff;
}
QLabel#statLabel {
    font-size: 11px;
    color: #8b949e;
    text-transform: uppercase;
}
QLabel#badge {
    background-color: #1f6feb22;
    color: #58a6ff;
    border: 1px solid #1f6feb44;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}
QLabel#badgeSuccess {
    background-color: #23863622;
    color: #3fb950;
    border: 1px solid #23863644;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}
QLabel#badgeWarning {
    background-color: #9e6a0322;
    color: #d29922;
    border: 1px solid #9e6a0344;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}
QLabel#badgeDanger {
    background-color: #da363322;
    color: #f85149;
    border: 1px solid #da363344;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* 分割器 */
QSplitter::handle {
    background-color: #30363d;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}

/* 滑块 */
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background-color: #21262d;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background-color: #1f6feb;
    border: none;
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}
QSlider::sub-page:horizontal {
    background-color: #1f6feb;
    border-radius: 2px;
}

/* 对话框 */
QDialog {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
}

/* 消息框 */
QMessageBox {
    background-color: #161b22;
}
"""


def apply_theme(app):
    """应用主题到应用程序"""
    app.setStyleSheet(DARK_THEME)
