import re
import warnings

from aqt.editor import Editor
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from my_custom_logic.common.util import strip, split


def is_sentence_experiment_type(editor: Editor) -> bool:
    note_type_name = editor.note.note_type()['name']
    return note_type_name == "Sentence Experiment"


def distribute_word_ipa_voice_hook(editor: Editor, html_contents: str, internal: bool, extended: bool):
    distribute(editor, html_contents, internal, extended)


def distribute(editor: Editor, html_contents: str, internal: bool, extended: bool):
    if not is_sentence_experiment_type(editor):
        return

    # Match the specific format
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
        plain_text = BeautifulSoup(html_contents, "html.parser").get_text()
        print(plain_text)

    word, ipa, sound, pos = split(plain_text)

    if ipa == "" and sound == "" and pos == "":
        return

    # Check if we are in the "Word" field
    current_field_name = editor.note.note_type()['flds'][editor.currentField]['name']
    if current_field_name != "Word":
        return

    # Update the "Word" field
    editor.note.fields[editor.currentField] = strip(word)

    # Find and update other fields
    for idx, fld in enumerate(editor.note.note_type()['flds']):
        if fld['name'] == 'Word':
            editor.note.fields[idx] = word
        elif fld['name'] == "IPA":
            editor.note.fields[idx] = ipa
        elif fld['name'] == "Voice":
            editor.note.fields[idx] = sound
        elif fld['name'] == "Part of Speech":
            editor.note.fields[idx] = pos

    # Force update of the editor UI to reflect changes
    editor.loadNote()
