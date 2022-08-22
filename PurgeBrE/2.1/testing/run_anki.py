from purge_bre import init_addon
from anki_testing import anki_running

with anki_running() as app:

    # Initialize our addon
    init_addon()

    # Run anki
    app.exec()
