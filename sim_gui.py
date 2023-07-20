# RUN: streamlit run sim_gui.py
import streamlit as st
import pandas as pd
import random
import test_sim
import sim

st.set_page_config(layout='wide')
ss = st.session_state

css = """
.css-1544g2n {
 padding-top: 48px;
}
.css-z5fcl4 {
 position: relative;
 padding-top: 48px;
}
"""
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)


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


main = st.container()


with st.sidebar:
    seed = st.number_input('random seed', value=43)
    with st.expander('context', expanded=True):
        use_ctx = st.multiselect('context to use', ['gender','age','platform','population','region'], ['gender','platform'])
        pass_ctx = st.checkbox('pass context to the bandit', value=True)
    with st.expander('context weights'):
        ctx_df = ctx_df.loc[ctx_df['key'].isin(use_ctx)]
        st.data_editor(ctx_df, disabled=('key','value'), column_config={'_index':None}, width=300)
    with st.expander('arms', expanded=True):
        arms = st.number_input('number of arms', value=3, min_value=2, max_value=1000)
        if st.button("randomize weights", use_container_width=True):
            random.seed(seed)
            sim.set_random_seed(seed)
            arm_df = get_arm_df(ctx_df)
            ss['arm_df'] = arm_df
        arm_df = ss.get('arm_df')
    with st.expander('arm weights'):
        st.data_editor(arm_df, disabled=('arm','key','value'), column_config={'_index':None}, width=300)
    with st.expander('trials', expanded=True):
        trials = st.selectbox('trials to simulate', [1,10,100,1_000,10_000,100_000], index=4)
        n_display = st.number_input('arms displayed per trial', value=1, min_value=1, max_value=arms)
        no_click = st.number_input('no click weight', value=100, step=10)
        algo = st.selectbox('algorithm', ['tsbd','ucb1','epsg'], format_func=ALGO.get)
        param_label,param_val = {'tsbd':(None,None),'ucb1':('alpha',1.0),'epsg':('epsilon',0.1)}[algo]
        algo_param = st.number_input(param_label, value=param_val, min_value=0.0, max_value=10.0, step=0.1) if param_label else None
        if st.button('run', type='primary', use_container_width=True, disabled=arm_df is None):
            random.seed(seed)
            sim.set_random_seed(seed)
            with st.spinner('running'):
                pool = list(range(1,arms+1))
                test_sim.core.db.clear() # XXX
                rows = test_sim.sim_many(trials, dict(pool=pool, n_disp=n_display, no_click_weight=no_click, algo=algo, room=2, ctx_config=df_to_ctx_weights(ctx_df), arm_config=df_to_arm_weights_dict(arm_df), param=algo_param, pass_ctx=pass_ctx))
                ss['rows'] = rows

c1,c2,c3=main.columns(3)
c1.title('Contextual Bandit Simulator')
ctx_list = ['']+list(sorted([f'{x[0]}:{x[1]}' for x in ctx_config if x[0] in use_ctx])) # XXX
selected_ctx = c2.selectbox('context', ctx_list)

if ss.get('rows'):
    rows = ss['rows']
    df = pd.DataFrame(rows, columns=['trial','arm','ctx','clicks','views','ctr'])
    df1 = df[df['ctx']==selected_ctx]
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
    c1.line_chart(df3_ctr,x='trial')
    c2.line_chart(df3_clicks,x='trial')
    c3.line_chart(df3_views,x='trial')
    #
    df4 = df[df['trial']==trials]
    df4 = df4[df4['ctx']!='']
    df4_ctr = df4.pivot_table(index=['ctx'], columns=['arm'], values='ctr').reset_index()
    c1.bar_chart(df4_ctr, x='ctx')
    df4_clicks = df4.pivot_table(index=['ctx'], columns=['arm'], values='clicks').reset_index()
    c2.bar_chart(df4_clicks, x='ctx')
    df4_views = df4.pivot_table(index=['ctx'], columns=['arm'], values='views').reset_index()
    c3.bar_chart(df4_views, x='ctx')
    #
    df5 = df[df['trial']==trials].groupby(['ctx']).agg({'clicks':'sum','views':'sum'}).reset_index()
    #
    c1.dataframe(df4_ctr.style.background_gradient(cmap ='coolwarm', axis=1).format(precision=4))
    c2.dataframe(df4_clicks.style.background_gradient(cmap ='coolwarm', axis=1))
    c3.dataframe(df4_views.style.background_gradient(cmap ='coolwarm', axis=1))

# TODO: reward over time VS context
# TODO: cumulative reward over time VS context
