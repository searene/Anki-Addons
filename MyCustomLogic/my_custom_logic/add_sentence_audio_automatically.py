import hashlib
import os
from typing import Optional

import aqt
import requests
from anki.models import FieldDict
from anki.notes import Note
from aqt import mw
from aqt.gui_hooks import editor_did_unfocus_field
from aqt.sound import play
from aqt.utils import showInfo


def get_field_by_name(target_field_name: str, note: Note) -> Optional[FieldDict]:
    """Get the field by name from the note."""
    for fld in note.note_type()['flds']:
        if fld['name'] == target_field_name:
            return fld
    return None


def fill_sentence_voice_automatically(changed: bool, note: Note, field_idx: int) -> bool:
    """Fetch the audio file from Azure TTS service and fill the Sentence Voice field automatically."""
    current_note_name = note.note_type()['name']
    if current_note_name not in ("English - Complete", "English - Complete - With Reverse"):
        # If nothing is changed, we just return "changed".
        # The official Anki website illustrates the usage of the editor_did_unfocus_field hook, fortunately.
        # Check the following URL for details: https://addon-docs.ankiweb.net/hooks-and-filters.html
        return changed
    current_field_name = note.note_type()['flds'][field_idx]['name']
    if current_field_name == "Sentence":
        sentence = note.fields[field_idx]
        if not sentence.strip():
            # return when "sentence" is empty (empty spaces are deemed as empty)
            return changed

        sentence_voice_field = get_field_by_name("Sentence Voice", note)
        sentence_voice_field_contents = note.fields[sentence_voice_field['ord']]
        if sentence_voice_field_contents.strip():
            # We don't update the "Sentence Voice" field since it's already filled
            return changed

        # Try fetching the voice
        filename = generate_voice(sentence)
        if filename is None:
            # Show an error message
            showInfo("Failed to generate voice. Please try again.")
            return changed
        note.fields[sentence_voice_field['ord']] = f"[sound:{filename}]"
        return True


def generate_voice(sentence: str) -> Optional[str]:
    """Generate voice using Microsoft's TTS service and save it to Anki's media collection directory."""
    # Fetch subscription key from the add-on's configuration
    config_file = mw.addonManager.getConfig("MyCustomLogic")
    if config_file is None or config_file["azure_subscription_key"] == "":
        showInfo("Please set azure_subscription_key in the add-on's configuration.")
        return None
    headers = {
        'Ocp-Apim-Subscription-Key': config_file["azure_subscription_key"],
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-24khz-96kbitrate-mono-mp3',
        'User-Agent': 'Anki Add-on'
    }

    body = f"""
    <speak version='1.0' xml:lang='en-US'><voice xml:lang='en-US' xml:gender='Female' name='en-US-JaneNeural'>
        {sentence.replace('&nbsp;', ' ')}
    </voice></speak>
    """

    response = requests.post('https://eastus.tts.speech.microsoft.com/cognitiveservices/v1',
                             headers=headers,
                             data=body,
                             proxies={
                                 "http": "http://127.0.0.1:7890",
                                 "https": "http://127.0.0.1:7890",
                             })

    if response.status_code == 200:
        # Generate a unique filename for the audio file
        filename = f"azure-{hashlib.md5(sentence.encode()).hexdigest()}.mp3"

        # Save the audio file to Anki's media collection directory
        with open(os.path.join(mw.col.media.dir(), filename), 'wb') as f:
            f.write(response.content)

        play(filename)
        return filename
    else:
        print(f"Failed to generate voice, response code: {response.status_code}, response contents: {response.text}")


def start():
    editor_did_unfocus_field.append(fill_sentence_voice_automatically)