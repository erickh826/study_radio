# Tickets

Issues found during Phase 1 code review (2026-04-21).

## Bugs

| ID | Severity | File(s) | Summary |
|---|---|---|---|
| [BUG-001](BUG-001_wrong-openai-client-class.md) | High | llm_service.py, tts_service.py | ~~`AsyncAzureOpenAI` used instead of `AsyncOpenAI`~~ — **closed** (dead code deleted; Azure-only) |
| [BUG-002](BUG-002_blocking-tts-call-in-async.md) | High | tts_service.py | ~~Blocking `.get()` call freezes event loop~~ — **closed** (run_in_executor + asyncio.gather) |
| [BUG-003](BUG-003_course-name-param-silently-dropped.md) | Medium | llm_service.py:43,67 | `course_name` accepted but never injected into LLM prompt |
| [BUG-004](BUG-004_unused-variable-audio-file-path.md) | Low | main.py:149,182 | Return value of `generate_audio()` assigned but never used |
| [BUG-005](BUG-005_hardcoded-debug-log-path.md) | Medium | debug_logger.py:8 | Log path hardcoded to a developer's local machine path |

## Architecture Gaps

| ID | Severity | Phase | Summary |
|---|---|---|---|
| [ARCH-001](ARCH-001_missing-vector-db-phase1.md) | High | 1 | ~~Vector DB embedding missing from upload pipeline~~ — **closed** (ChromaDB service added, wired into /upload) |
| [ARCH-002](ARCH-002_missing-frontend-phase1.md) | High | 1 | No frontend built — all US-01 through US-04 acceptance criteria unverifiable |

## Performance

| ID | Severity | File(s) | Summary |
|---|---|---|---|
| [PERF-001](PERF-001_sequential-tts-generation-too-slow.md) | High | tts_service.py | ~~Sequential TTS for 30-80 turns will exceed the 60s US-01 criterion~~ — **closed** (concurrent via asyncio.gather) |

## Tech Debt

| ID | Severity | File(s) | Summary |
|---|---|---|---|
| [DEBT-001](DEBT-001_excessive-debug-logging.md) | Medium | llm_service.py, tts_service.py, main.py | ~60% of code is debug logging; should be replaced with standard `logging` |

## Suggested Fix Order

1. **BUG-002** — unblock the event loop (risk: server hangs under any load)
2. **BUG-001** — fix broken OpenAI fallback path
3. **BUG-003** — inject `course_name` into prompt (easy, improves output quality)
4. **PERF-001** — concurrent TTS (depends on BUG-002 fix)
5. **ARCH-001** — add Vector DB embedding (prerequisite for Phase 2)
6. **ARCH-002** — build frontend (Phase 1 completion)
7. **DEBT-001** — logging cleanup (best done before Phase 2 adds more code)
8. **BUG-004 / BUG-005** — low-risk cleanup
