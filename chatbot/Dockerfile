FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copying dependency files first
COPY requirements.txt .
COPY runtime.txt .

# Installing dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy all necessary Python and data files ---
# Copy the application entry points
COPY app.py .
COPY rag.py .

# --- FINAL EXECUTION COMMAND ---
# Run the Streamlit app on port 80 to ensure it works with the Caddy reverse proxy 
# configured in your CI/CD pipeline (which maps 80/443 to port 80 of the container).
# Change 'app.py' to 'rag.py' if rag.py is your main Streamlit entry point.
CMD ["streamlit", "run", "app.py", "--server.port=80", "--server.enableCORS=true"]