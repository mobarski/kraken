
def random_ctx(ctx_config):
	ctx = {}
	for k in ctx_config:
		options,weights = ctx_config[k]
		ctx[k] = _weighted_choice(options, weights)
	return ctx

def random_click(arm_ids, arm_config, ctx={}, no_click_weight=0):
	kv_list = [f'{k}:{v}' for k,v in ctx.items()]
	kv_weights = [arm_config[kv] for kv in kv_list]
	weights = [sum(w) for w in zip(*kv_weights)]
	arm_weights = [no_click_weight] + [weights[i-1] for i in arm_ids]
	return _weighted_choice(tuple([None]+arm_ids), tuple(arm_weights))

# ---[ internal ]--------------------------------------------------------------

from random import randint
from functools import lru_cache

def _weighted_choice(options: tuple, weights: tuple):
	# TODO: better algo
	array = _get_options_array(options, weights)
	i = randint(0, len(array)-1)
	return array[i]

@lru_cache()
def _get_options_array(options, weights):
	out = []
	for x,w in zip(options,weights):
		if w>0:
			out.extend([x]*w)
	return out

# ---[ sandbox ]---------------------------------------------------------------

ctx_config = {
	'gender': [('m','f'), (45, 55)],
	'platform': [('web','mobile','tv'), (20, 50, 30)], 
}

arm_config = {
	'gender:m': [1,1,1, 2,2,2, 3,3,4],
	'gender:f': [4,4,4, 3,3,2, 2,1,1],
	'platform:web':    [1,2,3, 1,2,3, 4,5,1],
	'platform:mobile': [2,2,4, 2,3,4, 1,1,3],
	'platform:tv':     [1,1,1, 2,2,2, 3,3,3],
	'pos:1': [5,5,5, 5,5,5, 5,5,5],
	'pos:2': [3,3,3, 3,3,3, 3,3,3],
	'pos:3': [1,1,1, 1,1,1, 1,1,1],
}

pool = [1,2,3,4,5,6,7,8,9]

if __name__=="__main__":
	ctx = random_ctx(ctx_config)
	print(ctx)
	print(random_click(pool, arm_config, ctx))

