import sim
import db_shelve as db
from pprint import pprint
from random import random
from tqdm import tqdm

def sim_one(n_disp=3, no_click_weight=10):
	ctx = sim.random_ctx(sim.ctx_config)
	#
	if random()<=1.0:
		db.calculate_ctr(sim.pool, ctx)
		db.calculate_ucb(sim.pool, ctx)
	ids,vals = db.sorted_by_stat('ucb', sim.pool, ctx)
	disp_ids = ids[:n_disp]
	db.register_views(disp_ids, ctx)
	#
	click_id = sim.random_click(disp_ids, sim.arm_config, ctx, no_click_weight)
	if click_id:
		db.register_click(click_id, ctx)

def sim_many():
	for i in tqdm(range(1000)):
		sim_one()
	db.db.sync()
	#pprint(dict(db.db))

if 0:
	sim_many()
else:
	import profile
	import pstats
	profile.run('sim_many()','data/test2.prof_stats')
	p = pstats.Stats('data/test2.prof_stats')
	p.strip_dirs().sort_stats('tottime').print_stats(20)
