from aqt import QThread, pyqtSignal, mw


class SentenceGenerator(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, answer_func):
        super().__init__()
        self.answer = answer_func

    def run(self):
        # Fetch all the cards whose note type is "Sentence Experiment"
        due_note_ids = mw.col.find_notes("\"note:Sentence Experiment\" prop:due=0")
        empty_note_ids = [note_id for note_id in mw.col.find_notes("\"note:Sentence Experiment\"") if not mw.col.get_note(note_id)['Sentence'].strip()]
        note_ids = [*due_note_ids, *empty_note_ids]

        total_cards = len(note_ids)

        for index, note_id in enumerate(note_ids, start=1):
            note = mw.col.get_note(note_id)

            # Prepare the prompt for the answer method
            word = note['Word']
            official_word_definition = note['Official Word Definition']
            reference_paragraph = note['Reference Paragraph']

            # Emit progress signal
            self.progress_signal.emit(f"{index} / {total_cards}: Generating the sentence for the word \"{word}\"…")

            prompt = f"""
            Generate a sentence containing "{word}", the word in the generated sentence should have the following meaning:

            {official_word_definition}

            An example sentence is as follows:

            {reference_paragraph}

            You need to obey the following rules:
            1. Just generate the sentence, don't add extra explanations. 
            2. Wrap the word in the generate sentence with <b><u> HTML tags, e.g. <b><u>{word}</u></b>
            
            Again, don't add extra explanations! Just output the sentence! Somethings like the following contents are not allowd to be included in the response: I'm glad to help! Here's the generated sentence.
            """

            # Call the answer method and fill in the card's "Sentence" field
            sentence = self.answer(prompt)
            # sentence = sentence.replace(word, f"<b><u>{word}</u></b>")  # Bolden and underline the word
            note['Sentence'] = sentence

            # Call the generate_definition method
            # definition = self.generate_definition(word, sentence)
            # note['Sentence Definition'] = definition

            # Update the note to take effect
            mw.col.update_note(note)

        self.finished_signal.emit()

    def generate_definition(self, word: str, sentence: str) -> str:
        return self.answer(f"Define the word \"{word}\" in the following sentence accurately and concisely: {sentence}")
