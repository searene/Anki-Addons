
from anki_testing import anki_running

with anki_running() as app:

    # Initialize our addon
    from golden_dict_media import init_addon
    init_addon()

    # Run anki
    app.exec()
