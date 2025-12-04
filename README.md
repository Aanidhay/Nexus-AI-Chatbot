# AI Chatbot

An intelligent chatbot application with a modern UI that can engage in English conversations on any topic. This chatbot uses the free FLAN-T5 model from Google, which runs locally on your machine - no API keys required!

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

To run the chatbot:
```bash
streamlit run app.py
```

The application will open in your default web browser. The first run might take a few minutes as it downloads the model. 