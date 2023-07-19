import core_base
from core_base import *

# ---[ db specific ]----------------------------------------------------------

import redis

db = redis.Redis(host='localhost', port=6379, db=0)

def db_sync():
    pass # not used for redis

def db_set_many(key, kv_pairs):
    db.hmset(key, dict(kv_pairs))

def db_get_many(key, fields, as_type=int):
    "get dictionary of cached values for given key and fields"
    values = db.hmget(key, fields)
    return {k:as_type(v) for k,v in zip(fields, values) if v}

def db_increment_by_one(key, fields):
    batch = db.pipeline()
    for k in fields:
        batch.hincrby(key, k, 1)
    batch.execute()

def db_get_snapshot(key):
    # TODO: type conversion
    return db.hgetall(key)

core_base.db_sync = db_sync
core_base.db_set_many = db_set_many
core_base.db_get_many = db_get_many
core_base.db_increment_by_one = db_increment_by_one

