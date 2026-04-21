---
id: BUG-002
type: bug
severity: high
status: open
files:
  - backend/app/services/tts_service.py:165
---

# BUG-002: Blocking Synchronous Call Inside Async Function Blocks Event Loop

## Description
`_generate_azure_tts()` is an `async` function but calls the Azure Speech SDK's `.get()` method directly, which is a blocking synchronous call. This freezes the entire FastAPI event loop for the duration of every TTS synthesis — meaning no other requests can be processed while audio is being generated.

With 30–80 script turns per job, this blocks the server for potentially minutes at a time.

## Affected Code

**tts_service.py:165**
```python
# Bug — .get() is blocking, runs on the event loop thread
result = synthesizer.speak_text_async(item.text).get()
```

## Impact
- Entire FastAPI server is unresponsive during TTS generation
- Under any concurrent load, requests will time out
- Violates async contract; subtle in development but severe in any real usage

## Fix
Wrap the blocking call in `asyncio.get_event_loop().run_in_executor(None, ...)` to offload it to a thread pool:

```python
import asyncio

loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    None,
    lambda: synthesizer.speak_text_async(item.text).get()
)
```

## Further Improvement
Consider running all script items concurrently with `asyncio.gather()` after applying the executor fix, which would dramatically reduce total audio generation time for 30–80 turns.
