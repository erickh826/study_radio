---
id: PERF-001
type: performance
severity: high
status: open
files:
  - backend/app/services/tts_service.py:114
---

# PERF-001: Sequential TTS Generation Will Miss the 30-60s Acceptance Criterion

## Description
TTS audio is generated one script item at a time in a `for` loop. With 30–80 dialogue turns per script (as specified), and each Azure TTS call taking ~0.5–2s of network round-trip, total generation time will be 15–160 seconds before the user hears anything. This fails US-01's acceptance criterion:

> 系統能解析文件，並在 **30-60 秒內**開始播放音頻

## Affected Code

**tts_service.py:114**
```python
for idx, item in enumerate(script):
    ...
    result = synthesizer.speak_text_async(item.text).get()  # sequential + blocking
    audio_segments.append(segment)

# Only exports after ALL items done
final_audio = sum(audio_segments)
final_audio.export(str(output_path), format="mp3")
```

## Impact
- For a 50-turn script at ~1s/call = ~50s before any audio reaches the user
- Worse-case 80 turns at 2s/call = 160s — well outside the 60s target
- Compounded by BUG-002 (blocking `.get()` on the event loop)

## Fix Option A — Concurrent Generation (Recommended for Phase 1)
Fix BUG-002 first (wrap `.get()` in `run_in_executor`), then gather all items concurrently:

```python
import asyncio

async def _synthesize_item(item, speech_key, region):
    # create synthesizer, call run_in_executor
    ...

segments_with_index = await asyncio.gather(
    *[_synthesize_item(item, ...) for item in script]
)
# Sort by original index to preserve order before concatenating
```

## Fix Option B — Streaming (Phase 3 as per Action_plan.md)
Stream the first few audio segments to the frontend as soon as they are ready, so playback can start before all segments are generated. This is the spec's Phase 3 goal but may need to be pulled earlier if Option A still misses the 60s target for large documents.
