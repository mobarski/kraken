import sim
import db_shelve as core
from pprint import pprint
from random import random
from tqdm import tqdm

def sim_one(n_disp=3, no_click_weight=10):
	ctx = sim.random_ctx(sim.ctx_config)
	#
	if random()<=1.0:
		core.calculate_ctr(sim.pool, ctx)
		core.calculate_ucb(sim.pool, ctx)
	ids,vals = core.sorted_by_stat('ucb', sim.pool, ctx)
	disp_ids = ids[:n_disp]
	core.register_views(disp_ids, ctx)
	#
	click_id = sim.random_click(disp_ids, sim.arm_config, ctx, no_click_weight)
	if click_id:
		core.register_click(click_id, ctx)

def sim_many(n):
	for i in tqdm(range(n)):
		sim_one()
	core.sync()
	pprint(dict(core.db))

if 1:
	sim_many(100_000)
else:
	import profile
	import pstats
	profile.run('sim_many(10_000)','data/test2.prof_stats')
	p = pstats.Stats('data/test2.prof_stats')
	p.strip_dirs().sort_stats('tottime').print_stats(20)
