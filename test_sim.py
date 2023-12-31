from random import random
from tqdm import tqdm

import sim

#import core_kv as core
#import core_redis as core
import core_base as core

ctx_config = {
	'gender': [('m','f'), (45, 55)],
	'platform': [('web','mobile','tv'), (20, 50, 30)], 
}

# TODO: rename
arm_config = {
	'gender:m': [1,1,9, 2,2,2, 3,3,4],
	'gender:f': [4,4,4, 3,3,2, 2,1,1],
	'platform:web':    [4,2,3, 1,2,3, 4,5,1],
	'platform:mobile': [2,2,4, 2,3,4, 1,9,3],
	'platform:tv':     [6,1,1, 2,9,2, 3,3,3],
	'pos:1': [5,5,5, 5,5,5, 5,5,5],
	'pos:2': [3,3,3, 3,3,3, 3,3,3],
	'pos:3': [1,1,1, 1,1,1, 1,1,1],
}

dec_config_v1 = {
	# arm_id : (start, duration, decay)
	1 : (1000, 1000, 0.1),
	2 : (1500, 2000, 0.2),
	3 : (2000, 3000, 0.3),
	4 : (1200, 1000, 0.4),
	5 : (1700, 2000, 0.5),
	6 : (2200, 3000, 0.6),
	7 : (2400, 1000, 0.7),
	8 : (1000, 2000, 0.8),
	9 : (1200, 3000, 0.9),
}

pool = [1,2,3,4,5,6,7,8,9]
pool = [1,2,3]

# TODO: rename
new_config = {
	# arm_id : (start, duration)
	1 : (0, 1000),
	2 : (0, None),
	3 : (2000, 1000),
}

# TODO: seg, a VS a, seg ???
def sim_many(n_trials, config):
	room = config.get('room',1)
	pool = config.get('pool',[])
	step = config.get('step',100)
	out = []
	for i in tqdm(range(n_trials)):
		config['trial'] = i+1
		sim.sim_one(core, config)
		#
		if (i+1) % step == 0:
			segments = [x.partition(':seg:')[2] for x in core.db_scan(f'{room}:seg:')]
			for seg in segments:
				data = core.db_get_snapshot(f'{room}:seg:{seg}')
				c = data.get('clicks-agg',0)
				v = data.get('views-agg',1)
				#print(f'{i+1:6d} {c:6d} {v:6d} {c/v:.3f}')
				for a in pool:
					ca = data.get(f'clicks:{a}',0)
					va = data.get(f'views:{a}',1)
					rec = i+1, seg, a, '', ca, va, ca/va
					out.append(rec)
					# ctx
					if 1:
						for k,v in data.items():
							if k.startswith(f'views-ctx:{a}'):
								ctx_kv = k.partition(f':{a}:')[2]
								cc = data.get(f'clicks-ctx:{a}:{ctx_kv}',0)
								cv = data.get(f'views-ctx:{a}:{ctx_kv}',1)
								rec = i+1, seg, a, ctx_kv, cc, cv, cc/cv
								out.append(rec)
	core.db_sync()
	return out

if __name__=="__main__":
	if 1:
		rows = sim_many(100_000, dict(stat='ucb1', room=2, no_click_weight=10, pool=pool, arm_config=arm_config, ctx_config=ctx_config, new_config=new_config, decay_config=dec_config_v1))
		df = pd.DataFrame(rows, columns=['trial','arm','ctx','clicks','views','ctr'])
	else:
		import profile
		import pstats
		profile.run('sim_many(1_000)','data/test2.prof_stats')
		p = pstats.Stats('data/test2.prof_stats')
		p.strip_dirs().sort_stats('tottime').print_stats(20)
