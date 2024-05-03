import hashlib
import os

import requests
from aqt import mw
from aqt.utils import showInfo

from my_custom_logic.common.voice import VoiceGenerator


class MelloVoiceGenerator(VoiceGenerator):
    def generate_voice(self, sentence: str) -> str:
        try:
            response = requests.get(f"http://localhost:6839/audio", params={'text': sentence})
            response.raise_for_status()

            filename = f"mello-{hashlib.md5(sentence.encode()).hexdigest()}.wav"
            filepath = os.path.join(mw.col.media.dir(), filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return f"[sound:{filename}]"
        except requests.RequestException as e:
            showInfo(f"Failed to generate voice: {e}")
            return ""