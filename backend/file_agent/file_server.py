import os
import uvicorn
import shutil

from fastmcp import FastMCP
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from mcp.server.sse import SseServerTransport
from pathlib import Path
from starlette.responses import Response
# from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Filesystem Server")

ALLOWED_BASE_DIR = Path(os.getenv("MCP_WORKSPACE_DIR", "/workspace")).resolve()
ALLOWED_BASE_DIR.mkdir(parents=True, exist_ok=True)

def validate_path(path: str) -> Path:
    """Validate and resolve path within allowed directory"""
    try:
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = ALLOWED_BASE_DIR / target_path
        
        resolved_path = target_path.resolve()
        allowed_resolved = ALLOWED_BASE_DIR.resolve()
        
        if not str(resolved_path).startswith(str(allowed_resolved)):
            raise ValueError(f"Path outside allowed directory: {path}")
        
        return resolved_path
    except Exception as e:
        raise ValueError(f"Invalid path: {path} - {str(e)}")

@mcp.tool("read_file")
def read_file(path: str) -> str:
    """
    Read the content of a file by name or relative path from the workspace.
    If only the file name is given, it searches recursively under the workspace.
    """
    try:
        try:
            file_path = validate_path(path)
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f"File content of {file_path}:\n{f.read()}"
        except Exception:
            pass 

        matches = list(ALLOWED_BASE_DIR.rglob(path))
        if not matches:
            return f"Error: File named '{path}' not found in workspace."

        selected = matches[0]
        with open(selected, 'r', encoding='utf-8') as f:
            return f"File content of {selected}:\n{f.read()}"
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"


@mcp.tool("write_file")
def write_file(path: str, content: str) -> str:
    """Write content to a file"""
    try:
        file_path = validate_path(path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file {path}: {str(e)}"
    

@mcp.tool("list_directory")
def list_directory(path: str = ".") -> str:
    """List files and directories in a directory"""
    try:
        dir_path = validate_path(path)
        
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"
        
        if not dir_path.is_dir():
            return f"Error: Path is not a directory: {path}"
        
        items = []
        for item in sorted(dir_path.iterdir()):
            item_type = "directory" if item.is_dir() else "file"
            size = item.stat().st_size if item.is_file() else "-"
            items.append({
                "name": item.name,
                "type": item_type,
                "size": size
            })
        
        result = f"Contents of {path}:\n"
        for item in items:
            result += f"  {item['type']:9} {item['name']:30} {item['size']}\n"
        
        return result
    except Exception as e:
        return f"Error listing directory {path}: {str(e)}"

@mcp.tool("create_directory")
def create_directory(path: str) -> str:
    """Create a new directory"""
    try:
        dir_path = validate_path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return f"Successfully created directory: {path}"
    except Exception as e:
        return f"Error creating directory {path}: {str(e)}"

@mcp.tool("delete_file")
def delete_file(path: str) -> str:
    """Delete a file"""
    try:
        file_path = validate_path(path)
        
        if not file_path.exists():
            return f"Error: File not found: {path}"
        
        if file_path.is_file():
            file_path.unlink()
            return f"Successfully deleted file: {path}"
        elif file_path.is_dir():
            return f"Error: Path is a directory, use delete_directory instead: {path}"
        else:
            return f"Error: Unknown file type: {path}"
    except Exception as e:
        return f"Error deleting file {path}: {str(e)}"

@mcp.tool("delete_directory")
def delete_directory(path: str) -> str:
    """Delete a directory and all its contents"""
    try:
        dir_path = validate_path(path)
        
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"
        
        if not dir_path.is_dir():
            return f"Error: Path is not a directory: {path}"
        
        shutil.rmtree(dir_path)
        return f"Successfully deleted directory: {path}"
    except Exception as e:
        return f"Error deleting directory {path}: {str(e)}"

@mcp.tool("move_file")
def move_file(source: str, destination: str) -> str:
    """Move a file to directory"""
    try:
        source_path = validate_path(source)
        dest_path = validate_path(destination)
        
        if not source_path.exists():
            return f"Error: Source not found: {source}"
        
        # Create parent directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(source_path), str(dest_path))
        return f"Successfully moved {source} to {destination}"
    except Exception as e:
        return f"Error moving {source} to {destination}: {str(e)}"

@mcp.tool("get_file_info")
def get_file_info(path: str) -> str:
    """Get detailed information about a file or directory"""
    try:
        file_path = validate_path(path)
        
        if not file_path.exists():
            return f"Error: Path not found: {path}"
        
        stat = file_path.stat()
        info = {
            "path": str(file_path),
            "name": file_path.name,
            "type": "directory" if file_path.is_dir() else "file",
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:]
        }
        
        result = f"Information for {path}:\n"
        for key, value in info.items():
            result += f"  {key}: {value}\n"
        
        return result
    except Exception as e:
        return f"Error getting info for {path}: {str(e)}"

transport = SseServerTransport("/mcp-messages/")

async def handle_sse_handshake(request):
    """
    Handles the long-lived SSE connection.
    It must return a Response object when the connection is closed.
    """
    try:
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as (in_stream, out_stream):
            await mcp._mcp_server.run(
                in_stream,
                out_stream,
                mcp._mcp_server.create_initialization_options()
            )
    except Exception as e:
        print(f"Error during SSE connection: {e}")
    finally:
        return Response(status_code=200, content="SSE connection closed.")

sse_app = Starlette(
    routes=[
        Route("/mcp-sse", handle_sse_handshake, methods=["GET"]),
        Mount("/mcp-messages/", app=transport.handle_post_message)
    ]
)

app = FastAPI()
app.mount("/", sse_app)

if __name__ == "__main__":
    print("\n=== MCP Filesystem Assistant ===")
    print(f"Allowed base directory: {ALLOWED_BASE_DIR}")
    print("Ask me to help with file operations! Type 'quit' to exit.")
    print("Examples:")
    print("- 'Create a file called test.txt with hello world content'")
    print("- 'List files in the current directory'")
    print("- 'Read the contents of test.txt'")
    print("- 'Create a folder called documents'")
    uvicorn.run(app, host="0.0.0.0", port=8766)