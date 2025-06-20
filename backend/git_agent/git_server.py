import os
import subprocess
import uvicorn

from pathlib import Path
from typing import List, Dict, Any, Optional
# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from mcp.server.sse import SseServerTransport
from starlette.responses import Response

mcp = FastMCP("Git Server")


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

def run_git_command(cmd: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
    """Run a git command and return the result"""
    try:
        if cwd is None:
            cwd = ALLOWED_BASE_DIR
        
        cwd = validate_path(str(cwd))
        
        result = subprocess.run(
            ["git"] + cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

@mcp.tool("git_init")
def git_init(path: str = ".") -> str:
    """Initialize a new Git repository"""
    try:
        repo_path = validate_path(path)
        repo_path.mkdir(parents=True, exist_ok=True)
        
        result = run_git_command(["init"], cwd=repo_path)
        
        if result["success"]:
            return f"Initialized Git repository in {path}\n{result['stdout']}"
        else:
            return f"Error initializing repository: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_clone")
def git_clone(url: str, directory: str = None) -> str:
    """Clone a Git repository"""
    try:
        cmd = ["clone", url]
        if directory:
            cmd.append(directory)
            target_path = validate_path(directory)
        else:
            target_path = ALLOWED_BASE_DIR
        
        result = run_git_command(cmd, cwd=ALLOWED_BASE_DIR)
        
        if result["success"]:
            return f"Successfully cloned repository from {url}\n{result['stdout']}"
        else:
            return f"Error cloning repository: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_status")
def git_status(path: str = ".") -> str:
    """Get Git repository status"""
    try:
        repo_path = validate_path(path)
        result = run_git_command(["status", "--porcelain", "-b"], cwd=repo_path)
        
        if result["success"]:
            if result["stdout"]:
                return f"Git status for {path}:\n{result['stdout']}"
            else:
                return f"Working directory clean in {path}"
        else:
            return f"Error getting status: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_add")
def git_add(files: str, path: str = ".") -> str:
    """Add files to Git staging area"""
    try:
        repo_path = validate_path(path)
        
        if files == ".":
            cmd = ["add", "."]
        elif files == "-A" or files == "--all":
            cmd = ["add", "-A"]
        else:
            # Split multiple files by comma or space
            file_list = [f.strip() for f in files.replace(",", " ").split()]
            cmd = ["add"] + file_list
        
        result = run_git_command(cmd, cwd=repo_path)
        
        if result["success"]:
            return f"Successfully added files: {files}\n{result['stdout']}"
        else:
            return f"Error adding files: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_commit")
def git_commit(message: str, path: str = ".") -> str:
    """Commit changes to Git repository"""
    try:
        repo_path = validate_path(path)
        result = run_git_command(["commit", "-m", message], cwd=repo_path)
        
        if result["success"]:
            return f"Successfully committed changes: {message}\n{result['stdout']}"
        else:
            return f"Error committing changes: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_push")
def git_push(remote: str = "origin", branch: str = "main", path: str = ".") -> str:
    """Push changes to remote repository"""
    try:
        repo_path = validate_path(path)
        result = run_git_command(["push", remote, branch], cwd=repo_path)
        
        if result["success"]:
            return f"Successfully pushed to {remote}/{branch}\n{result['stdout']}"
        else:
            return f"Error pushing changes: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_pull")
def git_pull(remote: str = "origin", branch: str = "main", path: str = ".") -> str:
    """Pull changes from remote repository"""
    try:
        repo_path = validate_path(path)
        result = run_git_command(["pull", remote, branch], cwd=repo_path)
        
        if result["success"]:
            return f"Successfully pulled from {remote}/{branch}\n{result['stdout']}"
        else:
            return f"Error pulling changes: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_branch")
def git_branch(action: str = "list", branch_name: str = "", path: str = ".") -> str:
    """Manage Git branches (list, create, delete, switch)"""
    try:
        repo_path = validate_path(path)
        
        if action == "list":
            result = run_git_command(["branch", "-a"], cwd=repo_path)
        elif action == "create":
            if not branch_name:
                return "Error: Branch name required for create action"
            result = run_git_command(["branch", branch_name], cwd=repo_path)
        elif action == "delete":
            if not branch_name:
                return "Error: Branch name required for delete action"
            result = run_git_command(["branch", "-d", branch_name], cwd=repo_path)
        elif action == "switch" or action == "checkout":
            if not branch_name:
                return "Error: Branch name required for switch action"
            result = run_git_command(["checkout", branch_name], cwd=repo_path)
        else:
            return f"Error: Unknown action '{action}'. Use: list, create, delete, switch"
        
        if result["success"]:
            return f"Branch operation '{action}' completed:\n{result['stdout']}"
        else:
            return f"Error with branch operation: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_log")
def git_log(count: int = 10, path: str = ".") -> str:
    """Show Git commit history"""
    try:
        repo_path = validate_path(path)
        result = run_git_command([
            "log", 
            f"--max-count={count}", 
            "--oneline", 
            "--graph", 
            "--decorate"
        ], cwd=repo_path)
        
        if result["success"]:
            return f"Git log (last {count} commits):\n{result['stdout']}"
        else:
            return f"Error getting log: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_diff")
def git_diff(file: str = "", staged: bool = False, path: str = ".") -> str:
    """Show Git differences"""
    try:
        repo_path = validate_path(path)
        
        cmd = ["diff"]
        if staged:
            cmd.append("--cached")
        if file:
            cmd.append(file)
        
        result = run_git_command(cmd, cwd=repo_path)
        
        if result["success"]:
            if result["stdout"]:
                return f"Git diff:\n{result['stdout']}"
            else:
                return "No differences found"
        else:
            return f"Error getting diff: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_remote")
def git_remote(action: str = "list", name: str = "", url: str = "", path: str = ".") -> str:
    """Manage Git remotes"""
    try:
        repo_path = validate_path(path)
        
        if action == "list":
            result = run_git_command(["remote", "-v"], cwd=repo_path)
        elif action == "add":
            if not name or not url:
                return "Error: Both name and URL required for add action"
            result = run_git_command(["remote", "add", name, url], cwd=repo_path)
        elif action == "remove":
            if not name:
                return "Error: Remote name required for remove action"
            result = run_git_command(["remote", "remove", name], cwd=repo_path)
        else:
            return f"Error: Unknown action '{action}'. Use: list, add, remove"
        
        if result["success"]:
            return f"Remote operation '{action}' completed:\n{result['stdout']}"
        else:
            return f"Error with remote operation: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_stash")
def git_stash(action: str = "save", message: str = "", path: str = ".") -> str:
    """Manage Git stash"""
    try:
        repo_path = validate_path(path)
        
        if action == "save" or action == "push":
            cmd = ["stash", "push"]
            if message:
                cmd.extend(["-m", message])
        elif action == "pop":
            cmd = ["stash", "pop"]
        elif action == "list":
            cmd = ["stash", "list"]
        elif action == "drop":
            cmd = ["stash", "drop"]
        elif action == "clear":
            cmd = ["stash", "clear"]
        else:
            return f"Error: Unknown action '{action}'. Use: save, pop, list, drop, clear"
        
        result = run_git_command(cmd, cwd=repo_path)
        
        if result["success"]:
            return f"Stash operation '{action}' completed:\n{result['stdout']}"
        else:
            return f"Error with stash operation: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_merge")
def git_merge(branch: str, path: str = ".") -> str:
    """Merge a branch into current branch"""
    try:
        repo_path = validate_path(path)
        result = run_git_command(["merge", branch], cwd=repo_path)
        
        if result["success"]:
            return f"Successfully merged branch '{branch}':\n{result['stdout']}"
        else:
            return f"Error merging branch: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_reset")
def git_reset(mode: str = "mixed", target: str = "HEAD", path: str = ".") -> str:
    """Reset Git repository state"""
    try:
        repo_path = validate_path(path)
        
        valid_modes = ["soft", "mixed", "hard"]
        if mode not in valid_modes:
            return f"Error: Invalid mode '{mode}'. Use: {', '.join(valid_modes)}"
        
        result = run_git_command(["reset", f"--{mode}", target], cwd=repo_path)
        
        if result["success"]:
            return f"Successfully reset to {target} ({mode} mode):\n{result['stdout']}"
        else:
            return f"Error resetting: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool("git_config")
def git_config(action: str = "list", key: str = "", value: str = "", global_config: bool = False, path: str = ".") -> str:
    """Manage Git configuration"""
    try:
        repo_path = validate_path(path)
        
        if action == "list":
            cmd = ["config", "--list"]
            if global_config:
                cmd.append("--global")
        elif action == "get":
            if not key:
                return "Error: Key required for get action"
            cmd = ["config", key]
            if global_config:
                cmd.insert(1, "--global")
        elif action == "set":
            if not key or not value:
                return "Error: Both key and value required for set action"
            cmd = ["config", key, value]
            if global_config:
                cmd.insert(1, "--global")
        else:
            return f"Error: Unknown action '{action}'. Use: list, get, set"
        
        result = run_git_command(cmd, cwd=repo_path)
        
        if result["success"]:
            return f"Config operation '{action}' completed:\n{result['stdout']}"
        else:
            return f"Error with config operation: {result['stderr']}"
    except Exception as e:
        return f"Error: {str(e)}"

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
    print(f"Allowed base directory: {ALLOWED_BASE_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8767)