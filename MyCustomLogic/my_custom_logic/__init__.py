import aqt

from .addon_initializer import init_addon

if aqt.mw:
    init_addon()
