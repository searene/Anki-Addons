import aqt

from golden_dict_media.AddonInitializer import init_addon

if aqt.mw is not None:
    init_addon()
