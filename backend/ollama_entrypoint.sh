#!/bin/sh
set -e

if [ -z "$MODEL" ]; then
  echo "❌ The MODEL environment variable is not set. Cannot pull model."
  exit 1
fi

ollama serve &
pid=$!

echo "Ollama server started with PID $pid"

echo "Waiting for Ollama server to be ready..."
while ! ollama list > /dev/null 2>&1
do
  echo "Still waiting for Ollama..."
  sleep 1
done
echo "✅ Ollama server is ready."

echo "Pulling model '$MODEL' from environment..."
ollama pull "$MODEL"
echo "✅ Model '$MODEL' is ready."

wait $pid