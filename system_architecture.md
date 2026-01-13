## 2. 系統流程圖 (System Architecture & Flow)
這裡展示核心的 「雙軌制 (Two-Track)」 邏輯。
sequenceDiagram
    participant User as 👤 用戶 (Frontend)
    participant Director as 🎬 導播系統 (Backend Logic)
    participant AgentA as 🤖 Agent A (編劇/主講)
    participant AgentB as 🤓 Agent B (插播/問答)
    participant TTS as 🗣️ TTS Service
    participant DB as 🗄️ Vector DB (RAG)

    Note over User, DB: === 階段一：節目生成 (Initialization) ===
    User->>Director: 上傳 PDF 文件
    Director->>DB: 儲存並向量化文件 (Embeddings)
    Director->>AgentA: Prompt: "將內容轉為廣東話雙人廣播劇本"
    AgentA-->>Director: 回傳完整對話 Script (JSON格式)
    Director->>TTS: 請求生成主音軌 (Main_Track.mp3)
    TTS-->>Director: 回傳主音軌
    Director-->>User: 開始播放 Main_Track 🎵

    Note over User, DB: === 階段二：插播互動 (Interruption) ===
    User->>Director: 輸入問題："什麼是 ROI？"
    Director->>User: UI 顯示 "主持人正在看你的問題..." (主音軌繼續播放)
    
    par 後台處理
        Director->>AgentB: 檢索 DB + 用戶問題
        AgentB-->>Director: 生成插播回答 Script (口語化廣東話)
        Director->>TTS: 請求生成插播音軌 (QnA_Clip.mp3)
        TTS-->>Director: 回傳插播音軌
    end

    Note over User, Director: === 階段三：無縫拼接 (The Mix) ===
    Director->>User: 指令: 等當前句子結束，暫停 Main_Track
    User->>User: ⏸️ 暫停 Main_Track (記錄時間戳 T1)
    Director-->>User: ▶️ 播放 QnA_Clip.mp3
    User->>User: (播放回答: "哈哈，Peter問得好...")
    User->>User: ✅ QnA_Clip 播放結束
    User->>User: ▶️ 恢復 Main_Track (從 T1 繼續)