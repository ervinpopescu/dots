#!/bin/python

import sys

from PyQt5 import QtCore, QtWebEngineWidgets, QtWidgets


def loadCSS(view, path, name):
    path = QtCore.QFile(path)
    if not path.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
        return
    css = path.readAll().data().decode("utf-8")
    SCRIPT = """
    (function() {
    css = document.createElement('style');
    css.type = 'text/css';
    css.id = "%s";
    document.head.appendChild(css);
    css.innerText = `%s`;
    })()
    """ % (
        name,
        css,
    )

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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    view = QtWebEngineWidgets.QWebEngineView()
    settings = view.settings()
    showScrollBars = settings.ShowScrollBars
    settings.setAttribute(showScrollBars, False)
    view.load(QtCore.QUrl(sys.argv[1]))
    loadCSS(
        view,
        "/home/ervin/.config/md-preview/markdown.css",
        "script1",
    )
    view.show()
    sys.exit(app.exec_())
