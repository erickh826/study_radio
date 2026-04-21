---
id: BUG-003
type: bug
severity: medium
status: open
files:
  - backend/app/services/llm_service.py:43
  - backend/app/services/llm_service.py:67
---

# BUG-003: `course_name` Parameter Accepted but Never Injected into Prompt

## Description
`generate_script()` accepts a `course_name: Optional[str]` parameter, and both `/upload` and `/generate` endpoints pass it through. However, `AGENT_A_PROMPT_TEMPLATE` has no `{course_name}` placeholder, and the parameter is never used when formatting the prompt.

Users supplying a course name to improve script context get no benefit — it is silently discarded.

## Affected Code

**llm_service.py:43**
```python
async def generate_script(source_text: str, course_name: Optional[str] = None) -> List[ScriptItem]:
    ...
    prompt = AGENT_A_PROMPT_TEMPLATE.format(source_text=truncated_text)
    # course_name is never used ↑
```

## Impact
- Feature advertised in the API but has no effect
- Reduces output quality: the LLM has no topic context to anchor the radio show intro/style

## Fix
Add `course_name` context to the prompt template:

```python
AGENT_A_PROMPT_TEMPLATE = """You are a scriptwriter for a popular Hong Kong radio show.
Today's topic is: {course_name}
Convert the provided text into a lively dialogue...
"""

# When formatting:
prompt = AGENT_A_PROMPT_TEMPLATE.format(
    source_text=truncated_text,
    course_name=course_name or "General Study"
)
```
