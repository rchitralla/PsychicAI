import os
import streamlit as st
import subprocess
import openai

# Ensure the OpenAI API key is set
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    st.error('OPENAI_API_KEY environment variable is not set')
    st.stop()

# Set the OpenAI API key
openai.api_key = openai_api_key

def get_fortune():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a fortune teller."},
            {"role": "user", "content": "Give me a fun fortune."}
        ]
    )
    return response['choices'][0]['message']['content'].strip()

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
st.code(lolcat_fortune)

# Refresh button
if st.button('Get another fortune'):
    st.experimental_rerun()
