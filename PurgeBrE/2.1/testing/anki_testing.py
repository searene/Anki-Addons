# The code is taken from https://github.com/krassowski/anki_testing, I made some modifications
# coding: utf-8
import shutil
import tempfile
from contextlib import contextmanager

import os

import sys
from warnings import warn

sys.path.insert(0, 'anki_root')

import aqt
from aqt import _run
from aqt import AnkiApp
from aqt.profiles import ProfileManager


origin_sys_excepthook = sys.excepthook


@contextmanager
def temporary_user(dir_name, name="__Temporary Test User__", lang="en_US"):

    # prevent popping up language selection dialog
    original = ProfileManager.setDefaultLang

    def set_default_lang(profileManager):
        profileManager.setLang(lang)

    ProfileManager.setDefaultLang = set_default_lang

    pm = ProfileManager(base=dir_name)

    pm.setupMeta()

    # create profile no matter what (since we are starting in a unique temp directory)
    pm.create(name)

    # this needs to be called explicitly
    pm.setDefaultLang()

    pm.name = name

    yield name

    # cleanup
    pm.remove(name)
    ProfileManager.setDefaultLang = original


@contextmanager
def temporary_dir(name):
    # create a true unique temporary directory at every startup
    tempdir = tempfile.TemporaryDirectory(suffix='anki')
    yield tempdir.name
    tempdir.cleanup()


@contextmanager
def anki_running():

    # don't use the second instance mechanism, start a new instance every time
    def mock_secondInstance(ankiApp):

        # remove the superscript to the right of the word
        return False

    AnkiApp.secondInstance = mock_secondInstance

    # we need a new user for the test
    with temporary_dir("anki_temp_base") as dir_name:
        with temporary_user(dir_name) as user_name:
            argv=["anki", "-p", user_name, "-b", dir_name]
            app = _run(argv=argv, exec=False)

            # Anki sets its own error handler, which will prevent us from
            # obtaining error messages, unload it to use the original one
            # aqt.mw.errorHandler.unload()

            yield app

    # clean up what was spoiled
    aqt.mw.cleanupAndExit()

    # Anki sets sys.excepthook to None in cleanUpAndExit(),
    # which causes the next test to throw exceptions,
    # let's set it back
    sys.excepthook = origin_sys_excepthook

    # remove hooks added during app initialization
    from anki import hooks
    hooks._hooks = {}

    # test_nextIvl will fail on some systems if the locales are not restored
    import locale
    locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

