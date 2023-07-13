import db_shelve as db
from pprint import pprint
from random import choice,randint

import sim

POOL = [1,2,3]
SEG = ['gender']
CTX = sim.random_ctx(sim.ctx_config)
CTX_PER_ID = [{'pos':1},{'pos':2},{'pos':3}]

db.register_views(POOL, ctx=CTX, ctx_per_id=CTX_PER_ID, seg=SEG)
i = randint(0,len(POOL)-1)
a = POOL[i]
db.register_click(a, ctx=CTX, ctx2=CTX_PER_ID[i], seg=SEG)
db.calculate_ctr(POOL, ctx=CTX, seg=SEG)
db.calculate_ucb(POOL, ctx=CTX, seg=SEG)
pprint(dict(db.db.items()))

pprint(db.sorted_by_stat('ctr', POOL, ctx=CTX, seg=SEG))
pprint(db.sorted_by_stat('ucb', POOL, ctx=CTX, seg=SEG))
print(CTX)
