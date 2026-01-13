# Cantonese Radio Show Generator - Backend

FastAPI backend for Phase 1: Generate dual-host Cantonese radio show from PDF/text.

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- **LLM**: Choose `azure_openai` (recommended), `openai`, or `anthropic`
  - For Azure OpenAI: Set `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, and `AZURE_OPENAI_DEPLOYMENT`
  - For regular OpenAI: Set `OPENAI_API_KEY`
  - For Anthropic: Set `ANTHROPIC_API_KEY`
- **TTS**: Choose `azure` (recommended for Cantonese) or `openai`, set corresponding keys

### 3. Run the Server

**Option A: Docker (Recommended)**
```bash
cd backend
docker-compose up --build
```

**Option B: Local Python**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

**Note**: Docker is recommended for consistent environment across platforms. On Windows, Docker runs x86_64 natively without emulation issues.

## Known Issues

### Azure Speech SDK on Mac M1/M2/M3 (ARM64)

The Azure Speech SDK has known compatibility issues on Apple Silicon (M1/M2/M3) Macs running ARM64 architecture. You may encounter `SPXERR_INVALID_ARG` errors when using Azure TTS.

**Workarounds:**

1. **Use OpenAI TTS (Recommended for Mac ARM64)**
   - Set `TTS_PROVIDER=openai` in your `.env` file
   - Note: OpenAI TTS has limited Cantonese support compared to Azure TTS
   - Requires `OPENAI_API_KEY` to be set

2. **Run Python under Rosetta 2 (x86_64 emulation)**
   - Install Python for x86_64 architecture
   - Run: `arch -x86_64 python -m venv venv` (x86_64 version)
   - This may have performance implications

3. **Use Docker with x86_64 platform**
   - Run the backend in a Docker container with x86_64 emulation
   - This isolates the architecture compatibility issue

4. **Wait for Azure SDK update**
   - Monitor Azure Speech SDK releases for ARM64 support
   - Current SDK version: Check `requirements.txt`

**Status**: This is a known limitation of the Azure Speech SDK, not a bug in this application.

## Docker Setup (Recommended)

Docker provides a consistent development environment across platforms.

### Windows Development

Windows provides native x86_64 support, making Docker setup straightforward without emulation issues.

#### Prerequisites

- **Docker Desktop for Windows** installed and running
- **WSL 2** enabled (Docker Desktop will prompt you if needed)
- `.env` file configured (see "Configure Environment" section above)

#### Quick Start

1. **Open PowerShell or Command Prompt:**
   ```powershell
   cd backend
   ```

2. **Build and start the container:**
   ```powershell
   docker-compose up --build
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

#### Windows-Specific Notes

- **No Platform Emulation Needed**: Windows runs x86_64 natively, so no platform flags required
- **Path Separators**: Docker handles Windows paths automatically in docker-compose
- **Performance**: Native x86_64 execution provides optimal performance for Azure Speech SDK
- **WSL 2**: Docker Desktop uses WSL 2 backend on Windows for better performance

### Mac Development

For Mac M1/M2/M3 users, Docker with x86_64 emulation is available but may have compatibility issues. See "Known Issues" section below.

### Development Workflow

The docker-compose configuration mounts your code as volumes, so code changes will be reflected immediately (you may need to restart the container for some changes):

```bash
# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down

# Rebuild after dependency changes
docker-compose up --build
```

### Notes

- **Volumes**: Code, environment variables, and audio files are mounted as volumes for development
- **Python Version**: Uses Python 3.11 (Debian Bookworm default, audioop module exists)
- **Audio Files**: Generated audio files are persisted in `./static/audio/` on your host machine

### Production Deployment

For production, you can use the Dockerfile directly:

```bash
docker build -t cantonese-radio-backend .
docker run -p 8000:8000 --env-file .env cantonese-radio-backend
```

## API Endpoints

### `POST /upload`
Upload a PDF or TXT file and generate radio show.

**Request**: Multipart form data
- `file`: PDF (.pdf) or Text (.txt) file
- `course_name` (optional): Course/topic name

**Response**:
```json
{
  "job_id": "uuid",
  "script": [
    {
      "id": 1,
      "role": "Host_Male",
      "text": "各位聽眾大家好...",
      "duration_est": 3.5
    }
  ],
  "audio_url": "/static/audio/{job_id}.mp3",
  "status": "completed"
}
```

### `POST /generate`
Generate radio show from plain text.

**Request**:
```json
{
  "text": "Your source text here...",
  "course_name": "Optional course name"
}
```

**Response**: Same as `/upload`

### `GET /audio/{job_id}`
Download/serve generated audio file.

### `GET /health`
Check API health and configuration status.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and routes
│   ├── config.py            # Settings from .env
│   ├── models.py            # Pydantic models
│   └── services/
│       ├── __init__.py
│       ├── pdf_service.py   # PDF text extraction
│       ├── llm_service.py   # Agent A: Script generation
│       └── tts_service.py   # Audio generation
├── static/
│   └── audio/               # Generated audio files
├── requirements.txt
├── .env.example
└── README.md
```

## Notes

- **Phase 1 Scope**: Single-pass generation, no interruptions/Q&A yet
- **PDF Limits**: First 10 pages by default (configurable via `MAX_PDF_PAGES`)
- **Text Limits**: First 8000 characters sent to LLM (to control costs)
- **Audio Storage**: Files stored in `./static/audio/` (relative to backend root)

## Troubleshooting

1. **"API key not configured"**: Check your `.env` file has correct keys
2. **"Azure OpenAI endpoint/deployment not configured"**: Make sure you set all three: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, and `AZURE_OPENAI_DEPLOYMENT`
3. **"No text extracted from PDF"**: PDF might be image-based (OCR not implemented in Phase 1)
4. **TTS errors on Mac M1/M2/M3**: See "Known Issues" section above - use `TTS_PROVIDER=openai` as workaround
5. **"SPXERR_INVALID_ARG" on Mac ARM64**: This is the Azure Speech SDK compatibility issue - switch to OpenAI TTS or use x86_64 Python
6. **CORS errors**: Add your frontend URL to `CORS_ORIGINS` in `.env`

## Getting API Keys

### Azure OpenAI
1. Go to [Azure Portal](https://portal.azure.com/)
2. Create an "Azure OpenAI" resource
3. Go to "Keys and Endpoint" → Copy Key 1 and Endpoint URL
4. Go to "Model deployments" → Create a deployment (e.g., gpt-4) and note the deployment name
5. Set in `.env`: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`

### Azure Speech (TTS)
1. Go to [Azure Portal](https://portal.azure.com/)
2. Create a "Speech Services" resource
3. Go to "Keys and Endpoint" → Copy Key 1 and Region
4. Set in `.env`: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`

