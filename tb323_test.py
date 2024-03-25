#########################
# Import Libraries
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
from datetime import date, datetime, timedelta
from langchain.chat_models import ChatOpenAI
import copy
import os

#########################
# Functions

def READ_EXCEL(excel_location):

    """
    엑셀 파일에서 raw data가 있는 시트를 읽어옵니다.

    Parameters:
        excel_location: 엑셀 파일이 있는 파일 위치

    Returns:
        DF: 정리된 데이터프레임
    """
    
    EXCEL_FILE=pd.read_excel(excel_location, None)
    RAW_DATA_NAME=list(EXCEL_FILE.keys())[-1]
    RAW_DATA=pd.read_excel(excel_location, sheet_name=RAW_DATA_NAME)

    RAW_DATA_SORT1=RAW_DATA[['일','매체','광고유형','광고상품','Campaign','노출', '클릭', '광고비(콘솔)','광고비(VAT별도)', '유입수', '방문자수', '신규방문','예금_상담후결제', '예금_즉시결제', '대출','심사수', '승인수', '접수수', '예금+대출']]
    RAW_DATA_SORT1['일'].astype('date32[pyarrow]') #date 형식으로 전환해야 streamlit 환경에서 정상 구동
    RAW_DATA_SORT1[['노출', '클릭', '광고비(콘솔)','광고비(VAT별도)', '유입수', '방문자수', '신규방문','예금_상담후결제', '예금_즉시결제', '대출','심사수', '승인수', '접수수', '예금+대출']].astype(int)
    RAW_DATA_SORT1['예금']=RAW_DATA_SORT1['예금_상담후결제']+RAW_DATA_SORT1['예금_즉시결제'] # 예금 컬럼 제작
    PROCESSED_DF=RAW_DATA_SORT1[['일','매체','광고유형','광고상품','Campaign','노출', '클릭', '광고비(콘솔)','광고비(VAT별도)', '유입수', '방문자수', '신규방문','예금', '대출','심사수', '승인수', '접수수', '예금+대출']]

    return PROCESSED_DF


def DIVISION_INDICATORS(row):
    """
    컬럼간 나눗샘을 위한 함수, .apply 메서드를 위함.

    """
    if row.iloc[0] is None or row.iloc[0] == 0:
        return 0
    else:
        return row.iloc[1] / row.iloc[0]

def INDICATOR_BUILDER(DF):
    """
    READ_EXCEL(url)로 읽어온 데이터프레임에서 KPI를 계산하여 추가하는 함수
    DIVISION_INDICATORS(row) 함수 적용

    Parameters:
        DF: READ_EXCEL(url)로 읽어온 데이터프레임

    Returns:
        RES_DF: 정리된 데이터프레임
    """
    RES_DF=copy.deepcopy(DF)
    INDICATORS_LIST=['CPC','CPS','CPU','CPA','접수CPA','심사CPA','승인CPA','예금CPA','대출CPA']
    VARIABLE_LIST=['클릭','유입수', '방문자수','예금+대출','접수수','심사수','승인수','예금','대출']
    COUNTER=0
    for i in VARIABLE_LIST:
        DIVISION_DF=DF[[i,'광고비(VAT별도)']]
        RES_DF[INDICATORS_LIST[COUNTER]]=DIVISION_DF.apply(DIVISION_INDICATORS,axis=1)
        
        COUNTER+=1

    return RES_DF  

def ORGANIZE_RAW_DATA(PROCESSED_DF):

    """
    READ_EXCEL(url)로 읽어온 데이터프레임에서 위계적 분류 및 대출, 예금, 전체 데이터 계산 후 데이터프레임에 추가하는 함수
    'media', 'sort' 에캠페인 대분류, 세부 캠페인 분류 값 적용하여 정리
    INDICATOR_BUILDER(DF) 함수 적용

    Parameters:
        PROCESSED_DF: READ_EXCEL(url)로 읽어온 데이터프레임

    Returns:
        ARRANGED_DF: 정리된 데이터프레임
    """

    ALL_DF_LI=[]
    # 전체 데이터 정리
    TOT_DF=PROCESSED_DF.groupby('일').sum()
    TOT_DF_FILTER=TOT_DF.drop(columns=['매체','광고유형','광고상품','Campaign'])
    TOT_DF_INDICATOR=INDICATOR_BUILDER(TOT_DF_FILTER.reset_index())
    TOT_DF_MERGE=pd.merge(TOT_DF.reset_index(), TOT_DF_INDICATOR, how='inner')
    TOT_DF_MERGE[['sort','media']]='summary_total'
    TOT_DF_MERGE[['매체','광고유형','광고상품','Campaign']]='summary_total'
    ALL_DF_LI.append(TOT_DF_MERGE)
    # 예금, 대출 데이터 정리
    TOT_CAMP_A=PROCESSED_DF['Campaign'].unique()
    for camp in TOT_CAMP_A:    
        TOT_CAMP_DF_RAW=PROCESSED_DF[PROCESSED_DF['Campaign']==camp]
        TOT_CAMP_DF=TOT_CAMP_DF_RAW.groupby('일').sum()
        TOT_CAMP_DF_FILTER=TOT_CAMP_DF.drop(columns=['매체','광고유형','광고상품','Campaign'])
        TOT_CAMP_DF_INDICATOR=INDICATOR_BUILDER(TOT_CAMP_DF_FILTER.reset_index())
        TOT_CAMP_DF_MERGE=pd.merge(TOT_DF.reset_index(), TOT_DF_INDICATOR, how='inner')
        TOT_CAMP_DF_MERGE[['sort','media']]=camp+"_전체"
        TOT_CAMP_DF_MERGE[['매체','광고유형','광고상품','Campaign']]=camp+"_전체"
        ALL_DF_LI.append(TOT_CAMP_DF_MERGE)

    #위계적 데이터 정리
    SORT_C=PROCESSED_DF['광고상품'].unique()
    for i in SORT_C:
        SORTED_1=PROCESSED_DF[PROCESSED_DF['광고상품']==i]
        SORT_MEDIA_A=SORTED_1['매체'].unique()
        for j in SORT_MEDIA_A:
            SORTED_MEDIA=SORTED_1[SORTED_1['매체']==j]
            SORT_CAMP_A=SORTED_MEDIA['Campaign'].unique()
            for z in SORT_CAMP_A:
                SORTED_CAMP=SORTED_MEDIA[SORTED_MEDIA['Campaign']==z]
                SORT_CAT_A=SORTED_CAMP['광고유형'].unique()
                for a in SORT_CAT_A:
                    SORTED_CAT= SORTED_CAMP[SORTED_CAMP['광고유형']==a]
                    FIN_DF=SORTED_CAT.groupby('일').sum()
                    FIN_DF['광고유형']=a
                    FIN_DF['Campaign']=z
                    FIN_DF['매체']=j
                    FIN_DF['광고상품']=i
                    FIN_DF_FILTER=FIN_DF.drop(columns=['매체','광고유형','광고상품','Campaign'])
                    FIN_DF_INDICATOR=INDICATOR_BUILDER(FIN_DF_FILTER.reset_index())
                    FIN_DF_MERGE=pd.merge(FIN_DF.reset_index(), FIN_DF_INDICATOR, how='inner')
                    FIN_DF_MERGE[['CPC','CPS','CPU','CPA','접수CPA','심사CPA','승인CPA','예금CPA','대출CPA']].astype(int)
                    FIN_DF_MERGE['media']=i+"_"+j
                    FIN_DF_MERGE['sort']=i+"_"+j+'_'+z+"_"+a
                    ALL_DF_LI.append(FIN_DF_MERGE)
    #데이터 통합                
    ARRANGED_DF=pd.concat(ALL_DF_LI)

    return(ARRANGED_DF)


def get_campaigns_for_media(media, dataframe):
    """
    특정 미디어에 속하는 캠페인 목록을 추출합니다.

    Parameters:
        media (str): 캠페인을 필터링할 미디어 이름.
        dataframe (DataFrame): 캠페인 데이터를 포함한 데이터프레임.

    Returns:
        list: 해당 미디어에 속하는 캠페인 목록.
    """
    media_data = dataframe[dataframe['media'] == media]
    campaign_list = list(media_data['sort'].unique())

    return campaign_list

def get_date_list_from_dataframe(dataframe):
    """
    데이터프레임에서 전체 날짜 목록을 추출합니다.

    Parameters:
        dataframe (DataFrame): 날짜 정보가 포함된 데이터프레임.

    Returns:
        list: 데이터프레임의 전체 날짜 목록.
    """
    return list(dataframe['일'].astype('date32[pyarrow]').unique())

def generate_datetime_range(start, end, delta):
    """
    주어진 범위와 간격에 따라 datetime 범위를 생성합니다.

    Parameters:
        start (datetime): 시작 날짜.
        end (datetime): 종료 날짜.
        delta (timedelta): 간격.

    Returns:
        generator: 시작과 종료 사이의 datetime 범위를 생성하는 제너레이터.
    """
    current = start
    while current <= end:
        yield current
        current += delta

def generate_date_list(start_date, end_date, delta):
    """
    주어진 범위와 간격에 따라 날짜 리스트를 생성합니다.

    Parameters:
        start_date (datetime): 시작 날짜.
        end_date (datetime): 종료 날짜.
        delta (timedelta): 간격.

    Returns:
        list: 시작과 종료 사이의 날짜를 포함하는 리스트.
    """
    date_list = [dt for dt in generate_datetime_range(start_date, end_date, delta)]
    return date_list


def calculate_variation(main_dataframe, target_date, campaign_name):
    """
    주어진 데이터에서 특정 날짜에 대한 전일 대비 변화율을 계산합니다.

    Parameters:
        main_dataframe (DataFrame): 분석할 데이터프레임.
        target_date (datetime): 대상 날짜.
        campaign_name (str): 캠페인 이름.

    Returns:
        DataFrame: 변화율을 담은 데이터프레임.
    """
    target_campaign_df = main_dataframe[main_dataframe['sort'] == campaign_name].drop(labels=['sort', 'media'], axis=1)

    target_day_loc = np.where(target_campaign_df['일'] == target_date)[0][0]
    previous_day_loc = target_day_loc - 1

    if previous_day_loc != -1:
        previous_day_values = target_campaign_df.iloc[previous_day_loc].replace(0, 1)
        day_difference = target_campaign_df.iloc[target_day_loc, :].drop(labels=['일']) - target_campaign_df.iloc[previous_day_loc, :].drop(labels=['일'])
        day_rate = day_difference / previous_day_values
    else:
        previous_day_values = target_campaign_df.iloc[target_day_loc].replace(0, 1)
        day_difference = target_campaign_df.iloc[target_day_loc, :].drop(labels=['일']) -  target_campaign_df.iloc[target_day_loc, :].drop(labels=['일'])
        day_rate = day_difference / previous_day_values

    day_rate.drop(labels=['일'], inplace=True)
    day_rate = day_rate * 100
    day_rate = day_rate.astype(int)
    day_rate_df = day_rate.to_frame()
    day_rate_df.reset_index(inplace=True)
    day_rate_df.columns = ['index', 'values']

    return day_rate_df
def KPI_ACHIVE_CAL(DATA_DF,GOAL_DF):
    """
    KPI 달성률 계산

    Parameters:
        DATA_DF: 지정 날짜로 정리된 광고데이터프레임
        GOAL_DF: KPI 목표 데이터프레임
    
    Returns:
        DF: value 컬럼에 달성률 백분률, variable 컬럼에 지표명
    

    """
    TARGET_DF=DATA_DF[['광고비(VAT별도)','클릭','방문자수']]
    SUM_AR=TARGET_DF.sum()
    CPU=0 if SUM_AR['방문자수']==0 else SUM_AR['광고비(VAT별도)']/SUM_AR['방문자수']
    CPC=0 if SUM_AR['클릭']==0 else SUM_AR['광고비(VAT별도)']/SUM_AR['클릭']
    GOAL_DF.applymap(lambda x: 1 if x == 0 else x)
    RATE_COL=[float(SUM_AR['광고비(VAT별도)']/GOAL_DF['매체비'])*100,float(CPU/GOAL_DF['CPU'])*100,float(CPC/GOAL_DF['CPC'])*100,float(SUM_AR['방문자수']/GOAL_DF['방문자수'])*100]
    
    VAR_COL=list(GOAL_DF.columns)
    
    RES_DF=pd.DataFrame({'variable':VAR_COL,'value':np.round(RATE_COL,2)})
    
    return RES_DF

def generate_comment(dataframe, date, campaign_name, llm_model):
    """
    데이터프레임에서 특정 날짜와 캠페인에 대한 코멘트를 생성합니다.

    Parameters:
        dataframe (DataFrame): 분석할 데이터프레임.
        date (str): 대상 날짜.
        campaign_name (str): 캠페인 이름.
        llm_model: 미리 훈련된 언어 모델 객체.

    Returns:
        str: 생성된 코멘트.
    """
    target_df = dataframe[dataframe['sort'] == campaign_name]
    campaign_description = target_df.to_markdown()

    variation_data = calculate_variation(dataframe, date, campaign_name)
    fee = str(variation_data[variation_data['index'] == '광고비(VAT별도)']['values'].reset_index(drop=True)[0])
    visitor = str(variation_data[variation_data['index'] == '방문자수']['values'].reset_index(drop=True)[0])
    cpa = str(variation_data[variation_data['index'] == 'CPA']['values'].reset_index(drop=True)[0])
    cpu = str(variation_data[variation_data['index'] == 'CPU']['values'].reset_index(drop=True)[0])
    cps = str(variation_data[variation_data['index'] == 'CPS']['values'].reset_index(drop=True)[0])
    cpc = str(variation_data[variation_data['index'] == 'CPC']['values'].reset_index(drop=True)[0])
    variation_comment = f'주요 지표의 변화율은 다음과 같습니다. 음수는 감소를, 양수는 증가를 의미합니다. 광고비: {fee}%, 방문자: {visitor}%, ' \
                        f'CPC: {cpc}%, CPA: {cpa}%, CPU: {cpu}%, CPS: {cps}%'

    prompt = '''#명령:
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

    question = f'다음 데이터에서 {date} 의 내용을 설명해주세요. {campaign_description} {prompt} {variation_comment}'

    return llm_model.predict(question)

def create_donut_chart(response_percentage, topic_text):
    """
    입력된 응답에 따라 도넛 차트를 생성합니다.

    Parameters:
        response_percentage (float): 응답 비율.
        topic_text (str): 주제 텍스트.

    Returns:
        alt.LayerChart: 생성된 도넛 차트.
    """
    source = pd.DataFrame({
        "Topic": ['', topic_text],
        "% value": [100 - response_percentage, response_percentage]
    })
    source_bg = pd.DataFrame({
        "Topic": ['', topic_text],
        "% value": [100, 0]
    })

    plot = alt.Chart(source, title=topic_text + ' 달성률').mark_arc(innerRadius=80, cornerRadius=25).encode(
        theta="% value",
        color=alt.Color("Topic:N", scale=alt.Scale(domain=[topic_text, '']),
        legend=None),
    )

    text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700,
                          fontStyle="italic").encode(text=alt.value(f'{response_percentage} %'))
    plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=80, cornerRadius=20).encode(
        theta="% value",
        color=alt.Color("Topic:N", scale=alt.Scale(domain=[topic_text, '']),
        legend=None),
    )

    return plot_bg + plot + text

# Excel 파일을 로드하여 전처리한 데이터를 캐싱하는 함수
@st.cache_data
def load_data(url):
    """
    Excel 파일을 로드하여 전처리한 데이터를 캐싱하는 함수입니다.

    Parameters:
        url (str): Excel 파일의 URL.

    Returns:
        list: 전처리된 데이터.
    """
    # excel_preprocess 함수를 사용하여 데이터 전처리
    tbdata = ORGANIZE_RAW_DATA(READ_EXCEL(url))
    return tbdata


#######################
DATA_COLIMNS=['일','광고비(콘솔)','광고비(VAT별도)','CPC','CPS','CPU','CPA','접수CPA','심사CPA','승인CPA','예금CPA','대출CPA',
    '클릭','유입수', '방문자수','예금+대출','접수수','심사수','승인수','예금','대출','sort','media']

#######################
# Page Configuration
st.set_page_config(
    page_title="리포트 생성 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)
alt.themes.enable('dark')

# 01 상단바 
st.title('리포트 생성 대시보드')

#######################
# Load Data
# 엑셀 파일 업로드 가능 기능, 업로드가 없는 경우 GitHub의 더미 데이터로 대시보드를 구성합니다.
uploaded_file = st.file_uploader("업로드 할 파일 선택")


if uploaded_file is not None:
    preprocessed_data = load_data(uploaded_file)
    main_data_LOAD = preprocessed_data
    main_data=main_data_LOAD[DATA_COLIMNS]
    date_list = get_date_list_from_dataframe(main_data)
    
else:
    preprocessed_data = load_data('data/sample_4월_데일리 리포트_fin.xlsx')
    main_data_LOAD = preprocessed_data
    main_data=main_data_LOAD[DATA_COLIMNS]
    date_list = get_date_list_from_dataframe(main_data)

#######################
# Layout
with st.container():  
    logo, startdate, enddate, empty1 = st.columns([150,100,100,300])
    start_d='start_date'
    end_d='end_date'
    with logo:
        st.image('data/image1.jpeg')
    with startdate:    
        date_setting = st.date_input("시작일 - 종료일",list([date_list[0],date_list[-1]]),key=start_d,max_value=(date_list[-1]),min_value=(date_list[0]))
        date_setting_list=generate_date_list(date_setting[0],date_setting[-1],timedelta(days=1))
    #필요 리스트
    # main_data 의 media 컬럼
    com_list= list(main_data['media'].unique())


    ########## 선택상자 레이아웃 
    
    media_goods,media_type,empty3,empty4=st.columns([100,100,100,100])
    goods = 'goods'
    type = 'type'
    with media_goods:
        # 미디어 변수
        media_goods=st.selectbox('미디어&광고 상품', com_list,key=goods)

    m_t_list=get_campaigns_for_media(media_goods,main_data)
    

    with media_type:
        # 세부 종목 변수
      media_type = st.selectbox('광고 유형', m_t_list,key=type)   
   
   # 일자 해당 데이터 추출
    sub_camp_df = main_data[main_data['sort'] == media_type]
    specific_df = sub_camp_df[sub_camp_df['일'].isin(date_setting_list)].reset_index(drop=True)
    # 02 Campaign Information 

    # Campaign 정보 입력 
    # Markdown과 st.write()를 함께 사용하여 한 줄에 여러 내용을 표시
        
    Company = 'A' # 회사 설정 필요 
    st.markdown('<p class="small-title">1. Campaign Information : {} - {}</p>'.format(date_setting[0].year, date_setting[0].month), unsafe_allow_html=True)
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">캠페인명: {}사 {}월 캠페인</p>'.format(Company, date_setting[0].month), unsafe_allow_html=True)
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">운영일자: {}-{}-{}</p>'.format(date_setting[0].year, date_setting[0].month, date_setting[0].day), unsafe_allow_html=True) ##날짜 변경 필요
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">캠페인 시작일: {}-{}-{}</p>'.format(date_setting[0].year, date_setting[0].month, date_setting[0].day), unsafe_allow_html=True)
    st.markdown('<p class="general-text" style="margin-bottom: 3px;">캠페인 종료일: {}-{}-{}</p>'.format(date_setting[-1].year, date_setting[-1].month, date_setting[-1].day), unsafe_allow_html=True)

#   KPI 달성 데이터 생성
    
    
   
    # KPI 컨테이너 생성
    KPI=st.container(border=True)
    with KPI:
        st.write('달성 기준 작성')
        AD_FEE_AC,AD_CPU_AC,AD_CPC_AC,AD_VISITOR_AC=st.columns([100,100,100,100])
        with AD_FEE_AC:
            FEE_AC=st.number_input('매체비')
        with AD_CPU_AC:
            CPU_AC=st.number_input('CPU')
        with AD_CPC_AC:
            CPC_AC=st.number_input('CPC')
        with AD_VISITOR_AC:
            VISITOR_AC=st.number_input('방문자 수')
        KPI_GOAL_DF=pd.DataFrame({'매체비':[FEE_AC],'CPU':[CPU_AC],'CPC':[CPC_AC],'방문자수':[VISITOR_AC]})
        
        KPI_DF=KPI_ACHIVE_CAL(specific_df,KPI_GOAL_DF)
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
        

        base = alt.Chart(KPI_DF).mark_bar().encode(
            alt.X("value:Q").title("달성률"),
            alt.Y("variable:O").title('KPI'),
            text='value:Q'
        )
        KPI_chart = base.mark_bar() + base.mark_text(align='left', dx=2)
        st.altair_chart(KPI_chart, use_container_width=True)

        # KPI 달성율 그래프 등을 KPI 컨테이너에 추가
        ####그래프 여기에 추가하세요
        KPI_container.markdown("[KPI 달성율]")


    # 03 Media Trend

    # container
    st.markdown('<p class="small-title">2. Media Trend :</p>', unsafe_allow_html=True)
    media1, media2, media3 = st.columns([1.5,3,1]) 
    media3_key = 'media3'
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
        KPI_pie = create_donut_chart(KPI_DF.iloc[0][1],KPI_DF.iloc[0][0])

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

        # 수치 리스트   
        var_list = list(main_data.columns)[::-1]
        elements_to_remove=['media','sort','일','매체','광고유형','광고상품','Campaign']
        var_list = list(filter(lambda x: x not in elements_to_remove, var_list))


        with media3_container:
            var_name = st.selectbox("상세 지표", var_list)
            
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
        chart_df = main_data[main_data['media']==media_goods]
        
        
        source = chart_df[chart_df['일'].isin(date_setting_list)][['sort','일',var_name]]
        source['일'] = source['일'].astype(str)
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
        lin_chart = alt.layer(
            line, selectors, points, rules, text
        ).properties(
            width=600, height=300
        )
        
        st.altair_chart(lin_chart, use_container_width=True) 
        ################ chart 
    
    #코멘트 컨테이너
    ###################세부종목 데이터프레임 생성(코멘트 및 데일리 트렌드 데이터에 사용)
    
    #세부종목 데이터프레임의 날짜 리스트 추출
    comment_date_list = list(specific_df['일'].unique())
    ####################
    comment_container = st.container(border=True)
    with comment_container:
        comment_date=st.selectbox('코멘트 일자', comment_date_list)
        ###### 객체 생성 및 API 입력
        api_input = st.text_input('OpenAI API Key')
        if api_input:
            os.environ['OPENAI_API_KEY'] = api_input
            llm = ChatOpenAI(temperature=0,               # 창의성 (0.0 ~ 2.0) 
                 model_name='gpt-4',  # 모델명
                )
            if st.button('코멘트 생성'):
                st.spinner(text='in progress')
                st.write(generate_comment(main_data, comment_date, media_type, llm))
            else:
                st.write('no_comment')
        else:
            st.write('Type Your API Key to get the report.')

    # 04 Daily Trend
    st.markdown('<p class="small-title">3.Daily Trend : </p>', unsafe_allow_html=True)

    # 데일리 트렌드 컨테이너
    DailyTrend_container = st.container(border=True)
    
    with DailyTrend_container:
        st.write('데일리 트렌드 데이터')

        ############ 세부 종목 df
        st.write(specific_df)
        ############

    # 05 전일비교 Trend
    st.markdown('<p class="small-title">3.전일비교 Trend: </p>', unsafe_allow_html=True)

    # 전일비교 트렌드 컨테이너
    DayTrend_container = st.container(border=True)
    # 여기에 그래프나 데이터를 추가하세요.

    c_data = calculate_variation(main_data,comment_date,media_type)

    c_chart_b = alt.Chart(c_data).mark_bar().encode(
    x="index",
    y="values:Q",
    text='values:Q',
    color=alt.condition(
        alt.datum.values > 0,
        alt.value("blue"), # The positive color
        alt.value("red") # The negative color
            
        )
    )

    c_chart = c_chart_b.mark_bar() + c_chart_b.mark_text(fontSize=15,dy=alt.expr(alt.expr.if_(alt.datum.values <= 0, 10, -20)))
    st.altair_chart(c_chart, use_container_width=True)
    

    with DayTrend_container:
        st.write('전일 비교 트렌드 데이터 ['+str(var_name)+'] '+str(comment_date))
        
    # css
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

