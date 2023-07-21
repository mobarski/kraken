from random import Random

G1 = Random()
G2 = Random()
G3 = Random()

def set_random_seed(x):
	G1.seed(x)
	G2.seed(x)
	G3.seed(x)

def random_ctx(ctx_config):
	ctx = {}
	for k in ctx_config:
		options,weights = ctx_config[k]
		ctx[k] = _weighted_choice(options, weights)
	return ctx

def random_click(arm_ids, arm_config, ctx={}, no_click_weight=0, click_weight=1):
	kv_list = [f'{k}:{v}' for k,v in ctx.items()]
	kv_weights = [arm_config[kv] for kv in kv_list]
	weights = [sum(w) for w in zip(*kv_weights)]
	arm_weights = [no_click_weight] + [weights[i-1] if ctx else click_weight for i in arm_ids]
	return _weighted_choice(tuple([None]+arm_ids), tuple(arm_weights))

def sim_one(core, config):
	n_disp = config.get('n_disp',1)
	no_click_weight = config.get('no_click_weight',10)
	click_weight = config.get('click_weight',1)
	algo = config.get('algo','ucb1')
	stat = 'ctr' if algo in ['epsg'] else algo
	room = config.get('room',1)
	pool = config.get('pool',[])
	ctx_config = config.get('ctx_config',{})
	arm_config = config.get('arm_config',{})
	recalc_prob = config.get('recalc_prob',1.0)
	noise = config.get('noise',0.0) # TODO
	param = config.get('param')
	pass_ctx = config.get('pass_ctx',True)
	seg = config.get('seg',[]) or []
	#
	ctx = random_ctx(ctx_config)
	stats_ctx = ctx if pass_ctx else {} # TODO: better names
	#
	if G1.random()<=recalc_prob:
		if   stat=='ctr':  core.calculate_ctr(pool,  ctx, room=room, seg=seg) # core_base: 14k/s
		elif stat=='ucb1': core.calculate_ucb1(pool, ctx, room=room, seg=seg, alpha=param) # core_base: 12k/s
		elif stat=='tsbd': core.calculate_tsbd(pool, ctx, room=room, seg=seg) # core_base:  8k/s
	ids,vals = core.sorted_by_stat(stat, pool, stats_ctx, room=room, seg=seg, noise=noise)
	if algo=='epsg':
		if G2.random()<(param or 0):
			G2.shuffle(ids)
	disp_ids = ids[:n_disp]
	core.register_views(disp_ids, ctx, room=room, seg=seg)
	#
	click_id = random_click(disp_ids, arm_config, ctx, no_click_weight, click_weight)
	if click_id:
		core.register_click(click_id, ctx, room=room, seg=seg)

# ---[ internal ]--------------------------------------------------------------

from functools import lru_cache

def _weighted_choice(options: tuple, weights: tuple):
	# TODO: better algo
	array = _get_options_array(options, weights)
	i = G3.randint(0, len(array)-1)
	return array[i]

@lru_cache()
def _get_options_array(options, weights):
	out = []
	for x,w in zip(options,weights):
		if w>0:
			out.extend([x]*w)
	return out

# ---[ sandbox ]---------------------------------------------------------------

if __name__=="__main__":
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
	#
	ctx = random_ctx(ctx_config)
	print(ctx)
	print(random_click(pool, arm_config, ctx={}, no_click_weight=0, click_weight=1))


