#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anki.hooks import wrap
from aqt.editor import Editor, EditorWebView

import os
import sys
from BeautifulSoup import BeautifulSoup

from PyQt4.QtGui import *
from PyQt4.QtCore import *

REMOVE_ATTRIBUTES = [
        'color',
        'background-color',
]

def purgeAttributes(self, mime, _old):
    html = mime.html()
    soup = BeautifulSoup(html)
    newMime = QMimeData()
    for tag in soup.recursiveChildGenerator():
        # remove attributes in the list
        index = -1
        try:
            for key, value in tag.attrs:
                index += 1
                if key != 'style':
                    continue
                new = value.split(';')
                new = ';'.join([s for s in new
                    if s.split(':')[0].strip() not in REMOVE_ATTRIBUTES])
                tag.attrs[index] = (u'style', new)
        except AttributeError: 
            # 'NavigableString' object has no attribute 'attrs'
            pass

    # assign the modified html to new Mime
    newMime.setHtml(str(soup).decode('utf8'))

    # default _processHtml method
    return _old(self, newMime)

EditorWebView._processHtml = wrap(EditorWebView._processHtml, purgeAttributes, 'around')
