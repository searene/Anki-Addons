import hashlib
import os

import requests
from aqt import mw
from aqt.utils import showInfo

from my_custom_logic.common.util import get_config
from my_custom_logic.common.voice import VoiceGenerator


class MicrosoftVoiceGenerator(VoiceGenerator):
    def generate_voice(self, sentence: str) -> str:
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
            response.raise_for_status()

            filename = f"azure-{hashlib.md5(sentence.encode()).hexdigest()}.mp3"
            filepath = os.path.join(mw.col.media.dir(), filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return f"[sound:{filename}]"
        except requests.RequestException as e:
            showInfo(f"Failed to generate voice: {e}")
            return ""
