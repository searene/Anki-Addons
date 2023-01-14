#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This addon is used to purge the British pronunciation in longman dictionary. Because I'm learning American pronuncation.

author: Searene
"""
import platform
import re

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


def remove_longman5_dsl_bre(soup):
    audio_span = soup.findAll('span', attrs={'class': 'dsl_p'})
    if len(audio_span) > 1 and 'BrE' in audio_span[1].string:
        bre_span = audio_span[1]
        bre_span.nextSibling.nextSibling.extract()
        bre_span.nextSibling.extract()
        bre_span.extract()


def remove_unnecessary_tags_in_longman5_mdx(soup):
    audio_tag = soup.findAll('a', href=re.compile(r'.*las2_br.mp3$'))
    if len(audio_tag) > 0:
        audio_tag[0].extract()

    super_script_span = soup.findAll('span', attrs={'class': 'HOMNUM'})
    if len(super_script_span) > 0:
        super_script_span[0].extract()


def get_new_mime(mime: QMimeData):
    html = mime.html()
    soup = BeautifulSoup(html, get_parser())
    remove_longman5_dsl_bre(soup)
    remove_unnecessary_tags_in_longman5_mdx(soup)

    newMime = QMimeData()
    newMime.setHtml(str(soup))
    return newMime


def init_addon():
    gui_hooks.editor_will_process_mime.append(will_process_mime_handler)


def will_process_mime_handler(mime: QMimeData, editor_web_view: EditorWebView, internal: bool, extended: bool,
                              drop_event: bool):
    return get_new_mime(mime)
