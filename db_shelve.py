import shelve
from math import log, sqrt

db = shelve.open('data/test1.shelve')
room = 1 # TODO: param

def register_views(arm_ids, ctx={}, ctx_per_id=[], seg=[]):
	_register_stat('views', arm_ids, ctx, ctx_per_id, seg)


def register_click(arm_id, ctx={}, ctx2={}, seg=[]):
	_register_stat('clicks', [arm_id], ctx, [ctx2], seg)


def calculate_ctr(arm_ids, ctx={}, seg=[]):
	stat = 'ctr'
	segment = _segment_str(ctx, seg)
	for arm_id in arm_ids:
		kv = f'r{room}:{segment}|views:a{arm_id}'
		kc = f'r{room}:{segment}|clicks:a{arm_id}'
		key = f'r{room}:{segment}|{stat}:a{arm_id}'
		db[key] = db.get(kc,0) / db.get(kv,1)
		for k,v in ctx.items():
			kv = f'r{room}:{segment}|views-ctx:a{arm_id}:{k}:{v}'
			kc = f'r{room}:{segment}|clicks-ctx:a{arm_id}:{k}:{v}'
			key = f'r{room}:{segment}|{stat}-ctx:a{arm_id}:{k}:{v}'
			db[key] = db.get(kc,0) / db.get(kv,1)
	db.sync()

def calculate_ucb(arm_ids, ctx={}, seg=[]):
	"upper confidence band"
	alpha = 1.0 # exploration meta-param
	segment = _segment_str(ctx, seg)
	total_views = db.get(f'r{room}:{segment}|views-agg',0)
	for arm_id in arm_ids:
		arm_views = db.get(f'r{room}:{segment}|views:a{arm_id}',0.5)
		ctr = db.get(f'r{room}:{segment}|ctr:a{arm_id}',0)
		key = f'r{room}:{segment}|ucb:a{arm_id}'
		db[key] = ctr + alpha*sqrt(2*log(total_views)/arm_views)
		for k,v in ctx.items():
			arm_views = db.get(f'r{room}:{segment}|views-ctx:a{arm_id}:{k}:{v}',0.5)
			ctr = db.get(f'r{room}:{segment}|ctr-ctx:a{arm_id}:{k}:{v}',0)
			key = f'r{room}:{segment}|ucb-ctx:a{arm_id}:{k}:{v}'
			db[key] = ctr + alpha*sqrt(2*log(total_views)/arm_views)
	db.sync()

def sorted_by_stat(stat, arm_ids, ctx={}, seg=[]):
	"return arm ids sorted by given stat (descending), and stat values"
	segment = _segment_str(ctx, seg)
	if ctx:
		kv_stat_values = [[db.get(f'r{room}:{segment}|{stat}-ctx:a{a}:{k}:{v}',0) for k,v in ctx.items()] for a in arm_ids]
		stat_values = [sum(x)/len(x) for x in kv_stat_values] # TODO: replace sum/len with something better?
	else:
		stat_values = [db.get(f'r{room}:{segment}|{stat}:a{a}',0) for a in arm_ids]
	by_value = sorted(zip(arm_ids,stat_values), key=lambda x:x[1], reverse=True)
	sorted_ids = [x[0] for x in by_value]
	values = [x[1] for x in by_value]
	return sorted_ids, values


# ---[ internal ]--------------------------------------------------------------

def _inc(key):
	db[key] = db.get(key,0) + 1

def _segment_str(ctx, seg):
	# TODO: ctx_per_id
	return 'seg:'+','.join([str(ctx.get(k,'')) for k in seg])

def _register_stat(stat, arm_ids, ctx, ctx_per_id, seg):
	segment = _segment_str(ctx, seg)
	for arm_id in arm_ids:
		_inc(f'r{room}:{segment}|{stat}:a{arm_id}')
		_inc(f'r{room}:{segment}|{stat}-agg')
		for k,v in ctx.items():
			_inc(f'r{room}:{segment}|{stat}-ctx:a{arm_id}:{k}:{v}')
			_inc(f'r{room}:{segment}|{stat}-agg-ctx:{k}:{v}')
	for arm_id,aux_ctx in zip(arm_ids, ctx_per_id):
		for k,v in aux_ctx.items():
			_inc(f'r{room}:{segment}|{stat}-ctx:a{arm_id}:{k}:{v}')
			_inc(f'r{room}:{segment}|{stat}-agg-ctx:{k}:{v}')
	db.sync()
