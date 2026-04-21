"""
FastAPI main application
"""
# Fix for Python 3.13: import audioop fix before any pydub imports
import app.audioop_fix  # noqa: F401

import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.models import GenerateRequest, GenerateResponse, ScriptItem
from app.services.pdf_service import extract_text_from_pdf
from app.services.llm_service import generate_script
from app.services.tts_service import generate_audio
from app.services.vector_db_service import store_document
from app.debug_logger import log_debug


app = FastAPI(
    title="Cantonese Radio Show Generator",
    description="Phase 1: Generate dual-host Cantonese radio show from PDF/text",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio serving
# Ensure audio storage directory exists
audio_storage_dir = Path(settings.audio_storage_path)
audio_storage_dir.mkdir(parents=True, exist_ok=True)
# Mount static directory (relative to backend root when running from backend/)
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Cantonese Radio Show Generator API",
        "phase": 1
    }


@app.post("/upload", response_model=GenerateResponse)
async def upload_file(
    file: UploadFile = File(...),
    course_name: str = Form(None)
):
    """
    Upload PDF or TXT file and generate radio show.
    
    Supported file types: PDF (.pdf), Text (.txt)
    
    This endpoint:
    1. Extracts text from PDF or reads TXT file
    2. Generates script using LLM (Agent A)
    3. Generates audio using TTS
    4. Returns script and audio URL
    """
    job_id = str(uuid.uuid4())
    
    try:
        # #region agent log
        log_debug("debug-session", "run1", "F", "main.py:73", "Upload endpoint entry", {
            "job_id": job_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "has_course_name": bool(course_name)
        })
        # #endregion
        
        # Read file
        file_bytes = await file.read()
        file_extension = Path(file.filename).suffix.lower() if file.filename else ""
        
        # #region agent log
        log_debug("debug-session", "run1", "F", "main.py:79", "File read complete", {
            "file_size_bytes": len(file_bytes),
            "file_extension": file_extension,
            "content_type": file.content_type
        })
        # #endregion
        
        # Extract text based on file type
        if file_extension == ".txt" or (file.content_type and "text/plain" in file.content_type):
            # Handle TXT file
            try:
                # Try UTF-8 first
                text_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to other encodings
                try:
                    text_content = file_bytes.decode("latin-1")
                except UnicodeDecodeError:
                    text_content = file_bytes.decode("utf-8", errors="replace")
            
            # #region agent log
            log_debug("debug-session", "run1", "F", "main.py:95", "TXT file decoded", {
                "text_length": len(text_content),
                "encoding": "utf-8"
            })
            # #endregion
        elif file_extension == ".pdf" or (file.content_type and "pdf" in file.content_type):
            # Handle PDF file
            text_content = extract_text_from_pdf(file_bytes)
            
            # #region agent log
            log_debug("debug-session", "run1", "F", "main.py:103", "PDF text extracted", {
                "text_length": len(text_content)
            })
            # #endregion
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: PDF (.pdf) or Text (.txt). Got: {file_extension or file.content_type}"
            )
        
        # #region agent log
        log_debug("debug-session", "run1", "F", "main.py:85", "Text extracted", {
            "text_length": len(text_content),
            "text_preview": text_content[:200] if text_content else None
        })
        # #endregion
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No text extracted from file")

        # Store document in Vector DB for Phase 2 RAG (Agent B)
        store_document(job_id, text_content)

        # Generate script
        script = await generate_script(text_content, course_name)

        # Generate audio
        await generate_audio(script, job_id)
        audio_url = f"/static/audio/{job_id}.mp3"
        
        return GenerateResponse(
            job_id=job_id,
            script=script,
            audio_url=audio_url,
            status="completed"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/generate", response_model=GenerateResponse)
async def generate_from_text(request: GenerateRequest):
    """
    Generate radio show from plain text (no PDF upload).
    
    This endpoint:
    1. Generates script using LLM (Agent A)
    2. Generates audio using TTS
    3. Returns script and audio URL
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Generate script
        script = await generate_script(request.text, request.course_name)
        
        # Generate audio
        audio_file_path = await generate_audio(script, job_id)
        audio_url = f"/static/audio/{job_id}.mp3"
        
        return GenerateResponse(
            job_id=job_id,
            script=script,
            audio_url=audio_url,
            status="completed"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/audio/{job_id}")
async def get_audio(job_id: str):
    """
    Serve audio file by job ID.
    """
    audio_file = audio_storage_dir / f"{job_id}.mp3"
    
    if not audio_file.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=str(audio_file),
        media_type="audio/mpeg",
        filename=f"{job_id}.mp3"
    )


@app.get("/health")
async def health():
    """Health check with configuration status"""
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "tts_provider": settings.tts_provider,
        "llm_configured": bool(
            (settings.llm_provider == "azure_openai" and settings.azure_openai_api_key and settings.azure_openai_endpoint and settings.azure_openai_deployment) or
            (settings.llm_provider == "anthropic" and settings.anthropic_api_key)
        ),
        "tts_configured": bool(
            settings.tts_provider == "azure" and settings.azure_speech_key
        )
    }

