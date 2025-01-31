FROM python:3.11-slim

# Install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Python script
COPY pegar_noticias.py /app/pegar_noticias.py

# Set the working directory
WORKDIR /app

# Default command to run your script
CMD ["python", "pegar_noticias.py"]
