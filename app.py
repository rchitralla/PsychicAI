import os
import streamlit as st
import subprocess
import openai
import time
from openai.error import RateLimitError

# Ensure the OpenAI API key is set
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    st.error('OPENAI_API_KEY environment variable is not set')
    st.stop()

# Instantiate the OpenAI client
client = OpenAI(api_key=openai_api_key)

def get_fortune():
    retries = 5
    for i in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a fortune teller."},
                    {"role": "user", "content": "Give me a fun fortune."}
                ]
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            if i < retries - 1:
                time.sleep(2 ** i)  # Exponential backoff
            else:
                raise

def get_lolcat_fortune(fortune_text):
    result = subprocess.run(['lolcat'], input=fortune_text.encode('utf-8'), stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

# Streamlit app title
st.title('AI Lolcat Fortune')

try:
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
except RateLimitError:
    st.error("Rate limit exceeded. Please try again later.")
