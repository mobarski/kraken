# RUN: streamlit run sim_gui.py
import streamlit as st
import pandas as pd
import altair as alt

# TODO: delayed arm start
# TODO: sliding window for charts
# TODO: imputation: simple / bayesian

import random
import test_sim
import sim

# GRADIENTS
from matplotlib.colors import LinearSegmentedColormap
# streamlit/frontend/lib/src/theme/primitives/colors.ts
# #0068c9 dark blue
# #83c9ff light blue
# #ff2b2b dark red
# #ffabab light red
# #29b09d dark green
# #7defa1 light green
# #ff8700 dark orange
# #ffd16a light orange

#st_cmap = LinearSegmentedColormap.from_list('st_cmap', ['#0068c9','#ffffff','#ff2b2b']) # dark blue, white, dark red
st_cmap = LinearSegmentedColormap.from_list('st_cmap', ['#83c9ff','#ffffff','#ffabab']) # light blue, white, light red
#st_cmap = LinearSegmentedColormap.from_list('st_cmap', ['#3d9df3','#ffffff','#ff8c8c'])
# /GRADIENTS

st.set_page_config(layout='wide', page_title='MC Kraken') #, page_icon='🦑')
ss = st.session_state

css = """
/* sidebar */
.css-1544g2n {
 padding-top: 48px;
}
/* main */
.css-z5fcl4 {
 position: relative;
 padding-top: 36px;
}

/* c1 df */
/* div.css-1r6slb0:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(4) {
 margin-top: -70px;
} */
/* .css-tvhsbf {
 margin-top: -70px;
} */


"""
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)


ABOUT = """
Made by [Maciej Obarski](https://www.linkedin.com/in/mobarski/).\n
Follow me on [Twitter](https://twitter.com/KerbalFPV) for news about other projects.\n
Source code will be published [here](https://github.com/mobarski/kraken).
"""
# Source code can be found [here](https://github.com/mobarski/kraken).

ALGO = {
    'epsg':'Epsilon Greedy',
    'ucb1':'Upper Confidence Bound 1',
    'tsbd':'Thompson Sampling over Beta Distribution',
    'rand':'Random Arm',
}

ctx_config = [
    ('gender','woman',50),('gender','man',40),('gender','other',10),
    ('age','2x',20),('age','3x',30),('age','4x',20),('age','5x',10),('age','6x',5),('age','7+',15),
    ('platform','desktop',30),('platform','mobile',50),('platform','tablet',10),('platform','tv',5),('platform','console',5),
    ('population','rural',10),('population','suburban',30),('population','urban',40),('population','city',20),
    ('region','north',20),('region','south',20),('region','east',20),('region','west',20),('region','center',20),
]
ctx_df = pd.DataFrame(ctx_config,columns=['key','value','weight'])

def randomzed_arm_df(ctx_df):
    arm_config = []
    for i in range(arms):
        for key,value,_ in ctx_df.values:
            arm_config.append((i+1,key,value,random.randint(1,99)))
    return pd.DataFrame(arm_config, columns=['arm','key','value','weight'])

def randomized_nonlinear_config():
    out = {}
    pool = list(range(1,arms+1))
    v_pool = [nl_val, 1/nl_val] * nl_cnt
    ctx_weights = df_to_ctx_weights(ctx_df)
    ctx_pool = sim.random_ctx_combos(nl_cnt, 2, ctx_weights)
    a_pool = sim.random_arms(nl_cnt, pool)
    for a,ctx in zip(a_pool,ctx_pool):
        if ctx not in out: out[ctx] = {}
        out[ctx][a] = v_pool.pop(0)
    return out

def df_to_arm_weights_dict(arm_df):
    arm_df['kv'] = arm_df['key'] + ':' + arm_df['value']
    rows = arm_df.pivot(index='kv', columns='arm', values='weight').to_records()
    rows = [list(x) for x in rows]
    return {x[0]:x[1:] for x in rows}

def df_to_ctx_weights(ctx_df):
    rows = ctx_df.groupby('key').agg({'value':list, 'weight':list}).to_records()
    return {x[0]:(tuple(x[1]),tuple(x[2])) for x in rows}

# =============================================================================

with st.sidebar:
    with st.expander('context', expanded=True):
        use_ctx = st.multiselect('context to use in the simulation', ['gender','age','platform','population','region'], ['gender','platform'])
        pass_ctx = st.checkbox('pass context to the bandit', value=True)
        use_seg = st.multiselect('segment the context by', use_ctx if pass_ctx else [])
    with st.expander('context weights'):
        ctx_df = ctx_df.loc[ctx_df['key'].isin(use_ctx)]
        st.data_editor(ctx_df, disabled=('key','value'), column_config={'_index':None}, width=300)
        ctx_weights = df_to_ctx_weights(ctx_df)
    with st.expander('arms', expanded=True):
        sc1,sc2 = st.columns(2)
        arms = sc1.number_input('number of arms', value=3, min_value=2, max_value=9)
        pool = list(range(1,arms+1))
        seed1 = sc2.number_input('random seed (arms)', value=43)
        randomize = st.button("randomize arms weights", type='primary' if 'arm_df' not in ss else 'secondary', use_container_width=True)
    with st.expander('arms delay / non-linearity / decay'):
        sc1,sc2 = st.columns(2)
        delay_cnt = sc1.slider('delayed arms', min_value=0, max_value=arms-1, value=0, step=1)
        delay_start = sc2.slider('delay start', min_value=0, max_value=10_000, value=0, step=1_000)
        nl_cnt = sc1.number_input('non-linear combinations', value=3, min_value=0, max_value=5, step=1)
        nl_val = sc2.number_input('non-linearity strength',  value=5.0, min_value=1.0, max_value=5.0, step=0.5)
        dacay_type = st.radio('reward decay type',['none','global','per arm'],horizontal=True)
        if 1:
            sc1,sc2 = st.columns(2)
            decay_start_lo = lo = sc1.number_input('decay start (lo)', value=1_000, min_value=0, max_value=10_000, step=1_000)
            decay_start_hi = hi = sc2.number_input('decay start (hi)', value=5_000, min_value=0, max_value=10_000, step=1_000)
            decay_duration_lo = lo = sc1.number_input('decay duration (lo)', value=1_000, min_value=0, max_value=10_000, step=1_000)
            decay_duration_hi = hi = sc2.number_input('decay duration (hi)', value=5_000, min_value=0, max_value=10_000, step=1_000)
            decay_factor_lo = lo = sc1.number_input('decay factor (lo)', value=0.00, min_value=0.0, max_value=1.0, step=0.01)
            decay_factor_hi = hi = sc2.number_input('decay factor (hi)', value=0.05, min_value=0.0, max_value=1.0, step=0.01)
        else:
            decay_start = st.slider('decay start', min_value=0, max_value=10_000, value=(1_000,5_000), step=1_000)
            decay_duration = st.slider('decay duration', min_value=0, max_value=10_000, value=(1_000,10_000), step=1_000)
            decay_factor = st.slider('decay factor', min_value=0.0, max_value=1.0, value=(0.5,0.9), step=0.1)

        if randomize:
            random.seed(seed1)
            arm_df = randomzed_arm_df(ctx_df)
            ss['arm_df'] = arm_df
            nl_config = randomized_nonlinear_config()
            ss['nl_config'] = nl_config
            if dacay_type=='per arm':
                decay_config = sim.random_decay_config(pool, decay_start_lo, decay_start_hi, decay_duration_lo, decay_duration_hi, decay_factor_lo, decay_factor_hi)
            elif dacay_type=='global':
                a = pool[0]
                dc = sim.random_decay_config([a], decay_start_lo, decay_start_hi, decay_duration_lo, decay_duration_hi, decay_factor_lo, decay_factor_hi)
                decay_config = {x:dc[a] for x in pool}
            else:
                decay_config = {}
            ss['decay_config'] = decay_config
            delay_config = {a:(delay_start,None) for a in pool[-delay_cnt:]}
            ss['delay_config'] = delay_config
            st.experimental_rerun()
        arm_df = ss.get('arm_df')
        nl_config = ss.get('nl_config',{})
        decay_config = ss.get('decay_config',{})
        delay_config = ss.get('delay_config',{})
    with st.expander('arms weights'):
        st.data_editor(arm_df, disabled=('arm','key','value'), column_config={'_index':None}, width=300)
        st.write('non-linear config')
        st.write({str(k):str(v) for k,v in nl_config.items()})
        st.write('decay config')
        st.write(decay_config)
        st.write('delay config')
        st.write(delay_config)
    with st.expander('simulation', expanded=True):
        sc1,sc2 = st.columns(2)
        trials = sc1.selectbox('trials to simulate', [1,10,100,1_000,5_000, 10_000,20_000], index=4)
        data_step = sc1.selectbox('data step', [2,5,10,50,100,500], index=3)
        recalc_prob = sc1.number_input('recalc probability', value=1.0, min_value=0.01, max_value=1.0, step=0.05)
        n_display = sc2.number_input('arms pulled per trial', value=1, min_value=1, max_value=arms)
        no_click = sc2.number_input('no click weight', value=100, step=50)
        seed2 = sc2.number_input('random seed (trials)', value=43)
        algo = st.selectbox('algorithm', ['tsbd','ucb1','epsg','rand'], format_func=ALGO.get)
        param_label,param_val = {'tsbd':(None,None),'rand':(None,None),'ucb1':('alpha',1.0),'epsg':('epsilon',0.1)}[algo]
        algo_param = st.number_input(param_label, value=param_val, min_value=0.0, max_value=10.0, step=0.1) if param_label else None
        if st.button('run simulation', type='primary', use_container_width=True, disabled=arm_df is None):
            sim.set_random_seed(seed2)
            random.seed(seed2) # WHY TF this is needed ???
            with st.spinner('running'):
                pool = list(range(1,arms+1))
                test_sim.core.db.clear() # XXX
                rows = test_sim.sim_many(trials, dict(pool=pool, n_disp=n_display, no_click_weight=no_click, algo=algo, room=2, ctx_config=ctx_weights, arm_config=df_to_arm_weights_dict(arm_df), param=algo_param, pass_ctx=pass_ctx, step=data_step, seg=use_seg, nl_config=nl_config, recalc_prob=recalc_prob, decay_config=decay_config, new_config=delay_config))
                ss['rows'] = rows
    st.markdown(ABOUT)

# =============================================================================

seg_list = []
ctx_list = []
if ss.get('rows'):
    rows = ss['rows']
    df = pd.DataFrame(rows, columns=['trial','seg','arm','ctx','clicks','views','ctr'])
    seg_list = list(sorted(df['seg'].unique()))
    if '' not in seg_list:
        df_agg = df.groupby(['trial','arm','ctx']).agg({'clicks':'sum','views':'sum'}).reset_index()
        df_agg['seg'] = ''
        df_agg['ctr'] = df_agg['clicks'] / df_agg['views']
        df_agg = df_agg.reindex(columns=['trial','seg','arm','ctx','clicks','views','ctr'])
        df = pd.concat([df,df_agg])
        seg_list = list(sorted(df['seg'].unique()))
    #
    df_final = df[df['trial']==trials]
    ctx_list = list(sorted(df_final['ctx'].unique()))

c12,c3a,c3b,c3c = st.columns([12, 2,2,2])
c12.title('Monte Carlo simulator for the Kraken engine (contextual MAB)')
selected_seg = c3a.selectbox('segment', seg_list)
selected_grp = c3b.selectbox('context group', ['']+use_ctx)

ctx_list_filtered = [x for x in ctx_list if x.startswith(selected_grp) or x=='']
selected_ctx = c3c.selectbox('context', ctx_list_filtered)

#main = st.container()
main = st
c1,c2,c3,c3b=main.columns([3,3,2,1])

if ss.get('rows'):
    df1 = df[(df['ctx']==selected_ctx) & (df['seg']==selected_seg)]
    df0 = df[df['seg']==selected_seg]
    if selected_grp:
        df1 = df1[df1['ctx'].str.startswith(selected_grp+':') | (df1['ctx']=='')]
        df0 = df0[df0['ctx'].str.startswith(selected_grp+':') | (df0['ctx']=='')]
    # ROW 0
    df2 = df1[df1['trial']==trials]
    c1.metric('CTR', round(df2['clicks'].sum() / df2['views'].sum(),4))
    c2.metric('clicks', df2['clicks'].sum())
    c3.metric('views', df2['views'].sum())
    focus = c3b.radio('show', ['arms','context'], horizontal=True)
    # === COLUMNS ===
    c1,c2,c3=main.columns(3)
    # === ROW 1 ===
    if focus=='arms':
        col='arm'
        dfx = df1
    else:
        col='ctx'
        dfx = df0[df0['ctx']!=''] if not selected_ctx else df1
    df3_ctr = dfx.pivot_table(index=['trial'], columns=[col], values='ctr').reset_index()
    df3_views = dfx.pivot_table(index=['trial'], columns=[col], values='views').reset_index()
    df3_clicks = dfx.pivot_table(index=['trial'], columns=[col], values='clicks').reset_index()
    c1.line_chart(df3_ctr,x='trial', height=300)
    c2.line_chart(df3_clicks,x='trial', height=300)
    c3.line_chart(df3_views,x='trial', height=300)
    # === ROW 2 ===
    if selected_ctx:
        idx=['arm']
        col=None
        df4 = df0[(df0['trial']==trials) & (df0['ctx']==selected_ctx)]
    else:
        idx=['ctx']
        col=['arm']
        df4 = df0[df0['trial']==trials]
        #df4 = df4[df4['ctx']!='']
    df4_ctr    = df4.pivot_table(index=idx, columns=col, values='ctr').reset_index()
    df4_clicks = df4.pivot_table(index=idx, columns=col, values='clicks').reset_index()
    df4_views  = df4.pivot_table(index=idx, columns=col, values='views').reset_index()
    if 1:
        c1.bar_chart(df4_ctr, x=idx[0])
    else:
        c = alt.Chart(df4).mark_bar().encode(xOffset=alt.X('arm:O', title=None), x=alt.X('ctx'), y=alt.Y('ctr',title=None)).encode(color=alt.Color('arm:O', legend=None)).properties(height=350)
        c1.altair_chart(c, use_container_width=True, theme='streamlit')
    c2.bar_chart(df4_clicks, x=idx[0])
    c3.bar_chart(df4_views, x=idx[0])
    #
    #df5 = df[df['trial']==trials].groupby(['ctx']).agg({'clicks':'sum','views':'sum'}).reset_index()
    #
    # === ROW 3 ===
    idx='ctx'
    col='arm'
    df5 = df0[df0['trial']==trials]
    df5_ctr = df5.pivot_table(index=[idx], columns=[col], values='ctr').reset_index()
    df5_clicks = df5.pivot_table(index=[idx], columns=[col], values='clicks').reset_index()
    df5_views = df5.pivot_table(index=[idx], columns=[col], values='views').reset_index()
    c1.dataframe(df5_ctr.style.background_gradient(    cmap = st_cmap, axis=1).format(precision=4), hide_index=True, use_container_width=True)
    c2.dataframe(df5_clicks.style.background_gradient( cmap = st_cmap, axis=1).format(precision=0), hide_index=True, use_container_width=True)
    c3.dataframe(df5_views.style.background_gradient(  cmap = st_cmap, axis=1).format(precision=0), hide_index=True, use_container_width=True)
    #
    #main.dataframe(df1)
    #main.dataframe(df3_ctr)
    #main.dataframe(df4_ctr)
    #main.dataframe(df4)
    #main.dataframe(df4_ctr)
