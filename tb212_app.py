#########################
# Import libraries
import streamlit as st
from pygwalker.api.streamlit import StreamlitRenderer, init_streamlit_comm
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import pygwalker as pyg
from datetime import date, datetime, timedelta



#################### functions
#################### excel file processing
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
     ###### 세부 캠페인 복수인 경우 '전체' 생성, 각종 수치 계산식 입력 필요함 #####
    if len(z['sort'].unique())>1:
        df11=z.groupby('행 레이블').sum()
        df11['클릭율']=df11['클릭']/df11['노출']
        df11.reset_index(inplace=True)
        df11['sort']='전체'
        z=pd.concat([df11,z])
    return(z)
    

# 엑셀파일 입력시 단일 df 반환, 'media'컬럼에서 미디어 확인 가능 'sort'컬럼에서 세부 캠페인 확인 가능, date_data 함수 포함 
def excel_preprocess(exlfile):
    sheetnm=pd.read_excel(exlfile,None)
    
    sheetn=list(sheetnm.keys())
    sheetn.pop(4)
    sheetn.pop()
    sheetn.pop(0)

    stlist=[]

    for i in sheetn:
        ff=date_data(exlfile,i)
        ff['media']=i
        ff['sort']=i+' '+ff['sort']
        stlist.append(ff)
    xlsx_sum=pd.concat(stlist)
    pd.to_datetime(xlsx_sum['행 레이블'])

    xlsx_sum['행 레이블']=xlsx_sum['행 레이블'].apply(lambda x:x.date())
    return(xlsx_sum)

# media 종류에 따른 sort 리스트 생성, excel_preprocess 함수로 생성된 df 사용가능
def s_sort(media,df):
    df_sort=df[df['media']==media]
    sort_list=list(df_sort['sort'].unique())

    return (sort_list)

# df의 전체 날짜 생성 함수
def datelist(df):

    return list(df['행 레이블'].unique())
# date_setting 변수로부터 datetime의 list 추출 함수
def datetime_range(start, end, delta):
    current = start
    while current <= end:
        yield current
        current += delta
def date_list(start_date,end_date,delta):
    d_l = [dt for dt in datetime_range(start_date, end_date, delta)]
    return d_l

################## 캐싱 함수 모음
#excel 파일 로드 함수
@st.cache_data  # 👈 Add the caching decorator
def load_data(url):
    tbdata=excel_preprocess(url)
    return tbdata


#######################
# Page configuration
st.set_page_config(
    page_title="퍼포먼스 바이 TBWA",
    layout="wide", #centered or wide
    initial_sidebar_state="expanded") #auto/expanded/collapsed
alt.themes.enable('dark')


#01 상단바 
st.title('퍼포먼스 바이 TBWA')

#######################
# Load data
#액셀 파일 업로드 가능 기능, 업로드 없는 경우 github의 더미 데이터로 대시보드 구성
uploaded_file = st.file_uploader("Upload a file")
if uploaded_file is not None:
    tbdata= load_data(uploaded_file)
    lidate=datelist(tbdata)
else:
    tbdata=load_data('data/sample_4월_데일리 리포트_fin.xlsx')
    lidate=datelist(tbdata)

#######################
#layout
with st.container():  
    logo, startdate, enddate,empty1 = st.columns([150,100,100,300])
    start_d='start_date'
    end_d='end_date'
    with logo:
        st.image('data/image1.jpeg')
    with startdate:    
        date_setting = st.date_input("시작일 - 종료일",list([lidate[0],lidate[-1]]),key=start_d,max_value=(lidate[-1]),min_value=(lidate[0]))
        date_setting_list=date_list(date_setting[0],date_setting[-1],timedelta(days=1))
        

        
    # #02. Campaign Information 

    # #Campaign 정보 입력 
    # # Markdown과 st.write()를 함께 사용하여 한 줄에 여러 내용을 표시
        
    Company= 'A' ##회사 설정 필요 
    st.markdown('<p class="small-title">1. Campaign Information : {} - {}</p>'.format(date_setting[0].year, date_setting[0].month), unsafe_allow_html=True)
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">캠페인명: {}사 {}월 캠페인</p>'.format(Company, date_setting[0].month), unsafe_allow_html=True)
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">운영일자: {}-{}-{}</p>'.format(date_setting[0].year, date_setting[0].month, date_setting[0].day), unsafe_allow_html=True) ##날짜 변경 필요
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">캠페인 시작일: {}-{}-{}</p>'.format(date_setting[0].year, date_setting[0].month, date_setting[0].day), unsafe_allow_html=True)
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">캠페인 종료일: {}-{}-{}</p>'.format(date_setting[-1].year, date_setting[-1].month, date_setting[-1].day), unsafe_allow_html=True)


    # KPI 컨테이너 생성
    KPI, CKPI = st.columns([1,1]) 

    with KPI:
        # KPI 컨테이너의 스타일을 CSS로 지정하여 높이와 색상 조정
        st.markdown(
            """
            <style>
            .kpi-container {
            height: 200px; /* 원하는 높이 값(px)으로 수정 */
            border: 20px solid #FB5B5B; /* 테두리 스타일 지정 */
            padding: 10px; /* 안쪽 여백 설정 */
            }
            </style>

            """, unsafe_allow_html=True
        )
        # KPI 컨테이너 생성
        KPI_container = st.container(border=True)

        # KPI 달성율 그래프 등을 KPI 컨테이너에 추가
        ####그래프 여기에 추가하세요
        KPI_container.markdown("[KPI 달성율]")

    with CKPI:
        # CKPI 컨테이너의 스타일을 CSS로 지정하여 높이와 색상 조정
        st.markdown(
            """
            <style>
            .ckpi-container {
                height: 200px; /* 원하는 높이 값(px)으로 수정 */
                border: 20px #FB5B5B; /* 테두리 스타일 지정 */
                padding: 10px; /* 안쪽 여백 설정 */
            }
            </style>
            """, unsafe_allow_html=True
        )
        # CKPI 컨테이너 생성
        CKPI_container = st.container(border=True)

        # 회사 KPI 달성율 그래프 등을 CKPI 컨테이너에 추가
        ###그래프 여기에 추가하세요
        CKPI_container.write("[회사명 KPI 달성율]")

    #03.Media Trend

    #필요 리스트
    # tbdata 의 media 컬럼
    com_list= list(tbdata['media'].unique())


    ########## 선택상자 레이아웃 
    st.markdown('<p class="small-title">2. Media Trend :</p>', unsafe_allow_html=True)
    media_goods,media_type,empty3,empty4=st.columns([100,100,100,100])
    goods='goods'
    type='type'
    with media_goods:
        
        media_goods=st.selectbox('미디어&광고 상품', com_list,key=goods)

    m_t_list=s_sort(media_goods,tbdata)
    

    with media_type:
        media_type=st.selectbox('광고 유형', m_t_list,key=type)

    #container
    media1,media2,media3 = st.columns([1.5,3,1]) 
    media3_key='media3'
    with media1:
        # KPI 컨테이너의 스타일을 CSS로 지정하여 높이와 색상 조정
        st.markdown(
            """
            <style>
            .kpi-container {
            height: 200px; /* 원하는 높이 값(px)으로 수정 */
            border: 20px solid #FB5B5B; /* 테두리 스타일 지정 */
            padding: 10px; /* 안쪽 여백 설정 */
            }
            </style>

            """, unsafe_allow_html=True
        )
        # KPI 컨테이너 생성
        media1_container = st.container(border=True)

        # KPI 달성율 그래프 등을 KPI 컨테이너에 추가
        ####그래프 여기에 추가하세요
        media1_container.markdown("[매체 별 예산]")
    with media3:
        # CKPI 컨테이너의 스타일을 CSS로 지정하여 높이와 색상 조정
        st.markdown(
            """
            <style>
            .ckpi-container {
                height: 200px; /* 원하는 높이 값(px)으로 수정 */
                border: 20px #FB5B5B; /* 테두리 스타일 지정 */
                padding: 10px; /* 안쪽 여백 설정 */
            }
            </style>
            """, unsafe_allow_html=True
        )
        # CKPI 컨테이너 생성
        media3_container = st.container(border=True)

        # 회사 KPI 달성율 그래프 등을 CKPI 컨테이너에 추가
        ###그래프 여기에 추가하세요
        #######수치 리스트   
        vl= list(tbdata.columns)[::-1]
        vl.remove('행 레이블')
        vl.remove('sort')
        vl.remove('media')
        var_list = vl
        ########
        with media3_container:
            var_name=st.selectbox("상세 지표", var_list)
    with media2:
        # CKPI 컨테이너의 스타일을 CSS로 지정하여 높이와 색상 조정
        st.markdown(
            """
            <style>
            .ckpi-container {
                height: 200px; /* 원하는 높이 값(px)으로 수정 */
                border: 20px #FB5B5B; /* 테두리 스타일 지정 */
                padding: 10px; /* 안쪽 여백 설정 */
            }
            </style>
            """, unsafe_allow_html=True
        )
        # CKPI 컨테이너 생성
        media2_container = st.container(border=True)
        media2_container.write("[미디어-광고상품-광고유형 별 지표]")
        ################ df for chart, variable=source
        ccc=tbdata[tbdata['media']==media_goods]
        
        
        source = ccc[ccc['행 레이블'].isin(date_setting_list)][['sort','행 레이블',var_name]]
        source['행 레이블'] = source['행 레이블'].astype(str)
        source.columns=['s','d','v']
        
        ################ chart 
        # Create a selection that chooses the nearest point & selects based on x-value
        nearest = alt.selection_point(nearest=True, on='mouseover',
                                fields=['d'], empty=False)

        #The basic line
        line = alt.Chart(source).mark_line(interpolate='basis').enc임
        sub_camp_df=tbdata[tbdata['sort']==media_type]
        st.write(sub_camp_df[sub_camp_df['행 레이블'].isin(date_setting_list)])
    #04.전일비교 Trend
    st.markdown('<p class="small-title">3.전일비교 Trend: </p>', unsafe_allow_html=True)

    #전일비교 트렌드 컨테이너
    DayTrend_container = st.container(border=True)
    #여기에 그래프나 데이터를 추가하세요.
    with DayTrend_container:
        st.write('전일 비교 트렌드 데이터')
    #css
    st.markdown("""
    <style>
    .small-title {
        font-family: 'Arial', sans-serif;
        font-size:20px;
        color:#FB5B5B;
        font-weight: bold;
    }
    .general-text {
        font-family : 'Arial',sans-serif;
        font-size:18px;
        color :black;
        font-weight: regular;
    }
    </style>
    """, unsafe_allow_html=True)

