import aqt

from .AddonInitializer import init_addon

if aqt.mw is not None:
    init_addon()
