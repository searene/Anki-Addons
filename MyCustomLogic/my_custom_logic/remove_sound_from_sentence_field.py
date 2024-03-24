from typing import Optional

from anki.utils import strip_html_media
from aqt.gui_hooks import editor_will_process_mime
from aqt import QMimeData
from aqt.editor import EditorWebView


def get_plain_text(mime: QMimeData) -> Optional[str]:
    if mime.hasHtml():
        return strip_html_media(mime.html())
    if mime.hasText():
        return mime.text()
    return None


def remove_sound(plain_text: str) -> str:
    """Remove the sound tag from the plain text. For example,
       if the current contents are "[sound: abc.mp3] Hello World", it will return "Hello World"."""
    return plain_text.replace("[sound:", "").replace("]", "").strip()


def remove_sound_from_sentence_field(mime: QMimeData, editor_web_view: EditorWebView, internal: bool, extended: bool,
                              drop_event: bool):
    editor = editor_web_view.editor
    if editor.note.note_type()['flds'][editor.currentField]['name'] != "Sentence":
        return mime
    plain_text = get_plain_text(mime)
    if plain_text is None:
        return mime
    new_mime = QMimeData()
    new_mime.setText(remove_sound(plain_text))
    return new_mime


def start():
    editor_will_process_mime.append(remove_sound_from_sentence_field)
