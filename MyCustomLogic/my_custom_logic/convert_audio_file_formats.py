import subprocess

from aqt import mw
from aqt.gui_hooks import sync_will_start
from aqt.utils import showInfo


def convert_audio_files():
    # Path to your bash script
    script_path = "/Users/joeygreen/apps/scripts/convert_ogg_to_mp3.sh"
    try:
        subprocess.run(["zsh", script_path], check=True)
        print("Audio files are converted successfully.")
    except subprocess.CalledProcessError:
        showInfo("Failed to convert audio files.")


def replace_ogg_with_mp3():
    all_notes = mw.col.find_notes("")
    updated = 0

    for nid in all_notes:
        note = mw.col.get_note(nid)

        for fname, fval in note.items():
            if "[sound:" in fval and ".ogg]" in fval:
                ogg_file = fval.split('[sound:')[1].split('.ogg]')[0]
                note[fname] = fval.replace(f"{ogg_file}.ogg", f"{ogg_file}.mp3")
                mw.col.update_note(note)
                updated += 1

    print(f"Updated {updated} notes from ogg to mp3.")


def sync_will_start_callback():
    convert_audio_files()
    replace_ogg_with_mp3()


def start():
    sync_will_start.append(sync_will_start_callback)