import json
import os
import re
from typing import Optional, Tuple, List

from anki.models import FieldDict
from anki.notes import Note
from aqt import mw
from aqt.addons import AddonManager


def __get_addon_manager() -> AddonManager:
    if mw is None:
        raise Exception("Anki is not running")
    return mw.addonManager


def get_user_files_folder() -> str:
    addon_id = __get_addon_manager().addonFromModule(__name__)
    user_files_folder = os.path.join(__get_addon_manager().addonsFolder(), addon_id, 'user_files')
    os.makedirs(user_files_folder, exist_ok=True)
    return user_files_folder


def get_config() -> dict[str, str]:
    config_file_path = os.path.join(get_user_files_folder(), "config.json")
    if not os.path.exists(config_file_path):
        return {}
    with open(config_file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_field_by_name(target_field_name: str, note: Note) -> Optional[FieldDict]:
    """Get the field by name from the note."""
    note_type = note.note_type()
    if note_type is None:
        return None
    for fld in note_type['flds']:
        if fld['name'] == target_field_name:
            return fld
    return None


def strip(s: str) -> str:
    """Strip the string."""
    return s.strip().replace("&nbsp;", "")


def clean_cloze(text: str) -> str:
    """Remove cloze deletions from the text."""
    # Regex to find all cloze deletions and remove them
    cleaned_text = re.sub(r"\{\{c[0-9]+::(.*?)}}", r"\1", text)
    return cleaned_text


def split(text: str) -> Tuple[str, str, str, str]:
    print(text)
    match = re.match(r"([^/\d]+)[^/]*(/.+?/)\s*(\[sound:.+?])[\s●○]*(.*?)(?=\[sound:|$)", text)
    if match:
        word, ipa, sound, pos = match.groups()
        return word.strip(), ipa.strip(), sound.strip(), pos.strip()
    else:
        return text, "", "", ""


def remove_cloze(text: str) -> str:
    """
    Remove cloze deletions from the text.

    Examples:

    This is a cup of water. -> This is a cup of water.
    This is a {{c1::cup}} of water. -> This is a cup of water.
    This is a {{c1::cup::c}} of water. -> This is a cup of water.
    This is a {{c1::cup::c}} of {{c2::water}}. -> This is a cup of water.
    """
    # Regular expression to match and remove cloze deletions
    text = re.sub(r'\{\{c\d::(.*?)(::.*?)?\}\}', r'\1', text)
    return text


def get_cloze_contents(text: str) -> List[str]:
    """
    Get the cloze contents from the text. Ignore the part after the second "::" in each cloze.
    """
    # Find all cloze deletions in the text
    clozes = re.findall(r'\{\{c\d::(.*?)}}', text)

    # Extract the part before the second "::" in each cloze
    cloze_contents = [cloze.split('::')[0] for cloze in clozes]

    return cloze_contents


def get_field_contents(field_name: str, note: Note) -> Optional[str]:
    """Get the field contents by name from the note."""
    field = get_field_by_name(field_name, note)
    if field is None:
        return None
    return note.fields[field['ord']]


def to_plain_text(html: str) -> str:
    """Convert the HTML to plain text."""
    return re.sub(r"<.*?>", "", html)
