from aqt import *

from my_custom_logic.common.util import to_plain_text
from my_custom_logic.common.voice.mello import MelloVoiceGenerator


class SentenceVoiceGenerator(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.voice_generator = MelloVoiceGenerator()

    def run(self):
        note_type = mw.col.models.by_name("Sentence Experiment")
        if not note_type:
            raise Exception("Cannot find the note type: Sentence Experiment")

        due_note_ids = mw.col.find_notes("\"note:Sentence Experiment\" prop:due=0")
        empty_note_ids = [note_id for note_id in mw.col.find_notes("\"note:Sentence Experiment\"") if not mw.col.get_note(note_id)['Sentence Voice'].strip()]
        note_ids = [*due_note_ids, *empty_note_ids]

        total_cards = len(note_ids)

        for index, note_id in enumerate(note_ids, start=1):
            note = mw.col.get_note(note_id)

            sentence = to_plain_text(note['Sentence'])

            self.progress_signal.emit(f"{index} / {total_cards}: Generating the voice for the sentence \"{sentence}\"…")

            sentence_voice = self.voice_generator.generate_voice(sentence)
            note['Sentence Voice'] = sentence_voice

            mw.col.update_note(note)

        self.finished_signal.emit()
