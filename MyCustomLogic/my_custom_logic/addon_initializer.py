from . import add_sentence_audio_automatically
from . import convert_audio_file_formats
from . import distribute_longman_paste_contents
from . import strip_field_contents
from . import remove_sound_from_sentence_field


def init_addon():
    # Attach the function to the hook
    strip_field_contents.start()
    distribute_longman_paste_contents.start()
    convert_audio_file_formats.start()
    add_sentence_audio_automatically.start()
    remove_sound_from_sentence_field.start()


if __name__ == '__main__':
    init_addon()
