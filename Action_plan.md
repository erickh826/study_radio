4. Action Plan (執行計畫)
建議分為三個 Sprint (衝刺週期) 來完成 POC。

Phase 1: 基礎廣播功能 (The Radio) - 預計 3-5 天
目標: 上傳 PDF，聽到雙人廣東話講解。
Tasks:
搭建 FastAPI 後端與 React 前端框架。
實作 PDF 解析 (PyPDF2) 與 Vector DB 寫入。
Prompt Engineering (Agent A): 調試出最自然的「廣東話電台對話」Prompt。
整合 TTS，將對話轉為 MP3。
前端播放器實作 (單純播放，無插播)。
Phase 2: 實時插播邏輯 (The Interrupter) - 預計 5-7 天
目標: 能夠打字提問，並聽到回答插入。
Tasks:
Prompt Engineering (Agent B): 設計「簡短回答 + 回歸話題」的 Prompt。
實作 RAG 檢索邏輯 (根據問題找答案)。
前端導播邏輯 (關鍵):
監聽主音頻播放進度。
實作 pauseMain() -> playInsertion() -> resumeMain() 的 JavaScript 邏輯。
處理「句點檢測」 (不要在字中間切斷，最好依賴 JSON 的句子 ID 切換)。
Phase 3: 優化與修飾 (Polish) - 預計 3 天
目標: 降低延遲，提升體驗。
Tasks:
Streaming Response: 讓 TTS 支援串流播放，減少等待時間。
UI 優化: 加入音波圖 (Visualizer) 或當前字幕高亮。
背景音樂 (BGM): (Optional) 在後端混音時加入輕微的 Lo-Fi 背景音樂，提升電台感。