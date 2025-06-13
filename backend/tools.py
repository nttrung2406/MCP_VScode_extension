import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

def _make_mcp_request(server_url: str, tool_name: str, payload: dict) -> str:
    """Makes a POST request to a specific tool on an MCP server with detailed logging."""
    print("--------------------------------------------------")
    print(f"[TOOL RUN] Attempting to execute tool: '{tool_name}'")
    print(f"[TOOL RUN] Target Server: {server_url}")
    print(f"[TOOL RUN] Payload (Arguments): {payload}")
    
    try:
        url = f"{server_url}/call/{tool_name}"
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json().get("content", f"Tool '{tool_name}' executed but returned no specific content.")
        print(f"[TOOL RUN] Success! Result from server: {result}")
        print("--------------------------------------------------")
        return result
        
    except requests.exceptions.RequestException as e:
        error_message = f"Error connecting to MCP server for tool '{tool_name}': {e}"
        print(f"[TOOL RUN] FAILURE: {error_message}")
        print("--------------------------------------------------")
        return error_message
        
    except Exception as e:
        error_message = f"An unexpected error occurred during the tool call for '{tool_name}': {e}"
        print(f"[TOOL RUN] FAILURE: {error_message}")
        print("--------------------------------------------------")
        return error_message

# --- File System Tools ---
FILE_SERVER_URL = "http://file-server:8766/mc-sse"

class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = "Writes content to a specified file. Use this to create new files or overwrite existing ones."
    
    class ArgsSchema(BaseModel):
        path: str = Field(description="The file system path where the file should be written.")
        content: str = Field(description="The text or code content to write into the file.")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, path: str, content: str) -> str:
        return _make_mcp_request(FILE_SERVER_URL, self.name, {'path': path, 'content': content})

class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "Reads the entire content of a specified file."
    
    class ArgsSchema(BaseModel):
        path: str = Field(description="The path of the file to read.")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, path: str) -> str:
        return _make_mcp_request(FILE_SERVER_URL, self.name, {'path': path})

class ListDirectoryTool(BaseTool):
    name: str = "list_directory"
    description: str = "Lists all files and subdirectories in a given directory path."

    class ArgsSchema(BaseModel):
        path: str = Field(description="The path of the directory to list.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, path: str = ".") -> str:
        return _make_mcp_request(FILE_SERVER_URL, self.name, {'path': path})



class CreateDirectoryTool(BaseTool):
    name: str = "create_directory"
    description: str = "Creates a new directory at the specified path."

    class ArgsSchema(BaseModel):
        path: str = Field(description="The path where the new directory should be created.")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, path: str) -> str:
        return _make_mcp_request(FILE_SERVER_URL, self.name, {'path': path})

class DeleteFileTool(BaseTool):
    name: str = "delete_file"
    description: str = "Deletes a specified file."
    
    class ArgsSchema(BaseModel):
        path: str = Field(description="The path of the file to delete.")
    args_schema: Type[BaseModel] = ArgsSchema
    
    def _run(self, path: str) -> str:
        return _make_mcp_request(FILE_SERVER_URL, self.name, {'path': path})

class MoveFileTool(BaseTool):
    name: str = "move_file"
    description: str = "Moves or renames a file or directory."

    class ArgsSchema(BaseModel):
        source: str = Field(description="The source path of the file or directory to move.")
        destination: str = Field(description="The destination path.")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, source: str, destination: str) -> str:
        return _make_mcp_request(FILE_SERVER_URL, self.name, {'source': source, 'destination': destination})

class GetFileInfoTool(BaseTool):
    name: str = "get_file_info"
    description: str = "Gets detailed information about a file or directory."

    class ArgsSchema(BaseModel):
        path: str = Field(description="The path of the file or directory.")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, path: str) -> str:
        return _make_mcp_request(FILE_SERVER_URL, self.name, {'path': path})


# --- Coding Tools ---
CODE_SERVER_URL = "http://coding-server:8765/mc-sse"

class ExplainCodeTool(BaseTool):
    name: str = "explain_code"
    description: str = "Analyzes and explains a piece of code."

    class ArgsSchema(BaseModel):
        code: str = Field(description="The code snippet to explain.")
        language: str = Field(description="The programming language of the code.", default="auto")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, code: str, language: str = "auto") -> str:
        return _make_mcp_request(CODE_SERVER_URL, self.name, {'code': code, 'language': language})

class FixCodeErrorTool(BaseTool):
    name: str = "fix_code_error"
    description: str = "Fixes an error in a piece of code given the code and the error message."
    
    class ArgsSchema(BaseModel):
        code: str = Field(description="The code snippet with the error.")
        error_message: str = Field(description="The error message produced by the code.")
        language: str = Field(description="The programming language.", default="auto")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, code: str, error_message: str, language: str = "auto") -> str:
        return _make_mcp_request(CODE_SERVER_URL, self.name, {'code': code, 'error_message': error_message, 'language': language})

class CreateUnitTestsTool(BaseTool):
    name: str = "create_unit_tests"
    description: str = "Generates unit tests for a given piece of code."

    class ArgsSchema(BaseModel):
        code: str = Field(description="The code to generate tests for.")
        language: str = Field(description="The programming language.", default="auto")
        test_framework: str = Field(description="The testing framework to use.", default="auto")
    args_schema: Type[BaseModel] = ArgsSchema
    
    def _run(self, code: str, language: str = "auto", test_framework: str = "auto") -> str:
        return _make_mcp_request(CODE_SERVER_URL, self.name, {'code': code, 'language': language, 'test_framework': test_framework})

class CreateBoilerplateTool(BaseTool):
    name: str = "create_boilerplate"
    description: str = "Creates boilerplate code for various project types."
    
    class ArgsSchema(BaseModel):
        project_type: str = Field(description="The type of project (e.g., 'FastAPI web app', 'React component').")
        language: str = Field(description="The programming language for the boilerplate.")
        features: str = Field(description="Comma-separated list of additional features to include.", default="")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, project_type: str, language: str, features: str = "") -> str:
        return _make_mcp_request(CODE_SERVER_URL, self.name, {'project_type': project_type, 'language': language, 'features': features})

class CodeReviewTool(BaseTool):
    name: str = "code_review"
    description: str = "Performs a detailed review of a piece of code."
    
    class ArgsSchema(BaseModel):
        code: str = Field(description="The code snippet to review.")
        language: str = Field(description="The programming language.", default="auto")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, code: str, language: str = "auto") -> str:
        return _make_mcp_request(CODE_SERVER_URL, self.name, {'code': code, 'language': language})

class OptimizeCodeTool(BaseTool):
    name: str = "optimize_code"
    description: str = "Optimize code for performance, readability, or memory usage."
    
    class ArgsSchema(BaseModel):
        code: str = Field(description="The code snippet to optimize.")
        language: str = Field(description="The programming language.", default="auto")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, code: str, language: str = "auto") -> str:
        return _make_mcp_request(CODE_SERVER_URL, self.name, {'code': code, 'language': language})

class ConvertCodeTool(BaseTool):
    name: str = "convert_code"
    description: str = "Convert code from one programming language to another."
    
    class ArgsSchema(BaseModel):
        code: str = Field(description="The code snippet to convert.")
        language: str = Field(description="The programming language.", default="auto")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, code: str, language: str = "auto") -> str:
        return _make_mcp_request(CODE_SERVER_URL, self.name, {'code': code, 'language': language})

class GenerateDocumentationTool(BaseTool):
    name: str = "generate_documentation"
    description: str = "Creates professional documentation (e.g., API docs, docstrings) for a code snippet."

    class ArgsSchema(BaseModel):
        """
        Input schema for the GenerateDocumentationTool.
        Defines the arguments the language model needs to provide.
        """
        code: str = Field(description="The source code that needs documentation.")
        doc_type: str = Field(
            description="The type of documentation to generate (e.g., 'api', 'docstring', 'user guide').",
            default="api"
        )
        language: str = Field(
            description="The programming language of the code. Defaults to 'auto' for automatic detection.",
            default="auto"
        )
    
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, code: str, doc_type: str = "api", language: str = "auto") -> str:
        payload = {
            'code': code,
            'doc_type': doc_type,
            'language': language
        }
        return _make_mcp_request(CODE_SERVER_URL, self.name, payload)

# --- Git Tools ---
GIT_SERVER_URL = "http://git-server:8767/mc-sse"

class GitInitTool(BaseTool):
    name: str = "git_init"
    description: str = "Initializes a new Git repository."

    class ArgsSchema(BaseModel):
        path: str = Field(description="The directory path to initialize the repository in.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'path': path})

class GitCloneTool(BaseTool):
    name: str = "git_clone"
    description: str = "Clones a remote Git repository from a URL."

    class ArgsSchema(BaseModel):
        url: str = Field(description="The URL of the remote Git repository.")
        directory: str = Field(description="The local directory to clone into.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, url: str, directory: str = None) -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'url': url, 'directory': directory})

class GitStatusTool(BaseTool):
    name: str = "git_status"
    description: str = "Shows the status of the Git repository."
    
    class ArgsSchema(BaseModel):
        path: str = Field(description="The path to the repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'path': path})

class GitAddTool(BaseTool):
    name: str = "git_add"
    description: str = "Adds file contents to the staging area."

    class ArgsSchema(BaseModel):
        files: str = Field(description="The files to add. Use '.' to add all changes.")
        path: str = Field(description="The path to the repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, files: str, path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'files': files, 'path': path})

class GitCommitTool(BaseTool):
    name: str = "git_commit"
    description: str = "Records changes to the repository with a commit message."

    class ArgsSchema(BaseModel):
        message: str = Field(description="The commit message.")
        path: str = Field(description="The path to the repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, message: str, path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'message': message, 'path': path})
    
class GitPushTool(BaseTool):
    name: str = "git_push"
    description: str = "Pushes committed changes from a local branch to a remote repository."
    
    class ArgsSchema(BaseModel):
        remote: str = Field(description="The name of the remote repository to push to.", default="origin")
        branch: str = Field(description="The name of the local branch whose changes will be pushed.", default="main")
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, remote: str = "origin", branch: str = "main", path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'remote': remote, 'branch': branch, 'path': path})

class GitPullTool(BaseTool):
    name: str = "git_pull"
    description: str = "Fetches changes from a remote repository and merges them into the current local branch."
    
    class ArgsSchema(BaseModel):
        remote: str = Field(description="The name of the remote repository to pull from.", default="origin")
        branch: str = Field(description="The name of the remote branch to pull.", default="main")
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, remote: str = "origin", branch: str = "main", path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'remote': remote, 'branch': branch, 'path': path})

class GitBranchTool(BaseTool):
    name: str = "git_branch"
    description: str = "Manages Git branches. Actions can be 'list', 'create', 'delete', or 'switch'."

    class ArgsSchema(BaseModel):
        action: str = Field(description="The operation to perform: 'list', 'create', 'delete', 'switch'.", default="list")
        branch_name: str = Field(description="The name of the branch for 'create', 'delete', or 'switch' actions.", default="")
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, action: str = "list", branch_name: str = "", path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'action': action, 'branch_name': branch_name, 'path': path})

class GitLogTool(BaseTool):
    name: str = "git_log"
    description: str = "Shows the commit history for the repository."

    class ArgsSchema(BaseModel):
        count: int = Field(description="The maximum number of commits to show.", default=10)
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, count: int = 10, path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'count': count, 'path': path})

class GitDiffTool(BaseTool):
    name: str = "git_diff"
    description: str = "Shows the differences between commits, the commit and the working tree, etc."

    class ArgsSchema(BaseModel):
        file: str = Field(description="Optional. A specific file to diff. If empty, shows all changes.", default="")
        staged: bool = Field(description="If true, shows only changes in the staging area (i.e., 'git add'ed files).", default=False)
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, file: str = "", staged: bool = False, path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'file': file, 'staged': staged, 'path': path})

class GitRemoteTool(BaseTool):
    name: str = "git_remote"
    description: str = "Manages the set of tracked remote repositories. Actions can be 'list', 'add', or 'remove'."

    class ArgsSchema(BaseModel):
        action: str = Field(description="The operation to perform: 'list', 'add', 'remove'.", default="list")
        name: str = Field(description="The shortname of the remote (e.g., 'origin'). Required for 'add' and 'remove'.", default="")
        url: str = Field(description="The URL of the remote repository. Required for the 'add' action.", default="")
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, action: str = "list", name: str = "", url: str = "", path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'action': action, 'name': name, 'url': url, 'path': path})

class GitStashTool(BaseTool):
    name: str = "git_stash"
    description: str = "Temporarily shelves (or stashes) changes you've made to your working copy so you can work on something else."

    class ArgsSchema(BaseModel):
        action: str = Field(description="Action to perform: 'save', 'pop', 'list', 'drop', 'clear'.", default="save")
        message: str = Field(description="An optional descriptive message for 'save' action.", default="")
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, action: str = "save", message: str = "", path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'action': action, 'message': message, 'path': path})

class GitMergeTool(BaseTool):
    name: str = "git_merge"
    description: str = "Joins two or more development histories together by merging another branch into the current branch."

    class ArgsSchema(BaseModel):
        branch: str = Field(description="The name of the branch to merge into the current branch.")
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, branch: str, path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'branch': branch, 'path': path})

class GitResetTool(BaseTool):
    name: str = "git_reset"
    description: str = "Resets the current HEAD to a specified state. Can be used to unstage files or discard changes."

    class ArgsSchema(BaseModel):
        mode: str = Field(description="The reset mode. Must be one of 'soft', 'mixed', or 'hard'.", default="mixed")
        target: str = Field(description="The commit hash or branch name to reset to.", default="HEAD")
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, mode: str = "mixed", target: str = "HEAD", path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'mode': mode, 'target': target, 'path': path})

class GitConfigTool(BaseTool):
    name: str = "git_config"
    description: str = "Gets and sets repository or global configuration options."

    class ArgsSchema(BaseModel):
        action: str = Field(description="The operation to perform: 'list', 'get', 'set'.", default="list")
        key: str = Field(description="The configuration key (e.g., 'user.name'). Required for 'get' and 'set'.", default="")
        value: str = Field(description="The value to set for a key. Required for the 'set' action.", default="")
        global_config: bool = Field(description="If true, sets the configuration globally, otherwise for the local repo.", default=False)
        path: str = Field(description="The path to the local repository.", default=".")
    args_schema: Type[BaseModel] = ArgsSchema

    def _run(self, action: str = "list", key: str = "", value: str = "", global_config: bool = False, path: str = ".") -> str:
        return _make_mcp_request(GIT_SERVER_URL, self.name, {'action': action, 'key': key, 'value': value, 'global_config': global_config, 'path': path})