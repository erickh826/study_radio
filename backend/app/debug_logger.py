"""
Debug logging utility for runtime debugging
"""
import json
import os
import time

LOG_PATH = "/Users/kahochow/poc/.cursor/debug.log"


def log_debug(session_id: str, run_id: str, hypothesis_id: str, location: str, message: str, data: dict):
    """
    Log debug information to NDJSON file.
    
    Args:
        session_id: Debug session identifier
        run_id: Run identifier (e.g., "run1", "post-fix")
        hypothesis_id: Hypothesis identifier (e.g., "A", "B", "C")
        location: File and line location (e.g., "main.py:73")
        message: Log message description
        data: Dictionary of data to log
    """
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": session_id,
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "timestamp": int(time.time() * 1000)
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        # Silently fail if logging fails
        pass
