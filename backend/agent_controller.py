import asyncio
import os
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
# from langchain_community.llms import Ollama
# from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SkipValidation
from rich import print
from dotenv import load_dotenv
load_dotenv()
google_api_key=os.environ.get("GEMINI_API_KEY")

from tools import (WriteFileTool, ReadFileTool, ListDirectoryTool, CreateDirectoryTool, 
                   DeleteFileTool, MoveFileTool, GetFileInfoTool)

from tools import (ExplainCodeTool, FixCodeErrorTool, CreateUnitTestsTool, CreateBoilerplateTool, 
                   CodeReviewTool, OptimizeCodeTool, ConvertCodeTool, GenerateDocumentationTool)

from tools import (GitAddTool, GitBranchTool, GitCloneTool, GitCommitTool, GitConfigTool, 
                   GitDiffTool, GitInitTool, GitLogTool, GitMergeTool, GitPullTool, 
                   GitPushTool, GitRemoteTool, GitResetTool, GitStashTool, GitStatusTool, GetFileInfoTool)

all_tools = [
    # File Tools
    WriteFileTool(), ReadFileTool(), ListDirectoryTool(), CreateDirectoryTool(), 
    DeleteFileTool(), MoveFileTool(), GetFileInfoTool(),
    # Coding Tools
    ExplainCodeTool(), FixCodeErrorTool(), CreateUnitTestsTool(), CreateBoilerplateTool(), 
    CodeReviewTool(), OptimizeCodeTool(), ConvertCodeTool(), GenerateDocumentationTool(),
    # Git Tools
    GitInitTool(), GitCloneTool(), GitStatusTool(), GitAddTool(), GitCommitTool(),
    GitPushTool(), GitPullTool(), GitBranchTool(), GitLogTool(), GitDiffTool(),
    GitRemoteTool(), GitStashTool(), GitMergeTool(), GitResetTool(), GitConfigTool()
]

# ====================================== Only for testing ========================================
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="MCP Agent Controller",
    description="An API to trigger the CrewAI agent orchestration.",
    version="1.0.0"
)

class TaskRequest(BaseModel):
    prompt: str

# ====================================== Only for testing ========================================

llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",  
        verbose=True,
        temperature=0.6,
        google_api_key=google_api_key
)
class MCPTool(BaseTool):
    name: str
    description: str
    mcp_client: SkipValidation[any]

    def _run(self, argument: str) -> str:
        return asyncio.run(self.mcp_client.run_task(argument))

    async def _arun(self, argument: str) -> str:
        return await self.mcp_client.run_task(argument)

# --- Agent Instantiation ---

mcp_agent = Agent(
    role="Expert Full-Stack Developer and DevOps Specialist",
    goal="""
        You are responsible for handling all tasks related to file management, DevOps, 
        and full-stack software development. You must rely on the tools provided to interact with the system.
        """,
    backstory="""
        You are an experienced software engineer with deep expertise in DevOps, Git, and system automation.
        You can write, read, modify, and delete files, interact with Git, and analyze source code effectively.

        You always use the available tools to execute your tasks, never hallucinate output, and avoid writing imaginary content. 
        If a task requires file operations, use the corresponding File Tools. For version control, always use Git tools.
        """,
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=all_tools
)

def run_crew():
    print("--- MCP Direct Agent is Ready ---")
    print("Enter your request, or type 'quit' to exit.")
    while True:
        try:
            user_prompt = input("You: ")
            if user_prompt.lower() == 'quit':
                print("Exiting...")
                break

            print("\n==================== NEW TASK START ====================")
            print(f"[CONTROLLER] User Prompt: '{user_prompt}'")
            print("[CONTROLLER] Handing task to CrewAI Agent...")
            
            task = Task(
                description=user_prompt,
                expected_output='A confirmation of the completed actions, the result of each tool execution, and the final state of any created or modified resources.',
                agent=mcp_agent 
            )

            crew = Crew(
                agents=[mcp_agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True 
            )

            try:
                print("[bold green]Prompt for Gemini:[/bold green]", task.prompt)
                result = crew.kickoff()
            except Exception as e:
                import traceback
                print("Full traceback:")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
            
            print("\n[CONTROLLER] Task complete. Final Answer from Agent:")
            print("---------------------- FINAL RESULT ----------------------")
            print(result)
            print("===================== TASK END =====================\n")

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
# if __name__ == "__main__":
#     run_crew()


# ====================================== Only for testing ========================================
@app.post("/run-task")
def run_agent_task(request: TaskRequest):
    """
    Accepts a user prompt and kicks off the CrewAI task.
    """
    print("\n==================== NEW TASK START ====================")
    print(f"[CONTROLLER] Received prompt via API: '{request.prompt}'")
    print("[CONTROLLER] Handing task to CrewAI Agent...")

    try:
        task = Task(
            description=request.prompt,
            expected_output='A confirmation of the completed actions, the result of each tool execution, and the final state of any created or modified resources.',
            agent=mcp_agent 
        )

        crew = Crew(
            agents=[mcp_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True 
        )

        try:
            print("[bold green]Prompt for Gemini:[/bold green]", task.prompt)
            result = crew.kickoff()
        except Exception as e:
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

        
        print("\n[CONTROLLER] Task complete. Final Answer from Agent:")
        print("---------------------- FINAL RESULT ----------------------")
        print(result)
        print("===================== TASK END =====================\n")
        
        return {"status": "success", "result": result}

    except Exception as e:
        print(f"An error occurred while running the crew: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
def read_root():
    return {"message": "MCP Agent Controller is running. Send POST requests to /run-task."}

# ====================================== Only for testing ========================================
