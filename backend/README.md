# Backend Module - Quick Start with Ollama

This directory contains the FastAPI backend for the AI SRE Agent, configured to use **Ollama** for self-hosted LLM capabilities.

## Features

- **Self-hosted LLM**: Uses Ollama instead of cloud APIs
- **FastAPI framework**: High-performance async API
- **PostgreSQL**: Database for incidents, actions, and audit logs
- **Redis**: Caching and rate limiting
- **JWT authentication**: Secure API access
- **Prometheus metrics**: Built-in monitoring
- **Kubernetes integration**: Native K8s client support

## Quick Start with Docker Compose

### 1. Start Services (Including Ollama)

```bash
# From project root
docker-compose up -d

# Check services are running
docker-compose ps
```

### 2. Download Ollama Models

```bash
# Use the setup script
./scripts/setup-ollama-models.sh

# Or manually:
docker exec -it ai-sre-ollama ollama pull llama3.1:8b
docker exec -it ai-sre-ollama ollama pull nomic-embed-text
```

### 3. Verify Backend

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/api/docs
```

## Configuration

### Ollama Settings (Default)

The backend is pre-configured to use Ollama in [.env.example](.env.example):

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### Switching Models

To use a different Ollama model:

```bash
# Edit .env or set environment variable
export OLLAMA_MODEL=mistral:7b

# Pull the model
docker exec -it ai-sre-ollama ollama pull mistral:7b

# Restart backend
docker-compose restart backend
```

### Using OpenAI Instead (Optional)

If you prefer OpenAI:

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key-here
docker-compose restart backend
```

## API Endpoints

### Health & Status
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check with DB
- `GET /health/live` - Liveness probe
- `GET /metrics` - Prometheus metrics

### Core Features
- `POST /api/v1/ask` - Natural language queries
- `GET /api/v1/status` - Cluster health status
- `POST /api/v1/recommend` - Get recommendations
- `POST /api/v1/execute` - Execute actions
- `POST /api/v1/chat` - Chat interface

## Development

### Local Setup (Without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Install and start Ollama
curl https://ollama.ai/install.sh | sh
ollama serve

# In another terminal, pull models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# With coverage
pytest --cov=app tests/
```

## Project Structure

```
backend/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── Dockerfile             # Container image
├── app/
│   ├── core/
│   │   ├── config.py      # Configuration management
│   │   ├── llm_client.py  # Ollama/OpenAI client
│   │   ├── security.py    # JWT & authentication
│   │   ├── metrics.py     # Prometheus metrics
│   │   └── logging_config.py
│   ├── api/
│   │   └── v1/            # API v1 endpoints
│   │       ├── ask.py
│   │       ├── status.py
│   │       ├── actions.py
│   │       └── chat.py
│   ├── db/
│   │   ├── database.py    # Database connection
│   │   └── models.py      # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py     # Pydantic schemas
│   └── middleware/
│       ├── auth.py        # Auth middleware
│       └── rate_limit.py  # Rate limiting
└── tests/
```

## LLM Client Usage

The backend includes a unified LLM client that works with both Ollama and OpenAI:

```python
from app.core.llm_client import get_llm_client

# Get client (automatically uses configured provider)
llm = get_llm_client()

# Generate text
response = await llm.generate(
    prompt="Why are my pods crashing?",
    system="You are a Kubernetes SRE expert."
)

# Chat (multi-turn conversation)
response = await llm.chat(
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Analyze this error log..."}
    ]
)

# Generate embeddings for RAG
embedding = await llm.embeddings("Kubernetes deployment failed")
```

## Environment Variables

Key variables (see [.env.example](.env.example) for full list):

```bash
# LLM Provider
LLM_PROVIDER=ollama           # or 'openai'

# Ollama Config
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_TEMPERATURE=0.7

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Security
JWT_SECRET=your-secret-key
SECRET_KEY=your-secret-key

# Features
AUTH_ENABLED=true
RATE_LIMIT_ENABLED=true
```

## Troubleshooting

### Ollama Connection Issues

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# View Ollama logs
docker logs ai-sre-ollama

# Restart Ollama
docker-compose restart ollama
```

### Database Issues

```bash
# Check PostgreSQL
docker logs ai-sre-postgres

# Manual migration
docker-compose exec backend alembic upgrade head

# Reset database
docker-compose down -v
docker-compose up -d
```

### Model Not Found

```bash
# List available models
docker exec -it ai-sre-ollama ollama list

# Pull missing model
docker exec -it ai-sre-ollama ollama pull llama3.1:8b
```

## Performance Tips

1. **Use GPU**: Enable GPU support in docker-compose.yml for faster inference
2. **Adjust Context**: Reduce `OLLAMA_NUM_CTX` for faster responses
3. **Model Selection**: Use smaller models (mistral:7b) for speed
4. **Caching**: Enable Redis for response caching
5. **Connection Pooling**: Tune DB pool size for your workload

## Documentation

- [Ollama Configuration Guide](../docs/OLLAMA.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [API Documentation](http://localhost:8000/api/docs) (when running)
- [Terraform Infrastructure](../terraform/README.md)

## License

Copyright (c) 2026. See LICENSE file for details.
