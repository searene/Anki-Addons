#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path
from typing import Optional, Dict

import aqt
from PyQt6.QtCore import QMimeData
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QHBoxLayout, QLineEdit, QPushButton, \
    QMessageBox, QFileDialog
from anki.hooks import wrap
from anki.lang import _
from anki.utils import strip_html_media
from aqt.editor import Editor, EditorWebView
from aqt.utils import tooltip
from aqt import gui_hooks
from .mdict_query import IndexBuilder

import re
import platform
import os
import copy
import pickle
from bs4 import BeautifulSoup, Tag

resource_file_reader = {}


class Setup:
    config = dict(

        # check if there's any new goldendict media
        # or not everytime something is pasted
        check=True,

        # codes that don't need to be isChecked()
        codesIgnored=[],

        addressMap={},

        # it's more convenient to open the last-opened folder
        lastFolder=''
    )

    defaultConfig = copy.deepcopy(config)

    def __init__(self):
        self.checkConfig()
        self.loadConfigFromDisk()
        self.setupMenu()

    def setupMenu(self):
        """
        setup menu in anki
        """
        action = aqt.qt.QAction("GoldenDictMedia", aqt.mw)
        aqt.qt.qconnect(action.triggered, lambda: self.openSettingsDialog())
        aqt.mw.form.menuTools.addAction(action)

    def openSettingsDialog(self):
        self.s = SettingsDialog()
        self.s.exec()

    @classmethod
    def checkConfig(cls):
        """check if config file exists,
           and load the default configurations if needs
        """

        # GoldenDict folder
        Setup.gmFolder = os.path.join(aqt.mw.pm.addonFolder(), 'GoldenDictMedia')

        # if GoldenDictMedia's folder doesn't exist, create one
        if not os.path.exists(Setup.gmFolder):
            os.makedirs(Setup.gmFolder)

        Setup.configFile = os.path.join(Setup.gmFolder, 'config')
        if not os.path.exists(Setup.configFile):
            # if config file doesn't exist, create one
            open(Setup.configFile, 'a').close()

            # save the default config to disk
            cls.saveConfigToDisk()

    @classmethod
    def saveConfigToDisk(cls, configDict=None, configFile=None):
        """save Setup.config to the config file"""

        if not configDict:
            configDict = Setup.config
        if not configFile:
            configFile = Setup.configFile

        with open(configFile, 'wb') as f:
            pickle.dump(configDict, f)

    @classmethod
    def loadConfigFromDisk(cls):
        """load config file to Setup.config"""

        with open(Setup.configFile, 'rb') as f:
            Setup.config = pickle.load(f)


class AddNewWindow(QDialog):
    def __init__(self, code, filename):
        super(AddNewWindow, self).__init__()

        # whether current import is sucessful
        self.importRes = None

        self.code = code
        self.filename = filename
        self.setupUI()

    def setupUI(self):
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        promptLabel = QLabel('New media has been found, code: {}'.format(self.code))
        self.checkCb = QCheckBox('Ignore this dictionary and never prompt for it again')
        self.checkCb.clicked.connect(self.toggleSelectStatus)

        hbox = QHBoxLayout()
        pathLabel = QLabel('media path: ')
        self.pathEdit = QLineEdit()
        self.pathBtn = QPushButton('...')
        self.pathBtn.clicked.connect(self.select_media_path)
        hbox.addWidget(pathLabel)
        hbox.addWidget(self.pathEdit)
        hbox.addWidget(self.pathBtn)

        mainLayout.addWidget(promptLabel)
        mainLayout.addWidget(self.checkCb)
        mainLayout.addLayout(hbox)

        # add OK and Cancel buttons
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.save_media)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.cancel)
        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(okButton)
        btnLayout.addWidget(cancelButton)
        mainLayout.addLayout(btnLayout)

        self.setWindowTitle('Add New Goldendict Media')

    def cancel(self):
        self.importRes = False
        self.close()

    def toggleSelectStatus(self):
        """disable QLineEdit and QPushButton used to select the media folder if the QCheckBox is isChecked(), enable them otherwise"""
        if self.checkCb.isChecked():
            # disable
            self.pathEdit.setDisabled(True)
            self.pathBtn.setDisabled(True)
        else:
            # enable
            self.pathEdit.setEnabled(True)
            self.pathBtn.setEnabled(True)

    def select_media_path(self):
        lastFolder = Setup.config['lastFolder']
        if not os.path.exists(lastFolder):
            # if lastFolder's no longer existed, open the current folder,
            # which is usually Anki's collection.media
            lastFoder = ''

        # open a dialog, select a file, and assign the file path to the variable path, the file can be either a folder or a normal file

        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.FileMode.AnyFile)
        dlg.exec()
        path = dlg.selectedFiles()[0]

        self.pathEdit.setText(path)

        # save the last opened folder, so next time we can find the media more easily
        Setup.config['lastFolder'] = os.path.dirname(path)
        Setup.saveConfigToDisk()

    def save_media(self):
        if self.checkCb.isChecked():
            # ignore the media code
            if self.code not in Setup.config['codesIgnored']:
                Setup.config['codesIgnored'].append(self.code)
                Setup.saveConfigToDisk()
                tooltip('Current dictionary was ignored, click on reset to restore should you need it again')
                self.importRes = False
                self.close()
                return

        resource_path = self.pathEdit.text().strip()

        # remove the trailing / or \
        if resource_path.endswith('/') or resource_path.endswith('\\'):
            resource_path = resource_path[:-1]

        Setup.config['addressMap'][self.code] = resource_path
        Setup.saveConfigToDisk()
        self.importRes = True
        tooltip('Media import completed')
        self.close()


class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.setupUI()
        self.loadFromDisk()

    def setupUI(self):
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        self.importedLabel = QLabel("{} dictionaries imported"
                                    .format(len(Setup.config['addressMap'])))
        self.ignoredLabel = QLabel("{} dictionaries ignored"
                                   .format(len(Setup.config['codesIgnored'])))
        mainLayout.addWidget(self.importedLabel)
        mainLayout.addWidget(self.ignoredLabel)

        self.checkCb = QCheckBox('Check goldendict media everytime it pastes')
        mainLayout.addWidget(self.checkCb)

        # add OK and Cancel buttons
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.onOK)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.close)
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.reset)
        btnLayout = QHBoxLayout()
        btnLayout.addWidget(okButton)
        btnLayout.addWidget(cancelButton)
        btnLayout.addStretch(1)
        btnLayout.addWidget(resetButton)
        mainLayout.addLayout(btnLayout)

        self.setWindowTitle('GoldenDictMedia Settings')

    def onOK(self):
        self.saveToDisk()
        self.close()

    def saveToDisk(self, configDict=None, configFile=None):
        """save configurations on the window to the config file"""

        if not configDict:
            configDict = Setup.config
        if not configFile:
            configFile = Setup.configFile

        self.updateConfigFromUI(configDict)
        configDict['check'] = self.checkCb.isChecked()
        Setup.saveConfigToDisk(configDict, configFile)

    def updateUIFromConfig(self, configDict):
        self.checkCb.setChecked(configDict['check'])
        self.importedLabel.setText("{} dictionaries imported"
                                   .format(len(configDict['addressMap'])))
        self.ignoredLabel.setText("{} dictionaries ignored"
                                  .format(len(configDict['codesIgnored'])))

    def updateConfigFromUI(self, configDict):
        configDict['check'] = self.checkCb.isChecked()
        if self.importedLabel.text().startswith('0'):
            configDict['addressMap'] = {}
        if self.ignoredLabel.text().startswith('0'):
            configDict['codesIgnored'] = []

    def loadFromDisk(self):
        """load configurations from the config file to the window"""

        Setup.loadConfigFromDisk()
        self.updateUIFromConfig(Setup.config)

    def reset(self):
        """save the default configDict to disk then load it"""
        self.updateUIFromConfig(Setup.defaultConfig)

    def openWindow(self):
        """
        Show the settings dialog if the user clicked on the menu
        """
        self.updateUIFromConfig()
        self.settingsMw = self


def add_new_media(code: str, filename: str) -> bool:
    if code in Setup.config['codesIgnored']:
        # the code should be ignored
        return False

    # Let's deal with the new media
    anw = AddNewWindow(code, filename)
    anw.exec()

    # importRes represents whether importation is successful
    return anw.importRes


def get_parser():
    system = platform.system()
    if system == "Windows" or system == "Darwin":
        return "html.parser"
    else:
        return "lxml"


def get_file_path(link: Tag, address_map: Dict[str, str]) -> Optional[str]:
    if link.get('href'):
        # audio
        attr = 'href'
    elif link.get('src'):
        # image
        attr = 'src'
    else:
        # something else, I don't know, at least not
        # something we're looking for, skip
        return None

    goldenPath = link.get(attr)
    matchObj = re.search(r'(?<=(gdau|bres)://)[^/\\]*', goldenPath)
    if not matchObj:
        return None
    code = matchObj.group(0)
    if code not in address_map:
        # new media
        filename = os.path.basename(goldenPath)
        success = add_new_media(code, filename)
        if not success:
            # media import failed, continue to
            # process the next link
            return None

    # get the full path of the media file
    prefix = re.search(r'^(gdau|bres)://[^/\\]*', goldenPath).group(0)
    if address_map[code].endswith(".mdx"):
        return get_file_path_from_mdd_file(code, address_map[code], link[attr].replace(prefix, ''))
    else:
        return link[attr].replace(prefix, address_map[code])


def get_file_path_from_mdd_file(dict_code: str, mdd_file_path: str, relative_path: str) -> str:
    """relative_path: starting from /, e.g. /ame_start.wav"""
    base_file_name = os.path.basename(relative_path)
    if dict_code not in resource_file_reader:
        resource_file_reader[dict_code] = IndexBuilder(mdd_file_path, sql_index=True, check=True)
    index_builder: IndexBuilder = resource_file_reader[dict_code]
    resource_bytes = index_builder.mdd_lookup(relative_path.replace("/", "\\"))
    if len(resource_bytes) == 0:
        raise Exception("Cannot find file: " + relative_path)
    temp_file_name = os.path.join(tempfile.gettempdir(), base_file_name)
    with open(temp_file_name, 'wb') as f:
        f.write(resource_bytes[0])
    return temp_file_name


def import_media(self, mime, _old):
    """import audios and images from goldendict"""

    # find out where we are
    if aqt.dialogs._dialogs['AddCards'][1]:
        # we are adding cards
        window = aqt.dialogs._dialogs['AddCards'][1]
    elif aqt.dialogs._dialogs['Browser'][1]:
        # we are browsing cards
        window = aqt.dialogs._dialogs['Browser'][1]
    elif aqt.dialogs._dialogs['EditCurrent'][1]:
        # we are editing cards
        window = aqt.dialogs._dialogs['EditCurrent'][1]
    else:
        # I don't know where we are, just exit
        return mime

    new_mime = get_new_mime(mime, window.editor)

    # default _processHtml method
    return _old(self, new_mime)


def get_new_mime(old_mime: QMimeData, editor: Editor):
    if not old_mime.hasHtml():
        return old_mime
    html = old_mime.html()
    soup = BeautifulSoup(html, get_parser())
    addressMap = Setup.config['addressMap']

    # sound
    links = [link for link in soup.findAll('a', href=True) if 'gdau' in link['href']]

    # images
    links += [link for link in soup.findAll('img', src=True) if 'bres' in link['src']]

    for link in links:
        file_path = get_file_path(link, addressMap)

        # import the file to anki
        anki_media: str = editor._addMedia(file_path, canDelete=True)
        # sound
        if link.get('href'):
            link.name = 'span'
            # remove all the attributes in link
            link.attrs = {
                'class': 'golden-dict-media-word-sound',
                'data-original-href': link.get('href')
            }
            link.append(anki_media)

        # images
        else:
            img = BeautifulSoup(anki_media, get_parser())
            link.replaceWith(img)

    html = str(soup)

    # assign the modified html to new Mime
    new_mime = QMimeData()
    new_mime.setHtml(html)

    # set text so the addon is able to work even when StripHTML is on
    new_mime.setText(strip_html_media(html))
    return new_mime


def init_addon():
    gui_hooks.editor_will_process_mime.append(will_process_mime_handler)
    Setup()


def will_process_mime_handler(mime: QMimeData, editor_web_view: EditorWebView, internal: bool, extended: bool,
                              drop_event: bool):
    return get_new_mime(mime, editor_web_view.editor)
