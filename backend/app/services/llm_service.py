"""
LLM service for script generation (Agent A)
"""
import json
from typing import List, Optional
from app.models import ScriptItem
from app.config import settings
from app.debug_logger import log_debug


# Agent A Prompt from prompt_design.md
AGENT_A_PROMPT_TEMPLATE = """You are a scriptwriter for a popular Hong Kong radio show.
Convert the provided text into a lively dialogue between two hosts: 'Ah Ming' (Male, funny, asks distinct questions) and 'Miss Chan' (Female, professional, explains concepts).

Rules:
1. Use pure Cantonese (Traditional Chinese) with Hong Kong slang.
2. Keep the tone casual, like a morning talk show.
3. Split the content into 30-80 short dialogue turns, each 1-2 sentences.
4. Alternate between Host_Male (Ah Ming) and Host_Female (Miss Chan) naturally.
5. Output ONLY valid JSON array format, no markdown, no extra text.

Output format (JSON array):
[
  {{
    "id": 1,
    "role": "Host_Male",
    "text": "各位聽眾大家好，今日我哋講下市場營銷。",
    "duration_est": 3.5
  }},
  {{
    "id": 2,
    "role": "Host_Female",
    "text": "係呀，好多人以為 Marketing 淨係賣廣告，其實錯晒！",
    "duration_est": 4.2
  }}
]

Source text to convert:
{source_text}
"""


async def generate_script(source_text: str, course_name: Optional[str] = None) -> List[ScriptItem]:
    """
    Generate radio script using LLM (Agent A).
    
    Args:
        source_text: Source text content
        course_name: Optional course name for context
    
    Returns:
        List of ScriptItem objects
    """
    # Limit input text to leave room for prompt template (prompt template is ~500 chars)
    # Azure OpenAI has token limits, so we need to be more conservative
    max_source_length = 6000  # Reduced from 8000 to account for prompt template overhead
    truncated_text = source_text[:max_source_length]
    
    # #region agent log
    log_debug("debug-session", "run1", "I", "llm_service.py:54", "Text truncation", {
        "original_length": len(source_text),
        "truncated_length": len(truncated_text),
        "was_truncated": len(source_text) > max_source_length
    })
    # #endregion
    
    prompt = AGENT_A_PROMPT_TEMPLATE.format(source_text=truncated_text)
    
    if settings.llm_provider == "openai":
        script_json = await _call_openai(prompt)
    elif settings.llm_provider == "azure_openai":
        script_json = await _call_azure_openai(prompt)
    elif settings.llm_provider == "anthropic":
        script_json = await _call_anthropic(prompt)
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    
    # Parse and validate JSON
    # #region agent log
    log_debug("debug-session", "run1", "H", "llm_service.py:65", "About to parse script_json", {
        "script_json_length": len(script_json),
        "script_json_preview": script_json[:500] if script_json else None,
        "starts_with_bracket": script_json.strip().startswith("[") if script_json else False,
        "starts_with_brace": script_json.strip().startswith("{") if script_json else False
    })
    # #endregion
    
    try:
        script_data = json.loads(script_json)
        
        # #region agent log
        log_debug("debug-session", "run1", "H", "llm_service.py:74", "script_data parsed", {
            "script_data_type": type(script_data).__name__,
            "is_list": isinstance(script_data, list),
            "is_dict": isinstance(script_data, dict),
            "dict_keys": list(script_data.keys()) if isinstance(script_data, dict) else None,
            "list_length": len(script_data) if isinstance(script_data, list) else None
        })
        # #endregion
        
        # Handle case where response is wrapped in an object
        if isinstance(script_data, dict):
            # Check for error messages first
            if "error" in script_data:
                error_msg = script_data["error"]
                # #region agent log
                log_debug("debug-session", "run1", "H", "llm_service.py:88", "LLM returned error", {
                    "error_message": error_msg
                })
                # #endregion
                raise ValueError(f"LLM error: {error_msg}")
            
            # Try common keys that might contain the array
            for key in ["script", "data", "result", "output", "content"]:
                if key in script_data and isinstance(script_data[key], list):
                    # #region agent log
                    log_debug("debug-session", "run1", "H", "llm_service.py:98", f"Found array in dict key: {key}", {
                        "key": key,
                        "array_length": len(script_data[key])
                    })
                    # #endregion
                    script_data = script_data[key]
                    break
        
        if not isinstance(script_data, list):
            # #region agent log
            log_debug("debug-session", "run1", "H", "llm_service.py:108", "script_data is not a list after processing", {
                "script_data_type": type(script_data).__name__,
                "script_data_value": str(script_data)[:500]
            })
            # #endregion
            raise ValueError(f"LLM response is not a JSON array. Got: {type(script_data).__name__}")
        
        # Validate and fix items: ensure all have 'id' field
        # #region agent log
        log_debug("debug-session", "run1", "L", "llm_service.py:134", "Validating script items before creation", {
            "total_items": len(script_data),
            "sample_item_keys": list(script_data[0].keys()) if script_data and isinstance(script_data[0], dict) else None
        })
        # #endregion
        
        fixed_items = []
        items_missing_id = []
        for idx, item in enumerate(script_data):
            if not isinstance(item, dict):
                # #region agent log
                log_debug("debug-session", "run1", "L", "llm_service.py:142", "Skipping non-dict item", {
                    "index": idx,
                    "item_type": type(item).__name__,
                    "item_value": str(item)[:100]
                })
                # #endregion
                continue
            
            # Auto-assign ID if missing (use 1-based index)
            if "id" not in item or item.get("id") is None:
                item["id"] = idx + 1
                items_missing_id.append(idx + 1)
                # #region agent log
                log_debug("debug-session", "run1", "L", "llm_service.py:152", "Auto-assigned ID to item", {
                    "index": idx,
                    "assigned_id": idx + 1,
                    "item_keys": list(item.keys())
                })
                # #endregion
            
            fixed_items.append(item)
        
        # #region agent log
        if items_missing_id:
            log_debug("debug-session", "run1", "L", "llm_service.py:161", "Items missing ID were auto-fixed", {
                "items_fixed": len(items_missing_id),
                "fixed_indices": items_missing_id[:10]  # Log first 10
            })
        # #endregion
        
        # Create ScriptItem objects
        script_items = []
        validation_errors = []
        for idx, item in enumerate(fixed_items):
            try:
                script_items.append(ScriptItem(**item))
            except Exception as validation_error:
                # #region agent log
                log_debug("debug-session", "run1", "L", "llm_service.py:173", "Validation error for item", {
                    "index": idx,
                    "item_id": item.get("id"),
                    "item_keys": list(item.keys()),
                    "error_type": type(validation_error).__name__,
                    "error_message": str(validation_error)
                })
                # #endregion
                validation_errors.append((idx, str(validation_error)))
        
        if validation_errors:
            # #region agent log
            log_debug("debug-session", "run1", "H", "llm_service.py:115", "Error parsing script", {
                "error_type": "ValidationError",
                "error_message": f"{len(validation_errors)} items failed validation",
                "validation_errors": validation_errors[:5],  # First 5 errors
                "script_json_preview": script_json[:500] if script_json else None
            })
            # #endregion
            raise ValueError(f"Error parsing script: {len(validation_errors)} items failed validation. First error: {validation_errors[0][1]}")
        
        # #region agent log
        log_debug("debug-session", "run1", "H", "llm_service.py:103", "Script items created successfully", {
            "script_items_count": len(script_items),
            "items_fixed": len(items_missing_id)
        })
        # #endregion
        return script_items
    except json.JSONDecodeError as e:
        # #region agent log
        log_debug("debug-session", "run1", "H", "llm_service.py:108", "JSON decode error in generate_script", {
            "error_message": str(e),
            "script_json_preview": script_json[:500] if script_json else None
        })
        # #endregion
        raise ValueError(f"Invalid JSON from LLM: {e}")
    except Exception as e:
        # #region agent log
        log_debug("debug-session", "run1", "H", "llm_service.py:115", "Error parsing script", {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "script_json_preview": script_json[:500] if script_json else None
        })
        # #endregion
        raise ValueError(f"Error parsing script: {e}")


async def _call_openai(prompt: str) -> str:
    """Call OpenAI API"""
    from openai import AsyncAzureOpenAI
    
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured")
    
    client = AsyncAzureOpenAI(api_key=settings.openai_api_key)
    
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"} if "gpt-4" in settings.llm_model.lower() else None
    )
    
    content = response.choices[0].message.content
    
    # If response_format was used, wrap array in object, otherwise extract array
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "script" in parsed:
            return json.dumps(parsed["script"])
        elif isinstance(parsed, list):
            return content
        else:
            # Try to find array in response
            return content
    except:
        return content


async def _call_azure_openai(prompt: str) -> str:
    """Call Azure OpenAI API"""
    from openai import AsyncAzureOpenAI
    
    # #region agent log
    log_debug("debug-session", "run1", "A", "llm_service.py:117", "Azure OpenAI config check entry", {
        "has_api_key": bool(settings.azure_openai_api_key),
        "has_endpoint": bool(settings.azure_openai_endpoint),
        "has_deployment": bool(settings.azure_openai_deployment)
    })
    # #endregion
    
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        raise ValueError("Azure OpenAI API key or endpoint not configured")
    
    if not settings.azure_openai_deployment:
        raise ValueError("Azure OpenAI deployment name not configured")
    
    # #region agent log
    log_debug("debug-session", "run1", "B", "llm_service.py:128", "Azure OpenAI config values BEFORE client creation", {
        "endpoint": settings.azure_openai_endpoint,
        "deployment": settings.azure_openai_deployment,
        "api_version": settings.azure_openai_api_version,
        "endpoint_length": len(settings.azure_openai_endpoint),
        "deployment_length": len(settings.azure_openai_deployment),
        "endpoint_ends_with_slash": settings.azure_openai_endpoint.endswith("/"),
        "api_key_prefix": settings.azure_openai_api_key[:10] + "..." if settings.azure_openai_api_key else None
    })
    # #endregion
    
    # Fix: Remove trailing slash from endpoint (SDK handles it)
    endpoint_clean = settings.azure_openai_endpoint.rstrip('/')
    
    # #region agent log
    log_debug("debug-session", "run1", "B", "llm_service.py:165", "Endpoint after cleaning", {
        "original_endpoint": settings.azure_openai_endpoint,
        "cleaned_endpoint": endpoint_clean,
        "was_modified": endpoint_clean != settings.azure_openai_endpoint
    })
    # #endregion
    
    # Azure OpenAI uses different base URL and API version
    client = AsyncAzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=endpoint_clean
    )
    
    # #region agent log
    log_debug("debug-session", "run1", "C", "llm_service.py:138", "Client created, about to call API", {
        "model_param": settings.azure_openai_deployment,
        "prompt_length": len(prompt),
        "response_format": "json_object" if "gpt-4" in settings.azure_openai_deployment.lower() else None
    })
    # #endregion
    
    try:
        response = await client.chat.completions.create(
            model=settings.azure_openai_deployment,  # Use deployment name, not model name
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            # Don't use json_object format - it forces object output, but we want an array
            # The prompt should guide the format instead
            response_format=None
        )
        # #region agent log
        log_debug("debug-session", "run1", "D", "llm_service.py:150", "API call successful", {
            "response_received": True,
            "content_length": len(response.choices[0].message.content) if response.choices else 0
        })
        # #endregion
    except Exception as api_error:
        # #region agent log
        log_debug("debug-session", "run1", "E", "llm_service.py:155", "API call failed - error details", {
            "error_type": type(api_error).__name__,
            "error_message": str(api_error),
            "error_repr": repr(api_error),
            "has_status_code": hasattr(api_error, "status_code"),
            "status_code": getattr(api_error, "status_code", None),
            "has_response": hasattr(api_error, "response"),
            "response_body": str(getattr(api_error, "response", {}))
        })
        # #endregion
        raise
    
    content = response.choices[0].message.content
    
    # #region agent log
    log_debug("debug-session", "run1", "G", "llm_service.py:200", "Raw response content received", {
        "content_length": len(content),
        "content_preview": content[:500] if content else None,
        "content_type": type(content).__name__,
        "starts_with_bracket": content.strip().startswith("[") if content else False,
        "starts_with_brace": content.strip().startswith("{") if content else False,
        "contains_script_key": '"script"' in content if content else False
    })
    # #endregion
    
    # Same parsing logic as regular OpenAI
    try:
        parsed = json.loads(content)
        
        # #region agent log
        log_debug("debug-session", "run1", "G", "llm_service.py:212", "JSON parsed successfully", {
            "parsed_type": type(parsed).__name__,
            "is_dict": isinstance(parsed, dict),
            "is_list": isinstance(parsed, list),
            "dict_keys": list(parsed.keys()) if isinstance(parsed, dict) else None,
            "list_length": len(parsed) if isinstance(parsed, list) else None
        })
        # #endregion
        
        if isinstance(parsed, dict) and "script" in parsed:
            # #region agent log
            log_debug("debug-session", "run1", "G", "llm_service.py:220", "Extracting script from dict", {
                "script_type": type(parsed["script"]).__name__,
                "script_length": len(parsed["script"]) if isinstance(parsed["script"], list) else None
            })
            # #endregion
            return json.dumps(parsed["script"])
        elif isinstance(parsed, list):
            return content
        else:
            # #region agent log
            log_debug("debug-session", "run1", "G", "llm_service.py:228", "Unexpected parsed type", {
                "parsed_type": type(parsed).__name__,
                "parsed_value": str(parsed)[:200]
            })
            # #endregion
            return content
    except json.JSONDecodeError as e:
        # #region agent log
        log_debug("debug-session", "run1", "G", "llm_service.py:234", "JSON decode error", {
            "error_message": str(e),
            "content_preview": content[:500] if content else None
        })
        # #endregion
        return content
    except Exception as e:
        # #region agent log
        log_debug("debug-session", "run1", "G", "llm_service.py:240", "Unexpected error in parsing", {
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        # #endregion
        return content


async def _call_anthropic(prompt: str) -> str:
    """Call Anthropic (Claude) API"""
    from anthropic import AsyncAnthropic
    
    if not settings.anthropic_api_key:
        raise ValueError("Anthropic API key not configured")
    
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=4000,
        messages=[
            {"role": "user", "content": prompt}
        ],
        system="You are a helpful assistant that outputs only valid JSON arrays. No markdown, no code blocks."
    )
    
    content = response.content[0].text
    
    # Clean up markdown code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    return content

