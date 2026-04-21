---
id: DEBT-001
type: tech-debt
severity: medium
status: open
files:
  - backend/app/services/llm_service.py
  - backend/app/services/tts_service.py
  - backend/app/main.py
  - backend/app/debug_logger.py
---

# DEBT-001: Excessive Debug Logging Dominates Business Logic Code

## Description
`log_debug()` calls with `#region agent log` comment blocks are scattered throughout `llm_service.py`, `tts_service.py`, and `main.py`. Approximately 60% of the code in these files is debug instrumentation rather than business logic. This was useful during initial debugging but now significantly reduces readability and maintainability.

## Examples
`llm_service.py` contains ~25 separate `log_debug` blocks covering every intermediate step of JSON parsing. `tts_service.py` has ~15 blocks covering every Azure SDK call. The actual business logic is buried between them.

Additionally, the underlying `debug_logger.py`:
- Writes to a hardcoded local path (tracked separately in BUG-005)
- Uses a bare `except: pass` that silently swallows all errors
- Duplicates what Python's built-in `logging` module provides

## Impact
- Hard to read and review the actual flow of the code
- New developers (and future AI agents) must mentally filter out ~60% noise to understand the logic
- Increases maintenance surface: any refactor must update both logic and surrounding log calls

## Recommended Fix
Replace with Python's standard `logging` module:

```python
import logging
logger = logging.getLogger(__name__)

# Replace every log_debug(...) block with a single line:
logger.debug("Azure OpenAI config check: endpoint=%s deployment=%s", 
             bool(settings.azure_openai_endpoint), 
             bool(settings.azure_openai_deployment))
```

Configure log level via environment variable (`LOG_LEVEL=DEBUG` for dev, `INFO` for prod). Remove `debug_logger.py` entirely once migrated.

## Suggested Approach
1. Do this cleanup pass before Phase 2 development begins — adding Agent B and RAG on top of the current code will make the noise problem worse
2. Keep one `logger.info()` per major stage (upload received, script generated, audio exported) and `logger.debug()` for internals
3. Remove all `#region agent log` comment blocks
