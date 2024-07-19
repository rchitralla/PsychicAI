import os
import streamlit as st
import openai
import subprocess

# Set your OpenAI API key here
openai.api_key = os.getenv('OPENAI_API_KEY', 'your_openai_api_key')

def get_fortune():
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt="Give me a fun fortune.",
        max_tokens=50
    )
    return response.choices[0].text.strip()

def get_lolcat_fortune(fortune_text):
    result = subprocess.run(['lolcat'], input=fortune_text.encode('utf-8'), stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

# Streamlit app title
st.title('AI Lolcat Fortune')

# Get the AI-generated fortune and lolcat fortune
fortune_text = get_fortune()
lolcat_fortune = get_lolcat_fortune(fortune_text)

# Display the original fortune
st.subheader('AI-generated Fortune')
st.text(fortune_text)

# Display the lolcat fortune
st.subheader('Lolcat Fortune')
st.code(lolcat_fortune, language='')

# Refresh button
if st.button('Get another fortune'):
    st.experimental_rerun()
