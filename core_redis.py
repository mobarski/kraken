import core_base
from core_base import *

# ---[ db specific ]----------------------------------------------------------

import redis

db = redis.Redis(host='localhost', port=6379, db=0)

def sync():
    pass # not used for redis

def _increment_by_one(key, fields):
    batch = db.pipeline()
    for k in fields:
        batch.hincrby(key, k, 1)
    batch.execute()

def _set_many(key, kv_pairs):
    db.hmset(key, dict(kv_pairs))

def _get_cache(key, fields, as_type=int):
    "get dictionary of cached values for given key and fields"
    values = db.hmget(key, fields)
    return {k:as_type(v) for k,v in zip(fields, values) if v}

core_base.sync = sync
core_base._increment_by_one = _increment_by_one
core_base._set_many = _set_many
core_base._get_cache = _get_cache
