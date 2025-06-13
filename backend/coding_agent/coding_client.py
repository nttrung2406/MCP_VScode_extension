import asyncio
import json
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
            "stream": False,
            "options": {
                "temperature": 0.3,  
                "top_p": 0.9
            }
        }
        
        if tools:
            payload["tools"] = tools
        
        response = await self.client.post(f"{self.base_url}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Gracefully close the HTTP client."""
        await self.client.aclose()


class MCPCodingClient:
    # ================================ Isolation agent test =======================================
    
    # def __init__(self):
    #     self.session = None
    #     self.ollama = OllamaClient()
    #     self.available_tools = []
    

    # async def connect(self, server_url: str = "http://localhost:8765/mcp-sse"):
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
    #         print("Please ensure the coding_server.py is running in a separate terminal.")
    #         sys.exit(1)
    
    
    # ================================ Isolation agent test =======================================

    def __init__(self, server_url="http://coding-server:8765/mcp-sse"):
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
            print("MCPCodingClient connected successfully.")
        except Exception as e:
            print(f"[ERROR] MCPCodingClient failed to connect: {e}")
            raise
            
       
    def convert_mcp_tools_to_ollama_format(self) -> List[Dict]:
        """Convert MCP tools to Ollama tool format"""
        ollama_tools = []
        
        for tool in self.available_tools:
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name}",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            if tool.name == "explain_code":
                ollama_tool["function"]["parameters"] = { "type": "object", "properties": { "code": {"type": "string", "description": "The code to explain"}, "language": {"type": "string", "description": "Programming language (auto-detect if not specified)"} }, "required": ["code"] }
            elif tool.name == "fix_code_error":
                ollama_tool["function"]["parameters"] = { "type": "object", "properties": { "code": {"type": "string", "description": "The code with errors"}, "error_message": {"type": "string", "description": "The error message received"}, "language": {"type": "string", "description": "Programming language"} }, "required": ["code", "error_message"] }
            elif tool.name == "create_unit_tests":
                ollama_tool["function"]["parameters"] = { "type": "object", "properties": { "code": {"type": "string", "description": "The code to create tests for"}, "language": {"type": "string", "description": "Programming language"}, "test_framework": {"type": "string", "description": "Testing framework to use"} }, "required": ["code"] }
            elif tool.name == "create_boilerplate":
                ollama_tool["function"]["parameters"] = { "type": "object", "properties": { "project_type": {"type": "string", "description": "Type of project (web app, API, CLI, etc.)"}, "language": {"type": "string", "description": "Programming language"}, "features": {"type": "string", "description": "Additional features to include"} }, "required": ["project_type", "language"] }
            elif tool.name == "code_review":
                ollama_tool["function"]["parameters"] = { "type": "object", "properties": { "code": {"type": "string", "description": "The code to review"}, "language": {"type": "string", "description": "Programming language"} }, "required": ["code"] }
            elif tool.name == "optimize_code":
                ollama_tool["function"]["parameters"] = { "type": "object", "properties": { "code": {"type": "string", "description": "The code to optimize"}, "optimization_type": {"type": "string", "description": "Type of optimization (performance, readability, memory)"}, "language": {"type": "string", "description": "Programming language"} }, "required": ["code"] }
            elif tool.name == "convert_code":
                ollama_tool["function"]["parameters"] = { "type": "object", "properties": { "code": {"type": "string", "description": "The code to convert"}, "source_language": {"type": "string", "description": "Source programming language"}, "target_language": {"type": "string", "description": "Target programming language"} }, "required": ["code", "source_language", "target_language"] }
            elif tool.name == "generate_documentation":
                ollama_tool["function"]["parameters"] = { "type": "object", "properties": { "code": {"type": "string", "description": "The code to document"}, "doc_type": {"type": "string", "description": "Type of documentation (api, user, technical)"}, "language": {"type": "string", "description": "Programming language"} }, "required": ["code"] }
            
            ollama_tools.append(ollama_tool)
        
        return ollama_tools

            
    async def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool via MCP"""
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return str(result.content) if result.content else "Tool executed successfully"
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"
        
 
    
    async def process_user_request(self, user_input: str) -> str:
        """Process user request using Ollama with MCP coding tools"""
        ollama_tools = self.convert_mcp_tools_to_ollama_format()
        
        messages = [
            {"role": "system", "content": "You are a helpful coding assistant with access to powerful code analysis and generation tools. Use these tools when users ask about code-related tasks. Always use the most appropriate tool for the user's request."},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = await self.ollama.generate_with_tools(messages, ollama_tools)
            
            message = response.get("message", {})
            
            if "tool_calls" in message and message.get("tool_calls"):
                results = []
                
                for tool_call in message["tool_calls"]:
                    function = tool_call.get("function", {})
                    tool_name = function.get("name")
                    arguments = function.get("arguments", {})
                    
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            return f"❌ Error: Model provided invalid arguments for tool {tool_name}."

                    print(f"🔧 Executing tool: {tool_name}({arguments})")
                    
                    tool_result = await self.execute_tool(tool_name, arguments)
                    results.append(tool_result)
                
                messages.append(message)
                messages.append({
                    "role": "tool",
                    "content": "\n\n---\n\n".join(results)
                })
                
                final_response = await self.ollama.generate_with_tools(messages) 
                return final_response.get("message", {}).get("content", "No final response generated after tool use.")
            
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
        print("=== MCP Coding Assistant ===")
        print("I can help you with various coding tasks!")
        print()
        print("=" * 50)
        print()
        
        try:
            while True:
                try:
                    user_input = input("🧑 You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        print("Happy coding!")
                        break
                    
                    if user_input.lower() == 'help':
                        self.show_help()
                        continue
                    
                    if not user_input:
                        continue
                    
                    print("🤖 Assistant: ", end="", flush=True)
                    response = await self.process_user_request(user_input)
                    print(response)
                    print()
                    
                except KeyboardInterrupt:
                    print("\n👋 Happy coding!")
                    break
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
        finally:
            await self.ollama.close()
            print("Client connection closed.")
                
    
    def show_help(self):
        """Show help with example requests"""
        print("\n🔧 Available Coding Tools & Examples:\n"
              "1. Code Explanation: 'Explain this code: [your code here]'\n"
              "2. Error Fixing: 'Fix this error: [code] Error: [error message]'\n"
              "3. Unit Testing: 'Create tests for this function'\n"
              "4. Boilerplate Generation: 'Create a FastAPI web app boilerplate'\n"
              "5. Code Review: 'Review this code for best practices'\n"
              "6. Code Optimization: 'Optimize this code for performance'\n"
              "7. Language Conversion: 'Convert this Python code to JavaScript'\n"
              "8. Documentation: 'Generate documentation for this API'\n")

# async def main():
#     server_url = "http://localhost:8765/mcp-sse"
#     client = MCPCodingClient()
#     await client.connect()

# if __name__ == "__main__":
#     asyncio.run(main())