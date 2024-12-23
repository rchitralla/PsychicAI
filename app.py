import os
from openai import OpenAI
import streamlit as st

# Ensure the OpenAI API key is set
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    st.error('OPENAI_API_KEY environment variable is not set')
    st.stop()

# Set the OpenAI API key
client = OpenAI(
    api_key = openai_api_key,
)

def generate_john_response(user_input):
    messages = [
        {"role": "system", "content": "You are John, an underemployed philosophy grad mistaken for a deceased psychic prodigy, now working at the DIA. You rely on your philosophical insights and knack for improvisation to navigate this absurd world of psychic espionage. Your speech is filled with witty comments."},
        {"role": "user", "content": user_input}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    return response.choices[0].message.content.strip()


# Streamlit app
st.title('Project Stargate: AI Psychic Fortune Teller')
video_url = "https://www.youtube.com/watch?v=rZsMSyfEiY0"
st.video(video_url)

# Get user input
user_input = st.text_input("Ask John for help:")

if user_input:
    try:
        john_response = generate_john_response(user_input)
        st.write(f"**John's response:** {john_response}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
