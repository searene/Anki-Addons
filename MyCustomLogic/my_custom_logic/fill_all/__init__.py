import hashlib
import os
from typing import List, Optional, Dict

import requests
from anki.hooks import addHook
from aqt import mw
from aqt.editor import Editor
from aqt.sound import play
from aqt.utils import showInfo

from my_custom_logic.common.util import get_field_contents, remove_cloze, get_cloze_contents
from my_custom_logic.fill_all.word import fetch_word, Word


def get_word(editor: Editor) -> Optional[str]:
    word = get_field_contents("Word", editor.note)
    if word:
        return word
    sentence = get_field_contents("Sentence", editor.note)
    words = get_cloze_contents(sentence)
    if not words:
        return None
    return words[0]


def download_to_media_folder(audio_in_mdict: str) -> str:
    response = requests.get(f"http://localhost:8000/{audio_in_mdict.split('//')[1]}")
    if response.status_code == 200:
        # Generate a unique filename for the audio file
        filename = f"mdict-{hashlib.md5(audio_in_mdict.encode()).hexdigest()}.mp3"

        # Save the audio file to Anki's media collection directory
        with open(os.path.join(mw.col.media.dir(), filename), 'wb') as f:
            f.write(response.content)

        play(filename)
        return filename
    else:
        raise Exception("Failed to generate voice")


def get_sound(audio_in_mdict: str) -> str:
    audio_file_path = download_to_media_folder(audio_in_mdict)
    return f"[sound:{audio_file_path}]"


def get_field_contents_dict_for_cloze(word: Word, sentence: str) -> Dict[str, str]:
    res = {"Word": word.word}
    for word_entry in word.word_entries:
        for definition in word_entry.definitions:
            for example in definition.examples:
                if example.en == sentence:
                    res["Meaning"] = example.zh
                    res['Sentence Voice'] = get_sound(example.audio)
                    res["Word Meaning"] = f"<b>{definition.lex_unit if definition.lex_unit is not None else ''}</b> {definition.en} {definition.zh}"
                    res["Part of Speech"] = word_entry.pos
                    if word_entry.ipa:
                        res["IPA"] = word_entry.ipa
                    res["Pronunciation"] = get_sound(word_entry.pronunciation)
    return res


def on_generate_cloze_contents(editor: Editor):
    w = get_word(editor)
    if not w:
        showInfo("No word is available.")
        return
    sentence = remove_cloze(get_field_contents("Sentence", editor.note)).replace("&nbsp;", " ")
    word = fetch_word(w)
    if not word:
        showInfo("Didn't find the word in the dictionary: " + w)
        return

    field_contents_dict = get_field_contents_dict_for_cloze(word, sentence)
    fill_contents(editor, field_contents_dict)


def fill_contents(editor: Editor, field_contents_dict: Dict[str, str]):
    for idx, fld in enumerate(editor.note.note_type()['flds']):
        field_name = fld['name']
        if field_name in field_contents_dict:
            editor.note.fields[idx] = field_contents_dict[field_name]

    # Force update of the editor UI to reflect changes
    editor.loadNote()


def get_field_contents_dict_for_complete(word: Word, sentence: str) -> Dict[str, str]:
    res = {"Word": word.word}
    for word_entry in word.word_entries:
        for definition in word_entry.definitions:
            for example in definition.examples:
                if example.en == sentence:
                    res['Sentence Voice'] = get_sound(example.audio)
                    res["Meaning"] = f"<b>{definition.lex_unit if definition.lex_unit is not None else ''}</b> {definition.en} {definition.zh}"
                    res["Part of Speech"] = word_entry.pos
                    if word_entry.ipa:
                        res["IPA"] = word_entry.ipa
                    res["Pronunciation"] = get_sound(word_entry.pronunciation)
    return res


def on_generate_complete_contents(editor: Editor):
    w = get_field_contents("Word", editor.note)
    if not w:
        showInfo('No word is available.')
        return
    sentence = remove_cloze(get_field_contents("Sentence", editor.note)).replace("&nbsp;", " ")
    word = fetch_word(w)
    if not word:
        showInfo("Didn't find the word in the dictionary: " + w)
        return
    field_contents_dict = get_field_contents_dict_for_complete(word, sentence)
    fill_contents(editor, field_contents_dict)


def on_generate_contents_btn_clicked(editor: Editor):
    if editor.note.note_type()['name'] in ('English - Complete - With Reverse', 'English - Complete'):
        return on_generate_complete_contents(editor)
    elif editor.note.note_type()['name'] == 'English - Cloze':
        return on_generate_cloze_contents(editor)
    else:
        showInfo("This note type is not supported: " + editor.note.note_type()['name'])


def add_generate_contents_btn(buttons: List[str], editor: Editor) -> List[str]:
    """Add a custom button to the editor's button box."""
    icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'res', 'icon.png')
    editor._links['generate-cloze-contents'] = lambda editor: on_generate_contents_btn_clicked(editor)
    return buttons + [editor._addButton(icon_path,
                                        "generate-cloze-contents",
                                        "Generate Cloze Contents")]


def start():
    addHook("setupEditorButtons", lambda buttons, editor: add_generate_contents_btn(buttons, editor))
