#!/bin/bash
set -e

echo "==============================================="
echo "  MCP Backend Services Startup Script          "
echo "==============================================="
echo ""

cd "$(dirname "$0")"

# --- Step 1: Clean Slate Cleanup ---
echo "--- Ensuring all previous project containers are stopped and removed..."
docker compose down --remove-orphans > /dev/null 2>&1
echo "✅ Cleanup complete. All ports are now free."
echo ""


# --- Step 2: Build and Start Services ---
echo "--- Building and starting all MCP services in the background..."
docker compose up --build #-d > /dev/null 2>&1
echo "✅ Services are starting up..."
echo ""


# --- Step 3: Attach to the Controller for an Interactive Session ---
echo "--- Attaching to the agent-controller logs for interactive session ---"
echo "--- The system is now ready for prompts. ---"
echo ""
