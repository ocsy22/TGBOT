"""
主题和样式定义
"""

# 深色主题颜色
COLORS = {
    'bg_dark': '#0d1117',
    'bg_mid': '#161b22',
    'bg_card': '#1c2128',
    'bg_hover': '#21262d',
    'bg_selected': '#1f6feb',
    'accent_blue': '#1f6feb',
    'accent_blue_hover': '#388bfd',
    'accent_green': '#2ea043',
    'accent_red': '#da3633',
    'accent_orange': '#d29922',
    'text_primary': '#e6edf3',
    'text_secondary': '#8b949e',
    'text_disabled': '#484f58',
    'border': '#30363d',
    'border_focus': '#1f6feb',
    'scrollbar': '#30363d',
    'success': '#2ea043',
    'warning': '#d29922',
    'error': '#da3633',
    'info': '#1f6feb',
    'tag_blue': '#1f3a5f',
    'tag_green': '#1a3a2a',
    'tag_red': '#3d1a1a',
    'sidebar_width': '180px',
}

MAIN_STYLE = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'Microsoft YaHei UI', '微软雅黑', sans-serif;
    font-size: 13px;
}

/* 侧边栏 */
#sidebar {
    background-color: #0d1117;
    border-right: 1px solid #21262d;
    min-width: 180px;
    max-width: 180px;
}

#logo_area {
    padding: 16px 12px;
    border-bottom: 1px solid #21262d;
}

#logo_title {
    color: #e6edf3;
    font-size: 14px;
    font-weight: bold;
}

#logo_sub {
    color: #8b949e;
    font-size: 10px;
}

/* 导航按钮 */
#nav_btn {
    background: transparent;
    border: none;
    color: #8b949e;
    text-align: left;
    padding: 9px 12px 9px 16px;
    border-radius: 6px;
    font-size: 13px;
    margin: 1px 6px;
}

#nav_btn:hover {
    background-color: #21262d;
    color: #e6edf3;
}

#nav_btn[active="true"] {
    background-color: #21262d;
    color: #e6edf3;
    border-left: 2px solid #1f6feb;
}

/* 内容区 */
#content_area {
    background-color: #0d1117;
}

/* 页面标题 */
#page_title {
    color: #e6edf3;
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 2px;
}

#page_subtitle {
    color: #8b949e;
    font-size: 12px;
}

/* 卡片 */
QFrame#card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
}

/* 按钮 */
QPushButton {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}

QPushButton:pressed {
    background-color: #161b22;
}

QPushButton#primary_btn {
    background-color: #1f6feb;
    color: white;
    border: 1px solid #1f6feb;
    padding: 7px 16px;
    font-weight: 500;
}

QPushButton#primary_btn:hover {
    background-color: #388bfd;
    border-color: #388bfd;
}

QPushButton#danger_btn {
    background-color: transparent;
    color: #da3633;
    border: 1px solid #da3633;
}

QPushButton#danger_btn:hover {
    background-color: #3d1a1a;
}

QPushButton#success_btn {
    background-color: #2ea043;
    color: white;
    border: 1px solid #2ea043;
}

QPushButton#success_btn:hover {
    background-color: #3fb950;
}

QPushButton#icon_btn {
    background: transparent;
    border: none;
    color: #8b949e;
    padding: 4px;
    border-radius: 4px;
}

QPushButton#icon_btn:hover {
    background-color: #21262d;
    color: #e6edf3;
}

/* 输入框 */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: #1f6feb;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #1f6feb;
    outline: none;
}

QLineEdit:disabled {
    color: #484f58;
    background-color: #0d1117;
}

/* 下拉框 */
QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    padding: 6px 10px;
    padding-right: 24px;
}

QComboBox:hover {
    border-color: #8b949e;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8b949e;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    selection-background-color: #21262d;
    outline: none;
}

/* 标签 */
QLabel {
    color: #e6edf3;
    background: transparent;
}

QLabel#label_secondary {
    color: #8b949e;
    font-size: 12px;
}

/* 表格 */
QTableWidget {
    background-color: #0d1117;
    border: none;
    gridline-color: #21262d;
    color: #e6edf3;
    alternate-background-color: #0d1117;
    selection-background-color: #1f3a5f;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #21262d;
}

QTableWidget::item:selected {
    background-color: #1f3a5f;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    border: none;
    border-bottom: 1px solid #30363d;
    padding: 8px;
    font-size: 12px;
}

/* 列表 */
QListWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    alternate-background-color: #161b22;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #21262d;
}

QListWidget::item:selected {
    background-color: #1f3a5f;
    color: #e6edf3;
}

/* 滚动条 */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #484f58;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
}

QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 3px;
}

/* 进度条 */
QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #1f6feb;
    border-radius: 4px;
}

/* 复选框 */
QCheckBox {
    color: #e6edf3;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 3px;
    border: 1px solid #30363d;
    background: #0d1117;
}

QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #1f6feb;
    image: none;
}

QCheckBox::indicator:hover {
    border-color: #8b949e;
}

/* 单选框 */
QRadioButton {
    color: #e6edf3;
    spacing: 6px;
}

QRadioButton::indicator {
    width: 15px;
    height: 15px;
    border-radius: 7px;
    border: 1px solid #30363d;
    background: #0d1117;
}

QRadioButton::indicator:checked {
    background-color: #1f6feb;
    border-color: #1f6feb;
}

/* SpinBox */
QSpinBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    padding: 6px;
}

QSpinBox:focus {
    border-color: #1f6feb;
}

QSpinBox::up-button, QSpinBox::down-button {
    background: #21262d;
    border: none;
    width: 16px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #30363d;
}

/* 标签页 */
QTabWidget::pane {
    border: 1px solid #30363d;
    border-radius: 6px;
    background-color: #161b22;
}

QTabBar::tab {
    background: transparent;
    color: #8b949e;
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
}

QTabBar::tab:selected {
    color: #e6edf3;
    border-bottom: 2px solid #1f6feb;
}

QTabBar::tab:hover {
    color: #e6edf3;
}

/* 工具提示 */
QToolTip {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
}

/* 菜单 */
QMenu {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 4px;
    color: #e6edf3;
}

QMenu::item {
    padding: 6px 16px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #21262d;
}

QMenu::separator {
    height: 1px;
    background-color: #30363d;
    margin: 4px 0;
}

/* 对话框 */
QDialog {
    background-color: #161b22;
}

/* 分隔线 */
QFrame[frameShape="4"] {
    color: #30363d;
}

/* 状态标签 */
QLabel#status_running {
    color: #2ea043;
    background-color: #1a3a2a;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
}

QLabel#status_pending {
    color: #d29922;
    background-color: #2d2000;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
}

QLabel#status_failed {
    color: #da3633;
    background-color: #3d1a1a;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
}

QLabel#status_done {
    color: #8b949e;
    background-color: #21262d;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
}

/* 版本号 */
#version_label {
    color: #484f58;
    font-size: 10px;
}
"""
