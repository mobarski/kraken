import core_base
from core_base import *

# ---[ db specific ]----------------------------------------------------------

from kv import KV

db = KV.open('data/test2.kv')

def db_sync():
    db.sync()

core_base.db = db
core_base.db_sync = db_sync
