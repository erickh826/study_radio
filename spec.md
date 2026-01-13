## 3. 技術規格書 (Technical Spec)
3.1 核心技術棧 (Tech Stack)
Frontend: React (Next.js 推薦) + Tailwind CSS
原因: 處理 Audio State (暫停/播放/拼接) 需要強大的狀態管理。
Backend: Python (FastAPI)
原因: Python 是 LLM 開發的首選，LangChain/LlamaIndex 支援度最好。
Database: ChromaDB 或 FAISS (本地開發用) / Pinecone (雲端用)
用途: 儲存 PDF 內容，供 Agent B 做 RAG (Retrieval-Augmented Generation) 檢索。
3.2 AI 模型配置
LLM (大語言模型):
Model: GPT-4o 或 Claude 3.5 Sonnet
原因: 廣東話的俚語和語氣轉換需要高智商模型，小模型容易講出「書面語」。
TTS (語音合成):
Option A (高品質/貴): ElevenLabs (Multilingual v2) - 支援非常自然的中文/廣東話語氣。
Option B (高性價比): OpenAI TTS (tts-1-hd) - 速度快，廣東話尚可。
Option C (微軟): Azure AI Speech - 廣東話 (zh-HK) 支援度極佳，有多種語氣 (HiuGaai, WanLung)。推薦使用 Azure。


3.3 關鍵數據結構 (Data Structure)
主劇本 (Main Script JSON):
Agent A 不只生成文字，要生成帶有「角色標記」的 JSON，方便前端或後端切分語音。
```
[
  {
    "id": 1,
    "role": "Host_Male",
    "text": "各位聽眾大家好，今日我哋講下市場營銷。",
    "duration_est": 3.5
  },
  {
    "id": 2,
    "role": "Host_Female",
    "text": "係呀，好多人以為 Marketing 淨係賣廣告，其實錯晒！",
    "duration_est": 4.2
  }
]
```