#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This addon is used to purge the British pronunciation in longman dictionary. Because I'm learning American pronuncation.

author: Searene
"""
import platform

from PyQt6.QtCore import QMimeData
from aqt import gui_hooks
from aqt.editor import EditorWebView
from bs4 import BeautifulSoup


def get_parser():
    system = platform.system()
    if system == "Windows" or system == "Darwin":
        return "html.parser"
    else:
        return "lxml"


def get_new_mime(mime: QMimeData):
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
    return newMime


def init_addon():
    gui_hooks.editor_will_process_mime.append(will_process_mime_handler)


def will_process_mime_handler(mime: QMimeData, editor_web_view: EditorWebView, internal: bool, extended: bool,
                              drop_event: bool):
    return get_new_mime(mime)
