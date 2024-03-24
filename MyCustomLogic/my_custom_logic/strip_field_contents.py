from typing import Optional

from anki.utils import strip_html_media
from aqt import QMimeData
from aqt.editor import EditorWebView
from aqt.gui_hooks import editor_will_process_mime


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
    if editor_web_view.editor.note.note_type()['flds'][editor_web_view.editor.currentField]['name'] not in (
    "Sentence", "Meaning"):
        return mime
    plain_text = get_plain_text(mime)
    if plain_text is None:
        return mime
    new_mime = QMimeData()
    new_mime.setText(plain_text.strip())
    return new_mime


def start():
    editor_will_process_mime.append(will_process_mime_handler)
