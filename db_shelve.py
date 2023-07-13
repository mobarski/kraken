import shelve
from math import log, sqrt

db = shelve.open('data/test1.shelve')
exp_id = experiment_id = 1

# TODO: segment (as ctx keys)

def register_views(arm_ids, ctx={}, ctx_per_id=[]):
	_register_stat('views', arm_ids, ctx, ctx_per_id)


def register_click(arm_id, ctx={}, ctx2=[]):
	_register_stat('clicks', [arm_id], ctx, [ctx2])


def calculate_ctr(arm_ids, ctx={}):
	stat = 'ctr'
	for arm_id in arm_ids:
		kv = f'e{exp_id}:views:a{arm_id}'
		kc = f'e{exp_id}:clicks:a{arm_id}'
		key = f'e{exp_id}:{stat}:a{arm_id}'
		db[key] = db.get(kc,0) / db.get(kv,1)
		for k,v in ctx.items():
			kv = f'e{exp_id}:views-ctx:a{arm_id}:{k}:{v}'
			kc = f'e{exp_id}:clicks-ctx:a{arm_id}:{k}:{v}'
			key = f'e{exp_id}:{stat}-ctx:a{arm_id}:{k}:{v}'
			db[key] = db.get(kc,0) / db.get(kv,1)
	db.sync()

def calculate_ucb(arm_ids, ctx={}):
	"upper confidence band"
	alpha = 1.0 # exploration meta-param
	total_views = db.get(f'e{exp_id}:views-agg',0)
	for arm_id in arm_ids:
		arm_views = db.get(f'e{exp_id}:views:a{arm_id}',0.5)
		ctr = db.get(f'e{exp_id}:ctr:a{arm_id}',0)
		key = f'e{exp_id}:ucb:a{arm_id}'
		db[key] = ctr + alpha*sqrt(2*log(total_views)/arm_views)
		for k,v in ctx.items():
			arm_views = db.get(f'e{exp_id}:views-ctx:a{arm_id}:{k}:{v}',0.5)
			ctr = db.get(f'e{exp_id}:ctr-ctx:a{arm_id}:{k}:{v}',0)
			key = f'e{exp_id}:ucb-ctx:a{arm_id}:{k}:{v}'
			db[key] = ctr + alpha*sqrt(2*log(total_views)/arm_views)
	db.sync()

def sorted_by_stat(stat, arm_ids, ctx={}):
	if ctx:
		kv_stat_values = [[db.get(f'e{exp_id}:{stat}-ctx:a{a}:{k}:{v}',0) for k,v in ctx.items()] for a in arm_ids]
		stat_values = [sum(x)/len(x) for x in kv_stat_values] # TODO: replace sum/len with something better?
	else:
		stat_values = [db.get(f'e{exp_id}:{stat}:a{a}',0) for a in arm_ids]
	by_value = sorted(zip(arm_ids,stat_values), key=lambda x:x[1], reverse=True)
	sorted_ids = [x[0] for x in by_value]
	values = [x[1] for x in by_value]
	return sorted_ids, values


# ---[ internal ]--------------------------------------------------------------

def _inc(key):
	db[key] = db.get(key,0) + 1

def _register_stat(stat, arm_ids, ctx, ctx_per_id):
	for arm_id in arm_ids:
		_inc(f'e{exp_id}:{stat}:a{arm_id}')
		_inc(f'e{exp_id}:{stat}-agg')
		for k,v in ctx.items():
			_inc(f'e{exp_id}:{stat}-ctx:a{arm_id}:{k}:{v}')
			_inc(f'e{exp_id}:{stat}-agg-ctx:{k}:{v}')
	for arm_id,aux_ctx in zip(arm_ids, ctx_per_id):
		for k,v in aux_ctx.items():
			_inc(f'e{exp_id}:{stat}-ctx:a{arm_id}:{k}:{v}')
			_inc(f'e{exp_id}:{stat}-agg-ctx:{k}:{v}')
	db.sync()
