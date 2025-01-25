FROM python:3.11-slim

# Install necessary system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install transformers

# Download and organize Hugging Face model files
RUN mkdir -p /app/models/facebook-bart-large-cnn && \
    python -c "from transformers import AutoModelForSeq2SeqLM, AutoTokenizer; \
               AutoModelForSeq2SeqLM.from_pretrained('facebook/bart-large-cnn', cache_dir='/app/models/facebook-bart-large-cnn', force_download=True); \
               AutoTokenizer.from_pretrained('facebook/bart-large-cnn', cache_dir='/app/models/facebook-bart-large-cnn', force_download=True)" && \
    find /app/models/facebook-bart-large-cnn -type f -exec cp {} /app/models/facebook-bart-large-cnn/ \; && \
    rm -rf /app/models/facebook-bart-large-cnn/snapshots /app/models/facebook-bart-large-cnn/blobs /app/models/facebook-bart-large-cnn/refs

    # Test model loading during build
    RUN python -c "from transformers import pipeline; \
    summarizer = pipeline('summarization', model='facebook/bart-large-cnn'); \
    test_summary = summarizer('This is a test sentence to check if the summarization pipeline works.', max_length=20, min_length=5, do_sample=False); \
    print('Test summary:', test_summary)"

# Copy your Python script
COPY pegar_noticias.py /app/pegar_noticias.py

# Set the working directory
WORKDIR /app

# Default command to run your script
CMD ["python", "pegar_noticias.py"]