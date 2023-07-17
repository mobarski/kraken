from random import random
from tqdm import tqdm

import sim

#import core_kv as core
#import core_redis as core
import core_base as core

def sim_one(n_disp=3, no_click_weight=10, stat='ucb1', room=1):
	ctx = sim.random_ctx(sim.ctx_config)
	#
	if random()<=1.0: # TODO: param
		if   stat=='ctr':  core.calculate_ctr(sim.pool,  ctx, room=room)
		elif stat=='ucb1': core.calculate_ucb1(sim.pool, ctx, room=room)
		elif stat=='bucb': core.calculate_bucb(sim.pool, ctx, room=room)
	ids,vals = core.sorted_by_stat(stat, sim.pool, ctx, room=room)
	disp_ids = ids[:n_disp]
	core.register_views(disp_ids, ctx, room=room)
	#
	click_id = sim.random_click(disp_ids, sim.arm_config, ctx, no_click_weight)
	if click_id:
		core.register_click(click_id, ctx, room=room)

def sim_many(n, **kw):
	for i in tqdm(range(n)):
		sim_one(**kw)
	core.sync()

if 1:
	sim_many(10_000, stat='ctr', room=2)
else:
	import profile
	import pstats
	profile.run('sim_many(1_000)','data/test2.prof_stats')
	p = pstats.Stats('data/test2.prof_stats')
	p.strip_dirs().sort_stats('tottime').print_stats(20)
