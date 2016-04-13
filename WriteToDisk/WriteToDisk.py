from anki.db import DB
from anki.hooks import wrap
from aqt.utils import tooltip

def execute_with_commit(self, sql, *a, **ka): 
    res = execute_original(self, sql, *a, **ka)
    self.commit()
    return res

def executemany_after(self, sql, l):
    self.commit()

def executescript_after(self, sql):
    self.commit()

execute_original = DB.execute
DB.execute = execute_with_commit
DB.executemany = wrap(DB.executemany, executemany_after, "after")
DB.executescript = wrap(DB.executescript, executescript_after, "after")
