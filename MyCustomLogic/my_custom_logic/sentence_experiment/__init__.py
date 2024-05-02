import hashlib
import re
from typing import List, Optional

import requests
from aqt import mw
from aqt.gui_hooks import editor_did_paste
from aqt.qt import *
from aqt.utils import showInfo
from my_custom_logic.common import get_config, get_user_files_folder
from my_custom_logic.sentence_experiment.distribute_word_ipa_voice import distribute_word_ipa_voice_hook


def setup_menu():
    action = QAction("Generating Sentences with AI", mw)
    action.triggered.connect(show_dialog)
    mw.form.menuTools.addAction(action)


def show_dialog():
    dialog = QDialog(mw)
    layout = QVBoxLayout()
    text_area = QTextEdit()
    generate_button = QPushButton("Generate")
    generate_button.clicked.connect(lambda: prepare_generation(text_area.toPlainText(), dialog))
    layout.addWidget(text_area)
    layout.addWidget(generate_button)
    dialog.setLayout(layout)
    dialog.exec()


def prepare_generation(text: str, parent_dialog: QDialog):
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
    print(note.keys())
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
    if sentence:
        note['Sentence'] = generate_sentence(word, sentence)
        note['Definition'] = generate_definition(word, note['Sentence'])

    note.model()['did'] = deck_id
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


def generate_voice_microsoft(sentence: str) -> str:
    # Fetch subscription key and other necessary configuration details from the add-on's config
    config = get_config()
    if "azure_subscription_key" not in config:
        showInfo("Please set azure_subscription_key in the add-on's configuration.")
        return ""

    headers = {
        'Ocp-Apim-Subscription-Key': config["azure_subscription_key"],
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-24khz-96kbitrate-mono-mp3',
        'User-Agent': 'Anki Add-on'
    }

    body = f"""
    <speak version='1.0' xml:lang='en-US'>
        <voice xml:lang='en-US' xml:gender='Female' name='en-US-JaneNeural'>{sentence}</voice>
    </speak>
    """

    try:
        response = requests.post('https://eastus.tts.speech.microsoft.com/cognitiveservices/v1', headers=headers,
                                 data=body)
        response.raise_for_status()  # Raises stored HTTPError, if one occurred

        # Generate a unique filename for the audio file
        filename = f"azure-{hashlib.md5(sentence.encode()).hexdigest()}.mp3"
        filepath = os.path.join(mw.col.media.dir(), filename)

        # Save the audio file to Anki's media collection directory
        with open(filepath, 'wb') as f:
            f.write(response.content)

        # Return the Anki compatible reference to the file
        return f"[sound:{filename}]"
    except requests.RequestException as e:
        showInfo(f"Failed to generate voice: {e}")
        return ""


def generate_voice(word: str) -> str:
    return generate_voice_microsoft(word)


def answer(prompt: str) -> str:
    data = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=data)
        response.raise_for_status()  # Raise an exception if the status code is not 200
        return response.json()["response"]
    except requests.RequestException as e:
        return f"Error: {e}"


def start():
    editor_did_paste.append(distribute_word_ipa_voice_hook)
    setup_menu()
