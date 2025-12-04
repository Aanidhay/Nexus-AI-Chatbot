import streamlit as st
import requests
import os
import tempfile
import mimetypes
import uuid
import random
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import openai
import json
import rag

# Page configuration
st.set_page_config(
    page_title="NexusAI - Advanced Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)
# FORCE DEFAULT WHITE THEME
st.markdown("""
<style>
    body, .stApp, .block-container, .stSidebar {
        background-color: white !important;
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'file_content' not in st.session_state:
    st.session_state.file_content = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


# CSS for the app
st.markdown('''
<style>
    /* Main app container */
    .stApp {
        background: #0f0f0f;
        margin: 0;
        padding: 0;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        position: relative;
    }

    /* Chat messages container */
    .chat-messages {
        height: calc(100vh - 100px);
        overflow-y: auto;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    /* Chat message styling */
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        max-width: 80%;
        margin: 10px 0;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .user-message {
        align-self: flex-end;
        background: rgba(59, 130, 246, 0.1);
        border-color: rgba(59, 130, 246, 0.2);
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.4);
        transition: all 0.3s ease;
    }
    .user-message:hover {
        box-shadow: 0 0 50px rgba(59, 130, 246, 0.7);
        transform: scale(1.02);
    }

    .bot-message {
        align-self: flex-start;
        background: rgba(0, 255, 0, 0.1);
        border-color: rgba(0, 255, 0, 0.2);
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.3);
        transition: box-shadow 0.3s ease;
    }
    .bot-message:hover {
        box-shadow: 0 0 25px rgba(0, 255, 0, 0.5);
    }

    /* Input area styling */
    .input-area {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(15, 15, 15, 0.95);
        backdrop-filter: blur(10px);
        padding: 15px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        gap: 10px;
        z-index: 1000;
    }

    .input-container {
        flex: 1;
    }

    /* Sidebar styling */
    .stSidebar {
        background: rgba(15, 15, 15, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stTextInput > div > div {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 30px !important;
        height: 50px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        transform-style: preserve-3d !important;
    }
    .stButton button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 10px 20px rgba(0, 255, 136, 0.3) !important;
        background: linear-gradient(45deg, #00ff9d, #00b2ff) !important;
    }
    .stButton button:active {
        transform: translateY(-1px) scale(0.98) !important;
    }

    /* Clear button - now top left */
    .clear-button {
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 1000;
    }
    .clear-button button {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .clear-button button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3) !important;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
''', unsafe_allow_html=True)


# File processing functions
def process_file(file):
    # Get mime type from file extension
    file_type = mimetypes.guess_type(file.name)[0]
    if not file_type:
        # If mime type couldn't be guessed, try reading the content
        content = file.read(1024)
        file.seek(0)
        if content.startswith(b'%PDF-'):
            file_type = 'application/pdf'
        elif content.startswith(b'PK\x03\x04'):
            file_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            try:
                content.decode('utf-8')
                file_type = 'text/plain'
            except UnicodeDecodeError:
                file_type = 'application/octet-stream'
    file.seek(0)
    
    if file_type == 'application/pdf':
        return process_pdf(file)
    elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return process_docx(file)
    elif file_type in ['text/plain', 'text/csv']:
        return process_text(file)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def process_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def process_docx(file):
    doc = Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def process_text(file):
    return file.read().decode('utf-8')

# Sidebar for file uploads
with st.sidebar:
    st.header("File Upload")
    # RAG controls
    rag_enabled = st.checkbox('Enable RAG (Use uploaded files to augment answers)', value=False)
    rag_top_k = st.number_input('RAG: top K passages', min_value=1, max_value=10, value=3)

    uploaded_file = st.file_uploader("Upload a file", type=['pdf', 'docx', 'txt', 'csv'])
    if uploaded_file:
        try:
            content = process_file(uploaded_file)
            st.session_state.uploaded_files.append(uploaded_file.name)
            st.session_state.file_content += content
            st.success(f"Successfully processed {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")



# Main chat interface
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.messages:
    with st.container():
        st.markdown(f"""
        <div class="chat-message {'user-message' if message['role'] == 'user' else 'bot-message'}">
            <div><strong>{'You' if message['role'] == 'user' else 'TheScytheNexus AI'}:</strong></div>
            <div>{message['content']}</div>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Input area
st.markdown('<div class="input-area">', unsafe_allow_html=True)
cols = st.columns([6, 1])

def detect_language(text):
    """Detect the language of the input text"""
    # Simple detection for common languages
    if any(char in text for char in 'ऀ-ॿ'):
        return 'hindi'
    return 'english'

def translate_to_english(text, source_lang):
    """Translate text to English if it's not already in English"""
    if source_lang == 'hindi':
        # For simplicity, we'll use the Gemini API to translate
        try:
            response = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={st.secrets["gemini"]["api_key"]}',
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{
                        'parts': [{
                            'text': f"Translate this from {source_lang} to English: {text}"
                        }]
                    }]
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
        except:
            pass
    return text

def translate_response(text, target_lang):
    """Translate text to the target language if not English"""
    if target_lang != 'english':
        try:
            response = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={st.secrets["gemini"]["api_key"]}',
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{
                        'parts': [{
                            'text': f"Translate this from English to {target_lang} (keep it natural and conversational): {text}"
                        }]
                    }]
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
        except:
            pass
    return text

def process_input():
    if st.session_state.get(st.session_state.user_input_key, '').strip():
        user_input = st.session_state[st.session_state.user_input_key].strip()
        
        # Detect input language
        input_lang = detect_language(user_input)
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            # Check if asking about creator
            if any(phrase in user_input.lower() for phrase in ["who made you", "who created you", "your creator"]):
                ai_response = "TheScytheNexus made me!"
                if input_lang == 'hindi':
                    ai_response = "मुझे TheScytheNexus ने बनाया है!"
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            else:
                if st.session_state.file_content:
                    # Get AI response about the file content
                    with st.spinner("TheScytheNexus AI IS THINKING"):
                        # Include file content in the prompt
                        prompt = f"Document content:\n{st.session_state.file_content}\n\nQuestion: {user_input}"
                        
                        # If RAG enabled, retrieve top passages and prepend them as context
                        if 'rag_enabled' in locals() and rag_enabled and st.session_state.file_content:
                            try:
                                rag.build_index_from_texts([st.session_state.file_content])
                                retrieved = rag.retrieve(user_input, top_k=rag_top_k)
                                if retrieved:
                                    ctx = '\n--- Retrieved passages (RAG) ---\n'
                                    for r in retrieved:
                                        ctx += r['chunk'] + '\n\n'
                                    prompt = f"{ctx}\n\n" + prompt
                            except Exception as e:
                                # fail silently to avoid breaking chat if RAG fails
                                pass
                        
                        response = requests.post(
                            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={st.secrets["gemini"]["api_key"]}',
                            headers={'Content-Type': 'application/json'},
                            json={
                                'contents': [{
                                    'parts': [{
                                        'text': translate_to_english(prompt, input_lang) if input_lang != 'english' else prompt
                                    }]
                                }]
                            },
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            ai_response = response.json()['candidates'][0]['content']['parts'][0]['text']
                            # Translate response to user's language if needed
                            if input_lang != 'english':
                                ai_response = translate_response(ai_response, input_lang)
                        else:
                            ai_response = f"Failed to get response from Gemini: {response.status_code} {response.text}"
                    
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    with st.spinner("TheScytheNexus AI IS THINKING"):
                        response = requests.post(
                            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={st.secrets["gemini"]["api_key"]}',
                            headers={
                                'Content-Type': 'application/json'
                            },
                            json={
                                'contents': [{
                                    'parts': [{
                                        'text': translate_to_english(user_input, input_lang) if input_lang != 'english' else user_input
                                    }]
                                }]
                            },
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            ai_response = response.json()['candidates'][0]['content']['parts'][0]['text']
                            # Translate response to user's language if needed
                            if input_lang != 'english':
                                ai_response = translate_response(ai_response, input_lang)
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        else:
                            st.error(f"Failed to get response from Gemini: {response.status_code} {response.text}")
                    
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to Gemini API. Please check your internet connection.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with cols[0]:
    # Create a custom input field with autocomplete disabled
    if 'user_input_key' not in st.session_state:
        st.session_state.user_input_key = "user_input_" + str(uuid.uuid4())
        
    user_input = st.text_input(
        "Message",
        key=st.session_state.user_input_key,
        label_visibility="collapsed",
        on_change=process_input,
        autocomplete="off",
        placeholder="Type your message..."
    )
with cols[1]:
    if st.button("Send", use_container_width=True):
        process_input()
st.markdown('</div></div>', unsafe_allow_html=True)

# Clear chat button (top left)
with st.container():
    st.markdown('<div class="clear-button">', unsafe_allow_html=True)
    if st.button("Clear Chat", key="clear"):
        st.session_state.messages = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)