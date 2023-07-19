# RUN: streamlit run sim_gui.py
import streamlit as st
import pandas as pd
import random
import test_sim

ss = st.session_state

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
        use_ctx = st.multiselect('context to use', ['gender','age','platform','population','region'])
        st.checkbox('pass context to the bandit', value=True)
    with st.expander('context weights'):
        ctx_df = ctx_df.loc[ctx_df['key'].isin(use_ctx)]
        st.data_editor(ctx_df, disabled=('key','value'), column_config={'_index':None}, width=300)
    with st.expander('arms', expanded=True):
        arms = st.number_input('number of arms', value=9, min_value=2, max_value=1000)
        seed = st.number_input('random seed', value=42)
        if st.button("randomize weights", use_container_width=True):
            random.seed(seed)
            arm_df = get_arm_df(ctx_df)
            ss['arm_df'] = arm_df
        arm_df = ss.get('arm_df')
    with st.expander('arm weights'):
        st.data_editor(arm_df, disabled=('arm','key','value'), column_config={'_index':None}, width=300)
    with st.expander('trials', expanded=True):
        trials = st.selectbox('trials to simulate', [1,10,100,1_000,10_000,100_000], index=3)
        n_display = st.number_input('arms displayed per trial', value=1, min_value=1, max_value=arms)
        no_click = st.number_input('no click weight', value=100, step=10)
        st.divider()
        algo = st.selectbox('algorithm', ['tsbd','ucb1','epsg'], format_func=ALGO.get)
        param_label,param_val = {'tsbd':(None,None),'ucb1':('alpha',1.0),'epsg':('epsilon',0.1)}[algo]
        algo_param = st.number_input(param_label, value=param_val, min_value=0.0, max_value=10.0, step=0.1) if param_label else None
        if st.button('run', type='primary', use_container_width=True, disabled=arm_df is None):
            with st.spinner('running'):
                pool = list(range(1,arms+1))
                test_sim.sim_many(trials, pool=pool, n_disp=n_display, no_click_weight=no_click, stat=algo, room=2, ctx_config=df_to_ctx_weights(ctx_df), arm_config=df_to_arm_weights_dict(arm_df))

st.title('Contextual Bandit Simulator')

# TODO: reward over time VS context
# TODO: cumulative reward over time VS context
