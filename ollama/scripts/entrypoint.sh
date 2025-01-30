#!/bin/bash

# Cleanup on exit
trap 'rm -f /health/ready; kill $pid; exit 0' SIGTERM SIGINT

# Start Ollama
/bin/ollama serve &
pid=$!

# Wait for startup
sleep 5

echo "🔄 Pulling required models..."
mkdir -p /health

# Pull both models in sequence
ollama pull deepseek-r1:1.5b && \
ollama pull nomic-embed-text && \
touch /health/ready

echo "✅ Models ready!"

# Keep running
wait $pid