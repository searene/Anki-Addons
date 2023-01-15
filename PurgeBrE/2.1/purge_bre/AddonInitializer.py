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
from bs4 import BeautifulSoup, ResultSet


def get_parser():
    system = platform.system()
    if system == "Windows" or system == "Darwin":
        return "html.parser"
    else:
        return "lxml"


def remove_unnecessary_contents_in_longman5(soup):
    imgs = soup.findAll("img", src="qrcx://localhost/icons/playsound.png", alt="Play")
    for img in imgs:
        img.extract()

    audio_span = soup.findAll('span', attrs={'class': 'dsl_p'})
    if len(audio_span) > 1 and 'BrE' in audio_span[1].string:
        bre_span = audio_span[1]
        bre_span.nextSibling.nextSibling.extract()
        bre_span.nextSibling.extract()
        bre_span.extract()


def remove_bre_in_longman5_mdx(soup: BeautifulSoup):
    sound_tags: ResultSet = soup.find_all('span', attrs={'class': 'golden-dict-media-word-sound'})

    for sound_tag in sound_tags:
        if "/media/english/breProns" in sound_tag.get('data-original-href'):
            sound_tag.extract()
            break


def remove_superscript_next_to_word(soup):
    super_script_span = soup.findAll('span', attrs={'class': 'HOMNUM'})
    if len(super_script_span) > 0:
        super_script_span[0].extract()


# def remove_first_word_sound_in_longman5_mds(soup: BeautifulSoup):
#     sound_tags: ResultSet = soup.find_all('span', attrs={'class': 'golden-dict-media-word-sound'})
#
#     for sound_tag in sound_tags:
#         if sound_tag.parent is not None and sound_tag.parent['class'] == ['Head'] and len(sound_tag.find_all()) == 0 and len(sound_tag.parent.find_all(recursive=False)) == 4:
#             sound_tag.extract()
#             break


def remove_duplicate_sound(soup: BeautifulSoup):
    sound_tags: ResultSet = soup.find_all('span', attrs={'class': 'golden-dict-media-word-sound'})

    sounds = set()
    for sound_tag in sound_tags:
        # extract the sound file name using regex
        sound_file_name = re.search(r'\[sound:(.+)]', sound_tag.text).group(1)
        if sound_file_name in sounds:
            sound_tag.extract()
            continue
        sounds.add(sound_file_name)



def remove_unnecessary_tags_in_longman5_mdx(soup: BeautifulSoup):
    remove_bre_in_longman5_mdx(soup)
    remove_superscript_next_to_word(soup)
    remove_duplicate_sound(soup)


def get_new_mime(mime: QMimeData):
    html = mime.html()
    with open("/tmp/test_anki", "w", encoding="utf8") as f:
        f.write(html)
    soup = BeautifulSoup(html, get_parser())
    remove_unnecessary_contents_in_longman5(soup)
    remove_unnecessary_tags_in_longman5_mdx(soup)

    new_mime = QMimeData()
    new_mime.setHtml(str(soup))
    return new_mime


def init_addon():
    gui_hooks.editor_will_process_mime.append(will_process_mime_handler)


def will_process_mime_handler(mime: QMimeData, editor_web_view: EditorWebView, internal: bool, extended: bool,
                              drop_event: bool):
    return get_new_mime(mime)
