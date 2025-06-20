import requests
import json
import uuid
import threading
from typing import Dict, Any

class MCP_SSE_Connection:
    def __init__(self, server_base_url: str):
        self.server_base_url = server_base_url.rstrip('/')
        self._session = requests.Session()
        self._message_url = None
        self._listener_thread = None
        self._is_connected = False
        self._pending_requests: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._url_received_event = threading.Event()

    def _send_rpc_notification(self, method: str, params: dict):
        """Sends a JSON-RPC notification (no ID, no response expected)."""
        message_to_send = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        print(f"[MCPClient] Sending Notification -> Method: {method}")
        post_response = self._session.post(self._message_url, json=message_to_send, timeout=180)
        post_response.raise_for_status()

    def _send_rpc_request(self, method: str, params: dict, timeout: int = 180) -> Any:
        message_id = str(uuid.uuid4())
        event = threading.Event()
        self._pending_requests[message_id] = {"event": event, "response": None}

        message_to_send = {
            "method": "notifications/initialized",
            "jsonrpc": "2.0", 
            "method": method,             
            "params": params, 
            "id": message_id
        }

        print(f"[MCPClient] Sending RPC Request -> Method: {method}, ID: {message_id}")
        post_response = self._session.post(self._message_url, json=message_to_send, timeout=180)
        post_response.raise_for_status()

        event_was_set = event.wait(timeout=timeout)
        response_data = self._pending_requests.pop(message_id, None)

        if not event_was_set:
            raise TimeoutError(f"Request '{method}' (ID: {message_id}) timed out.")
        
        return response_data.get("response") if response_data else None

    def connect(self):
        """Performs the full, stateful, two-part MCP handshake."""
        with self._lock:
            if self._is_connected:
                return

            print(f"[MCPClient] Full Connection & Handshake sequence started...")
            try:
                self._url_received_event.clear()
                response = self._session.get(f"{self.server_base_url}/mcp-sse", headers={"Accept": "text/event-stream"}, stream=True, timeout=10)
                response.raise_for_status()
                self._listener_thread = threading.Thread(target=self._listen_for_responses, args=(response,), daemon=True)
                self._listener_thread.start()
                if not self._url_received_event.wait(timeout=180):
                    raise ConnectionError("Server did not provide a message URL within 10 seconds.")
                
                print("[MCPClient] Performing initialization handshake (Part 1/2)...")
                init_params = {
                    "protocolVersion": "1.0", 
                    "capabilities": {}, 
                    "clientInfo": 
                        {
                            "name": "autogen-mcp-client", 
                            "version": "0.1.0"
                        }
                    }
                init_response = self._send_rpc_request("initialize", init_params)
                print(f"[MCPClient] Handshake Part 1 successful. Server capabilities: {init_response}")

                print("[MCPClient] Finalizing handshake with 'initialized' notification (Part 2/2)...")
                self._send_rpc_notification("notifications/initialized", {})

                self._is_connected = True
                print(f"[MCPClient] Connection is now fully initialized and ready.")

            except Exception as e:
                print(f"[MCPClient] Connection failed during handshake: {e}")
                self._is_connected = False
                raise ConnectionError(f"Failed to initialize connection: {e}") from e

    def _listen_for_responses(self, response: requests.Response):
        print("[MCPClient Listener] Started.")
        try:
            for line in response.iter_lines():
                if not line.startswith(b'data:'): continue
                message_data_bytes = line[len(b'data:'):].strip()
                if not message_data_bytes: continue

                if not self._url_received_event.is_set():
                    relative_url = message_data_bytes.decode('utf-8')
                    self._message_url = f"{self.server_base_url}{relative_url}"
                    self._url_received_event.set()
                    continue

                try:
                    message = json.loads(message_data_bytes)
                    correlation_id = message.get("id")
                    if correlation_id in self._pending_requests:
                        request_info = self._pending_requests[correlation_id]
                        request_info["response"] = message.get("result") 
                        request_info["event"].set()
                except json.JSONDecodeError:
                    print(f"[MCPClient Listener] Received non-JSON data after handshake: {message_data_bytes}")
        except Exception as e:
            print(f"[MCPClient Listener] Error in listener thread: {e}")
        finally:
            print("[MCPClient Listener] Stopped.")
            self._is_connected = False
            
    def call_tool(self, tool_name: str, payload: dict) -> str:
        try:
            if not self._is_connected:
                self.connect()
            tool_params = {"name": tool_name, "arguments": payload}
            result = self._send_rpc_request("tools/call", tool_params)
            return str(result)
        except Exception as e:
            error_message = f"An error occurred during tool call '{tool_name}': {e}"
            print(f"[MCPClient] FAILURE: {error_message}")
            self._is_connected = False 
            return error_message