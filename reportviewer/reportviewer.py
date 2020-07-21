#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Report Viewer is python + qt piece of software
External program send list of html files, Viewer shows them
each in own tab and handling excel transformation.
If input files are excel, show "No preview, press Excel" page.
"""

__author__ = "Serge"

import sys
import os
import subprocess
from PyQt4 import QtCore, QtGui, QtWebKit
import HtmlToXlsx
import rv_gui


def standart_file_path(f_path):
    return '/'.join(f_path.split(os.sep))


def save_last_dir(l_dir):
    try:
        with open("last.dir", "w", encoding="utf-8") as f:
            f.write(l_dir)
    except:
        pass


def get_last_dir():
    try:
        with open("last.dir", "r", encoding="utf-8") as f:
            l_dir = f.read()
    except:
        l_dir = ""
    return l_dir


def start_progress(parent):
    """Create Qt Progress dialog and returns it"""
    progress = QtGui.QProgressDialog(parent)
    progress.setCancelButton(None)
    progress.setWindowTitle(u"Обработка")

    progress.show()
    progress.setValue(10)

    # Refresh gui
    app = QtGui.QApplication.instance()
    app.processEvents()

    return progress

# Buttons functions definitions

def excel(gui):
    """Transform html to excel and opens it"""

    mode = gui.file_list[0]
    if mode[0]:
        progress = start_progress(gui)

        cur_i = gui.tabWidget.currentIndex()
        f_path = gui.file_list[cur_i + 1]

        if f_path[1] == "":
            xlsx = HtmlToXlsx.transform(f_path[0], progress=progress, need_password=mode[1])
            f_path[1] = xlsx
        else:
            xlsx = f_path[1]

        progress.setValue(100)
        progress.close()

        if sys.platform == "win32":
            subprocess.Popen(["start", xlsx], shell=True)
        else:
            subprocess.Popen(["libreoffice " + xlsx], shell=True)
    else:
        for f_path in gui.file_list[1:]:
            file = f_path[0]
            if f_path[1] == "":
                xlsx = HtmlToXlsx.transform(file, need_password=mode[1])
                f_path[1] = xlsx


def print_dialog(gui):
    """Open system printing dialog"""

    # Is it dirty?
    children = gui.tabWidget.currentWidget().children()

    for child in children:
        if isinstance(child, QtWebKit.QWebView):
            view = child

    printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
    dialog = QtGui.QPrintDialog(printer)
    if dialog.exec_() != QtGui.QDialog.Accepted:
        return
    view.print_(printer)


def e_mail(gui):
    """Open Outlook if win32 and attach something. Should I zip it?"""
    progress = start_progress(gui)

    cur_i = gui.tabWidget.currentIndex()
    f_path = gui.file_list[cur_i + 1]

    if f_path[1] == "":
        xlsx = HtmlToXlsx.transform(f_path[0], progress)
        f_path[1] = xlsx
    else:
        xlsx = f_path[1]

    progress.setValue(100)
    progress.close()

    if sys.platform == "win32":
        subprocess.call(["start", "outlook.exe", "-a", xlsx], shell=True)


def file_open(gui):
    """Open file and refresh browser"""
    f_path = QtGui.QFileDialog.getOpenFileName(gui, directory=get_last_dir(), caption=u'Открыть файл', filter="*.html")
    if f_path != "":
        save_last_dir(os.path.realpath(os.path.dirname(f_path)))

        for i in range(1, len(gui.file_list)):
            if gui.file_list[i][0] == f_path:
                gui.tabWidget.setCurrentIndex(i - 1)
                break
        else:
            gui.open_file(f_path)
            gui.file_list.append([f_path, ""])
            gui.tabWidget.setCurrentIndex(len(gui.file_list) - 2)


class ControlMainWindow(QtGui.QMainWindow):
    """Wrapper to launch gui with my bindings, controls etc."""
    def __init__(self, parent=None, file_list=[]):
        mode = file_list[0]
        super(ControlMainWindow, self).__init__(parent)
        self.file_list = file_list
        if not mode[0]:
            return
        self.ui = rv_gui.Ui_ReportViewer()
        self.ui.setupUi(self)

        self.ui.excel.clicked.connect(lambda: excel(self))
        self.ui.printer.clicked.connect(lambda: print_dialog(self))
        self.ui.email.clicked.connect(lambda: e_mail(self))
        self.ui.fileopen.clicked.connect(lambda: file_open(self))

        self.tabWidget = QtGui.QTabWidget(self.ui.centralwidget)
        self.tabWidget.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.tabWidget.setTabShape(QtGui.QTabWidget.Rounded)
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.setObjectName("tabWidget")
        self.ui.verticalLayout_2.addWidget(self.tabWidget)

        self.tabWidget.tabCloseRequested.connect(self.close_handler)

        ico_path = os.path.dirname(os.path.realpath(sys.argv[0])) + os.sep + "rep.png"
        self.setWindowIcon(QtGui.QIcon(ico_path))

        for file in self.file_list[1:]:
            self.open_file(file[0])

    def open_file(self, f_path):
        """If we got html then display it, else - display empty.html"""
        if f_path == "":
            f_page = ""
        elif f_path.split(".")[-1] != "html":
            f_page = "empty.html"
        else:
            f_page = f_path

        f_name = os.path.basename(f_path)
        f_name = os.path.splitext(f_name)[0]

        qTab = QtGui.QWidget()

        self.tabWidget.addTab(qTab, (f_name))
        qWebView = QtWebKit.QWebView(qTab)
        verticalLayout = QtGui.QVBoxLayout(qTab)
        verticalLayout.addWidget(qWebView)
        qWebView.setProperty("url", QtCore.QUrl(standart_file_path(f_page)))
        qWebView.setObjectName(f_name)

    def close_handler(self, i):
        """Close tab with dialog"""
        message = QtGui.QMessageBox()
        message.setText(u"Вы уверены, что хотите закрыть вкладку?")
        message.setWindowTitle(u"Внимание")
        message.addButton(QtGui.QPushButton(u'Да'), QtGui.QMessageBox.YesRole)
        message.addButton(QtGui.QPushButton(u'Нет'), QtGui.QMessageBox.NoRole)
        reply = message.exec_()

        if reply == 0:
            self.tabWidget.removeTab(i)
            self.file_list.pop(i + 1)


def start_gui(file_list):
    mode = file_list[0]

    for i in range(1, len(file_list)):
        if file_list[i] != "":
            file_list[i] = [standart_file_path(os.path.realpath(file_list[i])), ""]
    app = QtGui.QApplication(sys.argv)
    mySW = ControlMainWindow(file_list=file_list)
    if mode[0]:
        mySW.show()
        sys.exit(app.exec_())
    else:
        excel(mySW)


if __name__ == "__main__":
    file_list = []
    warning = False
    if not sys.argv[1:]:
        file_list.append((True, False))
    else:
        mode_1 = True if sys.argv[1].lower() == 'true' else False
        if not mode_1 and sys.argv[1].lower() != 'false':
            print("Warning: did you mean one of two modes: true or false?")
            warning = True
        if not sys.argv[2:]:
            file_list.append((mode_1, False))
        else:
            if sys.argv[2].lower() == 'true':
                file_list.append((mode_1, True))
                file_list += sys.argv[3:]
            elif sys.argv[2].lower() == 'false':
                file_list.append((mode_1, False))
                file_list += sys.argv[3:]
            else:
                file_list.append((mode_1, False))
                file_list += sys.argv[2:]
        if not file_list[0][0] and not file_list[1:]:
            print("Warning: empty file_list.")
            warning = True
        if warning:
            print("Usage:")
            print("1) python script.py")
            print("2) python script.py <GUI: true/false> <path_to_html_1> <path_to_html_2>...")
            print("3) python script.py <GUI: true/false> <password: true/false> <path_to_html_1> <path_to_html_2>...")

        try:
            save_last_dir(os.path.realpath(os.path.dirname(file_list[1])))
        except IndexError:
            pass

    # print(file_list)

    start_gui(file_list)
