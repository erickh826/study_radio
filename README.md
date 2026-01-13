# Cantonese Radio Show Generator

A system for generating dual-host Cantonese radio shows from PDF/text content, with planned real-time Q&A interruption capabilities.

## Project Structure

- `backend/` - FastAPI backend (Python)
- `userstory.md` - User stories and requirements
- `system_architecture.md` - System design and flow
- `spec.md` - Technical specifications
- `Action_plan.md` - Development phases
- `prompt_design.md` - LLM prompt engineering

## Current Phase

**Phase 1: The Radio** - Basic broadcast functionality
- ✅ PDF/TXT upload and text extraction
- ✅ Script generation with dual-host dialogue (Agent A)
- ✅ Audio generation using Azure TTS
- ⏳ Real-time Q&A interruptions (Phase 2)
- ⏳ Polish and optimizations (Phase 3)

## Quick Start

See `backend/README.md` for detailed setup instructions.

### Windows Development (Recommended)

1. Install Docker Desktop for Windows
2. Clone this repository
3. Navigate to `backend/` directory
4. Copy `env_template.txt` to `.env` and configure API keys
5. Run `docker-compose up --build`

### Local Python Development

1. Install Python 3.11 or 3.12
2. Navigate to `backend/` directory
3. Create virtual environment: `python -m venv venv`
4. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
5. Install dependencies: `pip install -r requirements.txt`
6. Copy `env_template.txt` to `.env` and configure API keys
7. Run: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Technology Stack

- **Backend**: FastAPI (Python)
- **LLM**: Azure OpenAI (GPT-4o) / OpenAI / Anthropic Claude
- **TTS**: Azure Cognitive Services Speech (Cantonese voices)
- **Containerization**: Docker

## Development Notes

- **Windows**: Native x86_64 support - optimal for Azure Speech SDK
- **Mac M1/M2/M3**: May require Docker with x86_64 emulation or use OpenAI TTS as workaround
- **Phase 1**: Single-pass generation, no interruptions/Q&A yet

## License

[Your License Here]
