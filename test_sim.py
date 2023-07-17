import sim
#import core_kv as core
import core_redis as core
from random import random
from tqdm import tqdm

def sim_one(n_disp=3, no_click_weight=10, stat='ucb1'):
	ctx = sim.random_ctx(sim.ctx_config)
	#
	if random()<=1.0: # TODO: param
		if   stat=='ctr':  core.calculate_ctr(sim.pool, ctx)
		elif stat=='ucb1': core.calculate_ucb1(sim.pool, ctx)
		elif stat=='bucb': core.calculate_bucb(sim.pool, ctx)
	ids,vals = core.sorted_by_stat(stat, sim.pool, ctx)
	disp_ids = ids[:n_disp]
	core.register_views(disp_ids, ctx)
	#
	click_id = sim.random_click(disp_ids, sim.arm_config, ctx, no_click_weight)
	if click_id:
		core.register_click(click_id, ctx)

def sim_many(n, **kw):
	for i in tqdm(range(n)):
		sim_one(**kw)
	core.sync()

if 1:
	sim_many(10_000, stat='ctr')
else:
	import profile
	import pstats
	profile.run('sim_many(1_000)','data/test2.prof_stats')
	p = pstats.Stats('data/test2.prof_stats')
	p.strip_dirs().sort_stats('tottime').print_stats(20)
