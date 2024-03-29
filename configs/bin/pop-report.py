#!/bin/env python3
import argparse
import os
import sys
import threading

import inotify.adapters
import inotify.constants
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--message",
        type=str,
        required=True,
        help="Message to display in a pop-up",
    )
    parser.add_argument(
        "-t",
        "--topic",
        type=str,
        default=None,
        help="Topic of the message. "
        "New messages with the same topic "
        "will override the message in an already open window if available",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=int,
        default=450,
        help="Popup window duration in milliseconds (Default: 450)",
    )
    parser.add_argument(
        "-o",
        "--override-style",
        nargs="+",
        default=[],
        help="Override or add style options. "
        "Can take multiple arguments. Example: "
        'pop_report -m message -o "background-color: #ff555555" "font-family: CascadiaCode"',
    )
    return parser.parse_args()


def messageUpdate(topicPath, label):
    subscribe = inotify.adapters.Inotify()
    subscribe.add_watch(topicPath, inotify.constants.IN_CLOSE_WRITE)

    for event in subscribe.event_gen(yield_nones=False):
        if event[1] == ["IN_CLOSE_WRITE"]:
            with open(topicPath, "r") as topicFile:
                label.setText(topicFile.read())
        else:
            break


class MainWindow(QMainWindow):
    # Auto-closing window
    def __init__(self, parent=None):
        # Define window stuff
        super(MainWindow, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.X11BypassWindowManagerHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def showEvent(self, event):
        self.centerWin()

    def centerWin(self):
        # Center window once it shows itself
        screenWidth = QApplication.primaryScreen().size().width()
        screenHeight = QApplication.primaryScreen().size().height()
        popupHeight = self.geometry().height()
        popupWidth = self.geometry().width()
        popupXpos = int((screenWidth - popupWidth) / 2)
        popupYpos = int((screenHeight - popupHeight) / 2)
        self.move(popupXpos, popupYpos)

    def closeEvent(self, event):
        # Delete object
        self.deleteLater()


class TimedPopup(QLabel):
    def __init__(self, duration, topicPath, mainwin, parent=None):
        super(TimedPopup, self).__init__(parent=parent)
        self.timer = QtCore.QTimer()
        self.topicPath = topicPath
        self.duration = duration
        self.mainwin = mainwin

    def startTimer(self):
        self.timer.timeout.connect(self.close)
        self.timer.setInterval(self.duration)
        self.timer.start()

    def paintEvent(self, event):
        print("Reported message")
        self.startTimer()
        self.mainwin.centerWin()
        QLabel.paintEvent(self, event)

    def closeEvent(self, event):
        # Delete topic file
        if self.topicPath != None and os.path.isfile(self.topicPath):
            os.remove(self.topicPath)
        # Delete object
        self.mainwin.close()
        self.deleteLater()


def main():
    # Path to stylesheet file
    configPath = os.path.expanduser("~/.config/pop_report/")
    userConfig = f"{configPath}style.qss"

    # Parse command line arguments and declare variables
    args = parseArgs()
    message = args.message
    duration = args.duration
    styleO = args.override_style
    extraStyle = "".join(option + ";\n" for option in styleO)
    topicPath = None

    # Check if there's a window already for current topic
    topic = args.topic
    if topic:
        topicPath = os.path.expanduser(str(f"/tmp/report_{topic}"))
        print(topicPath)
        if os.path.isfile(topicPath):
            print("Topic already has a window, will rewrite contents")
            with open(topicPath, "w") as topicFile:
                topicFile.write(message)
            sys.exit()
        with open(topicPath, "w") as topicFile:
            topicFile.write(message)

    app = QApplication(sys.argv)
    window = MainWindow()
    popup = TimedPopup(duration, topicPath, window)
    popup.setAlignment(QtCore.Qt.AlignCenter)
    popup.setText(str(message))
    window.setCentralWidget(popup)

    if not os.path.isdir(configPath):
        os.makedirs(configPath)
    if not os.path.isfile(userConfig):
        # Set the style for the label
        defaultStyle = "border: 5px solid #ffffffff;\nbackground-color: #dd000000;\ncolor: #ffffffff;\nfont-family: Monospace;\nfont-size: 70px;\npadding: 20px;\n"
        with open(userConfig, "w") as userStyleSheet:
            userStyleSheet.write(defaultStyle)
    with open(userConfig, "r") as userStyleSheet:
        popup.setStyleSheet(userStyleSheet.read() + extraStyle)
    popup.ensurePolished()

    # Start watch if topic is set
    if topic:
        waitEdit = threading.Thread(target=messageUpdate, args=(topicPath, popup))
        waitEdit.start()

    # Make the window show itself
    window.show()
    # Run the app
    app.exec()


if __name__ == "__main__":
    main()
