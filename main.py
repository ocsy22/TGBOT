"""
Telegram Auto Publisher - 主入口
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QBrush

from core.database import init_db
from ui.main_window import MainWindow


def create_splash():
    """创建启动画面"""
    pix = QPixmap(480, 300)
    pix.fill(QColor('#0d1117'))

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 背景渐变效果
    from PyQt6.QtGui import QLinearGradient
    gradient = QLinearGradient(0, 0, 480, 300)
    gradient.setColorAt(0, QColor('#0d1117'))
    gradient.setColorAt(1, QColor('#161b22'))
    painter.fillRect(0, 0, 480, 300, QBrush(gradient))

    # 边框
    from PyQt6.QtGui import QPen
    painter.setPen(QPen(QColor('#30363d'), 1))
    painter.drawRect(0, 0, 479, 299)

    # 图标
    painter.setPen(QPen(QColor('#1f6feb')))
    painter.setFont(QFont('Segoe UI', 48))
    painter.drawText(0, 50, 480, 80, Qt.AlignmentFlag.AlignCenter, '✈️')

    # 标题
    painter.setPen(QPen(QColor('#e6edf3')))
    painter.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
    painter.drawText(0, 130, 480, 40, Qt.AlignmentFlag.AlignCenter, 'Telegram Auto Publisher')

    # 副标题
    painter.setPen(QPen(QColor('#8b949e')))
    painter.setFont(QFont('Segoe UI', 11))
    painter.drawText(0, 175, 480, 30, Qt.AlignmentFlag.AlignCenter, 'Auto Video System v1.2.0')

    # 加载提示
    painter.setFont(QFont('Segoe UI', 10))
    painter.drawText(0, 250, 480, 30, Qt.AlignmentFlag.AlignCenter, '正在加载...')

    painter.end()
    return pix


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Telegram Auto Publisher')
    app.setApplicationVersion('1.2.0')

    # 高DPI支持
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 显示启动画面
    splash_pix = create_splash()
    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    # 初始化数据库
    splash.showMessage('  初始化数据库...', Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                       QColor('#8b949e'))
    app.processEvents()
    init_db()

    splash.showMessage('  加载界面...', Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                       QColor('#8b949e'))
    app.processEvents()

    # 创建主窗口
    window = MainWindow()

    # 启动自动发布调度器
    from core.scheduler import get_scheduler
    scheduler = get_scheduler()
    scheduler.start()

    # 关闭启动画面，显示主窗口
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
