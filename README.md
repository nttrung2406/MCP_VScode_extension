# VSCODE Extension for Coding support
![alt text](MCP-system_architecture_2.jpg)

---
This is the README for VSCODE Extension for Coder support. This tool utilized:
- MCP Server - Client for agents
- Ollama to run LLMs locally
- Autogen to run agents orchestration

## Features

This tool wil support you to:
- Explain the piece of code.
- Write unit test for a function
- Fix error in the code.
- Create a boilerplate code.
- Write git commit, git command, etc
- Auto deploy with docker compose, run unit test and send notification (Developing)
## Requirements

- Python 3.10++ for backend.

- Nodejs for npm, npx.

- uv 

## Project structure
```
MCP-Server
├── backend/                            # Backend
│   ├── coding_agent/     
│   │   ├── __init__.py                   
│   │   ├── coding_client.py            # Use for isolation test coding agent   
│   │   ├── coding_server.py  
│   │   ├── run.sh 
│   ├── file_agent/      
│   │   ├── __init__.py                           
│   │   ├── file__client.py             # Use for isolation test file agent
│   │   ├── file__server.py  
│   │   ├── run.sh 
│   ├── git_agent/     
│   │   ├── __init__.py                            
│   │   ├── git_client.py               # Use for isolation test git agent
│   │   ├── git_server.py  
│   │   ├── run.sh 
│   ├── agents_orchestration_utils/   
│   │   ├── __init__.py                              
│   │   ├── autogen_config.py
│   │   ├── mcp_sse_connection.py
│   │   ├── stop_llm.py 
│   ├── llm_choice/     
│   │   ├── __init__.py                            
│   │   ├── llm_client.py
│   ├── agent_controller.py             # Multi agents orchestration
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── ollama_entrypoint.sh
│   ├── .env
├── src/                                # Ui for vscode view and webview
│   ├── tests/                          
|   |   ├── extension.test.ts   
│   ├── webview/     
|   |   ├── api.ts
|   |   ├── index.html
|   |   ├── style.css
|   |   ├── main.js  
│   ├── extension.ts   
├── workspace/                          # Empty directory                     
├── package.json 
├── .vscode-test.mjs
├── esbuild.config.mjs
├── esbuild.js                          # In ESModule format
├── run_all.sh
├── tsconfig.json
├── .gitignore
├── .vscodeignore
├── README.md
            
```
## Usage

- Setup uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv init <project name>
```
- Navigate to new folder, then run these commands:

```bash
npm install -g yo generator-code
yo code
```

- Choose following these configs:

```bash
What type of extension do you want to create?
>> New Extension (TypeScript)

What's the name of your extension? 
>> mcp-server

What's the identifier of your extension?
>> mcp-server

What's the description of your extension? 
>> You can skip this.

Initialize a git repository? 
>> Yes or No, your choice.

Bundle the source code with webpack:
>> esbuild

Which package manager to use?
>> npm 
```

- Then clone this repo

```bash
cd ..
git clone <repo-url>
cd mcp-server   # This is neccessary to run both service and extension
chmod +x run_all.sh
./run_all.sh
```

## Prepare .env file

```bash
#========================== PATH =====================================
OLLAMA_BASE_URL="http://ollama:11434"
FILE_SERVER_URL="http://file-server:8766"
CODE_SERVER_URL="http://coding-server:8765"
GIT_SERVER_URL="http://git-server:8767"

#========================== MODEL =====================================
LLM_PROVIDER=ollama  # Or gemini or claude
MODEL="ollama model"
GEMINI_MODEL="gemini-2.0-flash-lite"
CLAUDE_MODEL="your-claude-model"

#========================== API KEY =====================================
GEMINI_API_KEY="your-api-key"
GEMINI_API_KEY_CODE="your-api-key"
CLAUDE_API_KEY="your-api-key"
```

## Integrate in VSCode

After run <./run_all.sh>, go to VSCode
 >> Click "Run and Debug" (or press "Ctrl + Shift + D").

 >> Click :arrow_forward: to run extension (VSCode will open a new window which is the Client).
 
 >> In the Client window, open Command Pallet (or press "Ctrl + Shift + P") to type command.

**Note:**

Open launch.json in :gear: and type this line in the args section:

```bash
"--disable-extension=ms-python.vscode-pylance"
```

## Commands can be used in Command Pallet

```bash
Start MCP Agent Session
```

## Create a workspace for tool

In the *docker-compose.yml* file, modify the volumn of each service with the directory of the workspace.

Then you need to grand access for this tool (**Recommended**):

```bash
sudo chmod -R 755 workspace
```

If you need to write in this workspace, use this:

```bash
sudo chmod -R 777 workspace
```

## Issues

Please contact or open an issue for error founded.


---

**Enjoy!**
