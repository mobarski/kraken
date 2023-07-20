from random import random
from tqdm import tqdm

import sim

import core_kv as core
#import core_redis as core
#import core_base as core

ctx_config = {
	'gender': [('m','f'), (45, 55)],
	'platform': [('web','mobile','tv'), (20, 50, 30)], 
}

arm_config = {
	'gender:m': [1,1,9, 2,2,2, 3,3,4],
	'gender:f': [4,4,4, 3,3,2, 2,1,1],
	'platform:web':    [1,2,3, 1,2,3, 4,5,1],
	'platform:mobile': [2,2,4, 2,3,4, 1,9,3],
	'platform:tv':     [1,1,1, 2,9,2, 3,3,3],
	'pos:1': [5,5,5, 5,5,5, 5,5,5],
	'pos:2': [3,3,3, 3,3,3, 3,3,3],
	'pos:3': [1,1,1, 1,1,1, 1,1,1],
}

pool = [1,2,3,4,5,6,7,8,9]


def sim_many(n, config):
	room = config.get('room',1)
	pool = config.get('pool',[])
	X = 100
	for i in tqdm(range(n)):
		sim.sim_one(core, config)
		#
		if (i+1) % X == 0:
			data = core.db_get_snapshot(f'{room}:seg:')
			c = data.get('clicks-agg',0)
			v = data.get('views-agg',1)
			print(f'{i+1:6d} {c:6d} {v:6d} {c/v:.3f}')
			for a in pool:
				ca = data.get(f'clicks:{a}',0)
				va = data.get(f'views:{a}',1)
				print(f'{i+1:6d} {a:6d} {ca:6d} {va:6d} {ca/va:.3f}')
			# ctx
			if 0:
				for k,v in data.items():
					if k.startswith('views-agg-ctx:'):
						ctx_kv = k.partition(':')[2]
						cc = data.get(f'clicks-agg-ctx:{ctx_kv}',0)
						cv = data.get(f'views-agg-ctx:{ctx_kv}',1)
						print(f'{i+1:6d} {ctx_kv:20s} {cc:6d} {cv:6d} {cc/cv:.3f}')
	core.db_sync()

if __name__=="__main__":
	if 1:
		sim_many(100_000, dict(stat='ucb1', room=2, no_click_weight=10, pool=pool, arm_config=arm_config, ctx_config=ctx_config))
	else:
		import profile
		import pstats
		profile.run('sim_many(1_000)','data/test2.prof_stats')
		p = pstats.Stats('data/test2.prof_stats')
		p.strip_dirs().sort_stats('tottime').print_stats(20)
