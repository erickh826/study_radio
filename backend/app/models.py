"""
Pydantic models for request/response schemas
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ScriptItem(BaseModel):
    """Single dialogue item in the radio script"""
    id: int = Field(..., description="Sequential ID of the dialogue item")
    role: str = Field(..., description="Role: 'Host_Male' or 'Host_Female'")
    text: str = Field(..., description="Cantonese dialogue text")
    duration_est: Optional[float] = Field(None, description="Estimated duration in seconds")


class UploadRequest(BaseModel):
    """Request model for PDF upload (metadata)"""
    course_name: Optional[str] = Field(None, description="Optional course/topic name")


class GenerateRequest(BaseModel):
    """Request model for script generation"""
    text: str = Field(..., description="Source text content to convert to radio script")
    course_name: Optional[str] = Field(None, description="Optional course/topic name")


class GenerateResponse(BaseModel):
    """Response model for script generation"""
    job_id: str = Field(..., description="Unique job identifier")
    script: List[ScriptItem] = Field(..., description="Generated dialogue script")
    audio_url: Optional[str] = Field(None, description="URL to generated audio file")
    status: str = Field(..., description="Status: 'generating', 'completed', 'error'")


class TTSRequest(BaseModel):
    """Request model for TTS generation"""
    script: List[ScriptItem] = Field(..., description="Script to convert to audio")
    job_id: str = Field(..., description="Job identifier for file naming")

