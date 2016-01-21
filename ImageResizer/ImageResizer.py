#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anki.hooks import wrap
from aqt.utils import tooltip
from aqt.editor import Editor, EditorWebView
from aqt import mw

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import os
import pickle


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
        width = '500',
        height = '300',
        ratioKeep = 'width'
    )

    settingsMw = None
    addonDir = mw.pm.addonFolder()
    irFolder = os.path.join(addonDir, 'ImageResizer')
    pickleFile = os.path.join(irFolder, 'config.pickle')
    isPasting = False

    def __init__(self, imageResizer):
        self.checkConfigAndLoad()
        self.setupMenu()
        self.setupFunctions(imageResizer)

    def checkConfigAndLoad(self):
        """Check if the ImageResizer folder exists
           Create one if not, then load the configuration
        """
        if not os.path.exists(self.irFolder):
            os.makedirs(self.irFolder)
        if not os.path.exists(self.pickleFile):
            # dump the default config if config.pickle doesn't exist
            with open(self.pickleFile, 'wb') as f:
                pickle.dump(Setup.config, f)

        # load config.pickle
        with open(self.pickleFile, 'rb') as f:
            Setup.config = pickle.load(f)

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
        EditorWebView._processMime = wrap(EditorWebView._processMime, _processMime_around, 'around')
        Editor.imageResizer = imageResizer

        # resize image when pasting
        EditorWebView._processImage = wrap(EditorWebView._processImage, _processImage_around, 'around')

    def _settings(self):
        """
        Show the settings dialog if the user clicked on the menu
        """
        self.settingsMw = Settings(Setup.config)

def resize(mime):
    """Resize the image

    :mime: mime to be resized
    :returns: resized QImage

    """
    im = QImage(mime.imageData())
    if Setup.config['ratioKeep'] == 'height':
        # scale the image to the given height and keep ratio
        im = im.scaledToHeight(int(Setup.config['height']))
    elif Setup.config['ratioKeep'] == 'width':
        # scale the image to the given width and keep ratio
        im = im.scaledToWidth(int(Setup.config['width']))
    return im

def imageResizer(self):
    mime = mw.app.clipboard().mimeData()
    n = QMimeData()
    if mime.hasImage():
        Setup.isPasting = True
        n.setImageData(mime.imageData())
        QApplication.clipboard().setMimeData(n)
        QApplication.focusWidget().onPaste()

def ImageResizerButton(self):
    shortcut = '+' .join([k for k, v in Setup.config['keys'].items() if v == True])
    shortcut += '+' + Setup.config['keys']['Extra']
    self._addButton("Image Resizer", lambda s = self: imageResizer(self), _(shortcut), 
        text="Image Resizer", size=True)

def _processMime_around(self, mime, _old):
    """ process image only if QMimeData contains image
    """
    if mime.hasImage():
        return self._processImage(mime)
    else:
        return _old(self, mime)

def _processImage_around(self, mime, _old):
    """
    Resize the image before processing
    """
    if Setup.config['auto'] == True or Setup.isPasting == True:
        im = resize(mime)
        # assign the new imageData to the old _processImage function to use
        new = QMimeData()
        new.setImageData(im)
        ret = _old(self, new)
        Setup.isPasting = False
    else:
        ret = _old(self, mime)
    return ret

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
    def __init__(self, config):
        super(Settings, self).__init__()

        Setup.config = Setup.config
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
        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(okButton)
        btnLayout.addWidget(cancelButton)
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

