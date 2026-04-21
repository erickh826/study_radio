---
id: BUG-005
type: bug
severity: medium
status: open
files:
  - backend/app/debug_logger.py:8
---

# BUG-005: Debug Logger Hardcodes a Developer's Local Filesystem Path

## Description
`debug_logger.py` hardcodes an absolute path to a specific developer's machine:

```python
LOG_PATH = "/Users/kahochow/poc/.cursor/debug.log"
```

On any other machine (CI, staging, Docker container, another developer's laptop), this path does not exist. The logger silently swallows the `FileNotFoundError` (due to the bare `except Exception: pass`), so all debug logs are silently dropped everywhere except on that one machine.

## Impact
- Debug logging is completely non-functional in all non-local environments
- The bare `except` hides the failure, making it look like logging is working
- Path leaks a developer's username and local directory structure

## Fix
Use a configurable path via settings or environment variable, falling back to a project-relative path:

```python
import os

LOG_PATH = os.environ.get(
    "DEBUG_LOG_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "debug.log")
)
```

Or replace the custom logger entirely with Python's standard `logging` module, which is configurable via env/config without code changes.
