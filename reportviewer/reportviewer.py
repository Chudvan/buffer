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
import win32com.client
from pywintypes import com_error
from PyQt5 import QtCore, QtGui, QtWebEngineWidgets, QtWidgets
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
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
    progress = QtWidgets.QProgressDialog(parent)
    progress.setCancelButton(None)
    progress.setWindowTitle(u"Обработка")

    progress.show()
    progress.setValue(10)

    # Refresh gui
    app = QtWidgets.QApplication.instance()
    app.processEvents()

    return progress

# Buttons functions definitions


def create_excel_with_progress(gui, path, need_password=False):
    progress = start_progress(gui)
    xlsx, status = HtmlToXlsx.transform(path, progress=progress, need_password=need_password)
    progress.setValue(100)
    progress.close()
    return xlsx, status


def create_messagebox(title, text, icon):
    msg = QtWidgets.QMessageBox()
    ico_path = os.path.dirname(os.path.realpath(sys.argv[0])) + os.sep + "rep.png"
    msg.setWindowIcon(QtGui.QIcon(ico_path))
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(icon)
    msg.exec_()


def excel(gui):
    """Transform html to excel and opens it"""

    mode = gui.file_list[0]
    if mode[0]:
        cur_i = gui.tabWidget.currentIndex()
        if cur_i == -1:
            return

        f_path = gui.file_list[cur_i + 1]
        if f_path[1] == "":
            xlsx, status = create_excel_with_progress(gui, f_path[0], need_password=mode[1])
            if not status:
                return
            f_path[1] = xlsx
        else:
            xlsx = f_path[1]
            if not os.path.exists(xlsx):
                xlsx, status = create_excel_with_progress(gui, f_path[0], need_password=mode[1])
                if not status:
                    return

        if sys.platform == "win32":
            subprocess.Popen(["start", xlsx], shell=True)
        else:
            subprocess.Popen(["libreoffice " + xlsx], shell=True)
    else:
        for f_path in gui.file_list[1:]:
            file = f_path[0]
            if f_path[1] == "":
                xlsx, status = HtmlToXlsx.transform(file, need_password=mode[1])
                if not status:
                    print(f"Файл {xlsx} занят другой программой")
                    continue
                f_path[1] = xlsx


def print_dialog(gui):
    """Open system printing dialog"""

    # Is it dirty?
    if gui.tabWidget.currentWidget() is None:
        return
    children = gui.tabWidget.currentWidget().children()

    for child in children:
        if isinstance(child, QtWebEngineWidgets.QWebEngineView):
            view = child

    mode = gui.file_list[0]
    if not mode[2]:

        class PrinterHandler(object):
            def __init__(self):
                self.loop = QtCore.QEventLoop()
                self.printer = QPrinter(QPrinter.HighResolution)
                self.result = False

            def cancel(self):
                xpsStr = "Microsoft XPS Document Writer"
                if self.printer.printerName() == xpsStr and not self.result:
                    title = "Внимание"
                    text = "Выбран принтер Microsoft XPS Document Writer. Отменить печать невозможно."
                    icon = QtWidgets.QMessageBox.Critical
                    create_messagebox(title, text, icon)
                    return
                self.loop.quit()

        printerHandler = PrinterHandler()
        dialog = QPrintDialog(printerHandler.printer, view)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        result = False

        def print_preview(success):
            nonlocal result
            result = success
            printerHandler.loop.quit()

        progressbar = QtWidgets.QProgressDialog(view)
        progressbar.setWindowTitle("Печать")
        progressbar.findChild(QtWidgets.QProgressBar).setTextVisible(False)
        progressbar.setLabelText("Подождите. Идёт отправка файла на печать...")
        progressbar.setRange(0, 0)
        progressbar.show()
        progressbar.canceled.connect(printerHandler.cancel)
        page = view.page()
        page.print(printerHandler.printer, print_preview)
        printerHandler.loop.exec_()
        if not result:
            # NEED TO: progressbar закрывается?
            title = "Ошибка"
            text = "Ошибка печати."
            icon = QtWidgets.QMessageBox.Critical
            create_messagebox(title, text, icon)
        else:
            printerHandler.result = True
            progressbar.close()
            title = "Печать"
            text = "Файл отправлен на печать."
            icon = QtWidgets.QMessageBox.Information
            create_messagebox(title, text, icon)
    else:
        cur_i = gui.tabWidget.currentIndex()
        f_path = gui.file_list[cur_i + 1]
        if f_path[1] == "":
            xlsx, status = create_excel_with_progress(gui, f_path[0], need_password=mode[1])
            if not status:
                return
            f_path[1] = xlsx
        else:
            xlsx = f_path[1]
            if not os.path.exists(xlsx):
                xlsx, status = create_excel_with_progress(gui, f_path[0], need_password=mode[1])
                if not status:
                    return
        try:
            com_object = win32com.client.Dispatch("Excel.Application")
            workbook = com_object.Workbooks.Open(xlsx)
            workbook.PrintOut()
        except com_error:
            title = "Внимание"
            text = "На данном компьютере не установлен Excel."
            icon = QtWidgets.QMessageBox.Warning
            create_messagebox(title, text, icon)
        else:
            title = "Печать"
            text = "Файл отправлен на печать."
            icon = QtWidgets.QMessageBox.Information
            create_messagebox(title, text, icon)


def e_mail(gui):
    """Open Outlook if win32 and attach something. Should I zip it?"""
    cur_i = gui.tabWidget.currentIndex()
    if cur_i == -1:
        return

    f_path = gui.file_list[cur_i + 1]

    if f_path[1] == "":
        xlsx, status = create_excel_with_progress(gui, f_path[0], need_password=mode[1])
        if not status:
            return
        f_path[1] = xlsx
    else:
        xlsx = f_path[1]
        if not os.path.exists(xlsx):
            xlsx, status = create_excel_with_progress(gui, f_path[0], need_password=mode[1])
            if not status:
                return

    if sys.platform == "win32":
        subprocess.call(["start", "outlook.exe", "-a", xlsx], shell=True)


def file_open(gui):
    """Open file and refresh browser"""
    f_path = QtWidgets.QFileDialog.getOpenFileName(gui,
                                                   directory=get_last_dir(),
                                                   caption=u'Открыть файл',
                                                   filter="*.html")[0]
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


class ControlMainWindow(QtWidgets.QMainWindow):
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

        self.tabWidget = QtWidgets.QTabWidget(self.ui.centralwidget)
        self.tabWidget.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
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

        qTab = QtWidgets.QWidget()

        self.tabWidget.addTab(qTab, (f_name))
        qWebView = QtWebEngineWidgets.QWebEngineView(qTab)
        verticalLayout = QtWidgets.QVBoxLayout(qTab)
        verticalLayout.addWidget(qWebView)
        qWebView.setProperty("url", QtCore.QUrl(standart_file_path(f_page)))
        qWebView.setObjectName(f_name)

    def close_handler(self, i):
        """Close tab with dialog"""
        message = QtWidgets.QMessageBox()
        message.setText(u"Вы уверены, что хотите закрыть вкладку?")
        message.setWindowTitle(u"Внимание")
        message.addButton(QtWidgets.QPushButton(u'Да'), QtWidgets.QMessageBox.YesRole)
        message.addButton(QtWidgets.QPushButton(u'Нет'), QtWidgets.QMessageBox.NoRole)
        reply = message.exec_()

        if reply == 0:
            self.tabWidget.removeTab(i)
            self.file_list.pop(i + 1)


def start_gui(file_list):
    mode = file_list[0]

    for i in range(1, len(file_list)):
        if file_list[i] != "":
            file_list[i] = [standart_file_path(os.path.realpath(file_list[i])), ""]
    app = QtWidgets.QApplication(sys.argv)
    mySW = ControlMainWindow(file_list=file_list)
    if mode[0]:
        mySW.show()
        sys.exit(app.exec_())
    else:
        excel(mySW)


def usage(script_name):
    print("Usage:")
    print(f"1) python {script_name}")
    print(f"2) python {script_name} <GUI: true/false> <path_to_html_1> <path_to_html_2>...")
    print(f"3) python {script_name} <GUI: true/false> <password: true/false> <path_to_html_1> <path_to_html_2>...")
    print(f"4) python {script_name} <GUI: true/false> <password: true/false> <silent: "
          f"true/false> <path_to_html_1> <path_to_html_2>...")


if __name__ == "__main__":
    file_list = []
    mode = []
    default_mode = (True, False, False)
    if not sys.argv[1:]:
        file_list.append(default_mode)
    else:
        if sys.argv[1].lower() == "true":
            mode.append(True)
        elif sys.argv[1].lower() == "false":
            mode.append(False)
        else:
            print(f"Error: You have tried python {sys.argv[0]} {' '.join(sys.argv[1:])}")
            usage(sys.argv[0])
            sys.exit(-1)
        if not sys.argv[2:]:
            file_list.append(tuple(mode) + default_mode[1:])
        else:
            for i, arg in enumerate(sys.argv[2:]):
                if sys.argv[2:][i].lower() == "true":
                    mode.append(True)
                elif sys.argv[2:][i].lower() == "false":
                    mode.append(False)
                else:
                    file_list.append(tuple(mode) + default_mode[i + 1:])
                    file_list += sys.argv[2:][i:]
                    break
            else:
                i = len(sys.argv[2:])
                file_list.append(tuple(mode) + default_mode[i + 1:])
                file_list += sys.argv[2:][i:]
    if not file_list[0][0] and not file_list[1:]:
        print("Warning: empty file_list.")
        usage(sys.argv[0])
        sys.exit(-1)
    if file_list[1:]:
        save_last_dir(os.path.realpath(os.path.dirname(file_list[1])))

    start_gui(file_list)
