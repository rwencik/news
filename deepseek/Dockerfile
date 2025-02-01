FROM ubuntu:22.04

# Set non-interactive mode
ENV DEBIAN_FRONTEND=noninteractive

# Install required dependencies
RUN apt update && apt install -y \
    curl \
    git \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Create Ollama model directory
RUN mkdir -p /root/.ollama/models

# Copy the script to wait for Ollama and download the model
COPY download-model.sh /download-model.sh
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /download-model.sh && /download-model.sh

# Expose Ollama API port
EXPOSE 11434

# Copy and set up entrypoint script
RUN chmod +x /entrypoint.sh

# Use the fixed entrypoint to restart Ollama with the pre-downloaded model
CMD ["/entrypoint.sh"]
