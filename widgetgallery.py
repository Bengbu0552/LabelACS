# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
# Software ACS project: Stenosis Annotations.
# Developer: MA, Kochi University of Technology. 256013s@gs.kochi-tech.ac.jp
# Python, PyQt, Opencv.
# Beta version 0.0.

from __future__ import annotations
import sys
import yaml
from labelacs import label_main

from PySide6.QtCore import (QDateTime, QDir, QLibraryInfo, QSysInfo, Qt, QTimer, Slot, qVersion, QMetaObject)
from PySide6.QtGui import (QCursor, QDesktopServices, QGuiApplication, 
                           QIcon, QKeySequence, QShortcut, QStandardItem,
                           QStandardItemModel)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QMessageBox,
                               QCommandLinkButton, QDateTimeEdit, QDial,
                               QDialog, QDialogButtonBox, QPushButton, QFileSystemModel,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QListView, QMenu, QPlainTextEdit,
                               QProgressBar, QPushButton, QRadioButton,
                               QScrollBar, QSizePolicy, QSlider, QSpinBox,
                               QStyleFactory, QTableWidget, QTabWidget,
                               QTextBrowser, QTextEdit, QToolBox, QToolButton,
                               QTreeView, QVBoxLayout, QWidget, QFileDialog)

SYSTEMINFO = """<html><head/><body>
<h3>Operating System</h3><p>{}</p>
<h3>Qt Build</h3><p>{}</p>
<h3>Python</h3><p>{}</p>
<h3>Screens</h3>
{}
</body></html>"""


def class_name(o):
    return o.metaObject().className()

def help_url(page):
    """Build a Qt help URL from the page name"""
    major_version = qVersion().split('.')[0]
    return f"https://doc.qt.io/qt-{major_version}/{page}.html"

def launch_help(widget):
    """Launch a widget's help page"""
    url = help_url(class_name(widget).lower())
    QDesktopServices.openUrl(url)

def launch_module_help():
    QDesktopServices.openUrl(help_url("qtwidgets-index"))

def init_widget(w, name):
    """Init a widget for the gallery, give it a tooltip showing the
       class name"""
    w.setObjectName(name)
    w.setToolTip(class_name(w))

def embed_into_hbox_layout(w, margin=10):
    """Embed a widget into a layout to give it a frame"""
    result = QWidget()
    layout = QHBoxLayout(result)
    layout.setContentsMargins(margin, margin, margin, margin)
    layout.addWidget(w)
    return result

def format_geometry(rect):
    """Format a geometry as a X11 geometry specification"""
    w = rect.width()
    h = rect.height()
    x = rect.x()
    y = rect.y()
    return f"{w}x{h}{x:+d}{y:+d}"

def screen_info(widget):
    """Format information on the screens"""
    policy = QGuiApplication.highDpiScaleFactorRoundingPolicy()
    policy_string = str(policy).split('.')[-1]
    result = f"<p>High DPI scale factor rounding policy: {policy_string}</p><ol>"
    for screen in QGuiApplication.screens():
        current = screen == widget.screen()
        result += "<li>"
        if current:
            result += "<i>"
        name = screen.name()
        geometry = format_geometry(screen.geometry())
        dpi = int(screen.logicalDotsPerInchX())
        dpr = screen.devicePixelRatio()
        result += f'"{name}" {geometry} {dpi}DPI, DPR={dpr}'
        if current:
            result += "</i>"
        result += "</li>"
    result += "</ol>"
    return result

class WidgetGallery(QDialog):
    """Dialog displaying a gallery of Qt Widgets"""

    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('./logo/label_acs.jpg'))
        self.imgsize = 'default'
        self.sv_pth = ''
        self.txt = './setting.txt'
        self.content = {'img_size':self.imgsize, 'sv_root':self.sv_pth}

        self._style_combobox = QComboBox()
        init_widget(self._style_combobox, "styleComboBox")
        self._style_combobox.addItems(['Windows', 'Linux(Ubuntu)'])

        # help_label = QLabel("Press F1 to check the")
        help_label = QLabel("パンフレットは F1をお押してください.")
        init_widget(help_label, "help_label")

        # style_label = QLabel("Style:")
        style_label = QLabel("パソコンシステム(OS):")
        init_widget(style_label, "style_label")
        style_label.setBuddy(self._style_combobox)

        buttons_groupbox = self.create_buttons_groupbox()
        itemview_tabwidget = self.create_itemview_tabwidget()
        text_toolbox = self.create_text_toolbox()

        self._style_combobox.textActivated.connect(self.change_style)

        help_shortcut = QShortcut(self)
        help_shortcut.setKey(QKeySequence.StandardKey.HelpContents)
        help_shortcut.activated.connect(self.help_on_current_widget)

        top_layout = QHBoxLayout()
        top_layout.addWidget(style_label)
        top_layout.addWidget(self._style_combobox)
        top_layout.addStretch(1)
        top_layout.addWidget(help_label)
        top_layout.addStretch(1)

        start_button = QPushButton("start")
        start_button.clicked.connect(self.start2ann)
        
        dialog_buttonbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Help
                                            | QDialogButtonBox.StandardButton.Close)
        init_widget(dialog_buttonbox, "dialogButtonBox")
        dialog_buttonbox.helpRequested.connect(launch_module_help)
        dialog_buttonbox.rejected.connect(self.reject)

        main_layout = QGridLayout(self)
        main_layout.addLayout(top_layout, 0, 0, 1, 2)
        main_layout.addWidget(itemview_tabwidget, 1, 0, 1, 2)
        main_layout.addWidget(buttons_groupbox, 2, 0, 2, 1)
        main_layout.addWidget(text_toolbox, 1, 2, 1, 2)
        main_layout.addWidget(dialog_buttonbox, 2, 1, 1, 2)
        main_layout.addWidget(start_button, 2, 2, 2, 2)

        # qv = qVersion()
        self.setWindowTitle(f"LabelACS Beta v0.0")

    def setVisible(self, visible):
        super(WidgetGallery, self).setVisible(visible)
        if visible:
            self.windowHandle().screenChanged.connect(self.update_systeminfo)
            self.update_systeminfo()

    @Slot()
    def start2ann(self):
        print("ACS annotation!")
        ifos_pth = './setting.txt'
        with open(ifos_pth, 'r', encoding='utf-8') as txt_file:
            lines = txt_file.readlines()
        resize_info = None
        save_root = None
        for i in lines:
            i = i.strip()
            if i.split(':')[0] == 'img_size':
                resize_info = i.split(':')[-1]
            else:
                save_root = i.split(':')[-1]

        self.core_function = label_main(resize_info, save_root)
        QMetaObject.connectSlotsByName(self.core_function.show())

    @Slot(str)
    def change_style(self, style_name):
        QApplication.setStyle(QStyleFactory.create(style_name))

    @Slot()
    def save_dir(self):
        dir_dialog = QFileDialog.getExistingDirectory(self, "select a directory")
        if dir_dialog:
            print("directory:", dir_dialog)
            self.sv_pth = dir_dialog

    @Slot()
    def create_buttons_groupbox(self):
        result = QGroupBox("設定(Setting)")
        init_widget(result, "設定(Setting)")

        menu_toolbutton = QToolButton()
        init_widget(menu_toolbutton, "解像度変更")
        menu_toolbutton.setText("解像度変更(Image Resolution Setting)")

        tool_menu = QMenu(menu_toolbutton)
        menu_toolbutton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        action1 = tool_menu.addAction("32*32")
        action1.triggered.connect(lambda:self.size_trigger(action1.text()))
        action2 = tool_menu.addAction("64*64")
        action2.triggered.connect(lambda:self.size_trigger(action2.text()))
        action3 = tool_menu.addAction("128*128")
        action3.triggered.connect(lambda:self.size_trigger(action3.text()))
        menu_toolbutton.setMenu(tool_menu)

        label1 = QLabel("他のサイズをお入力してください:")
        size_edit = QLineEdit()
        size_edit.setPlaceholderText("幅*縦")
        ok_button = QPushButton('他のサイズを設定する')
        ok_button.clicked.connect(lambda:self.size_trigger(size_edit.text()))

        save_button = QPushButton("Save setting")
        save_button.clicked.connect(lambda:self.confirm_trigger())

        tool_layout = QHBoxLayout()
        tool_layout.addWidget(menu_toolbutton)
        tool_layout.addWidget(label1)
        tool_layout.addWidget(size_edit)

        savepth_pushbutton = QPushButton("アノテーションのファルダ設定")
        init_widget(savepth_pushbutton, "アノテーションのファルダ設定")
        savepth_pushbutton.clicked.connect(self.save_dir)

        button_layout = QVBoxLayout()
        button_layout.addLayout(tool_layout)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(savepth_pushbutton)
        button_layout.addWidget(save_button)

        main_layout = QHBoxLayout(result)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        return result
    
    def size_trigger(self, img_size):
        self.imgsize = img_size
        print(f"up-sample size {self.imgsize}")

    def confirm_trigger(self):
        QMessageBox.information(QWidget(), 'message', f'確認してください \n image_size={self.imgsize}')
        self.content = {'img_size':self.imgsize, 'sv_root':self.sv_pth}
        self.content = yaml.dump(self.content, allow_unicode=True)
        with open(self.txt, 'w+', encoding='utf-8') as f:
            f.write(self.content)

    def create_text_toolbox(self):
        result = QToolBox()
        init_widget(result, "toolBox")

        self._systeminfo_textbrowser = QTextBrowser()
        init_widget(self._systeminfo_textbrowser, "systemInfoTextBrowser")

        result.addItem(embed_into_hbox_layout(self._systeminfo_textbrowser), "ソフトウェアの情報")
        return result

    def create_itemview_tabwidget(self):
        result = QTabWidget()
        init_widget(result, "upperLeftTabWidget")
        result.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Ignored)

        tree_view = QTreeView()
        init_widget(tree_view, "treeView")
        filesystem_model = QFileSystemModel(tree_view)
        filesystem_model.setRootPath(QDir.rootPath())
        tree_view.setModel(filesystem_model)

        result.addTab(embed_into_hbox_layout(tree_view), "データのルートファルダ(Dataset root path)")
        return result

    @Slot()
    def update_systeminfo(self):
        """Display system information"""
        system_info = SYSTEMINFO.format(sys.version,
                                        QLibraryInfo.build(),
                                        QSysInfo.prettyProductName(),
                                        screen_info(self))
        self._systeminfo_textbrowser.setHtml(system_info)

    @Slot()
    def help_on_current_widget(self):
        """Display help on widget under mouse"""
        w = QApplication.widgetAt(QCursor.pos(self.screen()))
        while w:  # Skip over internal widgets
            name = w.objectName()
            if name and not name.startswith("qt_"):
                launch_help(w)
                break
            w = w.parentWidget()