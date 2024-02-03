import streamlit as st
from pygwalker.api.streamlit import StreamlitRenderer, init_streamlit_comm
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import pygwalker as pyg

def date_data(xlsxfile,sheet_no):
    a=pd.read_excel(xlsxfile,sheet_no)
    a.dropna(axis=0,how='all',inplace=True)
    a.dropna(axis=1,how='all',inplace=True)
    a.dropna(axis=0,how='any',inplace=True)

    hl=list(np.where([x=='행 레이블' for x in list(a.iloc[:,0])])[0])
    zz=a.iloc[hl[-1]:]
    al1=list(np.where([type(x)==str for x in list(zz.iloc[:,0])])[0])
    c=[]
    for i in al1:
        if i==0:
            cl=zz.iloc[i]
        else:
            cl2=zz.iloc[ind+1:i]
            if len(cl2)>=2:
                cl2.columns=cl
                cname=zz.iloc[ind,0]
                cl2['sort']=cname
                cl2["예금+대출율"] = cl2["예금+대출율"].replace('%','')
                cl2["예금+대출율"] = cl2["예금+대출율"].astype(float)
                cl2["클릭율"] = cl2["클릭율"].replace('%','')
                cl2["클릭율"] = cl2["클릭율"].astype(float)
                c.append(cl2)
        ind=i
    z=pd.concat(c)
    return(z)

# 엑셀파일 입력시 단일 df 반환, 'talbe_sort'컬럼에서 세부 캠페인 확인 가능 
def excel_preprocess(exlfile):
    sheetnm=pd.read_excel(exlfile,None)
    
    sheetn=list(sheetnm.keys())
    sheetn.pop(4)
    sheetn.pop()
    sheetn.pop(0)

    stlist=[]

    for i in sheetn:
        ff=date_data(exlfile,i)
        ff['sort']=i+' '+ff['sort']
        stlist.append(ff)
    xlsx_sum=pd.concat(stlist)
    return(xlsx_sum)

Tbdata=excel_preprocess('data/sample_4월_데일리 리포트_fin.xlsx')

st.set_page_config(
    page_title="TBWA dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

with st.sidebar:
    st.title('🏂TBWA dashboard')
    
    year_list = list(Tbdata['행 레이블'].unique())[::-1]
    vl= list(Tbdata.columns)[::-1]
    vl.remove('행 레이블')
    vl.remove('sort')
    var_list = vl
    com_list= list(Tbdata['sort'].unique())[::-1]
    selected_year = st.selectbox('Select a date', year_list)
    selected_var = st.selectbox('Select a variable', var_list)
    selected_com = st.selectbox('Select a campaign', com_list)

    df_selected_year = Tbdata[Tbdata['행 레이블'] == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by=selected_var, ascending=False)

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)
    
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
            y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="indicators", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
            x=alt.X(f'{input_x}:O', axis=alt.Axis(title="indicators", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
            color=alt.Color(f'max({input_color}):Q',
                             legend=None,
                             scale=alt.Scale(scheme=input_color_theme)),
            stroke=alt.value('black'),
            strokeWidth=alt.value(0.25),
        ).properties(width=900
        ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
        ) 
    # height=300
    return heatmap
    
col = st.columns((4, 4), gap='medium')

with col[0]:
    st.markdown('#### Gains/Losses')

        #pie chart

    source = Tbdata[Tbdata['행 레이블']==selected_year][[selected_var,'sort']]
    s1=source[source['sort']!='Summary_Total 행 레이블']
    s2=s1[s1['sort']!='Summary_대출 행 레이블']
    s3=s2[s2['sort']!='Summary_예금 행 레이블']

    source = pd.DataFrame({"category": s3['sort'], "value": s3[selected_var]})

    tbpie=(alt.Chart(source).mark_arc().encode(
        theta="value",
        color=alt.Color(field="category", type="nominal")
    ))

    st.altair_chart(tbpie, use_container_width=True)

    st.markdown('#### AD Fee heatmap')
    
    heatmap = make_heatmap(Tbdata,'행 레이블','sort',selected_var, selected_color_theme)
    st.altair_chart(heatmap, use_container_width=True)





with col[1]:
    st.markdown('#### PYGwalker') 

    init_streamlit_comm()

    st.cache_resource
    def get_pyg_renderer() -> "StreamlitRenderer":
    
    
        return StreamlitRenderer(Tbdata, spec="./gw_config.json", debug=False)
 
    renderer = get_pyg_renderer()
 

    renderer.render_explore()

