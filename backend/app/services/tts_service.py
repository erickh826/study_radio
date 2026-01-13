"""
TTS service for audio generation (Azure TTS or OpenAI TTS)
"""
# Fix for Python 3.13: import audioop fix before pydub
import app.audioop_fix  # noqa: F401

import os
import uuid
import tempfile
from pathlib import Path
from typing import List
from app.models import ScriptItem
from app.config import settings
from pydub import AudioSegment
from app.debug_logger import log_debug


async def generate_audio(script: List[ScriptItem], job_id: str) -> str:
    """
    Generate audio file from script using TTS.
    
    Args:
        script: List of ScriptItem objects
        job_id: Unique job identifier for file naming
    
    Returns:
        Path to generated audio file
    """
    # Ensure audio storage directory exists
    audio_dir = Path(settings.audio_storage_path)
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = audio_dir / f"{job_id}.mp3"
    
    if settings.tts_provider == "azure":
        await _generate_azure_tts(script, output_path)
    elif settings.tts_provider == "openai":
        await _generate_openai_tts(script, output_path)
    else:
        raise ValueError(f"Unsupported TTS provider: {settings.tts_provider}")
    
    return str(output_path)


async def _generate_azure_tts(script: List[ScriptItem], output_path: Path):
    """Generate audio using Azure Cognitive Services Speech"""
    import azure.cognitiveservices.speech as speechsdk
    import ssl
    import certifi
    import os
    
    # #region agent log
    # Check SSL certificate availability (hypothesis A: missing CA certs)
    ssl_context_available = None
    certifi_path = None
    ca_cert_paths = []
    try:
        ssl_context_available = ssl.create_default_context() is not None
        certifi_path = certifi.where() if hasattr(certifi, 'where') else None
        ca_bundle_paths = [
            '/etc/ssl/certs/ca-certificates.crt',
            '/etc/ssl/certs/ca-bundle.crt',
            '/usr/share/ca-certificates',
        ]
        for path in ca_bundle_paths:
            if os.path.exists(path):
                ca_cert_paths.append(path)
    except Exception as ssl_check_err:
        ssl_context_available = f"Error: {str(ssl_check_err)}"
    
    log_debug("debug-session", "run1", "A", "tts_service.py:48", "Azure TTS entry - SSL check", {
        "has_speech_key": bool(settings.azure_speech_key),
        "speech_region": settings.azure_speech_region,
        "script_length": len(script),
        "voice_male": settings.azure_voice_male,
        "voice_female": settings.azure_voice_female,
        "ssl_context_available": ssl_context_available,
        "certifi_path": certifi_path,
        "ca_cert_paths_found": ca_cert_paths,
        "tmpdir": os.environ.get("TMPDIR", "not_set")
    })
    # #endregion
    
    if not settings.azure_speech_key:
        raise ValueError("Azure Speech key not configured")
    
    # Initialize Azure Speech synthesizer
    # #region agent log
    log_debug("debug-session", "run1", "J", "tts_service.py:60", "Creating speech config", {
        "region": settings.azure_speech_region,
        "key_prefix": settings.azure_speech_key[:10] + "..." if settings.azure_speech_key else None
    })
    # #endregion
    
    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region
    )
    
    # Set output format
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
    )
    
    # #region agent log
    log_debug("debug-session", "run1", "K", "tts_service.py:79", "Speech config created", {
        "output_format": str(speech_config.output_format),
        "region": settings.azure_speech_region
    })
    # #endregion
    
    audio_segments = []
    
    for idx, item in enumerate(script):
        # Select voice based on role
        voice_name = (
            settings.azure_voice_male if item.role == "Host_Male" 
            else settings.azure_voice_female
        )
        
        # #region agent log
        log_debug("debug-session", "run1", "J", "tts_service.py:75", f"Processing script item {idx+1}/{len(script)}", {
            "item_id": item.id,
            "role": item.role,
            "voice_name": voice_name,
            "text_length": len(item.text),
            "text_preview": item.text[:100] if item.text else None
        })
        # #endregion
        
        # Create a new speech config with voice for this item
        # (We can't reuse the same config with different voices)
        item_speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region
        )
        item_speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
        )
        item_speech_config.speech_synthesis_voice_name = voice_name
        
        # #region agent log
        log_debug("debug-session", "run1", "M", "tts_service.py:102", "Item speech config created with voice", {
            "voice_name": voice_name,
            "voice_set": item_speech_config.speech_synthesis_voice_name == voice_name
        })
        # #endregion
        
        # Create synthesizer for this item with voice-specific config
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=item_speech_config,
            audio_config=None
        )
        
        # #region agent log
        log_debug("debug-session", "run1", "J", "tts_service.py:110", "About to call speak_text_async", {
            "text_length": len(item.text),
            "voice_name": voice_name,
            "using_text_not_ssml": True
        })
        # #endregion
        
        try:
            # Use speak_text_async instead of SSML - voice is set in speech_config
            result = synthesizer.speak_text_async(item.text).get()
        except Exception as tts_error:
            # #region agent log
            log_debug("debug-session", "run1", "J", "tts_service.py:112", "TTS synthesis exception", {
                "error_type": type(tts_error).__name__,
                "error_message": str(tts_error),
                "error_repr": repr(tts_error),
                "item_id": item.id,
                "voice_name": voice_name
            })
            # #endregion
            raise
        
        # #region agent log
        log_debug("debug-session", "run1", "J", "tts_service.py:120", "TTS result received", {
            "result_reason": str(result.reason),
            "result_reason_value": int(result.reason) if hasattr(result.reason, '__int__') else None,
            "is_completed": result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted,
            "is_canceled": result.reason == speechsdk.ResultReason.Canceled,
            "has_audio_data": result.audio_data is not None,
            "audio_data_length": len(result.audio_data) if result.audio_data else 0,
            "result_id": str(result.result_id) if hasattr(result, 'result_id') else None,
            "result_type": type(result).__name__
        })
        # #endregion
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file.write(result.audio_data)
                temp_path = temp_file.name
            
            try:
                # Load with pydub and append to segments
                segment = AudioSegment.from_mp3(temp_path)
                audio_segments.append(segment)
                # #region agent log
                log_debug("debug-session", "run1", "J", "tts_service.py:135", "Audio segment added", {
                    "segment_duration_ms": len(segment),
                    "total_segments": len(audio_segments)
                })
                # #endregion
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            # #region agent log
            log_debug("debug-session", "run1", "J", "tts_service.py:179", "Result not completed, analyzing failure", {
                "result_reason": str(result.reason),
                "result_reason_type": type(result.reason).__name__,
                "result_reason_int": int(result.reason) if hasattr(result.reason, '__int__') else None
            })
            # #endregion
            
            # Try to get cancellation details - use try-except with multiple approaches
            error_msg = f"TTS synthesis failed: {result.reason}"
            error_code = None
            error_details = None
            
            # Approach 1: Try CancellationDetails constructor
            try:
                cancellation_details = speechsdk.CancellationDetails(result)
                error_code = str(cancellation_details.error_code)
                error_details = str(cancellation_details.error_details) if cancellation_details.error_details else None
                # #region agent log
                log_debug("debug-session", "run1", "J", "tts_service.py:192", "CancellationDetails created successfully", {
                    "cancellation_reason": str(cancellation_details.reason),
                    "error_code": error_code,
                    "error_details": error_details,
                    "item_id": item.id
                })
                # #endregion
                error_msg = f"TTS synthesis failed: {cancellation_details.reason}"
                if error_details:
                    error_msg += f" - {error_details}"
                if error_code:
                    error_msg += f" (Error code: {error_code})"
            except Exception as cancel_error:
                # #region agent log
                log_debug("debug-session", "run1", "J", "tts_service.py:205", "CancellationDetails creation failed, trying alternative", {
                    "error_type": type(cancel_error).__name__,
                    "error_message": str(cancel_error),
                    "error_repr": repr(cancel_error),
                    "result_reason": str(result.reason),
                    "item_id": item.id
                })
                # #endregion
                
                # Approach 2: Try to get error code from result properties directly
                try:
                    if hasattr(result, 'error_code'):
                        error_code = str(result.error_code)
                    if hasattr(result, 'error_details'):
                        error_details = str(result.error_details)
                    # #region agent log
                    log_debug("debug-session", "run1", "J", "tts_service.py:218", "Got error info from result properties", {
                        "error_code": error_code,
                        "error_details": error_details,
                        "item_id": item.id
                    })
                    # #endregion
                except Exception as prop_error:
                    # #region agent log
                    log_debug("debug-session", "run1", "J", "tts_service.py:225", "Could not get error info from result properties", {
                        "prop_error": str(prop_error),
                        "item_id": item.id
                    })
                    # #endregion
                    pass
                
                # Build error message with whatever we have
                if error_code:
                    error_msg += f" (Error code: {error_code})"
                if error_details:
                    error_msg += f" - {error_details}"
                if not error_code and not error_details:
                    error_msg += f" (Could not retrieve details: {str(cancel_error)})"
            
            raise RuntimeError(error_msg)
    
    # Concatenate all segments
    if audio_segments:
        final_audio = sum(audio_segments)
        final_audio.export(str(output_path), format="mp3")
    else:
        raise ValueError("No audio segments generated")


async def _generate_openai_tts(script: List[ScriptItem], output_path: Path):
    """Generate audio using OpenAI TTS"""
    from openai import AsyncAzureOpenAI
    
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured")
    
    client = AsyncAzureOpenAI(api_key=settings.openai_api_key)
    
    audio_segments = []
    
    for item in script:
        # OpenAI TTS voice selection (limited Cantonese support)
        # Use 'alloy' for male, 'nova' for female (or 'shimmer' for softer female)
        voice = "alloy" if item.role == "Host_Male" else "nova"
        
        # Generate speech
        response = await client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=item.text,
            response_format="mp3"
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            async for chunk in response.iter_bytes():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        try:
            # Load with pydub and append
            segment = AudioSegment.from_mp3(temp_path)
            audio_segments.append(segment)
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    # Concatenate all segments
    if audio_segments:
        final_audio = sum(audio_segments)
        final_audio.export(str(output_path), format="mp3")
    else:
        raise ValueError("No audio segments generated")

