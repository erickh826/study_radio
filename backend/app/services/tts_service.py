"""
TTS service for audio generation (Azure TTS)
"""
# Fix for Python 3.13: import audioop fix before pydub
import app.audioop_fix  # noqa: F401

import asyncio
import os
import tempfile
from pathlib import Path
from typing import List
from app.models import ScriptItem
from app.config import settings
from pydub import AudioSegment


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
    else:
        raise ValueError(f"Unsupported TTS provider: {settings.tts_provider}")
    
    return str(output_path)


def _synthesize_item(item: ScriptItem) -> bytes:
    """Synthesize a single script item to raw MP3 bytes (blocking — run in executor)."""
    import azure.cognitiveservices.speech as speechsdk

    voice_name = (
        settings.azure_voice_male if item.role == "Host_Male"
        else settings.azure_voice_female
    )

    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region
    )
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
    )
    speech_config.speech_synthesis_voice_name = voice_name

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(item.text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data

    error_msg = f"TTS synthesis failed for item {item.id}: {result.reason}"
    try:
        details = speechsdk.CancellationDetails(result)
        if details.error_details:
            error_msg += f" - {details.error_details}"
        error_msg += f" (Error code: {details.error_code})"
    except Exception:
        pass
    raise RuntimeError(error_msg)


async def _generate_azure_tts(script: List[ScriptItem], output_path: Path):
    """Generate audio using Azure TTS. All items are synthesized concurrently."""
    if not settings.azure_speech_key:
        raise ValueError("Azure Speech key not configured")

    loop = asyncio.get_event_loop()

    # Run all TTS calls concurrently in the thread pool to avoid blocking the event loop
    audio_data_list: List[bytes] = await asyncio.gather(*[
        loop.run_in_executor(None, _synthesize_item, item)
        for item in script
    ])

    audio_segments = []
    for audio_data in audio_data_list:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        try:
            audio_segments.append(AudioSegment.from_mp3(tmp_path))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    if not audio_segments:
        raise ValueError("No audio segments generated")

    final_audio = sum(audio_segments)
    final_audio.export(str(output_path), format="mp3")



