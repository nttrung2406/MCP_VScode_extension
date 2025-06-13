#!/bin/bash
set -e

PORT=8765
MODEL_NAME="qwen3:1.7b"
MODEL_IMAGE="registry.ollama.ai/library/${MODEL_NAME}"
CONTAINER_NAME="ollama"

cleanup() {
  echo ""
  echo "[+] Script exiting. Cleaning up..."
  if [ -n "$SERVER_PID" ]; then
    echo "[+] Stopping MCP server (PID: $SERVER_PID)..."
    kill -TERM "$SERVER_PID" > /dev/null 2>&1 || true
  fi
  echo "[+] Cleanup complete."
}

# cd ..
echo "[+] Cleaning up previous Ollama container if exists..."
if docker ps -a --format '{{.Names}}' | grep -wq "${CONTAINER_NAME}"; then
  echo "[!] Found old '${CONTAINER_NAME}' container. Stopping and removing..."
  docker stop "${CONTAINER_NAME}" || true
  docker rm "${CONTAINER_NAME}" || true
else
  echo "[*] No existing '${CONTAINER_NAME}' container found."
fi

trap cleanup EXIT INT TERM

echo "[+] Forcing port ${PORT} to be free..."
fuser -k "${PORT}/tcp" > /dev/null 2>&1 || true
sleep 2

echo "[+] Starting Ollama..."
docker compose up -d

echo "[+] Waiting for Ollama API to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 1
done

echo "[+] Checking if model '${MODEL_NAME}' already exists..."
if curl -s http://localhost:11434/api/tags | grep -q "${MODEL_NAME}"; then
  echo "[*] Model '${MODEL_NAME}' already exists. Skipping pull."
else
  echo "[+] Pulling model: ${MODEL_NAME}..."
  docker exec "${CONTAINER_NAME}" ollama pull "${MODEL_NAME}"
fi

echo "[+] Checking for running containers using image '${MODEL_IMAGE}'..."
CONTAINERS=$(docker ps -q --filter "ancestor=${MODEL_IMAGE}")

if [ -n "$CONTAINERS" ]; then
  echo "[!] Found running containers using '${MODEL_IMAGE}':"
  docker ps --filter "ancestor=${MODEL_IMAGE}" --format "  -> {{.ID}} | {{.Names}} | {{.Status}}"

  echo -n "[-] Do you want to stop and remove them? (y/N): "
  read -r CONFIRM
  if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "[+] Stopping and removing containers..."
    docker stop $CONTAINERS
    docker rm $CONTAINERS
  else
    echo "[*] Skipping container cleanup."
  fi
else
  echo "[*] No containers running from '${MODEL_IMAGE}'."
fi

# cd coding_agent
echo "[+] Starting MCP server..."
uv run coding_server.py &

# echo "[+] Waiting for MCP server..."
# until nc -z localhost 8765; do
#   sleep 1
# done
sleep 5

echo "[+] MCP server is up. Starting MCP client..."
uv run coding_client.py

# & wait
