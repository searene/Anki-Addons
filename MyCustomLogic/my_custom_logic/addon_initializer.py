import subprocess
from typing import Optional

from anki.utils import strip_html_media
from aqt.utils import showInfo
from bs4 import BeautifulSoup, NavigableString
import re

from aqt.editor import Editor, EditorWebView
from aqt.gui_hooks import editor_did_paste, editor_will_process_mime, sync_will_start
from aqt import QMimeData, mw


def has_all_required_fields(editor: Editor) -> bool:
    """The current note type should have the following fields: Word, IPA, Pronunciation, Type"""
    required_fields = {"Word", "IPA", "Pronunciation", "Type"}
    current_fields = {fld['name'] for fld in editor.note.note_type()['flds']}
    return required_fields.issubset(current_fields)


def paste_hook(editor: Editor, html_contents: str, internal: bool, extended: bool):
    distribute_pasted_content(editor, html_contents, internal, extended)


def distribute_pasted_content(editor: Editor, html_contents: str, internal: bool, extended: bool):
    # Match the specific format
    plain_text = BeautifulSoup(html_contents, "html.parser").get_text()
    match = re.match(r"([^/]+)\s*/(.+?)/\s*\[sound:(.+?)]\s*(.+)", plain_text)

    if match and has_all_required_fields(editor):
        word, ipa, sound, type_info = match.groups()

        # Check if we are in the "Word" field
        current_field_name = editor.note.note_type()['flds'][editor.currentField]['name']
        if current_field_name == "Word":
            # Update the "Word" field
            editor.note.fields[editor.currentField] = word.strip()

            # Find and update other fields
            for idx, fld in enumerate(editor.note.note_type()['flds']):
                if fld['name'] == "IPA":
                    editor.note.fields[idx] = f"/{ipa}/"
                elif fld['name'] == "Pronunciation":
                    editor.note.fields[idx] = f"[sound:{sound}]"
                elif fld['name'] == "Type":
                    editor.note.fields[idx] = type_info

            # Force update of the editor UI to reflect changes
            editor.loadNote()


def get_plain_text(mime: QMimeData) -> Optional[str]:
    if mime.hasHtml():
        return strip_html_media(mime.html())
    if mime.hasText():
        return mime.text()
    return None


def will_process_mime_handler(mime: QMimeData, editor_web_view: EditorWebView, internal: bool, extended: bool,
                              drop_event: bool):
    """If the current pasted content has carriage returns or empty spaces before or after it, remove them."""
    # Check if the current field is called "Sentence"
    if editor_web_view.editor.note.note_type()['flds'][editor_web_view.editor.currentField]['name'] != "Sentence":
        return mime
    plain_text = get_plain_text(mime)
    if plain_text is None:
        return mime
    new_mime = QMimeData()
    new_mime.setText(plain_text.strip())
    return new_mime


def convert_audio_files():
    # Path to your bash script
    script_path = "/Users/joeygreen/apps/scripts/convert_ogg_to_mp3.sh"
    try:
        subprocess.run(["zsh", script_path], check=True)
        showInfo("Audio files are converted successfully.")
    except subprocess.CalledProcessError:
        showInfo("Failed to convert audio files.")


def replace_ogg_with_mp3():
    all_notes = mw.col.find_notes("")
    updated = 0

    for nid in all_notes:
        note = mw.col.get_note(nid)

        for fname, fval in note.items():
            if "[sound:" in fval and ".ogg]" in fval:
                ogg_file = fval.split('[sound:')[1].split('.ogg]')[0]
                note[fname] = fval.replace(f"{ogg_file}.ogg", f"{ogg_file}.mp3")
                mw.col.update_note(note)
                updated += 1

    showInfo(f"Updated {updated} notes from ogg to mp3.")


def sync_will_start_callback():
    convert_audio_files()
    replace_ogg_with_mp3()


def init_addon():
    # Attach the function to the hook
    editor_did_paste.append(paste_hook)
    editor_will_process_mime.append(will_process_mime_handler)
    sync_will_start.append(sync_will_start_callback)


if __name__ == '__main__':
    init_addon()