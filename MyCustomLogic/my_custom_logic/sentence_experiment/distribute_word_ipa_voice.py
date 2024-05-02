import re
import warnings

from aqt.editor import Editor
from aqt.gui_hooks import editor_did_paste
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning


def is_sentence_experiment_type(editor: Editor) -> bool:
    note_type_name = editor.note.note_type()['name']
    return note_type_name == "Sentence Experiment"


def distribute_word_ipa_voice_hook(editor: Editor, html_contents: str, internal: bool, extended: bool):
    distribute(editor, html_contents, internal, extended)


def distribute(editor: Editor, html_contents: str, internal: bool, extended: bool):
    # Match the specific format
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
        plain_text = BeautifulSoup(html_contents, "html.parser").get_text()
        print(plain_text)
    match = re.match(r"([^/\d]+)[^/]*/(.+?)/\s*\[sound:(.+?)]\s*([\u25cf\s\w]+)", plain_text)

    if match and is_sentence_experiment_type(editor):
        word, ipa, sound, type_info = match.groups()

        # Check if we are in the "Word" field
        current_field_name = editor.note.note_type()['flds'][editor.currentField]['name']
        if current_field_name != "Word":
            return

        # Update the "Word" field
        editor.note.fields[editor.currentField] = word.strip()

        # Find and update other fields
        for idx, fld in enumerate(editor.note.note_type()['flds']):
            if fld['name'] == 'Word':
                editor.note.fields[idx] = f"{word}"
            elif fld['name'] == "IPA":
                editor.note.fields[idx] = f"/{ipa}/"
            elif fld['name'] == "Voice":
                editor.note.fields[idx] = f"[sound:{sound}]"
            elif fld['name'] == "Part of Speech":
                editor.note.fields[idx] = type_info

        # Force update of the editor UI to reflect changes
        editor.loadNote()
