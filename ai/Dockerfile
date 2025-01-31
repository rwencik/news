# Use a lightweight Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install torch transformers fastapi uvicorn sentencepiece

# Pre-download models to avoid runtime errors inside the container
RUN python -c "from transformers import pipeline; \
    pipeline('summarization', model='facebook/bart-large-cnn'); \
    pipeline('translation', model='Helsinki-NLP/opus-mt-en-ROMANCE')"

# Copy application code
COPY app.py .

# Expose the FastAPI service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]