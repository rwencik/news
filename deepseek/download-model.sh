#!/bin/sh

# Start Ollama in the background
ollama serve &

# Wait until Ollama is ready
echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "Still waiting for Ollama..."
    sleep 2
done

echo "Ollama is ready! Pulling DeepSeek model..."
ollama pull deepseek-r1:8b

echo "Model downloaded successfully!"
