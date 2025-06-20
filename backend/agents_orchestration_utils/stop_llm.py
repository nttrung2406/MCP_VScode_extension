def sanitize_llm_config(config: dict) -> dict:
    allowed_keys = {
        "model", "config_list", "api_key", "api_type", "api_base",
        "api_version", "temperature", "max_tokens", "seed", "request_timeout",
        "functions", "function_call", "tool_choice"
    }
    cleaned = {k: v for k, v in config.items() if k in allowed_keys}
    dropped = {k: v for k, v in config.items() if k not in allowed_keys}
    if dropped:
        print(f"[WARN] Dropped invalid LLM config keys: {list(dropped.keys())}")
    return cleaned