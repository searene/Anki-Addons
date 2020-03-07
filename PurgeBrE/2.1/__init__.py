#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This addon is used to purge the British pronunciation in longman dictionary. Because I'm learning American pronuncation.

author: Searene
"""

from anki.hooks import wrap
from aqt.editor import Editor, EditorWebView

from bs4 import BeautifulSoup

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import platform


def get_parser():
    system = platform.system()
    if system == "Windows":
        return "html.parser"
    else:
        return "lxml"


def purgeBrE(self, mime, _old):
    """purge British pronunciation
    """
    html = mime.html()
    soup = BeautifulSoup(html, get_parser())
    audioSpan = soup.findAll('span', attrs={'class': 'dsl_p'})
    if len(audioSpan) > 1 and 'BrE' in audioSpan[1].string:
        breSpan = audioSpan[1]
        breSpan.nextSibling.nextSibling.extract()
        breSpan.nextSibling.extract()
        breSpan.extract()

    newMime = QMimeData()
    newMime.setHtml(str(soup))
    return _old(self, newMime)


EditorWebView._processHtml = wrap(EditorWebView._processHtml, purgeBrE, 'around')
