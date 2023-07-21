# RUN: streamlit run sim_gui.py
import streamlit as st
import pandas as pd
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

st.set_page_config(layout='wide', page_title='McKraken') #, page_icon='🦑')
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
"""
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)


ABOUT = """
Made by [Maciej Obarski](https://www.linkedin.com/in/mobarski/).\n
Follow me on [Twitter](https://twitter.com/KerbalFPV) for news and updates.\n
Source code can be found [here](https://github.com/mobarski/kraken).
"""

ALGO = {
    'epsg':'Epsilon Greedy',
    'ucb1':'Upper Confidence Bound 1',
    'tsbd':'Thompson Sampling over Beta Distribution',
}

ctx_config = [
    ('gender','woman',50),('gender','man',40),('gender','other',10),
    ('age','2x',20),('age','3x',30),('age','4x',20),('age','5x',10),('age','6x',5),('age','7+',15),
    ('platform','desktop',30),('platform','mobile',50),('platform','tablet',10),('platform','tv',5),('platform','console',5),
    ('population','rural',10),('population','suburban',30),('population','urban',40),('population','city',20),
    ('region','north',20),('region','south',20),('region','east',20),('region','west',20),('region','center',20),
]
ctx_df = pd.DataFrame(ctx_config,columns=['key','value','weight'])

def get_arm_df(ctx_df):
    arm_config = []
    for i in range(arms):
        for key,value,_ in ctx_df.values:
            arm_config.append((i+1,key,value,random.randint(1,99)))
    return pd.DataFrame(arm_config, columns=['arm','key','value','weight'])

def df_to_arm_weights_dict(arm_df):
    arm_df['kv'] = arm_df['key'] + ':' + arm_df['value']
    rows = arm_df.pivot(index='kv', columns='arm', values='weight').to_records()
    rows = [list(x) for x in rows]
    return {x[0]:x[1:] for x in rows}

def df_to_ctx_weights(ctx_df):
    rows = ctx_df.groupby('key').agg({'value':list, 'weight':list}).to_records()
    return {x[0]:(tuple(x[1]),tuple(x[2])) for x in rows}


with st.sidebar:
    with st.expander('context', expanded=True):
        use_ctx = st.multiselect('context to use in the simulation', ['gender','age','platform','population','region'], ['gender','platform'])
        pass_ctx = st.checkbox('pass context to the bandit', value=True)
        use_seg = st.multiselect('segment the context by', use_ctx if pass_ctx else [])
    with st.expander('context weights'):
        ctx_df = ctx_df.loc[ctx_df['key'].isin(use_ctx)]
        st.data_editor(ctx_df, disabled=('key','value'), column_config={'_index':None}, width=300)
    with st.expander('arms', expanded=True):
        sc1,sc2 = st.columns(2)
        arms = sc1.number_input('number of arms', value=3, min_value=2, max_value=1000)
        seed1 = sc2.number_input('random seed (arms)', value=43)
        nl_freq = sc1.number_input('🚧 non-linear combinations', value=0, min_value=0, max_value=5, step=1)
        nl_freq = sc2.number_input('🚧 non-linearity strength',  value=3.0, min_value=1.5, max_value=5.0, step=0.5)
        if st.button("randomize arms weights", type='primary', use_container_width=True):
            random.seed(seed1)
            arm_df = get_arm_df(ctx_df)
            ss['arm_df'] = arm_df
        arm_df = ss.get('arm_df')
    with st.expander('arm weights'):
        st.data_editor(arm_df, disabled=('arm','key','value'), column_config={'_index':None}, width=300)
    with st.expander('trials', expanded=True):
        sc1,sc2 = st.columns(2)
        trials = sc1.selectbox('trials to simulate', [1,10,100,1_000,10_000,100_000], index=4)
        data_step = sc1.selectbox('data step', [2,5,10,50,100,500], index=3)
        n_display = sc2.number_input('arms pulled per trial', value=1, min_value=1, max_value=arms)
        no_click = sc2.number_input('no click weight', value=100, step=50)
        seed2 = sc2.number_input('random seed (trials)', value=43)
        algo = st.selectbox('algorithm', ['tsbd','ucb1','epsg'], format_func=ALGO.get)
        param_label,param_val = {'tsbd':(None,None),'ucb1':('alpha',1.0),'epsg':('epsilon',0.1)}[algo]
        algo_param = st.number_input(param_label, value=param_val, min_value=0.0, max_value=10.0, step=0.1) if param_label else None
        if st.button('run simulation', type='primary', use_container_width=True, disabled=arm_df is None):
            sim.set_random_seed(seed2)
            random.seed(seed2) # WHY TF this is needed ???
            with st.spinner('running'):
                pool = list(range(1,arms+1))
                test_sim.core.db.clear() # XXX
                rows = test_sim.sim_many(trials, dict(pool=pool, n_disp=n_display, no_click_weight=no_click, algo=algo, room=2, ctx_config=df_to_ctx_weights(ctx_df), arm_config=df_to_arm_weights_dict(arm_df), param=algo_param, pass_ctx=pass_ctx, step=data_step, seg=use_seg))
                ss['rows'] = rows
    st.markdown(ABOUT)

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

c12,c3a,c3b = st.columns([2,0.5,0.5])
c12.title('Monte Carlo simulator for the Kraken engine (contextual MAB)')
selected_seg = c3a.selectbox('segment', seg_list) 
selected_ctx = c3b.selectbox('context', ctx_list)

main = st.container()
c1,c2,c3=main.columns(3)


if ss.get('rows'):
    df1 = df[(df['ctx']==selected_ctx) & (df['seg']==selected_seg)]
    df0 = df[df['seg']==selected_seg]
    #
    df2 = df1[df1['trial']==trials]
    c1,c2,c3 = main.columns(3)
    c1.metric('CTR', round(df2['clicks'].sum() / df2['views'].sum(),4))
    c2.metric('clicks', df2['clicks'].sum())
    c3.metric('views', df2['views'].sum())
    #
    df3_ctr = df1.pivot_table(index=['trial'], columns=['arm'], values='ctr').reset_index()
    df3_views = df1.pivot_table(index=['trial'], columns=['arm'], values='views').reset_index()
    df3_clicks = df1.pivot_table(index=['trial'], columns=['arm'], values='clicks').reset_index()
    c1.line_chart(df3_ctr,x='trial', height=300)
    c2.line_chart(df3_clicks,x='trial', height=300)
    c3.line_chart(df3_views,x='trial', height=300)
    #
    df4 = df0[df0['trial']==trials]
    #df4 = df4[df4['ctx']!='']
    df4_ctr = df4.pivot_table(index=['ctx'], columns=['arm'], values='ctr').reset_index()
    if 1:
        c1.bar_chart(df4_ctr, x='ctx')
    else:
        c1.bar_chart(df2,x='arm',y='ctr')
    df4_clicks = df4.pivot_table(index=['ctx'], columns=['arm'], values='clicks').reset_index()
    c2.bar_chart(df4_clicks, x='ctx')
    df4_views = df4.pivot_table(index=['ctx'], columns=['arm'], values='views').reset_index()
    c3.bar_chart(df4_views, x='ctx')
    #
    #df5 = df[df['trial']==trials].groupby(['ctx']).agg({'clicks':'sum','views':'sum'}).reset_index()
    #
    c1.dataframe(df4_ctr.style.background_gradient(cmap = st_cmap, axis=1).format(precision=4), use_container_width=True)
    c2.dataframe(df4_clicks.style.background_gradient(cmap = st_cmap, axis=1), use_container_width=True)
    c3.dataframe(df4_views.style.background_gradient(cmap = st_cmap, axis=1), use_container_width=True)
    #
    c1.dataframe(df4)
    c2.dataframe(df_agg)

# TODO: reward over time VS context
# TODO: cumulative reward over time VS context
