#!/usr/bin/env python3
import argparse
import os
import sys
import threading
from pathlib import Path

try:
    from PyQt5 import QtCore
    from PyQt5.QtGui import QColor
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
except ImportError:
    print("Error: PyQt5 not found. Please install it with 'pip install PyQt5' or via your package manager.", file=sys.stderr)
    sys.exit(1)

try:
    import inotify.adapters
    import inotify.constants
    HAS_INOTIFY = True
except ImportError:
    HAS_INOTIFY = False


def parseArgs():
    parser = argparse.ArgumentParser(description="Display a pop-up report message.")
    parser.add_argument("-m", "--message", type=str, required=True, help="Message to display")
    parser.add_argument("-t", "--topic", type=str, default=None, help="Topic of the message")
    parser.add_argument("-d", "--duration", type=int, default=450, help="Duration in milliseconds")
    parser.add_argument("-o", "--override-style", nargs="+", default=[], help="Override CSS styles")
    return parser.parse_args()


def messageUpdate(topicPath, label):
    if not HAS_INOTIFY:
        return
        
    subscribe = inotify.adapters.Inotify()
    subscribe.add_watch(str(topicPath), inotify.constants.IN_CLOSE_WRITE)

    for event in subscribe.event_gen(yield_nones=False):
        if event[1] == ["IN_CLOSE_WRITE"]:
            if topicPath.exists():
                label.setText(topicPath.read_text())
        else:
            break


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.X11BypassWindowManagerHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def showEvent(self, event):
        self.centerWin()

    def centerWin(self):
        screen = QApplication.primaryScreen().size()
        popup_size = self.geometry()
        x = (screen.width() - popup_size.width()) // 2
        y = (screen.height() - popup_size.height()) // 2
        self.move(x, y)

class TimedPopup(QLabel):
    def __init__(self, duration, topicPath, mainwin, parent=None):
        super().__init__(parent=parent)
        self.timer = QtCore.QTimer()
        self.topicPath = topicPath
        self.duration = duration
        self.mainwin = mainwin

    def startTimer(self):
        self.timer.timeout.connect(self.close)
        self.timer.setInterval(self.duration)
        self.timer.start()

    def paintEvent(self, event):
        self.startTimer()
        self.mainwin.centerWin()
        super().paintEvent(event)

    def closeEvent(self, event):
        if self.topicPath and self.topicPath.exists():
            try:
                self.topicPath.unlink()
            except OSError:
                pass
        self.mainwin.close()
        self.deleteLater()


def main():
    configPath = Path.home() / ".config" / "pop_report"
    userConfig = configPath / "style.qss"

    args = parseArgs()
    message = args.message
    duration = args.duration
    styleO = args.override_style
    extraStyle = "".join(f"{option};\n" for option in styleO)
    
    topicPath = None
    if args.topic:
        topicPath = Path(f"/tmp/report_{args.topic}")
        if topicPath.exists():
            topicPath.write_text(message)
            sys.exit()
        topicPath.write_text(message)

    app = QApplication(sys.argv)
    window = MainWindow()
    popup = TimedPopup(duration, topicPath, window)
    popup.setAlignment(QtCore.Qt.AlignCenter)
    popup.setText(message)
    window.setCentralWidget(popup)

    configPath.mkdir(parents=True, exist_ok=True)
    if not userConfig.exists():
        defaultStyle = (
            "border: 5px solid #ffffffff;\n"
            "background-color: #dd000000;\n"
            "color: #ffffffff;\n"
            "font-family: Monospace;\n"
            "font-size: 70px;\n"
            "padding: 20px;\n"
        )
        userConfig.write_text(defaultStyle)
    
    popup.setStyleSheet(userConfig.read_text() + extraStyle)
    popup.ensurePolished()

    if args.topic and HAS_INOTIFY:
        waitEdit = threading.Thread(target=messageUpdate, args=(topicPath, popup), daemon=True)
        waitEdit.start()

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
