#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anki.hooks import wrap
from aqt.editor import Editor, EditorWebView

from bs4 import BeautifulSoup

from PyQt4.QtGui import *
from PyQt4.QtCore import *

REMOVE_ATTRIBUTES = [
        'font-family',
        'font-size',
        'background-color',
        'line-height',
]

def setMinimalFont(self, mime, _old):
    html = mime.html()
    soup = BeautifulSoup(html, 'html.parser')
    newMime = QMimeData()
    for tag in soup.recursiveChildGenerator():
        # remove attributes in the list
        try:
            for key, value in tag.attrs.items():
                new = value.split(';')
                new = ';'.join([s for s in new
                    if s.split(':')[0].strip() not in REMOVE_ATTRIBUTES])
                tag.attrs[key] = new
        except AttributeError: 
            # 'NavigableString' object has no attribute 'attrs'
            pass

    # assign the modified html to new Mime
    newMime.setHtml(soup.prettify())

    # default _processHtml method
    return _old(self, newMime)

EditorWebView._processHtml = wrap(EditorWebView._processHtml, setMinimalFont, 'around')
