import os
import streamlit as st
import openai
import time

# Ensure the OpenAI API key is set
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    st.error('OPENAI_API_KEY environment variable is not set')
    st.stop()

# Instantiate the OpenAI client
client = openai.OpenAI(api_key=openai_api_key)

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
        except openai.error.OpenAIError as e:
            error_message = str(e).lower()
            if 'rate limit' in error_message and i < retries - 1:
                time.sleep(2 ** i)  # Exponential backoff for rate limit
            elif 'insufficient_quota' in error_message:
                st.error("You have exceeded your quota. Please check your OpenAI plan and billing details.")
                return None
            else:
                raise

# Streamlit app title
st.title('AI Fortune Teller')

try:
    # Get the AI-generated fortune
    fortune_text = get_fortune()

    # Display the fortune
    st.subheader('AI-generated Fortune')
    st.text(fortune_text or "No fortune available due to quota limit.")

    # Refresh button
    if st.button('Get another fortune'):
        st.experimental_rerun()
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
