#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anki.hooks import wrap
from anki.media import MediaManager
from aqt.utils import tooltip, showWarning
from aqt.editor import Editor, EditorWebView
from aqt import mw

from aqt.qt import *

import os
import pickle
import logging
import copy
import shutil
import tempfile
import ssl
import urllib.request, urllib.error, urllib.parse

addon_id = '1214357311'

# a temporary workaround to solve the CERTIFICATE_VERIFY_FAILED error
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

# Get log file
# 1214357311 is ImageResizer's addon ID
irFolder = os.path.join(mw.pm.addonFolder(), addon_id, 'user_files')
logFile = os.path.join(irFolder, 'imageResizer.log')

# if ImageResizer's folder doesn't exist, create one
if not os.path.exists(irFolder):
    os.makedirs(irFolder)

# create the logFile
open(logFile, 'w').close()

# setup logger
logging.basicConfig(format = '%(asctime)s - %(name)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s', filename = logFile, level = logging.DEBUG)
logger = logging.getLogger(__name__)

# settings main window, Qt won't show the window if
# we don't assign a global variable to Settings()

class Setup(object):

    """Do all the necessary initialization when anki
       loads the addon
    """

    config = dict(
        isUpScalingDisabled = False,
        auto = True,
        keys = dict(Ctrl = True, Alt = False, 
                Shift = True, Extra = 'V'),
        width = '400',
        height = '400',
        ratioKeep = 'height',
        scalingMode = 'fast'
    )

    defaultConfig = copy.deepcopy(config)

    settingsMw = None
    addonDir = mw.pm.addonFolder()

    irFolder = os.path.join(addonDir, addon_id, 'user_files')
    pickleFile = os.path.join(irFolder, 'config.pickle')

    def __init__(self, imageResizer):
        self.checkConfigAndLoad()
        self.setupMenu()
        self.setupFunctions(imageResizer)

        logger.debug('Setup init completed')

    def checkConfigAndLoad(self):
        """Check if the ImageResizer folder exists
           Create one if not, then load the configuration
        """
        if not os.path.exists(Setup.irFolder):
            logger.debug("config folder doesn't exist, creating a new one...")
            os.makedirs(Setup.irFolder)
        if not os.path.exists(Setup.pickleFile):
            # dump the default config if config.pickle doesn't exist
            logger.debug("config.pickle doesn't exist, creating one with the default settings: {}".format(Setup.defaultConfig))
            with open(Setup.pickleFile, 'wb') as f:
                pickle.dump(Setup.config, f)

        # load config.pickle
        logger.debug("loading config.pickle...")
        with open(self.pickleFile, 'rb') as f:
            Setup.config = pickle.load(f)
            logger.debug("loaded config: {}".format(Setup.config))

    def setupMenu(self):
        """
        setup menu in anki
        """
        action = QAction("Image Resizer", mw)
        action.triggered.connect(self._settings)
        mw.form.menuTools.addAction(action)

        # Setup config button
        mw.addonManager.setConfigAction(addon_id, self._settings)

    def setupFunctions(self, imageResizer):
        """Replace functions in anki
        """
        # setup button
        Editor.setupWeb = wrap(Editor.setupWeb, ImageResizerButton, 'after')
        Editor.imageResizer = imageResizer

        EditorWebView._processMime = wrap(EditorWebView._processMime, _processMime_around, 'around')

    def _settings(self):
        """
        Show the settings dialog if the user clicked on the menu
        """
        logger.debug('triggered settings dialog')
        self.settingsMw = Settings(self, Setup.config)

        self.settingsMw.showNormal()
        self.settingsMw.raise_()
        self.settingsMw.activateWindow()

def resize(im):
    """Resize the image
    :im: QImage to be resized
    :returns: resized QImage
    """
    logger.debug('resizing images...')
    logger.debug('image before resizing, width: {}, height: {}'.format(im.width(), im.height()))

    option = Setup.config['ratioKeep']
    isUpScalingDisabled = Setup.config['isUpScalingDisabled']
    heightInConfig = int(Setup.config['height'])
    widthInConfig = int(Setup.config['width'])
    transformationMode = Qt.FastTransformation if (Setup.config['scalingMode'] == 'fast') else Qt.SmoothTransformation

    if option == 'height' or option == 'either' and im.width() <= im.height():
        if im.height() <= heightInConfig and not isUpScalingDisabled or im.height() > heightInConfig:
            logger.debug('scale according to height: {}'.format(int(Setup.config['height'])))
            im = im.scaledToHeight(heightInConfig, transformationMode)
    elif option == 'width' or option == 'either' and im.height() < im.width():
        if im.width() <= widthInConfig and not isUpScalingDisabled or im.width() > widthInConfig:
            logger.debug('scale according to width: {}'.format(int(Setup.config['width'])))
            im = im.scaledToWidth(widthInConfig, transformationMode)
        
    logger.debug('image after resizing, width: {}, height: {}'.format(im.width(), im.height()))
    return im

def imageResizer(self, paste = True, mime = None):
    """resize the image contained in the clipboard
       paste: paste the resized image in the currently focused widget if the parameter is set True
       returns: QMimeData"""

    if mime == None:
        mime = mw.app.clipboard().mimeData()
    # check if mime contains any image related urls, and put the image data in the clipboard if it contains it
    mime = checkAndResize(mime, self)

    logger.debug('imageResizer called!')

    # check if mime contains images or any image file urls
    if mime.hasImage():
        logger.debug('mime contains images relative data in it: {}'.format(mime))
        logger.debug('paste action: {}'.format(paste))

        if paste:
            # paste it in the currently focused widget
            logger.debug('paste is True, paste it into current widget')
            clip = self.mw.app.clipboard()
            clip.setMimeData(mime, mode = QClipboard.Clipboard)

            focusedWidget = QApplication.focusWidget()
            # logger.debug(focusedWidget)
            # focusedWidget.paste()
            self.onPaste()

    return mime

def ImageResizerButton(self):
    shortcut = '+' .join([k for k, v in list(Setup.config['keys'].items()) if v == True])
    shortcut += '+' + Setup.config['keys']['Extra']
    self.addButton(func = lambda s = self: imageResizer(self), 
        icon = None, label = "Image Resizer", cmd = 'imageResizer(self)', keys = _(shortcut))
    

def _processMime_around(self, mime, _old):
    """I found that anki dealt with html, urls, text first before dealing with image, 
    I didn't find any advantages of it. If the user wants to copy an image from the web broweser, 
    it will make anki fetch the image again, which is a waste of time. the function will try to deal with image data first if mime contains it.contains

    This function is always called when pasting!"""

    # "Paste when resizing"
    if Setup.config['auto'] is False:
        logger.debug("Setup.config['auto'] is False, run the original _processMime directly")
        return _old(self, mime)

    logger.debug('grabbing MIME data: found formats {}'.format(mime.formats()))
    logger.debug('hasImage: {}'.format(mime.hasImage()))
    logger.debug('hasUrls: {}'.format(mime.hasUrls()))

    if mime.hasImage():

        # Resize the image, then pass to Anki
        logger.debug('found image in mime data: getting the resized QImage...')
        mime = self.editor.imageResizer(paste = False, mime = mime)

        logger.debug('let anki handle the resized image')
        return _old(self, mime)
        # return self._processImage(mime)

    if mime.hasUrls():
        logger.debug('found URL in mime data: resizing if necessary...')
        mime = self.editor.imageResizer(paste = False, mime = mime)

        logger.debug('let anki handle the resized image')
        return _old(self, mime)
    
    logger.debug("image data isn't detected, run the old _processMime function")
    return _old(self, mime)

def checkAndResize(mime, editor):
    """check if mime contains url and if the url represents a picture file path, fetch the url and put the image in the clipboard if the url represents an image file
    the function will resize the image if it finds that mime contains it

    :mime: QMimeData to be checked
    :editor: an instance of Editor

    :returns: image filled QMimeData if the contained url represents an image file, the original QMimeData otherwise
    """

    logger.debug('checking if mime data is an image or an URL to an image...')
    pic = ("jpg", "jpeg", "png", "tif", "tiff", "gif", "svg", "webp")

    if mime.hasImage():
        logger.debug('found image in mime, resize and return the mime')
        im = resize(mime.imageData())
        mime = QMimeData()
        mime.setImageData(im)

    elif mime.hasUrls():
        url = mime.urls()[0].toString()

        # check prefix
        prefix = url[:url.find(':')]

        # check suffix
        for suffix in pic:
            if url.lower().endswith(suffix):
                logger.debug('suffix {} meet requirements'.format(suffix))

                # fetch the image, put it in the mime and return it
                im = QImage()
                req = urllib.request.Request(url, None, {
                    'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
                filecontents = urllib.request.urlopen(req).read()
                
                im.loadFromData(filecontents)

                # resize it
                im = resize(im)

                mime = QMimeData()
                mime.setImageData(im)

                return mime

    return mime

class GrabKey(QWidget):
    """
    Grab the key combination to paste the resized image
    """
    def __init__(self, parent):
        super(GrabKey, self).__init__()
        self.parent = parent
        self.setupUI()

        # self.active is used to trace whether there's any key held now
        self.active = 0

        self.ctrl = False
        self.alt = False
        self.shift = False
        self.extra = None

    def setupUI(self):
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        label = QLabel('Please press the new key combination')
        mainLayout.addWidget(label)

        self.setWindowTitle('Grab key combination')
        self.show()

    def keyPressEvent(self, evt):
        self.active += 1
        if evt.key() >0 and evt.key() < 127:
            self.extra = chr(evt.key())
        elif evt.key() == Qt.Key_Control:
            self.ctrl = True
        elif evt.key() == Qt.Key_Alt:
            self.alt = True
        elif evt.key() == Qt.Key_Shift:
            self.shift = True

    def keyReleaseEvent(self, evt):
        self.active -= 1
        if self.active == 0:
            if not (self.ctrl or self.alt or self.shift):
                msg = QMessageBox()
                msg.setText('Please press at least one of these keys: Ctrl/Alt/Shift')
                msg.exec_()
                return
            Setup.config['keys'] = dict(Ctrl = self.ctrl, Alt = self.alt,
                Shift = self.shift, Extra = self.extra)
            self.parent.updateKeyCombinations()
            self.close()

class Settings(QWidget):
    """
    Image Resizer Settings Window
    """
    def __init__(self, setup, config, parent = None):
        super(Settings, self).__init__(parent=parent)

        self.parent = parent
        self.setup = setup
        self.pickleFile = Setup.pickleFile

        self.setupUI()
        self.checkPickle()

    def checkPickle(self):
        """if the config file exists, load it,
           or continue to use the default setting if the config file
           doesn't exist
        """
        if os.path.exists(self.pickleFile):
            self.loadFromDisk()

    def saveToDisk(self):
        """save settings to the current directory where the plugin lies,
           then close the settings window
        """
        Setup.config['isUpScalingDisabled'] = self.disableUpScalingCb.isChecked();
        Setup.config['auto'] = self.enableCb.isChecked()
        Setup.config['width'] = self.widthEdit.text()
        Setup.config['height'] = self.heightEdit.text()
        if self.ratioCb.currentIndex() == 0:
            Setup.config['ratioKeep'] = 'height'
        elif self.ratioCb.currentIndex() == 1:
            Setup.config['ratioKeep'] = 'width'
        elif self.ratioCb.currentIndex() == 2:
            Setup.config['ratioKeep'] = 'either'
        if self.scalingCb.currentIndex() == 0:
            Setup.config['scalingMode'] = 'fast'
        elif self.scalingCb.currentIndex() == 1:
            Setup.config['scalingMode'] = 'smooth'
        with open(self.pickleFile, 'wb') as f:
            pickle.dump(Setup.config, f)

        logger.debug('saved config to config.pickle: {}'.format(Setup.config))
        self.close()

    def fillInMissedKeys(self, previousConfig, newConfig):
        for key in previousConfig:
            if key not in newConfig:
                newConfig[key] = previousConfig[key]

    def loadFromDisk(self):
        """Load settings from disk
        """
        with open(self.pickleFile, 'rb') as f:
            Setup.config = pickle.load(f)

        self.fillInMissedKeys(Setup.defaultConfig, Setup.config)

        # reflect the settings on the window
        self.enableCb.setChecked(Setup.config['auto'])
        self.disableUpScalingCb.setChecked(Setup.config['isUpScalingDisabled'])
        self.updateKeyCombinations()
        self.widthEdit.setText(Setup.config['width'])
        self.heightEdit.setText(Setup.config['height'])
        if Setup.config['ratioKeep'] == 'height':
            self.ratioCb.setCurrentIndex(0)
        elif Setup.config['ratioKeep'] == 'width':
            self.ratioCb.setCurrentIndex(1)
        elif Setup.config['ratioKeep'] == 'either':
            self.ratioCb.setCurrentIndex(2)
        self.setLineEditState()
        if Setup.config['scalingMode'] == 'fast':
            self.scalingCb.setCurrentIndex(0)
        elif Setup.config['scalingMode'] == 'smooth':
            self.scalingCb.setCurrentIndex(1)
        logger.debug('config is loaded from config.pickle: {}'.format(Setup.config))

    def reset(self):
        """reset all configurations to default"""
        if os.path.exists(Setup.irFolder):
            logger.debug('removing ImageResizer\'s folder')
            shutil.rmtree(Setup.irFolder)
        logger.debug('set config to the default one: {}'.format(Setup.defaultConfig))
        Setup.config = copy.deepcopy(Setup.defaultConfig)
        self.setup.checkConfigAndLoad() 
        self.checkPickle()

    def updateKeyCombinations(self):
        """
        update the key combination label
        in the settings window according to Setup.config
        """
        label = self.grabKeyLabel
        label.setText('Shortcut to paste the resized image: ')

        # add ctrl/shift/alt
        [label.setText(label.text() + k + '+')
                for k, v in list(Setup.config['keys'].items())
                    if k != 'Extra' and v == True]

        # add the extra key
        if Setup.config['keys'].get('Extra'):
            label.setText(label.text() +
                    Setup.config['keys'].get('Extra'))

        logger.debug('shortcut is updated: {}'.format(Setup.config['keys']))

    def showGrabKey(self):
        self.GrabKeyWindow = GrabKey(self)

    def setupUI(self):
        # main layout
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        # add widgets to set shortcut
        self.enableCb = QCheckBox('Resize on pasting', self)
        self.disableUpScalingCb = QCheckBox('Disable upscaling', self)
        self.grabKeyLabel = QLabel('Shortcut to paste the resized image: Ctrl+Shift+V')
        grabKeyBtn = QPushButton('Grab the shortcut', self)
        grabKeyBtn.clicked.connect(self.showGrabKey)
        self.scalingCb = QComboBox(self)
        self.scalingCb.addItem('use fast resizing')
        self.scalingCb.addItem('use smooth resizing')
        keyHBox = QHBoxLayout()
        keyHBox.addWidget(self.grabKeyLabel)
        keyHBox.addWidget(grabKeyBtn)
        mainLayout.addWidget(self.enableCb)
        mainLayout.addWidget(self.disableUpScalingCb)
        mainLayout.addWidget(self.scalingCb)
        mainLayout.addLayout(keyHBox)

        # add widgets to set height and width
        widthLable = QLabel('width')
        heightLable = QLabel('height')
        self.widthEdit = QLineEdit(self)
        self.heightEdit = QLineEdit(self)
        self.ratioCb = QComboBox(self)
        self.ratioCb.addItem('scale to height and keep ratio')
        self.ratioCb.addItem('scale to width and keep ratio')
        self.ratioCb.addItem('scale to the maximum dimension and keep ratio')
        # QObject.connect(self.ratioCb, SIGNAL("currentIndexChanged(int)"), self.setLineEditState)
        self.ratioCb.currentIndexChanged.connect(self.setLineEditState)

        sizeLayout = QHBoxLayout()
        sizeLayout.addWidget(widthLable)
        sizeLayout.addWidget(self.widthEdit)
        sizeLayout.addWidget(heightLable)
        sizeLayout.addWidget(self.heightEdit)
        sizeLayout.addWidget(self.ratioCb)
        mainLayout.addLayout(sizeLayout)

        # add an horizontal line
        mainLayout.addWidget(self.hLine())

        # add OK and Cancel buttons
        okButton = QPushButton("OK")
        okButton.clicked.connect(self.saveToDisk)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.close)
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.reset)
        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(okButton)
        btnLayout.addWidget(cancelButton)
        btnLayout.addWidget(resetButton)
        mainLayout.addLayout(btnLayout)

        # center the window
        self.move(QDesktopWidget().availableGeometry().center() - self.frameGeometry().center())
        self.setWindowTitle('Image Resizer Settings')
        self.show()
        self.raise_()
        self.activateWindow()

    def disableLineEdit(self, lineEdit):
        lineEdit.setReadOnly(True)

        # change color
        palette = QPalette()
        palette.setColor(QPalette.Base, Qt.gray)
        palette.setColor(QPalette.Text, Qt.darkGray)
        lineEdit.setPalette(palette)

    def enableLineEdit(self, lineEdit):
        lineEdit.setReadOnly(False)

        # change color
        palette = QPalette()
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.Text, Qt.black)
        lineEdit.setPalette(palette)

    def setLineEditState(self):
        if self.ratioCb.currentIndex() == 0:
            self.disableLineEdit(self.widthEdit)
            self.enableLineEdit(self.heightEdit)
        elif self.ratioCb.currentIndex() == 1:
            self.disableLineEdit(self.heightEdit)
            self.enableLineEdit(self.widthEdit)
        elif self.ratioCb.currentIndex() == 2:
            self.enableLineEdit(self.heightEdit)
            self.enableLineEdit(self.widthEdit)

    def hLine(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

s = Setup(imageResizer)
