import re
import warnings

from aqt.editor import Editor
from aqt.gui_hooks import editor_did_paste
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from my_custom_logic.common.util import split


def has_all_required_fields(editor: Editor) -> bool:
    """The current note type should have the following fields: Word, IPA, Pronunciation, Type"""
    required_fields = {"Word", "IPA", "Pronunciation", "Part of Speech"}
    current_fields = {fld['name'] for fld in editor.note.note_type()['flds']}
    return required_fields.issubset(current_fields)


def paste_hook(editor: Editor, html_contents: str, internal: bool, extended: bool):
    distribute_pasted_content(editor, html_contents, internal, extended)


def distribute_pasted_content(editor: Editor, html_contents: str, internal: bool, extended: bool):
    if not has_all_required_fields(editor):
        return

    # Match the specific format
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
        plain_text = BeautifulSoup(html_contents, "html.parser").get_text()

    word, ipa, sound, pos = split(plain_text)

    if ipa == "" and sound == "" and pos == "":
        return

    # Check if we are in the "Word" field
    current_field_name = editor.note.note_type()['flds'][editor.currentField]['name']
    if current_field_name == "Word":
        # Update the "Word" field
        editor.note.fields[editor.currentField] = word

        # Find and update other fields
        for idx, fld in enumerate(editor.note.note_type()['flds']):
            if fld['name'] == "IPA":
                editor.note.fields[idx] = ipa
            elif fld['name'] == "Pronunciation":
                editor.note.fields[idx] = sound
            elif fld['name'] == "Part of Speech":
                editor.note.fields[idx] = pos

        # Force update of the editor UI to reflect changes
        editor.loadNote()


def start():
    editor_did_paste.append(paste_hook)
