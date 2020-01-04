#!/usr/bin/env python
# -*- coding: utf-8 -*-
from anki.hooks import wrap
from anki.utils import stripHTMLMedia
from aqt.editor import Editor, EditorWebView
from aqt.utils import tooltip
from aqt import dialogs, mw

import re
import os
import sys
import copy
import pickle
from BeautifulSoup import BeautifulSoup

from PyQt4.QtGui import *
from PyQt4.QtCore import *


class Setup:

    config = dict(

        # check if there's any new goldendict media 
        # or not everytime something is pasted
        check = True,

        # codes that don't need to be isChecked()
        codesIgnored = [],

        addressMap = {},

        # it's more convenient to open the last-opened folder
        lastFolder = ''
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
        action = QAction("GoldenDictMedia", mw)
        mw.connect(action, SIGNAL("triggered()"), self.openSettingsDialog)
        mw.form.menuTools.addAction(action)

    def openSettingsDialog(self):
        self.s = SettingsDialog()
        self.s.exec_()

    @classmethod
    def checkConfig(cls):
        """check if config file exists, 
           and load the default configurations if needs
        """

        # GoldenDict folder
        Setup.gmFolder = os.path.join(mw.pm.addonFolder(), 'GoldenDictMedia')

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
    def saveConfigToDisk(cls, configDict = None, configFile = None):
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

class addNewWindow(QDialog):
    def __init__(self, code, filename):
        super(addNewWindow, self).__init__()

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

        hbox =QHBoxLayout()
        pathLabel = QLabel('media path: ')
        self.pathEdit = QLineEdit()
        self.pathBtn = QPushButton('...')
        self.pathBtn.clicked.connect(self.selectMediaFolder)
        hbox.addWidget(pathLabel)
        hbox.addWidget(self.pathEdit)
        hbox.addWidget(self.pathBtn)

        mainLayout.addWidget(promptLabel)
        mainLayout.addWidget(self.checkCb)
        mainLayout.addLayout(hbox)

        # add OK and Cancel buttons
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.saveMedia)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.cancel)
        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(okButton)
        btnLayout.addWidget(cancelButton)
        mainLayout.addLayout(btnLayout)

        # center the window
        self.move(QDesktopWidget().availableGeometry().center() - self.frameGeometry().center())

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

    def selectMediaFolder(self):
        lastFolder = Setup.config['lastFolder']
        if not os.path.exists(lastFolder):
            # if lastFolder's no longer existed, open the current folder,
            # which is usually Anki's collection.media
            lastFoder = ''

        path = QFileDialog.getExistingDirectory(self, _("Select the media folder for this dictionary"), Setup.config['lastFolder'], QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        self.pathEdit.setText(path)

        # save the last opened folder, so next time we can find the media more easily
        Setup.config['lastFolder'] = os.path.dirname(path)
        Setup.saveConfigToDisk()

    def saveMedia(self):
        if self.checkCb.isChecked():
            # ignore the media code
            if self.code not in Setup.config['codesIgnored']:
                Setup.config['codesIgnored'].append(self.code)
                Setup.saveConfigToDisk()
                tooltip('Current dictionary was ignored, click on reset to restore should you need it again')
                self.importRes = False
                self.close()
                return

        folder = self.pathEdit.text().strip()

        # remove the trailing / or \ 
        if folder.endswith('/') or folder.endswith('\\'):
            folder = folder[:-1]

        fullPath = os.path.join(self.pathEdit.text(), self.filename)
        if not (os.path.exists(fullPath) and os.path.exists(folder)):
            msg = QMessageBox(self)
            msg.setText("Folder doesn't exist or doesn't contain the needed media, please select again")
            msg.setWindowTitle("Directory selected is not the right one")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg.exec_()
            return

        Setup.config['addressMap'][self.code] = folder
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

        print 'setupUI, Setup.config: {}'.format(Setup.config)
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

        # center the window
        self.move(QDesktopWidget().availableGeometry().center() - self.frameGeometry().center())

        self.setWindowTitle('GoldenDictMedia Settings')

    def onOK(self):
        self.saveToDisk()
        self.close()

    def saveToDisk(self, configDict = None, configFile = None):
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

def addNewMedia(code, filename):
    if code in Setup.config['codesIgnored']:
        # the code should be ignored
        return False

    # Let's deal with the new media
    anw = addNewWindow(code, filename)
    anw.exec_()
    
    # importRes represents whether importation is successful
    return anw.importRes

def urlToLink_around(self, url, _old):
    pic = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif", ".svg", ".webp")
    ext = os.path.splitext(url)[-1]
    if (os.path.isabs(url) == False) and (ext in pic):
        # goldendict's img url is a relative path, which is
        # already processed, skip it
        return '<img src={}>'.format(url)

    return _old(self, url)

def importMedia(self, mime, _old):
    """import audios and images from goldendict"""

    # find out where we are
    if dialogs._dialogs['AddCards'][1]:
        # we are adding cards
        window = dialogs._dialogs['AddCards'][1]
    elif dialogs._dialogs['Browser'][1]:
        # we are browsing cards
        window = dialogs._dialogs['Browser'][1]
    elif dialogs._dialogs['EditCurrent'][1]:
        # we are editing cards
        window = dialogs._dialogs['EditCurrent'][1]
    else:
        # I don't know where we are, just exit
        return _old(self, mime) 

    html = mime.html()
    soup = BeautifulSoup(html)
    newMime = QMimeData()
    addressMap = Setup.config['addressMap']

    # sound
    links = [link for link in soup.findAll('a') if 'gdau' in link['href']]

    # images
    links += [link for link in soup.findAll('img') if 'bres' in link['src']]


    for link in links:
        if link.get('href'):
            # audio
            attr = 'href'
        elif link.get('src'):
            # image
            attr = 'src'
        else:
            # something else, I don't know, at least not 
            # something we're looking for, skip
            continue

        goldenPath = link.get(attr)
        matchObj = re.search(r'(?<=(gdau|bres)://)[^/\\]*', goldenPath)
        if not matchObj:
            continue
        code = matchObj.group(0)
        if code not in addressMap:
            # new media
            filename = os.path.basename(goldenPath)
            res = addNewMedia(code, filename)
            if not res:
                # media import failed, continue to
                # process the next link
                continue

        # get the full path of the media file
        prefix = re.search(r'^(gdau|bres)://[^/\\]*', goldenPath).group(0)
        filePath = link[attr].replace(prefix, addressMap[code])

        # import the file to anki
        ankiMedia = window.editor._addMedia(filePath, canDelete=True)
        # sound
        if attr == 'href': 
            span = link.parent
            # delete the original link, 
            # because we don't need it any more
            del link
            # append ankiMedia
            span.string = ankiMedia

        # images
        else:
            img = BeautifulSoup(ankiMedia)
            link.replaceWith(img)

    html = str(soup).decode('utf8')

    # assign the modified html to new Mime
    newMime = QMimeData()
    newMime.setHtml(html)

    # set text so the addon is able to work even when StripHTML is on
    newMime.setText(stripHTMLMedia(html))

    # default _processHtml method
    return _old(self, newMime)

EditorWebView._processHtml = wrap(EditorWebView._processHtml, importMedia, 'around')
Editor.urlToLink = wrap(Editor.urlToLink, urlToLink_around, 'around')
setup = Setup()
