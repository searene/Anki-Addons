#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anki.hooks import wrap
from aqt.editor import Editor, EditorWebView

import platform
from bs4 import BeautifulSoup

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

REMOVE_ATTRIBUTES = [
        'color',
        'background-color',
]

def get_parser():
    system = platform.system()
    if system == "Windows":
        return "html.parser"
    else:
        return "lxml"

def purgeAttributes(self, mime, _old):
    html = mime.html()
    soup = BeautifulSoup(html, get_parser())
    newMime = QMimeData()
    for tag in soup.recursiveChildGenerator():
        # remove attributes in the list
        index = -1
        try:
            for attr in tag.attrs:
                index += 1
                if attr.name != 'style':
                    continue
                new = attr.value.split(';')
                new = ';'.join([s for s in new
                    if s.split(':')[0].strip() not in REMOVE_ATTRIBUTES])
                tag.attrs[index] = (u'style', new)
        except AttributeError:
            # 'NavigableString' object has no attribute 'attrs'
            pass

    # assign the modified html to new Mime
    newMime.setHtml(str(soup))

    # default _processHtml method
    return _old(self, newMime)

EditorWebView._processHtml = wrap(EditorWebView._processHtml, purgeAttributes, 'around')
