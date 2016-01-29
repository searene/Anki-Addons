#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anki.hooks import wrap
from aqt.editor import Editor, EditorWebView
from aqt import dialogs

import os
import sys
from BeautifulSoup import BeautifulSoup

from PyQt4.QtGui import *
from PyQt4.QtCore import *

addressMap = {'e73293ef041cad84654c62963f7b6bb7': '/media/OS/Dictionaries/longman5/En-En-Longman_DOCE5.dsl.dz.files', 
        '4f74aab894b66b99af88061eadcf5104': '/media/OS/Dictionaries/Webster\'s Collegiate Dictionary/Webster\'s Collegiate Dictionary.dsl.files'}

def importMedia(self, mime, _old):
    """import audios and images from goldendict"""

    # find out where we are
    if dialogs._dialogs['AddCards'][1]:
        # we are adding cards
        window = dialogs._dialogs['AddCards'][1]
    elif dialogs._dialogs['Browser'][1]:
        # we are browsing cards
        window = dialogs._dialogs['Browser'][1]
    else:
        # I don't know where we are, just exit
        return _old(self, mime) 

    html = mime.html()
    soup = BeautifulSoup(html)
    newMime = QMimeData()

    # sound
    links = [link for link in soup.findAll('a') if 'gdau' in link['href']]

    # images
    links += [link for link in soup.findAll('img') if 'bres' in link['src']]
    
    for src, target in addressMap.items():

        # remove \ or / in the end of every addressMap item
        src = src[:-1] if src[-1] == '/' else src
        target = target[-1] if target[-1] == '/' or target[-1] == '\\' else target

        for link in links:

            attr = 'href' if link.get('href') else 'src'

            if src in link[attr]:

                # get the full path of the media file
                file = link[attr].replace(src, target)
                file = file[file.find(':') + 3:]

                # import the file to anki
                ankiMedia = window.editor._addMedia(file, canDelete=True)
                # sound
                if attr == 'href': 
                    span = link.parent
                    # delete the original link, because we don't need it any more
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

    # default _processHtml method
    return _old(self, newMime)

EditorWebView._processHtml = wrap(EditorWebView._processHtml, importMedia, 'around')
