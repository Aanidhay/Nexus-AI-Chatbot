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

# Placeholder for the actual RAG functionality
# The 'rag' module is assumed to have 'build_index_from_texts' and 'retrieve' functions.
# Since you did not provide the 'rag' module, I will mock it for the code to run,
# but you MUST replace this with your actual RAG library/implementation.
class MockRAG:
    """Mock RAG functionality for demonstration purposes."""
    def build_index_from_texts(self, texts):
        st.session_state._rag_index = True # Mocking index creation

    def retrieve(self, query, top_k=3):
        # Mocking retrieval by returning random snippets from the loaded content
        if st.session_state.file_content:
            chunks = st.session_state.file_content.split('\n')
            # Filter non-empty chunks and select the top_k
            non_empty_chunks = [c.strip() for c in chunks if c.strip()]
            random_chunks = random.sample(non_empty_chunks, min(top_k, len(non_empty_chunks)))
            return [{'chunk': c} for c in random_chunks]
        return []

rag = MockRAG()

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="NexusAI - Advanced Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Initialize Session State ---
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'file_content' not in st.session_state:
    st.session_state.file_content = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_input_key' not in st.session_state:
    # Use a unique key for the input to prevent focus/clearing issues on re-run
    st.session_state.user_input_key = "user_input_" + str(uuid.uuid4())


# --- 3. Custom CSS (As Provided) ---
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
    .chat-container {
        padding-top: 50px; /* Space for the top clear button */
        padding-bottom: 90px; /* Space for the bottom input area */
        height: 100vh;
        overflow-y: auto;
        padding-left: 20px;
        padding-right: 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    /* Ensure chat container takes up necessary space */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
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
        margin-left: auto; /* Push user message to the right */
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
        margin-right: auto; /* Keep bot message to the left */
        background: rgba(0, 255, 0, 0.1);
        border-color: rgba(0, 255, 0, 0.2);
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.3);
        transition: box-shadow 0.3s ease;
    }
    .bot-message:hover {
        box-shadow: 0 0 25px rgba(0, 255, 0, 0.5);
    }
    
    .chat-message div:first-child {
        font-weight: 700;
        margin-bottom: 5px;
        color: #00ff9d; /* Highlight name */
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
        /* Match sidebar width */
        margin-left: 300px;
    }
    
    /* Adjust input area position when sidebar is collapsed */
    .stApp > header + div > div > section.main[data-testid="stSidebar"] + div .input-area {
        margin-left: 0px;
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
    .stButton button {
        background: linear-gradient(45deg, #00ff9d, #00b2ff);
        color: #0f0f0f !important;
        font-weight: bold;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 5px 15px rgba(0, 255, 136, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
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
    /* Adjust clear button position when sidebar is expanded */
    .stApp > header + div > div > section.main > div > div:first-child .clear-button {
        left: 320px;
    }
    .clear-button button {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        color: white;
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

# --- Retrieve API Key Once ---
GEMINI_API_KEY = None
try:
    # Access the environment variable injected by Docker, which Streamlit maps to st.secrets
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Configuration Error: GEMINI_API_KEY not found in environment secrets.")

# --- File Processing Functions ---
def process_pdf(file):
    """Extracts text from a PDF file."""
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def process_docx(file):
    """Extracts text from a DOCX file."""
    doc = Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def process_text(file):
    """Reads content from a text or CSV file."""
    return file.read().decode('utf-8')

def process_file(file):
    """Determines file type and calls the appropriate processing function."""
    # Reset file pointer to the start
    file.seek(0)
    
    # Get mime type from file extension
    file_type = mimetypes.guess_type(file.name)[0]
    
    # Simple fallback check for common file types if mimetypes fails
    if not file_type:
        content_peek = file.read(1024)
        file.seek(0)
        if content_peek.startswith(b'%PDF-'):
            file_type = 'application/pdf'
        elif content_peek.startswith(b'PK\x03\x04'):
            file_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            try:
                content_peek.decode('utf-8')
                file_type = 'text/plain'
            except UnicodeDecodeError:
                file_type = 'application/octet-stream'
    
    if file_type == 'application/pdf':
        return process_pdf(file)
    elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return process_docx(file)
    elif file_type in ['text/plain', 'text/csv']:
        return process_text(file)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

# --- Sidebar for File Uploads and RAG Controls ---
with st.sidebar:
    st.header("File Upload")
    
    # RAG controls
    rag_enabled = st.checkbox('Enable RAG (Use uploaded files to augment answers)', value=False, key="rag_toggle")
    rag_top_k = st.number_input('RAG: top K passages', min_value=1, max_value=10, value=3, key="rag_k_value")
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Upload a file for RAG", 
        type=['pdf', 'docx', 'txt', 'csv'], 
        key="file_uploader_widget",
        help="Upload a document (PDF, DOCX, TXT, or CSV) to provide context for the AI's answers."
    )
    
    # Process the file if a new one is uploaded
    if uploaded_file and uploaded_file.name not in st.session_state.uploaded_files:
        try:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                # Clear existing content before processing new file(s)
                st.session_state.file_content = ""
                st.session_state.uploaded_files = [uploaded_file.name] # Only allow one file for simplicity
                
                content = process_file(uploaded_file)
                st.session_state.file_content += content
                
                # Build RAG index only once a file is processed
                if rag_enabled and st.session_state.file_content:
                    rag.build_index_from_texts([st.session_state.file_content])
                
                st.success(f"Successfully processed **{uploaded_file.name}**")
                st.info(f"Loaded content size: {len(st.session_state.file_content):,} characters.")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.session_state.uploaded_files = [] # Clear the file from the list if processing failed

    # Display list of uploaded files (currently only one supported)
    if st.session_state.uploaded_files:
        st.markdown(f"**Files Loaded:** {', '.join(st.session_state.uploaded_files)}")
    
# --- Multilingual Helper Functions ---
def detect_language(text):
    """Detect the language of the input text (simplified for Hindi/English)."""
    # Simple check for Devanagari script (used in Hindi)
    if any('\u0900' <= char <= '\u097F' for char in text):
        return 'hindi'
    return 'english'

def translate_to_english(text, source_lang):
    """Translate text to English if it's not already in English."""
    if source_lang == 'hindi' and GEMINI_API_KEY:
        try:
            prompt = f"Translate the following Hindi text to English. Respond with ONLY the English translation and no other text: {text}"
            response = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}',
                headers={'Content-Type': 'application/json'},
                json={'contents': [{'parts': [{'text': prompt}]}]},
                timeout=30
            )
            if response.status_code == 200:
                # Assuming the model returns the text correctly
                return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            st.warning(f"Translation (to English) failed: {e}. Using original text.")
    return text

def translate_response(text, target_lang):
    """Translate English text to the target language if not English."""
    if target_lang != 'english' and GEMINI_API_KEY:
        try:
            prompt = f"Translate the following English response to {target_lang} (keep it natural and conversational). Respond with ONLY the translated text and no other text: {text}"
            response = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}',
                headers={'Content-Type': 'application/json'},
                json={'contents': [{'parts': [{'text': prompt}]}]},
                timeout=30
            )
            if response.status_code == 200:
                # Assuming the model returns the text correctly
                return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            st.warning(f"Translation (to {target_lang}) failed: {e}. Using English response.")
    return text

# --- Core Logic for Processing Input and Generating Response ---
def process_input():
    """Handles user input, calls the Gemini API (with RAG and translation), and updates chat."""
    global GEMINI_API_KEY # Use the global variable
    
    if not GEMINI_API_KEY:
        st.error("API key is missing. Please check your deployment secrets.")
        return
        
    # Check if input is valid
    user_input = st.session_state.get(st.session_state.user_input_key, '').strip()
    if not user_input:
        return
        
    # Clear the input field immediately after processing
    st.session_state[st.session_state.user_input_key] = ""
    
    # Detect input language
    input_lang = detect_language(user_input)
    
    # Add user message to display list
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    try:
        # 1. Handle special creator query
        if any(phrase in user_input.lower() for phrase in ["who made you", "who created you", "your creator", "who is thescythenexus"]):
            ai_response = "TheScytheNexus made me!"
            if input_lang == 'hindi':
                ai_response = "मुझे TheScytheNexus ने बनाया है! (Mujhe TheScytheNexus ne banaya hai!)"
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
        else:
            # 2. General AI Response Logic (with RAG/Translation)
            with st.spinner("TheScytheNexus AI IS THINKING..."):
                final_prompt = user_input
                
                # --- RAG Integration ---
                if st.session_state.file_content and st.session_state.rag_toggle:
                    try:
                        # RAG is enabled and content is loaded
                        retrieved = rag.retrieve(user_input, top_k=st.session_state.rag_k_value)
                        
                        if retrieved:
                            # Prepend retrieved passages to the prompt for grounding
                            ctx = 'You are an expert AI. Use the following context to answer the user\'s question. If the question cannot be answered from the context, state that explicitly.\n'
                            ctx += '\n--- Retrieved passages (RAG) ---\n'
                            for r in retrieved:
                                ctx += r['chunk'] + '\n\n'
                            
                            final_prompt = f"{ctx}\n\nUser Question: {user_input}"
                        else:
                            st.info("RAG enabled, but no relevant passages were retrieved. Using general knowledge/full document content.")
                    except Exception:
                        st.warning("RAG retrieval failed. Proceeding with general model call.")
                
                # If RAG is disabled but a file is uploaded, include ALL content (simple context)
                elif st.session_state.file_content:
                    final_prompt = f"The following is a document:\n{st.session_state.file_content}\n\nYour task is to answer the user's question based on this document. User Question: {user_input}"

                # --- Translation (Input) ---
                prompt_for_model = translate_to_english(final_prompt, input_lang)
                
                # --- API Call ---
                response = requests.post(
                    f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}',
                    headers={'Content-Type': 'application/json'},
                    json={'contents': [{'parts': [{'text': prompt_for_model}]}]},
                    timeout=30
                )
                
                if response.status_code == 200:
                    ai_response_english = response.json()['candidates'][0]['content']['parts'][0]['text']
                    
                    # --- Translation (Output) ---
                    ai_response = translate_response(ai_response_english, input_lang)
                    
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    st.error(f"Failed to get response from Gemini: {response.status_code}. Response: {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to Gemini API. Please check your internet connection.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        
    # Re-run the script to update the chat display after appending new messages
    st.rerun()

# --- 4. Main Chat Interface Display ---
# Use a custom container for the chat area to control height and scrolling
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display messages
for message in st.session_state.messages:
    # Use st.columns to simulate the alignment or rely on CSS classes
    role_class = 'user-message' if message['role'] == 'user' else 'bot-message'
    
    # Use HTML/CSS to render the message with custom styling
    st.markdown(f"""
    <div style="display: flex; {'justify-content: flex-end;' if message['role'] == 'user' else 'justify-content: flex-start;'}">
        <div class="chat-message {role_class}">
            <div><strong>{'You' if message['role'] == 'user' else 'TheScytheNexus AI'}:</strong></div>
            <div>{message['content']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) # Close chat-container


# --- 5. Input Area (Fixed at Bottom) ---
# This is a hack to get a fixed input bar that takes the full width minus the sidebar
# The CSS handles the positioning and margin
st.markdown('<div class="input-area">', unsafe_allow_html=True)
input_cols = st.columns([6, 1])

with input_cols[0]:
    # Text input for user message
    # The key is set in session state to prevent Streamlit's default clearing behavior
    st.text_input(
        "Message",
        key=st.session_state.user_input_key,
        label_visibility="collapsed",
        on_change=process_input,
        autocomplete="off",
        placeholder="Type your message...",
        # Ensure the on_change triggers the processing logic
    )

with input_cols[1]:
    # Send button
    if st.button("Send", use_container_width=True):
        # Explicitly check and run process_input if the button is pressed
        # This handles the case where the user uses the mouse to click Send
        process_input()

st.markdown('</div>', unsafe_allow_html=True) # Close input-area

# --- 6. Clear Chat Button (Fixed Top Left) ---
# The position is controlled by CSS
st.markdown('<div class="clear-button">', unsafe_allow_html=True)
if st.button("Clear Chat", key="clear"):
    st.session_state.messages = []
    # Preserve RAG content and file content on clear
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)