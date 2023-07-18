from math import log, sqrt
from random import betavariate


def register_views(arm_ids, ctx={}, ctx_per_id=[], seg=[], room=1):
    _increment_stat('views', arm_ids, ctx, ctx_per_id, seg, room)


def register_click(arm_id, ctx={}, ctx2={}, seg=[], room=1):
    _increment_stat('clicks', [arm_id], ctx, [ctx2], seg, room)


# TODO: noise=0.0
def sorted_by_stat(stat, arm_ids, ctx={}, seg=[], room=1):
    "return arm ids sorted by given stat (descending), and stat values"
    segment = _segment_str(ctx, seg)
    ctx_items = tuple(ctx.items()) # optimization
    if ctx:
        keys = [f'{stat}-ctx:{a}:{k}:{v}' for k,v in ctx_items for a in arm_ids]
        cache = _get_cache(f'{room}:{segment}', keys, as_type=float)
        kv_stat_values = [[cache.get(f'{stat}-ctx:{a}:{k}:{v}',0) for k,v in ctx_items] for a in arm_ids]
        stat_values = [sum(x)/len(x) for x in kv_stat_values] # TODO: replace sum/len with something better?
    else:
        keys = [f'{stat}:{a}' for a in arm_ids]
        cache = _get_cache(f'{room}:{segment}', keys, as_type=float)
        stat_values = [cache.get(f'{stat}:{a}',0) for a in arm_ids]
    by_value = sorted(zip(arm_ids,stat_values), key=lambda x:x[1], reverse=True)
    sorted_ids = [x[0] for x in by_value]
    values = [x[1] for x in by_value]
    return sorted_ids, values

# NOTE: all calculate_* functions will be refactored as they use the same code pattern
#       they repeat the code for now to make it easier to understand

def calculate_ctr(arm_ids, ctx={}, seg=[], room=1):
    "calculate click-through rate for each arm and context"
    stat = 'ctr' # STAT SPECIFIC
    ctx_items = tuple(ctx.items()) # optimization
    segment = _segment_str(ctx, seg)
    # cache values from DB
    keys = _get_keys(arm_ids, ctx_items)
    cache = _get_cache(f'{room}:{segment}', keys)
    #
    kv_pairs = []
    for arm_id in arm_ids:
        key_v = f'views:{arm_id}'
        key_c = f'clicks:{arm_id}'
        val = cache.get(key_c,0) / cache.get(key_v,1) # STAT SPECIFIC
        key = f'{stat}:{arm_id}'
        kv_pairs.append((key,val))
        for k,v in ctx_items:
            key_v = f'views-ctx:{arm_id}:{k}:{v}'
            key_c = f'clicks-ctx:{arm_id}:{k}:{v}'
            val = cache.get(key_c,0) / cache.get(key_v,1) # STAT SPECIFIC
            key = f'{stat}-ctx:{arm_id}:{k}:{v}'
            kv_pairs.append((key,val))
    _set_many(f'{room}:{segment}', kv_pairs)


def calculate_ucb1(arm_ids, ctx={}, seg=[], room=1, alpha=1.0):
    "calculate upper confidence bound (UCB1) for each arm and context"
    stat = 'ucb1' # STAT SPECIFIC
    ctx_items = tuple(ctx.items()) # optimization
    segment = _segment_str(ctx, seg)
    # cache values from DB
    keys = _get_keys(arm_ids, ctx_items) + ['views-agg']
    cache = _get_cache(f'{room}:{segment}', keys, as_type=float)
    #
    total_views = cache.get(f'views-agg',1) # STAT SPECIFIC
    log_total_views = log(total_views)      # STAT SPECIFIC
    kv_pairs = []
    for arm_id in arm_ids:
        arm_views = cache.get(f'views:{arm_id}',1)
        arm_clicks = cache.get(f'clicks:{arm_id}',0)
        ctr = arm_clicks / arm_views
        val = ctr + alpha*sqrt(2*log_total_views/arm_views) # STAT SPECIFIC
        key = f'{stat}:{arm_id}'
        kv_pairs.append((key,val))
        for k,v in ctx_items:
            arm_views = cache.get(f'views-ctx:{arm_id}:{k}:{v}',1)
            arm_clicks = cache.get(f'clicks-ctx:{arm_id}:{k}:{v}',0)
            ctr = arm_clicks / arm_views
            val = ctr + alpha*sqrt(2*log_total_views/arm_views) # STAT SPECIFIC
            key = f'{stat}-ctx:{arm_id}:{k}:{v}'
            kv_pairs.append((key,val))
    _set_many(f'{room}:{segment}', kv_pairs)


def calculate_bucb(arm_ids, ctx={}, seg=[], room=1, zscore=1.96):
    "calculate bayesian upper confidence bound (BUCB) for each arm and context, zscore=1.96 for 95% confidence (normal distribution))"
    stat = 'bucb' # STAT SPECIFIC
    ctx_items = tuple(ctx.items()) # optimization
    segment = _segment_str(ctx, seg)
    # cache values from DB
    keys = _get_keys(arm_ids, ctx_items) + ['views-agg']
    cache = _get_cache(f'{room}:{segment}', keys, as_type=float)
    #
    kv_pairs = []
    for arm_id in arm_ids:
        arm_views = cache.get(f'views:{arm_id}',1)
        arm_clicks = cache.get(f'clicks:{arm_id}',0)
        ctr = arm_clicks / arm_views
        sigma = sqrt(ctr*(1-ctr)/arm_views) # STAT SPECIFIC
        val = ctr + zscore*sigma            # STAT SPECIFIC
        key = f'{stat}:{arm_id}'
        kv_pairs.append((key,val))
        for k,v in ctx_items:
            arm_views = cache.get(f'views-ctx:{arm_id}:{k}:{v}',1)
            arm_clicks = cache.get(f'clicks-ctx:{arm_id}:{k}:{v}',0)
            ctr = arm_clicks / arm_views
            sigma = sqrt(ctr*(1-ctr)/arm_views) # STAT SPECIFIC
            val = ctr + zscore*sigma            # STAT SPECIFIC
            key = f'{stat}-ctx:{arm_id}:{k}:{v}'
            kv_pairs.append((key,val))
    _set_many(f'{room}:{segment}', kv_pairs)


def calculate_tsbd(arm_ids, ctx={}, seg=[], room=1):
    "calculate Thompson Sampling over Beta Distribution for each arm and context"
    stat = 'tsbd' # STAT SPECIFIC
    ctx_items = tuple(ctx.items()) # optimization
    segment = _segment_str(ctx, seg)
    # cache values from DB
    keys = _get_keys(arm_ids, ctx_items) + ['views-agg']
    cache = _get_cache(f'{room}:{segment}', keys, as_type=float)
    #
    kv_pairs = []
    for arm_id in arm_ids:
        arm_views = cache.get(f'views:{arm_id}',1)
        arm_clicks = cache.get(f'clicks:{arm_id}',0)
        ctr = arm_clicks / arm_views
        alpha = arm_clicks + 1            # STAT SPECIFIC
        beta = arm_views - arm_clicks + 1 # STAT SPECIFIC
        val = betavariate(alpha, beta)    # STAT SPECIFIC
        key = f'{stat}:{arm_id}'
        kv_pairs.append((key,val))
        for k,v in ctx_items:
            arm_views = cache.get(f'views-ctx:{arm_id}:{k}:{v}',1)
            arm_clicks = cache.get(f'clicks-ctx:{arm_id}:{k}:{v}',0)
            ctr = arm_clicks / arm_views
            alpha = arm_clicks + 1            # STAT SPECIFIC
            beta = arm_views - arm_clicks + 1 # STAT SPECIFIC
            val = betavariate(alpha, beta)    # STAT SPECIFIC
            key = f'{stat}-ctx:{arm_id}:{k}:{v}'
            kv_pairs.append((key,val))
    _set_many(f'{room}:{segment}', kv_pairs)

# ---[ internal ]--------------------------------------------------------------

def _get_keys(arm_ids, ctx_items):
    keys = []
    for arm_id in arm_ids:
        keys.append(f'views:{arm_id}')
        keys.append(f'clicks:{arm_id}')
        for k,v in ctx_items:
            keys.append(f'views-ctx:{arm_id}:{k}:{v}')
            keys.append(f'clicks-ctx:{arm_id}:{k}:{v}')
    return keys

def _segment_str(ctx, seg):
    "return segment string for given context and segment"
    # TODO: ctx_per_id
    return 'seg:'+','.join([str(ctx.get(k,'')) for k in seg])

def _increment_stat(stat, arm_ids, ctx, ctx_per_id, seg, room):
    "increment stat for each arm and context"
    segment = _segment_str(ctx, seg)
    ctx_items = tuple(ctx.items()) # optimization
    todo = []
    for arm_id in arm_ids:
        todo.append(f'{stat}:{arm_id}')
        todo.append(f'{stat}-agg')
        for k,v in ctx_items:
            todo.append(f'{stat}-ctx:{arm_id}:{k}:{v}')
            todo.append(f'{stat}-agg-ctx:{k}:{v}')
    for arm_id,aux_ctx in zip(arm_ids, ctx_per_id):
        for k,v in aux_ctx.items():
            todo.append(f'{stat}-ctx:{arm_id}:{k}:{v}')
            todo.append(f'{stat}-agg-ctx:{k}:{v}')
    _increment_by_one(f'{room}:{segment}', todo)

# ---[ db specific ]----------------------------------------------------------

db = {}

def sync():
    pass # not used

def _increment_by_one(key, fields):
    for k in fields:
        db[f'{key}|{k}'] = db.get(f'{key}|{k}',0) + 1

def _set_many(key, kv_pairs):
    for k,v in kv_pairs:
        db[f'{key}|{k}'] = v

def _get_cache(key, fields, as_type=int):
    return {k:as_type(db.get(f'{key}|{k}',0)) for k in fields if db.get(f'{key}|{k}')}
