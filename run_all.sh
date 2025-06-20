#!/bin/bash

set -e

# --- Introduction ---
echo "================================================="
echo "  MCP Multi-Agent Project Setup & Build Script   "
echo "================================================="
echo ""

cd "$(dirname "$0")"

echo "--- Step 1: Setting up VS Code Extension (Frontend) ---"

if [ ! -d "node_modules" ]; then
  echo "Node modules not found. Running 'npm install'..."
  npm install
else
  echo "Node modules found. Skipping 'npm install'."
fi

echo "Compiling TypeScript extension source to 'dist/extension.js'..."
npm run compile
echo "✅ Frontend build complete."
echo ""


# --- Step 2: Backend Information ---
echo "--- Step 2: Verifying Backend Setup ---"

if [ -f "backend/run_controller.sh" ]; then
  echo "Found backend run script at 'backend/run_controller.sh'."
  echo "The backend services will be started automatically by the extension."
  echo "✅ Backend is ready."
else
  echo "❌ CRITICAL ERROR: Backend script 'backend/run_controller.sh' not found!"
  exit 1
fi
echo ""


# --- Final Instructions ---
echo "================================================="
echo "               🚀 All Set To Go! 🚀              "
echo "================================================="
echo "You can now launch the extension in VS Code:"
echo "1. Make sure you are in the main VS Code window with the project code."
echo "2. Press F5 to start the Extension Development Host."
echo "3. In the new window that appears, open the Command Palette (Ctrl+Shift+P)."
echo "4. Run the command 'Start MCP Agent Session'."
echo ""