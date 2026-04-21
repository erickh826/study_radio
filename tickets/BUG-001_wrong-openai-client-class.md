---
id: BUG-001
type: bug
severity: high
status: open
files:
  - backend/app/services/llm_service.py:234
  - backend/app/services/tts_service.py:297
---

# BUG-001: Wrong OpenAI Client Class Used for Regular OpenAI Provider

## Description
Both `_call_openai()` and `_generate_openai_tts()` import and use `AsyncAzureOpenAI` instead of `AsyncOpenAI`. `AsyncAzureOpenAI` requires Azure-specific parameters (`azure_endpoint`, `api_version`, `azure_deployment`). When `llm_provider = "openai"` or `tts_provider = "openai"`, these functions will fail at runtime.

## Affected Code

**llm_service.py:234**
```python
# Bug
from openai import AsyncAzureOpenAI
client = AsyncAzureOpenAI(api_key=settings.openai_api_key)

# Fix
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=settings.openai_api_key)
```

**tts_service.py:297**
```python
# Bug
from openai import AsyncAzureOpenAI
client = AsyncAzureOpenAI(api_key=settings.openai_api_key)

# Fix
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=settings.openai_api_key)
```

## Impact
Any user/environment using standard OpenAI (not Azure) for LLM or TTS will get an immediate runtime error. The fallback path is completely broken.

## Fix
Replace `AsyncAzureOpenAI` with `AsyncOpenAI` in both functions. No other changes needed.
