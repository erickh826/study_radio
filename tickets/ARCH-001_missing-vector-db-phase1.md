---
id: ARCH-001
type: architecture
severity: high
status: open
phase: 1
files:
  - backend/app/main.py
  - backend/app/services/ (missing: vector_db_service.py)
---

# ARCH-001: Vector DB Embedding Missing from Phase 1 Upload Pipeline

## Description
The system architecture specifies that when a user uploads a PDF, the backend should store and vectorize the content (Embeddings) into a Vector DB (ChromaDB or FAISS locally) as part of Phase 1 initialization. This step is entirely missing.

## Spec Reference
**system_architecture.md:**
```
User->>Director: 上傳 PDF 文件
Director->>DB: 儲存並向量化文件 (Embeddings)   ← not implemented
Director->>AgentA: Prompt: "將內容轉為廣東話雙人廣播劇本"
```

**spec.md:**
```
Database: ChromaDB 或 FAISS (本地開發用) / Pinecone (雲端用)
用途: 儲存 PDF 內容，供 Agent B 做 RAG 檢索
```

## Current State
The `/upload` endpoint extracts text and passes it directly to LLM script generation. Nothing is stored in a vector database.

## Impact
- Phase 2 (Agent B / RAG Q&A) cannot be built without this foundation
- Each Q&A question would need to re-process the full document from scratch
- Blocks US-03 and US-04 (user question → interruption flow)

## Required Work
1. Add dependency: `chromadb` or `faiss-cpu` + `sentence-transformers` / `openai embeddings`
2. Create `backend/app/services/vector_db_service.py` with:
   - `store_document(job_id, text)` — chunk, embed, and persist
   - `retrieve_context(job_id, query, top_k)` — similarity search for Agent B
3. Call `store_document()` in the `/upload` endpoint after text extraction
4. Use `job_id` as the collection/namespace key so each upload is isolated
