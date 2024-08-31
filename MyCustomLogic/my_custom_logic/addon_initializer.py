from . import add_sentence_audio_automatically, fill_all
from . import convert_audio_file_formats
from . import distribute_longman_paste_contents
from . import strip_field_contents
from . import remove_sound_from_sentence_field
from . import show_added_sentences_today
from . import sentence_experiment


def init_addon():
    # Attach the function to the hook
    strip_field_contents.start()
    distribute_longman_paste_contents.start()
    convert_audio_file_formats.start()
    # add_sentence_audio_automatically.start()
    remove_sound_from_sentence_field.start()
    show_added_sentences_today.start()
    sentence_experiment.start()
    fill_all.start()
