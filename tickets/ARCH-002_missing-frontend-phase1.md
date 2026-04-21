---
id: ARCH-002
type: architecture
severity: high
status: open
phase: 1
files:
  - (missing: frontend/)
---

# ARCH-002: Frontend (React Audio Player) Not Built — Phase 1 Incomplete

## Description
Phase 1 in Action_plan.md explicitly includes building the React/Next.js frontend with an audio player. No frontend directory exists in the project. The backend API is ready but there is no UI for the user to interact with.

## Spec Reference
**Action_plan.md Phase 1 tasks:**
```
搭建 FastAPI 後端與 React 前端框架
前端播放器實作 (單純播放，無插播)
```

**spec.md:**
```
Frontend: React (Next.js 推薦) + Tailwind CSS
原因: 處理 Audio State (暫停/播放/拼接) 需要強大的狀態管理
```

## User Story Coverage Blocked
| User Story | Requirement | Blocked By |
|---|---|---|
| US-01 | Upload PDF and start hearing audio within 30-60s | No upload UI |
| US-02 | Dual-host audio playback | No audio player |
| US-03 | Type a question while audio plays | No input UI |
| US-04 | Hear interruption answer | No playback director logic |
| US-05 | Cantonese colloquial output | Partially met (backend only) |

## Required Work
1. Scaffold Next.js app: `npx create-next-app frontend --typescript --tailwind`
2. **Upload page**: file picker (PDF/TXT) + optional course name field → POST `/upload`
3. **Audio player component**:
   - Standard play/pause/seek controls
   - Display current script line (highlight by `ScriptItem.id`)
   - Show which host is speaking (Male / Female indicator)
4. **State**: loading → generating → playing states with appropriate UI feedback
5. Wire to backend at `http://localhost:8000`

## Note for Phase 2
The frontend architecture for Phase 2 (interruption logic) needs to be considered upfront:
- Main audio track state (currentTime, paused)
- Insertion queue management
- `pauseMain() → playInsertion() → resumeMain()` director pattern (system_architecture.md Phase 3)

Design Phase 1 player components to be extensible for this.
