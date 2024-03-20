import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import openai
from datetime import date, datetime, timedelta
from langchain.chat_models import ChatOpenAI
import os


api = st.text_input('OpenAI API Key')
if api:
    os.environ['OPENAI_API_KEY'] = api
    
    llm = ChatOpenAI(temperature=0,               # 창의성 (0.0 ~ 2.0) 
                    
                    model_name='gpt-4',  # 모델명
                    )
    question='what day is today'
    st.write(llm.predict(question))
else:
    st.write('type api')
st.selectbox('select',[1,2,3,4,5])
