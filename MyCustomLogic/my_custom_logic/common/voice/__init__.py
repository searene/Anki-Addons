from abc import ABC, abstractmethod


class VoiceGenerator(ABC):
    @abstractmethod
    def generate_voice(self, sentence: str) -> str:
        """ Generate voice from text and return an Anki-compatible audio reference. """
        pass
