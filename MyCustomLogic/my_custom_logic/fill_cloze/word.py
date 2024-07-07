import json
from typing import List, Optional

import requests
from bs4 import BeautifulSoup


class Example:
    def __init__(self, audio: str, en: str, zh: str):
        self.audio = audio
        self.en = en
        self.zh = zh

    def __str__(self):
        return f"Example(audio={self.audio}, en={self.en}, zh={self.zh})"

    def to_dict(self):
        return {
            "audio": self.audio,
            "en": self.en,
            "zh": self.zh
        }


class Definition:
    def __init__(self, definition: str, examples: List[Example]):
        self.definition = definition
        self.examples = examples

    def __str__(self):
        examples_str = ", ".join(str(example) for example in self.examples)
        return f"Definition(definition={self.definition}, examples=[{examples_str}])"

    def to_dict(self):
        return {
            "definition": self.definition,
            "examples": [example.to_dict() for example in self.examples]
        }


class WordEntry:
    def __init__(self, ipa: str, part_of_speech: str, pronunciation: str, definitions: List[Definition]):
        self.ipa = ipa
        self.pos = part_of_speech
        self.pronunciation = pronunciation
        self.definitions = definitions

    def __str__(self):
        definitions_str = ", ".join(str(definition) for definition in self.definitions)
        return f"WordEntry(ipa={self.ipa}, pos={self.pos}, pronunciation={self.pronunciation}, definitions=[{definitions_str}])"

    def to_dict(self):
        return {
            "ipa": self.ipa,
            "part_of_speech": self.pos,
            "pronunciation": self.pronunciation,
            "definitions": [definition.to_dict() for definition in self.definitions]
        }


class Word:
    def __init__(self, word: str, word_entries: List[WordEntry]):
        self.word = word
        self.word_entries = word_entries

    def __str__(self):
        word_entries_str = ", ".join(str(entry) for entry in self.word_entries)
        return f"Word(word={self.word}, word_entries=[{word_entries_str}])"

    def to_dict(self):
        return {
            "word": self.word,
            "word_entries": [entry.to_dict() for entry in self.word_entries]
        }


def get_soup(word: str) -> BeautifulSoup:
    try:
        response = requests.get(f"http://localhost:8000/{word}")
        response.raise_for_status()  # Raise an exception if the status code is not 200
    except requests.RequestException as e:
        print(f"Error: {e}")
        raise e

    return BeautifulSoup(response.text, 'html.parser')


def fetch_word(word: str) -> Optional[Word]:
    soup = get_soup(word)
    word_entries = []

    for entry_div in [child for child in soup.children if child.name == 'div']:
        proncodes = entry_div.select_one('span.entry span.entryhead span.proncodes')
        if proncodes is None:
            ipa = None
        else:
            ipa = proncodes.get_text(strip=True).strip()

        pos_span = entry_div.select_one('span.entry span.entryhead span.pos')
        gram_span = entry_div.select_one('span.entry span.entryhead span.gram')
        part_of_speech = (pos_span.get_text(strip=True) if pos_span else '') + ' ' + (
            gram_span.get_text(strip=True) if gram_span else '').strip()

        pronunciation = ''
        for a_tag in entry_div.select('span.entry span.entryhead a'):
            if 'ame' in a_tag.get('href', ''):
                pronunciation = a_tag['href']
                break

        definitions = []
        for sense_span in entry_div.select('span.entry span.sense'):
            definition_text = sense_span.select_one('span.def').get_text(strip=True)

            examples = []
            for example_span in sense_span.select('span.example'):
                expen = example_span.select_one('expen')
                expcn = example_span.select_one('expcn')
                if expen and expcn:
                    audio = expen.select_one('a')['href']
                    en = expen.get_text(strip=True)
                    zh = expcn.get_text(strip=True)
                    examples.append(Example(audio=audio, en=en, zh=zh))

            definitions.append(Definition(definition=definition_text, examples=examples))

        word_entry = WordEntry(
            ipa=ipa,
            part_of_speech=part_of_speech,
            pronunciation=pronunciation,
            definitions=definitions
        )
        word_entries.append(word_entry)

    word = Word(word=word, word_entries=word_entries) if word_entries else None
    post_process(word)
    return word


def add_missing_ipa(word: Word) -> None:
    # Get the first ipa
    ipa_list = [entry.ipa for entry in word.word_entries if entry.ipa is not None]
    if not ipa_list:
        return
    ipa = ipa_list[0]
    for entry in word.word_entries:
        if entry.ipa is None:
            entry.ipa = ipa


def post_process(word: Word) -> None:
    add_missing_ipa(word)


if __name__ == "__main__":
    w = fetch_word("test")
    json_str = json.dumps(w.to_dict(), indent=2, ensure_ascii=False)
    print(json_str)
