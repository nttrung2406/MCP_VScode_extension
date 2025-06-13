import re
from pathlib import Path
# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP
import requests
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from mcp.server.sse import SseServerTransport
import uvicorn

mcp = FastMCP("Coding Assistant Server")
OLLAMA_BASE_URL = "http://localhost:11434"
CODER_MODEL = "qwen3:1.7b"

class OllamaCodeHelper:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = CODER_MODEL
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response from Ollama"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1, 
                "top_p": 0.9
            }
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            return f"Error communicating with Ollama: {str(e)}"

code_helper = OllamaCodeHelper()

def detect_language(code: str) -> str:
    """Detect programming language from code"""
    if re.search(r'\bdef\s+\w+\s*\(', code) and re.search(r':\s*$', code, re.MULTILINE):
        return "python"
    elif re.search(r'\bfunction\s+\w+\s*\(', code) or re.search(r'=>', code):
        return "javascript"
    elif re.search(r'\bpublic\s+class\s+\w+', code) or re.search(r'\bpublic\s+static\s+void\s+main', code):
        return "java"
    elif re.search(r'#include\s*<', code) or re.search(r'\bint\s+main\s*\(', code):
        return "c++"
    elif re.search(r'\bfn\s+\w+\s*\(', code) or re.search(r'\blet\s+mut\s+', code):
        return "rust"
    elif re.search(r'\bfunc\s+\w+\s*\(', code) or re.search(r'\bpackage\s+main', code):
        return "go"
    else:
        return "unknown"

@mcp.tool("explain_code")
def explain_code(code: str, language: str = "auto") -> str:
    """Explain what a piece of code does"""
    if language == "auto":
        language = detect_language(code)
    
    system_prompt = f"""You are a code explanation expert. Analyze the provided {language} code and provide:
    1. A clear, concise explanation of what the code does
    2. Break down complex parts step by step
    3. Explain any algorithms or design patterns used
    4. Mention potential improvements or best practices
    5. Keep explanations accessible but technically accurate"""
    
    prompt = f"""Please explain this {language} code:

    ```{language}
    {code}
    ```

    Provide a comprehensive but clear explanation suitable for developers."""
    
    try:
        explanation = code_helper.generate_response(prompt, system_prompt)
        return f"Code Explanation ({language}):\n\n{explanation}"
    except Exception as e:
        return f"Error explaining code: {str(e)}"

@mcp.tool("fix_code_error")
def fix_code_error(code: str, error_message: str, language: str = "auto") -> str:
    """Fix code errors and provide corrected version"""
    if language == "auto":
        language = detect_language(code)
    
    system_prompt = f"""You are a code debugging expert. Given code with an error, provide:
    1. Identification of the error and its cause
    2. The corrected code
    3. Explanation of what was wrong and how you fixed it
    4. Tips to avoid similar errors in the future
    Focus on providing working, clean code."""
        
    prompt = f"""Fix this {language} code that has an error:

    **Code:**
    ```{language}
    {code}
    ```

    **Error Message:**
    {error_message}

    Please provide the corrected code and explain the fix."""
    
    try:
        fix_response = code_helper.generate_response(prompt, system_prompt)
        return f"Code Fix ({language}):\n\n{fix_response}"
    except Exception as e:
        return f"Error fixing code: {str(e)}"

@mcp.tool("create_unit_tests")
def create_unit_tests(code: str, language: str = "auto", test_framework: str = "auto") -> str:
    """Create unit tests for the provided code"""
    if language == "auto":
        language = detect_language(code)
    
    if test_framework == "auto":
        framework_map = {
            "python": "pytest",
            "javascript": "jest",
            "java": "junit",
            "c++": "googletest",
            "rust": "builtin",
            "go": "builtin"
        }
        test_framework = framework_map.get(language, "builtin")
    
    system_prompt = f"""You are a unit testing expert. Create comprehensive unit tests for the provided code using {test_framework} for {language}. Include:
    1. Test cases for normal/expected inputs
    2. Edge cases and boundary conditions
    3. Error/exception handling tests
    4. Mock objects where appropriate
    5. Clear test names and documentation
    6. Proper test structure and assertions"""
    
    prompt = f"""Create unit tests for this {language} code using {test_framework}:

    ```{language}
    {code}
    ```

    Generate comprehensive test cases that cover various scenarios."""
    
    try:
        tests = code_helper.generate_response(prompt, system_prompt)
        return f"Unit Tests ({language} - {test_framework}):\n\n{tests}"
    except Exception as e:
        return f"Error creating unit tests: {str(e)}"

@mcp.tool("create_boilerplate")
def create_boilerplate(project_type: str, language: str, features: str = "") -> str:
    """Create boilerplate code for different project types"""
    system_prompt = f"""You are a project template expert. Create clean, well-structured boilerplate code for {project_type} projects in {language}. Include:
    1. Proper project structure
    2. Essential dependencies/imports
    3. Basic configuration
    4. Example implementation
    5. Comments explaining key parts
    6. Best practices for the technology stack"""
    
    features_text = f" with features: {features}" if features else ""
    
    prompt = f"""Create boilerplate code for a {project_type} project in {language}{features_text}.

    Provide:
    1. Main application structure
    2. Configuration files if needed
    3. Example code demonstrating core functionality
    4. Brief setup instructions

    Make it production-ready and follow best practices."""
    
    try:
        boilerplate = code_helper.generate_response(prompt, system_prompt)
        return f"Boilerplate Code ({project_type} - {language}):\n\n{boilerplate}"
    except Exception as e:
        return f"Error creating boilerplate: {str(e)}"

@mcp.tool("code_review")
def code_review(code: str, language: str = "auto") -> str:
    """Perform a code review and provide suggestions"""
    if language == "auto":
        language = detect_language(code)
    
    system_prompt = f"""You are a senior code reviewer. Analyze the provided {language} code and provide:
    1. Code quality assessment
    2. Performance considerations
    3. Security issues (if any)
    4. Best practices recommendations
    5. Refactoring suggestions
    6. Maintainability improvements
    Be constructive and specific in your feedback."""
    
    prompt = f"""Please review this {language} code and provide detailed feedback:

    ```{language}
    {code}
    ```

    Focus on code quality, performance, security, and maintainability."""
    
    try:
        review = code_helper.generate_response(prompt, system_prompt)
        return f"Code Review ({language}):\n\n{review}"
    except Exception as e:
        return f"Error reviewing code: {str(e)}"

@mcp.tool("optimize_code")
def optimize_code(code: str, optimization_type: str = "performance", language: str = "auto") -> str:
    """Optimize code for performance, readability, or memory usage"""
    if language == "auto":
        language = detect_language(code)
    
    system_prompt = f"""You are a code optimization expert. Optimize the provided {language} code for {optimization_type}. Provide:
    1. The optimized version of the code
    2. Explanation of optimizations made
    3. Performance/readability improvements achieved
    4. Any trade-offs made
    5. Benchmarking suggestions if applicable"""
        
    prompt = f"""Optimize this {language} code for {optimization_type}:

    ```{language}
    {code}
    ```

    Provide the optimized version with detailed explanations of improvements."""
    
    try:
        optimization = code_helper.generate_response(prompt, system_prompt)
        return f"Code Optimization ({language} - {optimization_type}):\n\n{optimization}"
    except Exception as e:
        return f"Error optimizing code: {str(e)}"

@mcp.tool("convert_code")
def convert_code(code: str, source_language: str, target_language: str) -> str:
    """Convert code from one programming language to another"""
    system_prompt = f"""You are a code conversion expert. Convert code from {source_language} to {target_language}. Ensure:
    1. Functionality remains exactly the same
    2. Follow {target_language} best practices and idioms
    3. Use appropriate libraries and frameworks for {target_language}
    4. Maintain code structure and readability
    5. Add comments explaining any language-specific changes"""
    
    prompt = f"""Convert this {source_language} code to {target_language}:

    ```{source_language}
    {code}
    ```

    Ensure the converted code maintains the same functionality and follows {target_language} best practices."""
        
    try:
        conversion = code_helper.generate_response(prompt, system_prompt)
        return f"Code Conversion ({source_language} → {target_language}):\n\n{conversion}"
    except Exception as e:
        return f"Error converting code: {str(e)}"

@mcp.tool("generate_documentation")
def generate_documentation(code: str, doc_type: str = "api", language: str = "auto") -> str:
    """Generate documentation for code"""
    if language == "auto":
        language = detect_language(code)
    
    system_prompt = f"""You are a documentation expert. Generate {doc_type} documentation for the provided {language} code. Include:
    1. Clear descriptions of functionality
    2. Parameter and return value documentation
    3. Usage examples
    4. Error handling information
    5. Performance considerations where relevant
    Use appropriate documentation format for {language}."""
    
    prompt = f"""Generate {doc_type} documentation for this {language} code:

    ```{language}
    {code}
    ```

    Create comprehensive documentation suitable for developers."""
    
    try:
        documentation = code_helper.generate_response(prompt, system_prompt)
        return f"Documentation ({language} - {doc_type}):\n\n{documentation}"
    except Exception as e:
        return f"Error generating documentation: {str(e)}"

transport = SseServerTransport("/mcp-messages/")

async def handle_sse_handshake(request):
    async with transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (in_stream, out_stream):
        await mcp._mcp_server.run(
            in_stream,
            out_stream,
            mcp._mcp_server.create_initialization_options()
        )

sse_app = Starlette(
    routes=[
        Route("/mcp-sse", handle_sse_handshake, methods=["GET"]),
        
        Mount("/mcp-messages/", app=transport.handle_post_message)
    ]
)

app = FastAPI()
app.mount("/", sse_app)

if __name__ == "__main__":
    print("\n=== MCP Code Assistant ===")
    print(f"Using Ollama model: {CODER_MODEL}")
    print("Available tools:")
    print("- explain_code: Explain what code does")
    print("- fix_code_error: Fix code errors")
    print("- create_unit_tests: Generate unit tests")
    print("- create_boilerplate: Create project boilerplate")
    print("- code_review: Perform code review")
    print("- optimize_code: Optimize code performance/readability")
    print("- convert_code: Convert between programming languages")
    print("- generate_documentation: Create code documentation")
    # mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)
    uvicorn.run(app, host="0.0.0.0", port=8765)
