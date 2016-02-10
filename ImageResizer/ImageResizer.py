#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anki.hooks import wrap
from anki.media import MediaManager
from aqt.utils import tooltip, showWarning
from aqt.editor import Editor, EditorWebView
from aqt import mw

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *

import os
import pickle
import logging
import copy
import shutil
import uuid
import tempfile
import urllib2


# Get log file
irFolder = os.path.join(mw.pm.addonFolder(), 'ImageResizer')
logFile = os.path.join(irFolder, 'imageResizer.log')

# if ImageResizer's folder doesn't exist, create one
if not os.path.exists(irFolder):
    os.makedirs(irFolder)

# create the logFile
open(logFile, 'a').close()

# setup logger
logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename = logFile, level = logging.DEBUG)
logger = logging.getLogger(__name__)

# global variable to record whether anki is processing an image file or not, the addon will try to scale the image in the writeData function is the variable is set True
processingPic = False

# current image file's suffix
curSuffix = None

# settings main window, Qt won't show the window if
# we don't assign a global variable to Settings()

class Setup(object):

    """Do all the necessary initialization when anki
       loads the addon
    """

    config = dict(
        auto = True,
        keys = dict(Ctrl = True, Alt = False, 
                Shift = True, Extra = 'V'),
        width = '400',
        height = '400',
        ratioKeep = 'height'
    )

    defaultConfig = copy.deepcopy(config)

    settingsMw = None
    addonDir = mw.pm.addonFolder()

    logger.debug("Get addon Dir {}".format(addonDir))

    irFolder = os.path.join(addonDir, 'ImageResizer')

    logger.debug("ImageResizer's config folder: {}".format(irFolder))

    pickleFile = os.path.join(irFolder, 'config.pickle')

    logger.debug("pickleFile: {}".format(pickleFile))

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
        mw.connect(action, SIGNAL("triggered()"), self._settings)
        mw.form.menuTools.addAction(action)

    def setupFunctions(self, imageResizer):
        """Replace functions in anki
        """
        # setup button
        Editor.setupButtons = wrap(Editor.setupButtons, ImageResizerButton, 'after')
        Editor.imageResizer = imageResizer

        # wrap writeData so we can scale the image file beforehand
        MediaManager.writeData = wrap(MediaManager.writeData, _writeData_around, 'around')
        EditorWebView._processMime = wrap(EditorWebView._processMime, _processMime_around, 'around')

    def _settings(self):
        """
        Show the settings dialog if the user clicked on the menu
        """
        self.settingsMw = Settings(self, Setup.config)

def resize(im):
    """Resize the image

    :im: QImage to be resized
    :returns: resized QImage

    """
    logger.debug('resizing images...')
    logger.debug('image before resizing, width: {}, height: {}'.format(im.width(), im.height()))
    if Setup.config['ratioKeep'] == 'height':
        # scale the image to the given height and keep ratio
        logger.debug('scale according to height: {}'.format(Setup.config['height']))
        im = im.scaledToHeight(int(Setup.config['height']))
    elif Setup.config['ratioKeep'] == 'width':
        # scale the image to the given width and keep ratio
        logger.debug('scale according to width: {}'.format(Setup.config['width']))
        im = im.scaledToWidth(int(Setup.config['width']))
    logger.debug('image after resizing, width: {}, height: {}'.format(im.width(), im.height()))
    return im

def imageResizer(self, paste = True):
    """resize the image contained in the clipboard
       paste: paste the resized image in the currently focused widget if the parameter is set True

       returns: QMimeData"""

    global processingPic

    mime = mw.app.clipboard().mimeData()

    # check if mime contains any image related urls, and put the image data in the clipboard if it contains it
    mime = checkPicFile(mime)

    # check if mime contains images or any image file urls
    if mime.hasImage():
        logger.debug('mime contains images relative data in it, set processingPic as True and paste it, _writeData_around will resize it')

        # set processingPic as True so that _writeData_around will resize the image
        processingPic = True

        if paste:
            # paste it in the currently focused widget
            QApplication.focusWidget().onPaste()

    return mime

def ImageResizerButton(self):
    shortcut = '+' .join([k for k, v in Setup.config['keys'].items() if v == True])
    shortcut += '+' + Setup.config['keys']['Extra']
    self._addButton("Image Resizer", lambda s = self: imageResizer(self), _(shortcut), 
        text="Image Resizer", size=True)

def _processMime_around(self, mime, _old):
    """I found that anki dealt with html, urls, text first before dealing with image, I didn't find any advantages in it. If the user wants to copy an image from the web broweser, it will cause anki to fetch the image again, which is a waste of time. the function will try to deal with image data first if mime contains it"""

    if Setup.config['auto'] == False:
        return _old(self, mime)

    logger.debug('getting the resized QImage...')
    mime = self.editor.imageResizer(paste = False)

    if mime.hasImage():

        logger.debug('set processingPic as True so _writeData_around will resize it')
        global processingPic
        processingPic = True

        logger.debug('let anki handle the resized image')
        return self._processImage(mime)

    else:
        logger.debug("image data isn't detected, run the old _processMime function")
        return _old(self, mime)

def _writeData_around(self, opath, filecontents, _old):
    """scale the image contained in filecontents before it is written in disk"""

    global processingPic, curSuffix

    logger.debug("entered _writeData_around, processingPic: {}, curSuffix: {}, Setup.config['auto']: {}".format(processingPic, curSuffix, Setup.config['auto']))

    try:
        if processingPic:
            # This is an image file, scale it

            # load filecontents to QImage
            im = QImage()
            im.loadFromData(filecontents)

            # get the resized image data with the help of QMime
            im_resized = resize(im)

            # get the filecontents of the resized image, I cannot find a convenient API to acheive this, so I decided to save the QImage to disk and read it to filecontents
            logger.debug('Writing the resized image to disk to read the file contents in the image...')
            fp = tempfile.NamedTemporaryFile()
            logger.debug('temporary file name: {}'.format(fp.name))
            im_resized.save(fp.name, curSuffix if curSuffix else 'PNG')
            fp.seek(0)
            filecontents = fp.read()
            fp.close()
    except Exception, e:
        showWarning(_("An error occurred while opening %s") % e)
    finally:
        processingPic = False
        curSuffix = None

        logger.debug('calling the old writeData function...')
        return _old(self, opath, filecontents)

def checkPicFile(mime):
    """check if mime contains url and if the url represents a picture file path, fetch the url and put the image in the clipboard if the url represents an image file

    :mime: QMimeData to be checked
    :returns: image filled QMimeData if the contained url represents an image file, the original QMimeData otherwise

    """
    logger.debug('checking if url contained in mime is a pic file...')
    pic = ("jpg", "jpeg", "png", "tif", "tiff", "gif", "svg", "webp")
    # if mime doesn't contain url, return None directly
    if not mime.hasUrls():
        logger.debug('mime doesn\'t contain urls')
        return mime
    url = mime.urls()[0].toString()

    # check prefix
    if not url.startswith('file://'):
        logger.debug('prefix doesn\'t qualify')
        return mime

    # check suffix
    for suffix in pic:
        if url.endswith(suffix):
            logger.debug('suffix {} meet requirements'.format(suffix))
            global curSuffix
            curSuffix = suffix

            # fetch the image, put it in the mime and return it
            im = QImage()
            im.load(url[7:])
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
    def __init__(self, setup, config):
        super(Settings, self).__init__()

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
        Setup.config['auto'] = self.enableCb.isChecked()
        Setup.config['width'] = self.widthEdit.text()
        Setup.config['height'] = self.heightEdit.text()
        if self.ratioCb.currentIndex() == 0:
            Setup.config['ratioKeep'] = 'height'
        elif self.ratioCb.currentIndex() == 1:
            Setup.config['ratioKeep'] = 'width'
        with open(self.pickleFile, 'wb') as f:
            pickle.dump(Setup.config, f)

        logger.debug('saved config to config.pickle: {}'.format(Setup.config))
        self.close()

    def loadFromDisk(self):
        """Load settings from disk
        """
        with open(self.pickleFile, 'rb') as f:
            Setup.config = pickle.load(f)

        # reflect the settings on the window
        self.enableCb.setChecked(Setup.config['auto'])
        self.updateKeyCombinations()
        self.widthEdit.setText(Setup.config['width'])
        self.heightEdit.setText(Setup.config['height'])
        if Setup.config['ratioKeep'] == 'height':
            self.ratioCb.setCurrentIndex(0)
        elif Setup.config['ratioKeep'] == 'width':
            self.ratioCb.setCurrentIndex(1)
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
        label.setText('Current Key Combinations to paste the resized image: ')

        # add ctrl/shift/alt
        [label.setText(label.text() + k + '+')
                for k, v in Setup.config['keys'].items()
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
        self.enableCb = QCheckBox('Automatically resize the image when pasting', self)
        self.grabKeyLabel = QLabel('Current Key Combinations to paste the resized image: Ctrl+Shift+V')
        grabKeyBtn = QPushButton('Grab the key combinations', self)
        grabKeyBtn.clicked.connect(self.showGrabKey)
        keyHBox = QHBoxLayout()
        keyHBox.addWidget(self.grabKeyLabel)
        keyHBox.addWidget(grabKeyBtn)
        mainLayout.addWidget(self.enableCb)
        mainLayout.addLayout(keyHBox)

        # add widgets to set height and width
        widthLable = QLabel('width')
        heightLable = QLabel('height')
        self.widthEdit = QLineEdit(self)
        self.heightEdit = QLineEdit(self)
        self.ratioCb = QComboBox(self)
        self.ratioCb.addItem('scale to height and keep ratio')
        self.ratioCb.addItem('scale to width and keep ratio')
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

    def hLine(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

s = Setup(imageResizer)
