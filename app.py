import streamlit as st
import subprocess

def get_fortune():
    result = subprocess.run(['fortune'], stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

def get_lolcat_fortune(fortune_text):
    result = subprocess.run(['lolcat'], input=fortune_text.encode('utf-8'), stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

st.title('Lolcat Fortune')

fortune_text = get_fortune()
lolcat_fortune = get_lolcat_fortune(fortune_text)

st.subheader('Original Fortune')
st.text(fortune_text)

st.subheader('Lolcat Fortune')
st.code(lolcat_fortune, language='')

if st.button('Get another fortune'):
    st.experimental_rerun()
