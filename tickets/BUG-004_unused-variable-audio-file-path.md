---
id: BUG-004
type: bug
severity: low
status: open
files:
  - backend/app/main.py:149
  - backend/app/main.py:182
---

# BUG-004: Return Value of `generate_audio()` Assigned but Never Used

## Description
In both `/upload` and `/generate` endpoints, the return value of `generate_audio()` is captured into `audio_file_path` but never referenced. The audio URL is instead hardcoded as a string template `/static/audio/{job_id}.mp3`.

## Affected Code

**main.py:149 and main.py:182**
```python
audio_file_path = await generate_audio(script, job_id)  # return value ignored
audio_url = f"/static/audio/{job_id}.mp3"               # hardcoded instead
```

## Impact
- Currently harmless because the hardcoded path happens to be correct
- Creates a hidden coupling: if `audio_storage_path` config or the static mount path ever changes, `generate_audio()` would write to a different location than the URL points to, silently serving a 404
- Misleads readers into thinking `audio_file_path` is used somewhere

## Fix
Derive `audio_url` from the actual returned path, or remove the assignment:

```python
audio_file_path = await generate_audio(script, job_id)
# Convert absolute storage path to a URL-relative path
audio_url = "/" + Path(audio_file_path).relative_to(Path("static").parent).as_posix()
```

Or at minimum, remove the unused variable:
```python
await generate_audio(script, job_id)
audio_url = f"/static/audio/{job_id}.mp3"
```
