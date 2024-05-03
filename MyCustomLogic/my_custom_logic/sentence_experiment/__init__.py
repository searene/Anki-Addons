import re
from typing import List, Optional

import requests
from aqt import mw
from aqt.gui_hooks import editor_did_paste, editor_will_process_mime
from aqt.qt import *

from my_custom_logic.common.util import get_user_files_folder
from my_custom_logic.sentence_experiment.distribute_word_ipa_voice import distribute_word_ipa_voice_hook
from my_custom_logic.sentence_experiment.sentence_generator import SentenceGenerator
from my_custom_logic.sentence_experiment.sentence_voice_generator import SentenceVoiceGenerator
from my_custom_logic.sentence_experiment.trim_official_word_definition import trim_official_word_definition_handler


def setup_menu():
    action = QAction("Generate Sentences with AI", mw)
    action.triggered.connect(show_dialog)
    mw.form.menuTools.addAction(action)


def show_dialog():
    dialog = QDialog(mw)
    layout = QVBoxLayout()
    tabs = QTabWidget()

    # Add Words tab
    add_words_tab = QWidget()
    add_words_layout = QVBoxLayout()
    text_area = QTextEdit()
    add_button = QPushButton("Add")
    add_button.clicked.connect(lambda: add_words(text_area.toPlainText(), dialog))
    add_words_layout.addWidget(text_area)
    add_words_layout.addWidget(add_button)
    add_words_tab.setLayout(add_words_layout)

    # Generate Sentences tab
    generate_sentences_tab = QWidget()
    generate_sentences_layout = QVBoxLayout()
    generate_button = QPushButton("Generate")
    progress_text_area = QTextEdit()
    progress_text_area.setReadOnly(True)
    generate_sentences_layout.addWidget(generate_button)
    generate_sentences_layout.addWidget(progress_text_area)
    generate_sentences_tab.setLayout(generate_sentences_layout)

    # Add tabs to the QTabWidget
    tabs.addTab(add_words_tab, "Add Words")
    tabs.addTab(generate_sentences_tab, "Generate Sentences")

    layout.addWidget(tabs)
    dialog.setLayout(layout)

    sentence_generator = SentenceGenerator(answer)
    sentence_generator.progress_signal.connect(progress_text_area.append)
    sentence_generator.finished_signal.connect(lambda: progress_text_area.append("Sentence Generation is Finished"))

    voice_generator = SentenceVoiceGenerator()
    voice_generator.progress_signal.connect(progress_text_area.append)
    voice_generator.finished_signal.connect(lambda: progress_text_area.append("Voice Generation is Finished."))

    # Start the SentenceVoiceGenerator when the SentenceGenerator has finished
    sentence_generator.finished_signal.connect(voice_generator.start)

    generate_button.clicked.connect(sentence_generator.start)

    dialog.exec()


def generate(progress_text_area: QTextEdit, answer: callable, sentence_generator: SentenceGenerator, voice_generator: SentenceVoiceGenerator):
    sentence_generator = SentenceGenerator(answer)
    sentence_generator.progress_signal.connect(progress_text_area.append)
    sentence_generator.finished_signal.connect(lambda: progress_text_area.append("Sentence Generation is Finished"))

    voice_generator = SentenceVoiceGenerator()
    voice_generator.progress_signal.connect(progress_text_area.append)
    voice_generator.finished_signal.connect(lambda: progress_text_area.append("Voice Generation is Finished."))

    # Start the SentenceVoiceGenerator when the SentenceGenerator has finished
    sentence_generator.finished_signal.connect(voice_generator.start)

    sentence_generator.start()


def generate_sentences(progress_text_area: QTextEdit):
    # Fetch all the cards whose note type is "Sentence Experiment"
    note_type = mw.col.models.by_name("Sentence Experiment")
    if not note_type:
        raise Exception("Cannot find the note type: Sentence Experiment")

    note_ids = mw.col.find_notes(f"mid:{note_type['id']}")
    total_cards = len(note_ids)

    for index, note_id in enumerate(note_ids, start=1):
        note = mw.col.get_note(note_id)

        # Prepare the prompt for the answer method
        word = note['Word']
        official_word_definition = note['Official Word Definition']
        reference_paragraph = note['Reference Paragraph']

        prompt = f"""
        Generate a sentence containing "{word}", the word in the generated sentence should have the following meaning:

        {official_word_definition}

        An example sentence is as follows:

        {reference_paragraph}

        Just generate the sentence, don't add extra explanations. Also, notice that you only need to make sure their meanings are the same, you don't need to make them in the same context or situation.
        """

        # Call the answer method and fill in the card's "Sentence" field
        sentence = answer(prompt)
        sentence = sentence.replace(word, f"<b><u>{word}</u></b>")  # Bolden and underline the word
        note['Sentence'] = sentence

        # Call the generate_definition method
        definition = generate_definition(word, sentence)
        note['Sentence Definition'] = definition

        # Update the note to take effect
        mw.col.update_note(note)

        # Update the progress text area
        progress_text_area.append(f"{index} / {total_cards}: Generating the sentence for the word \"{word}\"…")


def add_words(text: str, parent_dialog: QDialog):
    words = text.strip().split('\n')
    selection_results = {}

    for word in words:
        word = word.strip()
        if not word:
            continue
        sentences = search_in_file(word)
        if len(sentences) > 1:
            sentence = choose_sentence(sentences, word)
            selection_results[word] = sentence
        elif sentences:
            selection_results[word] = sentences[0]
        else:
            selection_results[word] = None

    parent_dialog.close()  # Close the initial dialog after selections
    generate_all_cards(selection_results)


def search_in_file(word: str) -> List[str]:
    path = os.path.join(get_user_files_folder(), "A Short History of Nearly Everything.txt")
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    sentences = re.split(r'[.\n]', content)
    return [s.strip() + "." for s in sentences if re.search(r'\b' + word + r'\b', s)]


def choose_sentence(sentences: List[str], word: str) -> str:
    dialog = QDialog(mw)
    dialog.setWindowTitle(f"Choose a sentence for: {word}")
    combo = QComboBox()
    combo.addItems(sentences)
    button = QPushButton("Select")
    layout = QVBoxLayout()
    layout.addWidget(QLabel(f"Choose a sentence for the word: {word}"))
    layout.addWidget(combo)
    layout.addWidget(button)
    dialog.setLayout(layout)
    button.clicked.connect(dialog.accept)
    dialog.exec()
    return combo.currentText()


def generate_all_cards(selection_results):
    for word, sentence in selection_results.items():
        create_card(word, sentence)


def get_paragraph(content: str, sentence: str) -> Optional[str]:
    paragraphs = content.split('\n')
    for paragraph in paragraphs:
        if sentence in paragraph:
            return paragraph
    return None


def create_card(word: str, sentence: Optional[str]):
    deck_name = "Sentence Experiment Deck"
    deck_id = mw.col.decks.id(deck_name)
    mw.col.decks.select(deck_id)

    note_type = mw.col.models.by_name("Sentence Experiment")
    if not note_type:
        raise Exception("Cannot find the note type: Sentence Experiment")

    note = mw.col.new_note(note_type)
    note['Word'] = word
    if sentence:
        path = os.path.join(get_user_files_folder(), "A Short History of Nearly Everything.txt")
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        paragraph = get_paragraph(content, sentence)
        if not paragraph:
            raise Exception("Cannot find the paragraph containing the following sentence: " + sentence)
        sentence = re.sub(r'\b' + word + r'\b', f"<b><u>{word}</u></b>", sentence)
        paragraph = re.sub(r'\b' + word + r'\b', f"<b><u>{word}</u></b>", paragraph)
        note['Reference Sentence'] = sentence
        note['Reference Paragraph'] = paragraph
    # note['IPA'] = generate_ipa(word)
    # note['Voice'] = generate_voice(word)
    # if sentence:
    # note['Sentence'] = generate_sentence(word, sentence)
    # note['Sentence Definition'] = generate_definition(word, note['Sentence'])

    note.note_type()['did'] = deck_id
    mw.col.addNote(note)


def generate_definition(word: str, sentence: str) -> str:
    return answer(f"Define the word \"{word}\" in the following sentence accurately and concisely: {sentence}")


def generate_sentence(word: str, context: str) -> str:
    paragraph = context  # Simplification for example; fetch actual paragraph in implementation
    return answer(
        f"Generate a sentence containing \"{word}\", the meaning of the word in the generated sentence should be the same to the meaning of the word in the following sentence:\n\n{context}\n\nJust generate the sentence, don't add extra explanations. Also notice that you only need to make sure their meanings are the same, you don't need to make them in the same context or situation."
    )


def generate_ipa(word: str) -> str:
    return answer(f"Generate IPA for \"{word}\", only generate the word, don't add extra explanations.")


def answer(prompt: str) -> str:
    data = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=data)
        response.raise_for_status()  # Raise an exception if the status code is not 200
        res = response.json()["response"]
        print(f"prompt:\n{prompt}\n\nresponse:\n{res}\n\n")
        return res
    except requests.RequestException as e:
        return f"Error: {e}"


def start():
    editor_did_paste.append(distribute_word_ipa_voice_hook)
    editor_will_process_mime.append(trim_official_word_definition_handler)
    setup_menu()
