#!/bin/sh

# Start Ollama in the background
ollama serve &  

# Wait until Ollama is ready
until curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "Waiting for Ollama to start..."
    sleep 2
done

# Keep the container running
tail -f /dev/null
