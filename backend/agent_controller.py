import os
import autogen
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agents_orchestration_utils.stop_llm import sanitize_llm_config
from agents_orchestration_utils.autogen_config import get_autogen_config

# --- Configuration and Setup ---
load_dotenv()
google_api_key = os.environ.get("GEMINI_API_KEY")
gemini_model = os.environ.get("GEMINI_MODEL")

if not google_api_key:
    raise RuntimeError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")


config_list = [
    {
        "model": gemini_model,
        "api_key": google_api_key,
        "api_type": "google"
    }
]
   # For Ollama 
   # {
   #     "model": model,
   #     "api_type": "ollama",
   #     "client_host": "http://ollama:11434/",
   #     "max_tokens": 512,
   #     "native_tool_calls": True,
   #     "hide_tools": "if_any_run"
   # }

llm_config = {
    "config_list": config_list,
    "temperature": 0.5,
    "seed": None,
    "debug": True
}

sanitized_llm_config = sanitize_llm_config(llm_config)

app = FastAPI(
    title="MCP Agent Controller API",
    description="An API to trigger the AutoGen agent group chat for the VS Code Extension."
)

origins = ["*"] 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskRequest(BaseModel):
    prompt: str

# --- API Endpoint ---
@app.post("/run-task")
def run_agent_task(request: TaskRequest):
    """
    Accepts a user prompt from the UI and kicks off the AutoGen Group Chat.
    """
    print("\n==================== NEW AUTOGEN TASK START (FROM UI) ====================")
    print(f"[CONTROLLER] Received prompt via API: '{request.prompt}'")
    print("[CONTROLLER] Initializing AutoGen Group Chat...")

    try:
        user_proxy, assistant, context_handling = get_autogen_config(sanitized_llm_config)

        groupchat = autogen.GroupChat(
            agents=[user_proxy, assistant],
            messages=[],
            max_round=20,
            speaker_selection_method="round_robin",
            allow_repeat_speaker=False,
        )
        
        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config=sanitized_llm_config
        )
        
        context_handling.add_to_agent(manager)

        user_proxy.initiate_chat(
            manager,
            message=request.prompt,
        )

        result = list(groupchat.messages)
        print("\n===================== TASK END (FROM UI) =====================\n")
        
        return {"status": "success", "result": result}

    except Exception as e:
        print(f"[CONTROLLER] An error occurred during the autogen chat: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/")
def read_root():
    return {"message": "MCP Agent Controller is running."}
