#!/bin/python

import argparse
import os
import sys
from PyQt5 import QtCore, QtWebEngineWidgets, QtWidgets


def loadCSS(view, path, name):
    path = QtCore.QFile(path)
    if not path.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
        return
    css = path.readAll().data().decode("utf-8")
    SCRIPT = f"""
    (function() {{
    css = document.createElement('style');
    css.type = 'text/css';
    css.id = "{name}";
    document.head.appendChild(css);
    css.innerText = String.raw `{css}`;
    }})()"""
    script = QtWebEngineWidgets.QWebEngineScript()
    view.page().runJavaScript(
        SCRIPT, QtWebEngineWidgets.QWebEngineScript.ApplicationWorld
    )
    script.setName(name)
    script.setSourceCode(SCRIPT)
    script.setInjectionPoint(QtWebEngineWidgets.QWebEngineScript.DocumentReady)
    script.setRunsOnSubFrames(True)
    script.setWorldId(QtWebEngineWidgets.QWebEngineScript.ApplicationWorld)
    view.page().scripts().insert(script)


def run(view, app, to_open):
    view.load(QtCore.QUrl(to_open))
    loadCSS(
        view,
        "/home/ervin/.config/md-preview/markdown.css",
        "script1",
    )
    view.show()
    sys.exit(app.exec_())


def main():
    parser = argparse.ArgumentParser(description="open url/file/text in qt window")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-u",
        "--url",
        default=None,
        help="url to open in qt window",
    )
    group.add_argument(
        "-f",
        "--file",
        dest="file",
        default=None,
        help="file to open in qt window",
    )
    args = parser.parse_args()
    arg_values = [i for i in vars(args).values() if i is not None]
    app = QtWidgets.QApplication(arg_values)
    view = QtWebEngineWidgets.QWebEngineView()
    settings = view.settings()
    showScrollBars = settings.ShowScrollBars
    settings.setAttribute(showScrollBars, False)
    if args.url is not None:
        run(view, app, args.url)
    elif args.file is not None:
        run(
            view,
            app,
            "file://" + os.path.join(os.path.abspath(os.path.curdir), args.file),
        )
    parser.print_help()


if __name__ == "__main__":
    main()
