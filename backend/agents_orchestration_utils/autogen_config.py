import os
from pathlib import Path
import autogen
import time 

from dotenv import load_dotenv
from typing import Optional
from autogen.agentchat.contrib.capabilities import transform_messages, transforms

from .mcp_sse_connection import MCP_SSE_Connection

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

FILE_SERVER_URL: Optional[str]  = os.environ.get("FILE_SERVER_URL")
CODE_SERVER_URL: Optional[str]  = os.environ.get("CODE_SERVER_URL")
GIT_SERVER_URL: Optional[str] = os.environ.get("GIT_SERVER_URL")

file_client = MCP_SSE_Connection(FILE_SERVER_URL)
code_client = MCP_SSE_Connection(CODE_SERVER_URL)
git_client = MCP_SSE_Connection(GIT_SERVER_URL)

RPM_LIMIT = 30
RPM_DELAY_SECONDS = 60 / RPM_LIMIT 

def add_rate_limit_delay(*args, **kwargs):
    """
    A simple hook function to be called after an agent reply.
    It enforces a delay to stay within the API's RPM limit.
    """
    print(f"[RATE LIMIT] Enforcing {RPM_DELAY_SECONDS:.1f}s delay to stay within {RPM_LIMIT} RPM limit.")
    time.sleep(RPM_DELAY_SECONDS)

# --- File System Tools ---

def write_file(path: str, content: str) -> str:
    """Writes content to a specified file, creating it if it doesn't exist or overwriting it if it does.

    Args:
        path (str): The destination file path (e.g., 'mcp_workspace/my_notes.txt').
        content (str): The text content to write into the file.
    """
    return file_client.call_tool("write_file", {'path': path, 'content': content})

def read_file(path: str) -> str:
    """Reads the entire content of a specified file.

    Args:
        path (str): The path of the file to read.
    """
    return file_client.call_tool("read_file", {'path': path})

def list_directory(path: str = ".") -> str:
    """Lists all files and subdirectories in a given directory path.

    Args:
        path (str): The path of the directory to list. Defaults to the current directory.
    """
    return file_client.call_tool("list_directory", {'path': path})

def create_directory(path: str) -> str:
    """Creates a new directory at the specified path.

    Args:
        path (str): The full path of the new directory to be created.
    """
    return file_client.call_tool("create_directory", {'path': path})

def delete_file(path: str) -> str:
    """Deletes a specified file.

    Args:
        path (str): The path of the file to delete.
    """
    return file_client.call_tool("delete_file", {'path': path})

def move_file(source: str, destination: str) -> str:
    """Moves or renames a file or directory.

    Args:
        source (str): The path of the source file or directory.
        destination (str): The path of the destination.
    """
    return file_client.call_tool("move_file", {'source': source, 'destination': destination})

def get_file_info(path: str) -> str:
    """Gets detailed information about a file or directory, such as size and modification date.

    Args:
        path (str): The path of the file or directory to inspect.
    """
    return file_client.call_tool("get_file_info", {'path': path})


# --- Coding Tools ---

def explain_code(code: str, language: str = "auto") -> str:
    """Analyzes and provides a detailed explanation of a piece of code.

    Args:
        code (str): The code snippet to explain.
        language (str): The programming language of the code. Defaults to "auto".
    """
    return code_client.call_tool("explain_code", {'code': code, 'language': language})

def fix_code_error(code: str, error_message: str, language: str = "auto") -> str:
    """Fixes an error in a piece of code given the code and the full error message.

    Args:
        code (str): The code snippet containing the error.
        error_message (str): The full error message produced by the code.
        language (str): The programming language of the code. Defaults to "auto".
    """
    return code_client.call_tool("fix_code_error", {'code': code, 'error_message': error_message, 'language': language})

def create_unit_tests(code: str, language: str = "auto", test_framework: str = "auto") -> str:
    """Generates unit tests for a given piece of code.

    Args:
        code (str): The code snippet to generate tests for.
        language (str): The programming language of the code. Defaults to "auto".
        test_framework (str): The desired testing framework (e.g., 'pytest', 'jest'). Defaults to "auto".
    """
    return code_client.call_tool("create_unit_tests", {'code': code, 'language': language, 'test_framework': test_framework})

def create_boilerplate(project_type: str, language: str, features: str = "") -> str:
    """Creates boilerplate code for various project types.

    Args:
        project_type (str): The type of project (e.g., 'fastapi', 'react-app', 'cli-tool').
        language (str): The primary programming language for the project.
        features (str): A comma-separated list of additional features (e.g., 'docker,auth').
    """
    return code_client.call_tool("create_boilerplate", {'project_type': project_type, 'language': language, 'features': features})

def code_review(code: str, language: str = "auto") -> str:
    """Performs a detailed review of a piece of code, suggesting improvements.

    Args:
        code (str): The code snippet to review.
        language (str): The programming language of the code. Defaults to "auto".
    """
    return code_client.call_tool("code_review", {'code': code, 'language': language})

def optimize_code(code: str, language: str = "auto") -> str:
    """Optimizes code for performance, readability, or memory usage.

    Args:
        code (str): The code snippet to optimize.
        language (str): The programming language of the code. Defaults to "auto".
    """
    return code_client.call_tool("optimize_code", {'code': code, 'language': language})

def convert_code(code: str, from_language: str, to_language: str) -> str:
    """Converts a code snippet from one programming language to another.

    Args:
        code (str): The code snippet to convert.
        from_language (str): The source programming language.
        to_language (str): The target programming language.
    """
    return code_client.call_tool("convert_code", {'code': code, 'from_language': from_language, 'to_language': to_language})


def generate_documentation(code: str, doc_type: str = "api", language: str = "auto") -> str:
    """Creates professional documentation for a code snippet.

    Args:
        code (str): The code snippet to document.
        doc_type (str): The type of documentation (e.g., 'docstrings', 'readme', 'api'). Defaults to "api".
        language (str): The programming language of the code. Defaults to "auto".
    """
    return code_client.call_tool("generate_documentation", {'code': code, 'doc_type': doc_type, 'language': language})


# --- Git Tools ---

def git_init(path: str = ".") -> str:
    """Initializes a new Git repository in a specified directory.

    Args:
        path (str): The directory path where the repository should be initialized. Defaults to the current directory.
    """
    return git_client.call_tool("git_init", {'path': path})

def git_clone(url: str, directory: str = ".") -> str:
    """Clones a remote Git repository from a URL into a local directory.

    Args:
        url (str): The URL of the remote Git repository to clone.
        directory (str): The local directory path to clone the repository into. Defaults to the current directory.
    """
    return git_client.call_tool("git_clone", {'url': url, 'directory': directory})

def git_status(path: str = ".") -> str:
    """Shows the status of the Git repository, including staged, unstaged, and untracked files.

    Args:
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_status", {'path': path})

def git_add(files: str, path: str = ".") -> str:
    """Adds file contents to the staging area for the next commit.

    Args:
        files (str): The files to add. Use '.' to add all changes, or specify a file path (e.g., 'src/main.py').
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_add", {'files': files, 'path': path})

def git_commit(message: str, path: str = ".") -> str:
    """Records changes staged in the index to the repository with a commit message.

    Args:
        message (str): The commit message describing the changes.
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_commit", {'message': message, 'path': path})

def git_push(remote: str = "origin", branch: str = "main", path: str = ".") -> str:
    """Pushes committed changes from a local branch to a remote repository.

    Args:
        remote (str): The name of the remote repository. Defaults to "origin".
        branch (str): The name of the local branch to push. Defaults to "main".
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_push", {'remote': remote, 'branch': branch, 'path': path})

def git_pull(remote: str = "origin", branch: str = "main", path: str = ".") -> str:
    """Fetches changes from a remote repository and merges them into the current local branch.

    Args:
        remote (str): The name of the remote repository to pull from. Defaults to "origin".
        branch (str): The name of the remote branch to pull. Defaults to "main".
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_pull", {'remote': remote, 'branch': branch, 'path': path})

def git_branch(action: str = "list", branch_name: str = "", path: str = ".") -> str:
    """Manages Git branches. Actions can be 'list', 'create', 'delete', or 'switch'.

    Args:
        action (str): The operation to perform: 'list', 'create', 'delete', or 'switch'. Defaults to 'list'.
        branch_name (str): The name of the branch for 'create', 'delete', or 'switch' actions.
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_branch", {'action': action, 'branch_name': branch_name, 'path': path})

def git_log(count: int = 10, path: str = ".") -> str:
    """Shows the commit history for the repository.

    Args:
        count (int): The number of recent commits to display. Defaults to 10.
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_log", {'count': count, 'path': path})

def git_diff(file: str = "", staged: bool = False, path: str = ".") -> str:
    """Shows the differences between commits, the commit and the working tree, etc.

    Args:
        file (str): The specific file to diff. If empty, shows all changes.
        staged (bool): If True, shows only changes in the staging area. Defaults to False.
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_diff", {'file': file, 'staged': staged, 'path': path})

def git_remote(action: str = "list", name: str = "", url: str = "", path: str = ".") -> str:
    """Manages the set of tracked remote repositories. Actions can be 'list', 'add', or 'remove'.

    Args:
        action (str): The operation to perform: 'list', 'add', or 'remove'. Defaults to 'list'.
        name (str): The name of the remote for 'add' or 'remove' actions (e.g., 'origin', 'upstream').
        url (str): The URL of the remote repository for the 'add' action.
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_remote", {'action': action, 'name': name, 'url': url, 'path': path})

def git_stash(action: str = "save", message: str = "", path: str = ".") -> str:
    """Temporarily shelves (or stashes) changes you've made to your working copy.

    Args:
        action (str): The stash action: 'save', 'pop', 'apply', 'list'. Defaults to 'save'.
        message (str): An optional message to identify the stash when using 'save'.
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_stash", {'action': action, 'message': message, 'path': path})

def git_merge(branch: str, path: str = ".") -> str:
    """Joins two or more development histories together by merging another branch into the current branch.

    Args:
        branch (str): The name of the branch to merge into the current branch.
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_merge", {'branch': branch, 'path': path})

def git_reset(mode: str = "mixed", target: str = "HEAD", path: str = ".") -> str:
    """Resets the current HEAD to a specified state, useful for unstaging files or discarding changes.

    Args:
        mode (str): The reset mode: 'soft', 'mixed', 'hard'. Defaults to "mixed".
        target (str): The commit or reference to reset to. Defaults to "HEAD".
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_reset", {'mode': mode, 'target': target, 'path': path})

def git_config(action: str = "list", key: str = "", value: str = "", global_config: bool = False, path: str = ".") -> str:
    """Gets and sets repository or global configuration options.

    Args:
        action (str): The action: 'get', 'set', 'list'. Defaults to 'list'.
        key (str): The configuration key to get or set (e.g., 'user.name').
        value (str): The value to set for the specified key.
        global_config (bool): If True, applies the configuration globally. Defaults to False.
        path (str): The path to the Git repository. Defaults to the current directory.
    """
    return git_client.call_tool("git_config", {'action': action, 'key': key, 'value': value, 'global_config': global_config, 'path': path})


def get_autogen_config(llm_config: dict):
    """
    A function to create and configure a robust, two-agent tool-calling system
    with intelligent context handling.
    """
    available_tools = [
        write_file, read_file, list_directory, create_directory, delete_file, move_file, get_file_info,
        explain_code, fix_code_error, create_unit_tests, create_boilerplate, code_review, optimize_code, convert_code, generate_documentation,
        git_init, git_clone, git_status, git_add, git_commit, git_push, git_pull, git_branch, git_log, git_diff, git_remote, git_stash, 
        git_merge, git_reset, git_config
    ]
    
    context_handling = transform_messages.TransformMessages(
        transforms=[
            transforms.MessageHistoryLimiter(max_messages=10),
        ]
    )
    
    assistant = autogen.AssistantAgent(
        name="Tool_Assistant",
        llm_config=llm_config,
        system_message = f"""You are a highly capable assistant who must solve tasks **only** by using the registered tools in this {available_tools} You are not allowed to write raw code or natural language explanations unless a tool returns them.

            **Your responsibilities:**
            1. Analyze the user request and decompose it into sub-tasks.
            2. Use the available tools strategically and sequentially to complete those sub-tasks.
            3. Combine multiple tools as needed — do not assume a single tool is enough.
            4. When interacting with files, always verify their existence using `list_directory` before accessing them.
            5. When unsure about a file/directory path, retrieve or create it using available tools.
            6. For each tool call, be precise and use the correct parameters — no guessing.

            **Strict rules:**
            - You MUST NOT write Python code or shell commands directly.
            - You MUST NOT respond with explanations, summaries, or any text not coming from a tool.
            - You MUST respond **only** with valid tool calls like:
            `write_file(path="utils.py", content="...")`
            - End the task explicitly with: `TERMINATE`

            You are allowed and expected to:
            - Call multiple tools in a sequence
            - Loop back to re-analyze if a tool result requires follow-up actions
            - Create files, directories, or git operations if needed to fulfill the goal
        """ 
    )

    context_handling.add_to_agent(assistant)

    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=8,
        code_execution_config={"work_dir": "mcp_workspace"},
        llm_config=None
    )
    # assistant.register_reply("rate_limit_hook", add_rate_limit_delay)

    
    
    for tool in available_tools:
        assistant.register_for_llm(name=tool.__name__, description=tool.__doc__)(tool)
        user_proxy.register_for_execution(name=tool.__name__)(tool)

    return user_proxy, assistant, context_handling