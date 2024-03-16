import aqt

from .addon_initializer import init_addon

if aqt.mw is not None:
    init_addon()
