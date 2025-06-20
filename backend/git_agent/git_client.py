import os
import json
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Any
from mcp import ClientSession
from mcp.client.sse import sse_client
import requests
import httpx

# ============ Definition ======================
_orig_request = httpx.AsyncClient.request
async def _patched_request(self, method, url, *args, **kwargs):
    kwargs.setdefault("follow_redirects", True)
    return await _orig_request(self, method, url, *args, **kwargs)
httpx.AsyncClient.request = _patched_request

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
MODEL = os.getenv("MODEL")
# ============ Definition ======================
class OllamaClient:
    def __init__(self, model = MODEL, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def generate_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Generate response using Ollama with tool calling support"""
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "stream": False
        }
        
        response = requests.post(f"{self.base_url}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()

class MCPGitClient:
    
    # ==================================== Isolation agent testing ==============================================================

    # def __init__(self):
    #     self.session = None
    #     self.ollama = OllamaClient()
    #     self.available_tools = []
    

    # async def connect(self, server_url: str = "http://localhost:8767/mcp-sse"):
    #     """Connect to the MCP server via the SSE handshake endpoint."""
    #     print(f"Attempting to connect to MCP server at {server_url}...")
    #     try:
    #         async with sse_client(server_url) as (read, write):
    #             async with ClientSession(read, write) as session:
    #                 self.session = session
                    
    #                 await session.initialize()
                    
    #                 tools_result = await session.list_tools()
    #                 self.available_tools = tools_result.tools
                    
    #                 print(f"\nSuccessfully connected to MCP Filesystem Server!")
    #                 print(f"Available tools: {[tool.name for tool in self.available_tools]}")
    #                 print("-" * 20)
                    
    #                 await self.interactive_session()
    #     except Exception as e:
    #         print(f"\n[ERROR] Failed to connect to server at {server_url}: {e}")
    #         print("Please ensure the git_server.py is running in a separate terminal.")
    #         sys.exit(1)
            
            
    # ==================================== Isolation agent testing ==============================================================
 
    def __init__(self, server_url="http://git-server:8767/mc-sse"):
        self.ollama = OllamaClient(model=MODEL, base_url="http://ollama:11434")
        self.session = None
        self.available_tools = []
        self.server_url = server_url
        self.is_connected = False
    
    async def connect(self):
        """Connects to the server but does not start an interactive loop."""
        if self.is_connected:
            return
        try:
            self.read_stream, self.write_stream = await sse_client(self.server_url)
            self.session = ClientSession(self.read_stream, self.write_stream)
            await self.session.initialize()
            tools_result = await self.session.list_tools()
            self.available_tools = tools_result.tools
            self.is_connected = True
            print("MCPCodingClient connected successfully.")
        except Exception as e:
            print(f"[ERROR] MCPCodingClient failed to connect: {e}")
            raise
    
    def convert_mcp_tools_to_ollama_format(self) -> List[Dict]:
        """Convert MCP Git tools to Ollama tool format"""
        ollama_tools = []
        
        # Define tool parameter schemas
        tool_schemas = {
            "git_init": {
                "properties": {"path": {"type": "string", "description": "Repository path", "default": "."}},
                "required": []
            },
            "git_clone": {
                "properties": {
                    "url": {"type": "string", "description": "Repository URL"},
                    "directory": {"type": "string", "description": "Target directory"}
                },
                "required": ["url"]
            },
            "git_status": {
                "properties": {"path": {"type": "string", "description": "Repository path", "default": "."}},
                "required": []
            },
            "git_add": {
                "properties": {
                    "files": {"type": "string", "description": "Files to add (e.g., '.', 'file.txt', 'file1.txt,file2.txt')"},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": ["files"]
            },
            "git_commit": {
                "properties": {
                    "message": {"type": "string", "description": "Commit message"},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": ["message"]
            },
            "git_push": {
                "properties": {
                    "remote": {"type": "string", "description": "Remote name", "default": "origin"},
                    "branch": {"type": "string", "description": "Branch name", "default": "main"},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": []
            },
            "git_pull": {
                "properties": {
                    "remote": {"type": "string", "description": "Remote name", "default": "origin"},
                    "branch": {"type": "string", "description": "Branch name", "default": "main"},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": []
            },
            "git_branch": {
                "properties": {
                    "action": {"type": "string", "description": "Action: list, create, delete, switch", "default": "list"},
                    "branch_name": {"type": "string", "description": "Branch name (required for create/delete/switch)"},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": []
            },
            "git_log": {
                "properties": {
                    "count": {"type": "integer", "description": "Number of commits to show", "default": 10},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": []
            },
            "git_diff": {
                "properties": {
                    "file": {"type": "string", "description": "Specific file to diff"},
                    "staged": {"type": "boolean", "description": "Show staged changes", "default": False},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": []
            },
            "git_remote": {
                "properties": {
                    "action": {"type": "string", "description": "Action: list, add, remove", "default": "list"},
                    "name": {"type": "string", "description": "Remote name"},
                    "url": {"type": "string", "description": "Remote URL"},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": []
            },
            "git_stash": {
                "properties": {
                    "action": {"type": "string", "description": "Action: save, pop, list, drop, clear", "default": "save"},
                    "message": {"type": "string", "description": "Stash message"},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": []
            },
            "git_merge": {
                "properties": {
                    "branch": {"type": "string", "description": "Branch to merge"},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": ["branch"]
            },
            "git_reset": {
                "properties": {
                    "mode": {"type": "string", "description": "Reset mode: soft, mixed, hard", "default": "mixed"},
                    "target": {"type": "string", "description": "Reset target", "default": "HEAD"},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": []
            },
            "git_config": {
                "properties": {
                    "action": {"type": "string", "description": "Action: list, get, set", "default": "list"},
                    "key": {"type": "string", "description": "Config key"},
                    "value": {"type": "string", "description": "Config value"},
                    "global_config": {"type": "boolean", "description": "Global config", "default": False},
                    "path": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": []
            }
        }
        
        for tool in self.available_tools:
            tool_name = tool.name
            schema = tool_schemas.get(tool_name, {
                "properties": {},
                "required": []
            })
            
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description or f"Execute {tool_name} Git operation",
                    "parameters": {
                        "type": "object",
                        "properties": schema.get("properties", {}),
                        "required": schema.get("required", [])
                    }
                }
            }
            
            ollama_tools.append(ollama_tool)
        
        return ollama_tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute a Git tool via MCP"""
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return str(result.content) if result.content else "Tool executed successfully"
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"
    
    async def process_user_request(self, user_input: str) -> str:
        """Process user request using Ollama with MCP Git tools"""
        ollama_tools = self.convert_mcp_tools_to_ollama_format()
        
        messages = [
            {
                "role": "system",
                "content": """You are a helpful Git assistant with access to comprehensive Git tools. Use the available tools to help users with Git operations including:

            - Repository management (init, clone, status)
            - File operations (add, commit, push, pull)
            - Branch management (create, switch, merge, delete)
            - History and differences (log, diff)
            - Remote operations (add, remove, push, pull)
            - Advanced operations (stash, reset, config)

            Always use the appropriate Git tools when users ask about Git operations. Provide clear explanations of what each operation does and any important considerations."""
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        
        try:
            response = self.ollama.generate_with_tools(messages, ollama_tools)
            message = response.get("message", {})
            
            if "tool_calls" in message:
                results = []
                
                for tool_call in message["tool_calls"]:
                    function = tool_call.get("function", {})
                    tool_name = function.get("name")
                    arguments = function.get("arguments", {})
                    
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)
                    
                    print(f"Executing Git tool: {tool_name} with arguments: {arguments}")
                    
                    tool_result = await self.execute_tool(tool_name, arguments)
                    results.append(f"Git tool {tool_name} result:\n{tool_result}")
                
                messages.append(message)
                messages.append({
                    "role": "tool",
                    "content": "\n\n".join(results)
                })
                
                final_response = self.ollama.generate_with_tools(messages, ollama_tools)
                return final_response.get("message", {}).get("content", "No response generated")
            
            else:
                return message.get("content", "No response generated")
                
        except Exception as e:
            return f"❌ Error processing request: {str(e)}"
    
    async def run_task(self, user_input: str) -> str:
        """Connects, processes a single request, and returns the result."""
        try:
            await self.connect()
            response = await self.process_user_request(user_input)
            return response
        finally:
            if self.session:
                await self.session.close()
            self.is_connected = False   
            
    async def interactive_session(self):
        """Interactive session with user"""
        print("\n=== MCP Git Assistant ===")
        print("Ask me to help with Git operations! Type 'quit' to exit.")
        print("\nExample commands:")
        print("- 'Initialize a new Git repository'")
        print("- 'Check the status of my repository'")
        print("- 'Add all files and commit with message \"Initial commit\"'")
        print("- 'Create a new branch called feature-branch'")
        print("- 'Show the last 5 commits'")
        print("- 'Show differences in my files'")
        print("- 'Push changes to origin main'")
        print("- 'Configure my Git username and email'")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("Git Assistant: ", end="", flush=True)
                response = await self.process_user_request(user_input)
                print(response)
                print()
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")


# async def main():
#     server_url = "http://localhost:8767/mcp-sse"
#     client = MCPGitClient()
#     await client.connect()

# if __name__ == "__main__":
#     asyncio.run(main())