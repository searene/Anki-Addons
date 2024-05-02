from aqt import mw
from aqt.qt import QAction, qconnect
from aqt.utils import showText

from my_custom_logic.common import get_field_contents


def extract_sentences():
    # Get all cards added today
    card_ids = mw.col.find_cards(f"added:1")
    sentences = []

    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        note = card.note()
        if 'English' not in note.note_type()['name']:
            continue
        # Assuming "Sentence" is the field name
        sentence = get_field_contents("Sentence", note).replace("&nbsp;", " ")
        if sentence and sentence not in sentences:
            sentences.append(sentence)

    display_text = "\n".join(sentences)
    showText("Is there any grammatical error in any of the following sentence/expressions? Notice that each sentence/expression is independent of each other:\n" + display_text)


def start():
    action = QAction("Show Sentences from Today's Cards", mw)
    qconnect(action.triggered, extract_sentences)
    mw.form.menuTools.addAction(action)
