import os
import requests
from google import genai
# import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
client = genai.Client()

class FlexibleLLMClient:
    def __init__(self):
        self.provider = LLM_PROVIDER.lower() if LLM_PROVIDER else "ollama"

        if self.provider == "ollama":
            self.base_url = os.getenv("OLLAMA_BASE_URL")
            self.model_name = os.getenv("MODEL")
            if not self.base_url or not self.model_name:
                raise ValueError("OLLAMA_BASE_URL and MODEL must be set for the ollama provider.")
        
        elif self.provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY_CODE")
            gemini_model_name = os.getenv("GEMINI_MODEL")
            if not api_key or not gemini_model_name:
                raise ValueError("GEMINI_API_KEY_CODE and GEMINI_MODEL must be set for the gemini provider.")
            
            self.client = genai.Client(api_key=api_key)
            self.model_name = gemini_model_name
        
        elif self.provider == "claude":
            self.api_key = os.getenv("CLAUDE_API_KEY")
            claude_model_name = os.getenv("CLAUDE_MODEL")
            self.model_name = claude_model_name
            if not self.api_key:
                raise ValueError("CLAUDE_API_KEY must be set for the claude provider.")
        
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.provider}")

    def generate_response(self, prompt: str, system_prompt: str) -> str:
        """
        Takes a user prompt and a system prompt, formats them,
        and calls the appropriate LLM chat method.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages)

    def chat(self, messages: list[dict]) -> str:
        """
        Internal method to handle the actual API call to the selected provider.
        """
        system_prompt = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                user_messages.append(msg)

        if self.provider == "ollama":
            payload = {
                "model": self.model_name,
                "messages": messages, 
                "stream": False,
                "options": { "temperature": 0.5, "top_p": 0.9 },
            }
            res = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=180)
            res.raise_for_status()
            return res.json().get("message", {}).get("content", "")

        elif self.provider == "gemini":
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_messages,
            )
            return response.text
            
        elif self.provider == "claude":
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": self.model_name,
                "max_tokens": 4096,
                "temperature": 0.5,
                "system": system_prompt,
                "messages": user_messages,
            }
            res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=90)
            res.raise_for_status()
            return res.json()["content"][0]["text"]

        else:
            raise ValueError("Unknown provider")