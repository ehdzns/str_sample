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
from langchain.chat_models import ChatOpenAI


#################### functions
#################### excel file processing
def date_data(xlsxfile,sheet_no):
    a=pd.read_excel(xlsxfile,sheet_no)
    a.dropna(axis=0,how='all',inplace=True)
    a.dropna(axis=1,how='all',inplace=True)
    # KPI 정보 추출 코드
    if sheet_no=='Summary_Total':
        kp_df_to=a[a[a.columns[0]]=='KPI']
        kp_df_to.dropna(axis=1,how='all',inplace=True)
        kp_df_to.columns=['sort','광고비(VAT별도).','CPU.','심사CPA.']
        kp_df_to['방문자수.']=None
        kp_df_to=kp_df_to[['광고비(VAT별도).','CPU.','심사CPA.','방문자수.','sort',]]

        res_df=kp_df_to.reset_index(drop=True)
    else:
        kpi_c=a[a[a.columns[0]]=='매체비(계획)']
        kpi_b=a[a[a.columns[0]]=='CPU(계획)']
        kpi_d=a[a[a.columns[0]]=='심사 CPA(계획)']
        kpi_e=a[a[a.columns[0]]=='방문자수(계획)']
        kpi_df_e=pd.concat([kpi_c,kpi_b,kpi_d,kpi_e])
        kpi_df_e.dropna(axis=1,how='all',inplace=True)
        
        len1=len(kpi_df_e.columns)
        i=0
        kpi_li=[]
        while i<len1-1:
            
            kpi_df=kpi_df_e.iloc[:,[i,i+1]]
            A=kpi_df.iloc[0,0]
            B=kpi_df.iloc[0,1]
            if kpi_df.iloc[1,0]=='CPU(계획)':
                C=kpi_df.iloc[1,1]
                D=None
                E=None
            elif kpi_df.iloc[1,0].replace(' ','')=='심사CPA(계획)':
                D=kpi_df.iloc[1,1]
                C=None
                E=None 
            else:
                E=kpi_df.iloc[1,1]
                C=None
                D=None
            kpi_di={'광고비(VAT별도).':[B],'CPU.':[C],'심사CPA.':[D],'방문자수.':[E],'sort':[A]}
            kpi_df_ap=pd.DataFrame(kpi_di)
            kpi_li.append(kpi_df_ap)
            i+=2

        res_df=pd.concat(kpi_li)

    # 일자별 데이터 처리 진행 코드   
    a.dropna(axis=0,how='any',inplace=True)

    hl=list(np.where([x=='행 레이블' for x in list(a.iloc[:,0])])[0])
    zz=a.iloc[hl[-1]:]
    al1=list(np.where([type(x)==str for x in list(zz.iloc[:,0])])[0])
    c=[]
    sort_li=['전체']
    for i in al1:
        if i==0:
            cl=zz.iloc[i]
        else:
            cl2=zz.iloc[ind+1:i]
            if len(cl2)>=2:
                cl2.columns=cl
                cname=zz.iloc[ind,0]
                sort_li.append(cname)
                cl2['sort']=cname
                cl2["예금+대출율"] = cl2["예금+대출율"].replace('%','')
                cl2["예금+대출율"] = cl2["예금+대출율"].astype(float)
                cl2["클릭율"] = cl2["클릭율"].replace('%','')
                cl2["클릭율"] = cl2["클릭율"].astype(float)
                c.append(cl2)
        ind=i
    
    z=pd.concat(c)
    # 세부 캠페인 복수인 경우 '전체' 생성, 각종 수치 계산식 입력 필요함
    if len(z['sort'].unique())>1:
        df11=z.groupby('행 레이블').sum()
        df11['클릭율']=df11['클릭']/df11['노출']
        df11.reset_index(inplace=True)
        df11['sort']='전체'
        z=pd.concat([df11,z])


    # kpi 데이터의 세부 켐페인명 설정
    s_kpi_n=len(res_df['sort'])
    n=0
    while n<s_kpi_n:
        res_df['sort'].iloc[n]=sort_li[n]
        n+=1
    kpi_date_li=[z,res_df]
    
    return(kpi_date_li)
    

# 엑셀파일 입력시 일자별 df (final_df_kpi[0]), kpi 정보(final_df_kpi[1])로 리스트 반환, 'media'컬럼에서 미디어 확인 가능 'sort'컬럼에서 세부 캠페인 확인 가능, date_data 함수 포함 
def excel_preprocess(exlfile):
    sheetnm=pd.read_excel(exlfile,None)
    
    sheetn=list(sheetnm.keys())
    sheetn.pop(4)
    sheetn.pop()
    sheetn.pop(0)

    stlist=[]
    kpilist=[]
    for i in sheetn:
        
        f=date_data(exlfile,i)
        ff=f[0]
        ff_kpi=f[1]
        ff['media']=i
        ff['sort']=i+' '+ff['sort']
        ff_kpi['media']=i
        ff_kpi['sort']=i+' '+ff_kpi['sort']
        stlist.append(ff)
        kpilist.append(ff_kpi)
    xlsx_sum=pd.concat(stlist)
    xlsx_sum_kpi=pd.concat(kpilist)
    pd.to_datetime(xlsx_sum['행 레이블'])

    xlsx_sum['행 레이블']=xlsx_sum['행 레이블'].apply(lambda x:x.date())
    final_df_kpi=[xlsx_sum,xlsx_sum_kpi]
    return(final_df_kpi)

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

# KPI 데이터 달성 비율 추출 함수, excel_preprocess 함수 결과값을 tbdata에 입력
def kpi_achiev(tbdata,m,sem,end_date):
    kpi_dff=tbdata[1]
    tbdatadff=tbdata[0]
    kdf=kpi_dff[kpi_dff['media']==m]

    tbdf=tbdatadff[tbdatadff['media']==m]

    start_date = tbdatadff['행 레이블'].unique()[0]  # Replace with your start date

    delta = timedelta(days=1)

    date_list = [dt for dt in datetime_range(start_date, end_date, delta)]

    tbdf=tbdf[tbdf['행 레이블'].isin(date_list)]

    if len(kdf)>1:
        # 세부 캠페인 정렬
        kdf1=kdf[kdf['sort']==sem]
        kdf1.dropna(axis=1,how='any',inplace=True)
        tbdf1=tbdf[tbdf['sort']==sem]
        
        #공결값 없는 열 이름 리스트 추출
        ioo=kdf1.drop(['sort','media'],axis=1)
        kpical_li=list(ioo.columns)
        
        # 현황 합계 KPI 데이터프레임 생성
        budget_sum=tbdf1['광고비(VAT별도).'].sum()
        visitors_sum=tbdf1['방문자수.'].sum()
        CPU_sum=budget_sum/visitors_sum
        CPA=budget_sum/sum(tbdf1['심사수.'])
        kpi_period=pd.DataFrame({'광고비(VAT별도).':[budget_sum],'방문자수.':[visitors_sum],'CPU.':[CPU_sum],'심사CPA.':[CPA]})
        

        # KPI 달성 비율 생성 df 및 시각화를 위한 wideform 변환
        kpi_r=kpi_period[kpical_li]
        kpi_a=kdf1[kpical_li].astype(float)
        kpi_r, kpi_a = kpi_r.align(kpi_a, axis=1, fill_value=0)
        result = np.where(kpi_a != 0, np.divide(kpi_r, kpi_a), 0)
        result_df=pd.DataFrame(result, columns=kpi_a.columns, index=kpi_a.index)
        datt=pd.melt(result_df,value_vars=kpical_li)
        
    else: #세부 캠페인 없는 경우
        kdf.dropna(axis=1,how='any',inplace=True)
        ioo=kdf.drop(['sort','media'],axis=1)
        kpical_li=list(ioo.columns)
        

        budget_sum=tbdf['광고비(VAT별도).'].sum()
        visitors_sum=tbdf['방문자수.'].sum()
        CPU_sum=budget_sum/visitors_sum
        CPA=budget_sum/sum(tbdf['심사수.'])
        kpi_period=pd.DataFrame({'광고비(VAT별도).':[budget_sum],'방문자수.':[visitors_sum],'CPU.':[CPU_sum],'심사CPA.':[CPA]})

        
        kpi_r=kpi_period[kpical_li]
        kpi_a=kdf[kpical_li].astype(float)
        kpi_r, kpi_a = kpi_r.align(kpi_a, axis=1, fill_value=0)
        result = np.where(kpi_a != 0, np.divide(kpi_r, kpi_a), 0)
        result_df2=pd.DataFrame(result, columns=kpi_a.columns, index=kpi_a.index)
        datt=pd.melt(result_df2,value_vars=kpical_li)

    datt['value']=datt['value']*100
    datt['value']=datt['value'].astype(int)
    return(datt)
###변화량 데이터 함수

def v_change(main_df,day,detail_camp):
    
    ta_df=main_df[main_df['sort']==detail_camp].drop(labels=['sort','media'],axis=1)
    
    day_loc=np.where(ta_df['행 레이블']==day)[0][0]
    pre_day_loc=day_loc-1

    if pre_day_loc !=-1:
        pre_day_rv=ta_df.iloc[pre_day_loc].replace(0,1)
        daydif=ta_df.iloc[day_loc,:].drop(labels=['행 레이블'])-ta_df.iloc[pre_day_loc,:].drop(labels=['행 레이블'])
        dayrate=daydif/pre_day_rv
        

    else:
        pre_day_rv=ta_df.iloc[day_loc].replace(0,1)
        daydif=ta_df.iloc[day_loc,:].drop(labels=['행 레이블'])-ta_df.iloc[day_loc,:].drop(labels=['행 레이블'])
        dayrate=daydif/pre_day_rv

    dayrate.drop(labels=['행 레이블'],inplace=True)
    dayrate=dayrate*100
    dayrate=dayrate.astype(int) 
    dayrate_df=dayrate.to_frame()
    dayrate_df.reset_index(inplace=True)
    dayrate_df.columns=['index','values']
    
    return(dayrate_df)


################## 코멘트 생성 함수, v_change 함수 포함


# 객체 생성
llm = ChatOpenAI(temperature=0,               # 창의성 (0.0 ~ 2.0) 
                 
                 model_name='gpt-4',  # 모델명
                )

def coment_generation(df,date,sort,llm):
    
    tp_md=df[df['sort']==sort]
    cc=tp_md.to_markdown()
    
    
    c_data=v_change(df,date,sort)
    # 변화율 데이터 추출
    fee=str(c_data[c_data['index']=='광고비(VAT별도).']['values'].reset_index(drop=True)[0])
    visitor=str(c_data[c_data['index']=='방문자수.']['values'].reset_index(drop=True)[0])
    cpa=str(c_data[c_data['index']=='CPA.']['values'].reset_index(drop=True)[0])
    cpu=str(c_data[c_data['index']=='CPU.']['values'].reset_index(drop=True)[0])
    cps=str(c_data[c_data['index']=='CPS.']['values'].reset_index(drop=True)[0])
    cpc=str(c_data[c_data['index']=='CPC.']['values'].reset_index(drop=True)[0])
    vary=f'주요 지표의  변화율은 다음과 같다. 음수는 감소, 양수는 증가이다. 광고비: {fee}%, 방문자: {visitor}% ,CPC: {cpc}%, CPA: {cpa}%, CPU: {cpu}%, CPS: {cps}%'
    prompt='''#명령:
            “너는 퍼포먼스 마케터야. 광고 캠페인의 성과와 지표의 변화에 대해서 데일리 리포트 코멘트를 작성하려고 해. 지켜야할 규칙, 출력문을 토대로 주어진 데이터의 데일리 리포트 코멘트를 작성해줘.”
            #비용 관련 지표:
            “CPC, CPS, CPU, 신규방문CPU, 접수CPA, 심사CPA, 승인 CPA, CPA, 예금CPA, 대출CPA”
            #제약조건:
            - 코드블록을 사용하지 않는다.
            - 리포트 코멘트에 어울리는 단어와 문장을 사용한다.
            - 출력문 이외의 것은 출력하지 않는다.
            #“[지표의 변화에 대한 코멘트]”의 규칙 사항:
            - 전일과 대비하여 -3% 이상 감소한 지표에 대해 하나씩 언급하고 코멘트를 작성한다. 
            - 구체적인 숫자를 사용하여 설명한다.
            - 감소율이 큰 지표들 먼저 설명한다. 

            #“[캠페인에 대한 평가]”의 규칙 사항:
            - -3%이상 변화한 비용 관련 지표들에 대해 다른 지표와의 연관성을 분석한다. 
            - 연관성 분석을 통해 감소한 이유를 분석한다. 
            - 구체적인 숫자를 사용하여 설명한다.
            - 전일 대비 지표들의 변화를 분석하여 캠페인의 효율성을 검토한다.

            #출력문:
            [지표의 변화에 대한 코멘트]
            - 
            [캠페인에 대한 평가]
            -'''
    question = f'다음 데이터에서 {str(date)} 의 내용을 설명해줘  {cc} {prompt} {vary}'  

    return(llm.predict(question))

################## 그레프 관련 함수 모음
#달성률 차트
def make_donut(input_response, input_text):
    
  source = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100, 0]
  })
    
  plot = alt.Chart(source,title=input_text + ' 달성률').mark_arc(innerRadius=80,cornerRadius=25).encode(
      theta="% value",
      
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          ),
                      legend=None),
  )#.properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=80, cornerRadius=20).encode(
      theta="% value",
      
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          ),  # 31333F
                      legend=None),
  )#.properties(width=130, height=130)
  return plot_bg + plot + text

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
    tbdata_li= load_data(uploaded_file)
    tbdata=tbdata_li[0]
    tbKPI=tbdata_li[1]
    lidate=datelist(tbdata)
else:
    tbdata_li=load_data('data/sample_4월_데일리 리포트_fin.xlsx')
    tbdata=tbdata_li[0]
    tbKPI=tbdata_li[1]
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
    #필요 리스트
    # tbdata 의 media 컬럼
    com_list= list(tbdata['media'].unique())


    ########## 선택상자 레이아웃 
    
    media_goods,media_type,empty3,empty4=st.columns([100,100,100,100])
    goods='goods'
    type='type'
    with media_goods:
        # 미디어 변수
        media_goods=st.selectbox('미디어&광고 상품', com_list,key=goods)

    m_t_list=s_sort(media_goods,tbdata)
    

    with media_type:
        # 세부 종목 변수
      media_type=st.selectbox('광고 유형', m_t_list,key=type)   
   
    # #02. Campaign Information 

    # #Campaign 정보 입력 
    # # Markdown과 st.write()를 함께 사용하여 한 줄에 여러 내용을 표시
        
    Company= 'A' ##회사 설정 필요 
    st.markdown('<p class="small-title">1. Campaign Information : {} - {}</p>'.format(date_setting[0].year, date_setting[0].month), unsafe_allow_html=True)
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">캠페인명: {}사 {}월 캠페인</p>'.format(Company, date_setting[0].month), unsafe_allow_html=True)
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">운영일자: {}-{}-{}</p>'.format(date_setting[0].year, date_setting[0].month, date_setting[0].day), unsafe_allow_html=True) ##날짜 변경 필요
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">캠페인 시작일: {}-{}-{}</p>'.format(date_setting[0].year, date_setting[0].month, date_setting[0].day), unsafe_allow_html=True)
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">캠페인 종료일: {}-{}-{}</p>'.format(date_setting[-1].year, date_setting[-1].month, date_setting[-1].day), unsafe_allow_html=True)

#   KPI 달성 데이터 생성
    
    KPI_DF=kpi_achiev(tbdata_li,media_goods,media_type,date_setting[-1])
   
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

        #### KPI 달성 bar 그레프
        KPI_container = st.container(border=True)
        

        base=alt.Chart(KPI_DF).mark_bar().encode(
            alt.X("value:Q").title("달성률"),
            alt.Y("variable:O").title('KPI'),
            text='value:Q'
        )
        KPI_chart=base.mark_bar() + base.mark_text(align='left', dx=2)
        st.altair_chart(KPI_chart, use_container_width=True)

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

    #container
    st.markdown('<p class="small-title">2. Media Trend :</p>', unsafe_allow_html=True)
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
        KPI_pie=make_donut(KPI_DF.iloc[0][1],KPI_DF.iloc[0][0])

        st.altair_chart(KPI_pie, use_container_width=True)
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

        ######수치 리스트   
        vl= list(tbdata.columns)[::-1]
        vl.remove('행 레이블')
        vl.remove('sort')
        vl.remove('media')
        var_list = vl
        ######

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
        line = alt.Chart(source).mark_line(interpolate='linear').encode(
            alt.X('d', title="날짜"),
            alt.Y('v', type='quantitative',title=var_name),
            color='s:N'
        )

        # Transparent selectors across the chart. This is what tells us
        # the x-value of the cursor
        selectors = alt.Chart(source).mark_point().encode(
            x='d',
            opacity=alt.value(0),
        ).add_params(
            nearest
        )

        # Draw points on the line, and highlight based on selection
        points = line.mark_point().encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0))
        )

        # Draw text labels near the points, and highlight based on selection
        text = line.mark_text(align='left', dx=5, dy=-5).encode(
            text=alt.condition(nearest, 'v:Q', alt.value(' '))
        )

        # Draw a rule at the location of the selection
        rules = alt.Chart(source).mark_rule(color='gray').encode(
            x='d',
        ).transform_filter(
            nearest
        )

        # Put the five layers into a chart and bind the data
        lin_chart=alt.layer(
            line, selectors, points, rules, text
        ).properties(
            width=600, height=300
        )
        
        st.altair_chart(lin_chart, use_container_width=True) 
        ################ chart 

    #코멘트 컨테이너
    comment_container = st.container(border=True)
    with comment_container:
        
        if st.button('코멘트 생성'):
            st.write(coment_generation(tbdata,date_setting[-1],media_type,llm))
        else:
            st.write('no_coment')

    #03. Daily Trend
    st.markdown('<p class="small-title">3.Daily Trend : </p>', unsafe_allow_html=True)

    #데일리 트렌드 컨테이너
    DailyTrend_container = st.container(border=True)
    #여기에 그래프나 데이터를 추가하세요.
    with DailyTrend_container:
        st.write('데일리트렌드 데이터')

        ############ 세부 종목 df
        sub_camp_df=tbdata[tbdata['sort']==media_type]
        st.write(sub_camp_df[sub_camp_df['행 레이블'].isin(date_setting_list)].reset_index(drop=True))
        ############

    #04.전일비교 Trend
    st.markdown('<p class="small-title">3.전일비교 Trend: </p>', unsafe_allow_html=True)

    #전일비교 트렌드 컨테이너
    DayTrend_container = st.container(border=True)
    #여기에 그래프나 데이터를 추가하세요.

    c_data=v_change(tbdata,date_setting[-1],media_type)

    c_chart_b=alt.Chart(c_data).mark_bar().encode(
    x="index",
    y="values:Q",
    text='values:Q',
    color=alt.condition(
        alt.datum.values > 0,
        alt.value("blue"),  # The positive color
        alt.value("red")  # The negative color
            
        )
    )

    c_chart=c_chart_b.mark_bar() + c_chart_b.mark_text(fontSize=15,dy=alt.expr(alt.expr.if_(alt.datum.values <= 0, 10, -20)))
    st.altair_chart(c_chart, use_container_width=True)
    

    with DayTrend_container:
        st.write('전일 비교 트렌드 데이터 '+str(var_name)+' '+str(date_setting[-1]))
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

