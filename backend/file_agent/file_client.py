import asyncio
import sys
from typing import List, Dict, Any
from mcp import ClientSession
from mcp.client.sse import sse_client
import httpx

_orig_request = httpx.AsyncClient.request
async def _patched_request(self, method, url, *args, **kwargs):
    kwargs.setdefault("follow_redirects", True)
    return await _orig_request(self, method, url, *args, **kwargs)
httpx.AsyncClient.request = _patched_request

class OllamaClient:
    def __init__(self, model: str = "qwen3:1.7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate_with_tools(self, messages: List[Dict], tools: List[Dict] = None) -> Dict:
        """
        Generate response from Ollama, optionally with tool calling support.
        If `tools` is None, it generates a standard chat completion.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        if tools:
            payload["tools"] = tools
        
        response = await self.client.post(f"{self.base_url}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Gracefully close the HTTP client."""
        await self.client.aclose()

class MCPFilesystemClient:

    # ==================================== Isolation agent testing ==============================================================

    # def __init__(self):
    #     self.session = None
    #     self.ollama = OllamaClient()
    #     self.available_tools = []
    

    # async def connect(self, server_url: str = "http://localhost:8766/mcp-sse"):
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
    #         print("Please ensure the file__server.py is running in a separate terminal.")
    #         sys.exit(1)
            
            
    # ==================================== Isolation agent testing ==============================================================
    
    def __init__(self, server_url="http://file-server:8766/mcp-sse"): # server_url: str = "http://localhost:8766/mcp-sse"
        self.ollama = OllamaClient(model="qwen3:1.7b", base_url="http://ollama:11434")
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
            print("MCPFilesystemClient connected successfully.")
        except Exception as e:
            print(f"[ERROR] MCPFilesystemClient failed to connect: {e}")
            raise    

    def convert_mcp_tools_to_ollama_format(self) -> List[Dict]:
        """Convert MCP tools (with schema from server) to Ollama tool format"""
        ollama_tools = []
        for tool in self.available_tools:
            properties = tool.inputSchema.get("properties", {})
            required = tool.inputSchema.get("required", [])

            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Execute the {tool.name} tool",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
            ollama_tools.append(ollama_tool)
        return ollama_tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool via MCP"""
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return str(result.content) if result.content else "Tool executed successfully with no output."
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"
    
    async def process_user_request(self, user_input: str) -> str:
        """Process user request using Ollama with MCP tools"""
        ollama_tools = self.convert_mcp_tools_to_ollama_format()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant with access to a virtual filesystem. Use the available tools to help users with file operations like creating, reading, listing, and deleting files and directories. Always confirm the action taken and its result."},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = await self.ollama.generate_with_tools(messages, ollama_tools)
            message = response.get("message", {})
            
            if "tool_calls" in message and message.get("tool_calls"):
                tool_results = []
                messages.append(message)

                for tool_call in message["tool_calls"]:
                    function = tool_call.get("function", {})
                    tool_name = function.get("name")
                    arguments = function.get("arguments", {})
                    
                    print(f"🔧 Executing tool: {tool_name}({arguments})")
                    
                    tool_result = await self.execute_tool(tool_name, arguments)
                    tool_results.append(tool_result)

                messages.append({
                    "role": "tool",
                    "content": "\n\n---\n\n".join(tool_results)
                })
                
                final_response = await self.ollama.generate_with_tools(messages) # No ollama_tools
                return final_response.get("message", {}).get("content", "No final response generated.")
            
            else:
                return message.get("content", "No response generated.")
                
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
        print("=== MCP Filesystem Assistant ===")
        print("I can help you manage files in the 'mcp_workspace' directory.")
        print("Type 'quit' to exit.")
        print("=" * 50)
        print()
        
        try:
            while True:
                try:
                    user_input = input("🧑 You: ").strip()
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        print("Goodbye!")
                        break
                    if not user_input:
                        continue
                    
                    print("🤖 Assistant: ", end="", flush=True)
                    response = await self.process_user_request(user_input)
                    print(response)
                    print()
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
        finally:
            await self.ollama.close()
            print("Client connection closed.")

# async def main():
#     server_url="http://localhost:8766/mcp-sse"
#     client = MCPFilesystemClient()
#     await client.connect()

# if __name__ == "__main__":
#     asyncio.run(main())