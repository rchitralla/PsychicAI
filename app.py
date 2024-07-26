import os
import streamlit as st
from openai import OpenAI
from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np

# Ensure the OpenAI API key is set
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    st.error('OPENAI_API_KEY environment variable is not set')
    st.stop()

# Set the OpenAI API key
client = OpenAI(api_key=openai_api_key)

# Load the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load or create the FAISS index
index_file = 'faiss_index.bin'
vector_dimension = 384  # for 'all-MiniLM-L6-v2'

if os.path.exists(index_file):
    index = faiss.read_index(index_file)
else:
    index = faiss.IndexFlatL2(vector_dimension)

# Sample documents (in practice, load from a file or database)
documents = [
    "The universe is a vast expanse filled with mysteries and wonders.",
    "Philosophy helps us explore the depths of human thought and existence.",
    "Psychic phenomena are often misunderstood and require a nuanced approach.",
    "The Department of Inexplicable Affairs deals with cases that defy conventional explanation."
]

# Encode the documents and add them to the FAISS index
document_embeddings = model.encode(documents, convert_to_tensor=True).cpu().detach().numpy()
index.add(document_embeddings)

# Save the FAISS index
faiss.write_index(index, index_file)

def search_documents(query):
    query_embedding = model.encode([query], convert_to_tensor=True).cpu().detach().numpy()
    D, I = index.search(query_embedding, k=3)
    
    st.write(f"Search distances: {D}")
    st.write(f"Search indices: {I}")
    
    # Validate indices to ensure they are within the range of the documents list
    valid_indices = [i for i in I[0] if 0 <= i < len(documents)]
    
    return [documents[i] for i in valid_indices]

def generate_john_response(user_input):
    try:
        relevant_docs = search_documents(user_input)
        st.write(f"Relevant documents: {relevant_docs}")
        
        if not relevant_docs:
            augmented_input = user_input
        else:
            augmented_input = user_input + " " + " ".join(relevant_docs)
        
        messages = [
            {"role": "system", "content": "You are John, an underemployed philosophy grad mistaken for a deceased psychic prodigy, now working at the Department of Inexplicable Affairs (DIA). You rely on your philosophical insights and knack for improvisation to navigate this absurd world of psychic espionage. Your speech is filled with pseudo-philosophical babble and humorous reflections."},
            {"role": "user", "content": augmented_input}
        ]
        
        response = client.create_chat_completion(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        return response.choices[0].message['content'].strip()
    except Exception as e:
        st.error(f"An error occurred while generating the response: {str(e)}")
        return ""

# Streamlit app
st.title('Project Stargate: AI Psychic Fortune Teller')

# Get user input
user_input = st.text_input("Ask John for help:")

if user_input:
    try:
        john_response = generate_john_response(user_input)
        if john_response:
            st.write(f"**John's response:** {john_response}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
