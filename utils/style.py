import base64
import streamlit as st
from .data import P

def header():
 css=(P/'assets/ui.css').read_text(encoding='utf-8')
 st.markdown('<style>'+css+'</style>',unsafe_allow_html=True)
 logo=base64.b64encode((P/'assets/xinjiang_university.jpg').read_bytes()).decode()
 st.markdown(f'''<div class="brand"><img alt="Xinjiang University" src="data:image/jpeg;base64,{logo}"><div><strong>OasisInsight</strong><small>Xinjiang University · Team OasisInsight</small></div><span class="badge">Urumqi · 2016–2023</span></div>''',unsafe_allow_html=True)

def finding(text):
 st.markdown(f'<div class="finding"><small>KEY FINDING</small><p>{text}</p></div>',unsafe_allow_html=True)

def about():
 with st.expander('About / Team'):
  st.markdown('**Team Members**  \n李春晖 · 郭超 · 张夏璇\n\n**Institution**  \n新疆大学 · Xinjiang University')
  st.caption('OasisInsight connects multi-source observations, trajectory analysis, spatial validation and rule-based governance support for dryland oasis cities.')
def footer():
 st.markdown('<div class="footer">Developed by Chunhui Li, Chao Guo, and Xiaxuan Zhang · Xinjiang University<br><small>Research demonstration · Precomputed observations and model results</small></div>',unsafe_allow_html=True)
