# Ollama Configuration and Setup Guide

This project uses [Ollama](https://ollama.ai/) for self-hosted LLM capabilities, providing a privacy-focused and cost-effective alternative to cloud-based LLM services like OpenAI.

## Why Ollama?

- **Self-hosted**: Run LLMs on your own infrastructure
- **Privacy**: No data sent to third-party APIs
- **Cost-effective**: No per-token pricing
- **Performance**: Low-latency responses
- **Variety**: Support for multiple open-source models (Llama 3.1, Mistral, CodeLlama, etc.)

## Recommended Models

### For Production (Main LLM)
- **llama3.1:8b** (Default) - Best balance of performance and resource usage
  - 8B parameters, ~4.7GB RAM required
  - Good general reasoning and instruction following
- **llama3.1:70b** - Best quality (requires GPU)
  - 70B parameters, ~40GB RAM required
  - Superior reasoning for complex SRE tasks
- **mistral:7b** - Fast and efficient alternative
  - 7B parameters, ~4.1GB RAM required
  - Good for quick responses

### For Embeddings
- **nomic-embed-text** (Default) - Optimized for RAG
  - 137M parameters, 768-dimensional embeddings
  - Fast and accurate text embeddings
- **mxbai-embed-large** - Alternative with larger dimensions
  - 1024-dimensional embeddings

## Installation

### Option 1: Docker Compose (Recommended for Dev)

The provided `docker-compose.yml` includes Ollama:

```bash
# Start all services including Ollama
docker-compose up -d

# Pull the main model (first time only)
docker exec -it ai-sre-ollama ollama pull llama3.1:8b

# Pull the embedding model
docker exec -it ai-sre-ollama ollama pull nomic-embed-text

# Verify models are available
docker exec -it ai-sre-ollama ollama list
```

### Option 2: Local Installation

```bash
# macOS
curl https://ollama.ai/install.sh | sh

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows (use WSL2)
curl -fsSL https://ollama.com/install.sh | sh
```

Then pull the models:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### Option 3: Kubernetes Deployment

Ollama is deployed as part of the Helm chart in the `ai-engine` pod.

```bash
# Check Ollama pod status
kubectl get pods -n ai-sre-agent | grep ollama

# Pull models in Kubernetes
kubectl exec -it -n ai-sre-agent deployment/ollama -- ollama pull llama3.1:8b
kubectl exec -it -n ai-sre-agent deployment/ollama -- ollama pull nomic-embed-text
```

## Configuration

### Environment Variables

```bash
# LLM Provider
LLM_PROVIDER=ollama

# Ollama Connection
OLLAMA_BASE_URL=http://ollama:11434  # For Docker Compose
# OLLAMA_BASE_URL=http://localhost:11434  # For local dev

# Model Selection
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Generation Parameters
OLLAMA_TIMEOUT=120
OLLAMA_NUM_CTX=4096        # Context window size
OLLAMA_NUM_PREDICT=2000    # Max tokens to generate
OLLAMA_TEMPERATURE=0.7     # Creativity (0.0-1.0)
OLLAMA_TOP_P=0.9
OLLAMA_TOP_K=40
```

### Switching Models

To use a different model, update the environment variable and pull the model:

```bash
# For Mistral
export OLLAMA_MODEL=mistral:7b
ollama pull mistral:7b

# For larger Llama model (requires more RAM/GPU)
export OLLAMA_MODEL=llama3.1:70b
ollama pull llama3.1:70b

# For CodeLlama (better at code understanding)
export OLLAMA_MODEL=codellama:13b
ollama pull codellama:13b
```

## GPU Acceleration

### Enable GPU in Docker Compose

Uncomment the GPU section in `docker-compose.yml`:

```yaml
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Verify GPU Usage

```bash
# Check Ollama is using GPU
docker exec -it ai-sre-ollama nvidia-smi

# Monitor GPU usage during inference
watch -n 1 nvidia-smi
```

## Performance Tuning

### Context Window Size

Adjust `OLLAMA_NUM_CTX` based on your use case:

- **2048**: Fast, for simple queries
- **4096**: Default, good balance
- **8192**: For complex multi-turn conversations
- **16384**: Maximum context (requires more RAM)

### Batch Size

For high-throughput scenarios, configure batch processing:

```bash
# Set in Ollama container
OLLAMA_NUM_PARALLEL=4  # Number of parallel requests
```

### Memory Management

Monitor Ollama memory usage:

```bash
# Check container memory
docker stats ai-sre-ollama

# Kubernetes
kubectl top pod -n ai-sre-agent ollama-xxx
```

## API Usage Examples

### Direct Ollama API

```bash
# Generate text
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Why are my pods crashing?",
  "stream": false
}'

# Chat completion
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1:8b",
  "messages": [
    {"role": "system", "content": "You are an SRE assistant."},
    {"role": "user", "content": "What is causing high CPU usage?"}
  ]
}'

# Generate embeddings
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Kubernetes pod restart issue"
}'
```

### Python Client (Built-in)

The backend includes an Ollama client in `app/core/llm_client.py`:

```python
from app.core.llm_client import get_llm_client

llm = get_llm_client()

# Generate
response = await llm.generate(
    prompt="Analyze this error: OOMKilled",
    system="You are a Kubernetes SRE expert."
)

# Chat
response = await llm.chat(
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "What's wrong?"}
    ]
)

# Embeddings
vector = await llm.embeddings("Kubernetes deployment failed")
```

## Troubleshooting

### Model Not Found

```bash
# List available models
ollama list

# Pull missing model
ollama pull llama3.1:8b
```

### Connection Refused

```bash
# Check Ollama service is running
docker ps | grep ollama
curl http://localhost:11434/api/tags

# Check container logs
docker logs ai-sre-ollama
```

### Out of Memory

```bash
# Use smaller model
ollama pull llama3.1:8b  # instead of 70b

# Or increase Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory: 8GB+
```

### Slow Generation

```bash
# Check if GPU is being used
docker exec -it ai-sre-ollama nvidia-smi

# Reduce context window
export OLLAMA_NUM_CTX=2048

# Use smaller/faster model
export OLLAMA_MODEL=mistral:7b
```

## Model Comparison

| Model | Size | RAM Required | Speed | Quality | Best For |
|-------|------|--------------|-------|---------|----------|
| llama3.1:8b | 4.7GB | 8GB | Fast | Good | General use |
| llama3.1:70b | 40GB | 48GB+ | Slow | Excellent | Complex reasoning |
| mistral:7b | 4.1GB | 6GB | Very Fast | Good | Quick responses |
| codellama:13b | 7.4GB | 12GB | Medium | Good | Code analysis |
| phi3:medium | 7.9GB | 10GB | Fast | Good | Efficient alternative |

## Switching to OpenAI (Optional)

If you prefer to use OpenAI instead:

```bash
# Update environment
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_MODEL=gpt-4

# No need to run Ollama service
```

## Resource Requirements

### Minimum (8B models)
- CPU: 4 cores
- RAM: 8GB
- Storage: 10GB

### Recommended (8B models with GPU)
- CPU: 8 cores
- RAM: 16GB
- GPU: NVIDIA with 8GB+ VRAM
- Storage: 20GB

### High-Performance (70B models)
- CPU: 16+ cores
- RAM: 64GB+
- GPU: NVIDIA A100 or similar (40GB+ VRAM)
- Storage: 100GB

## Production Considerations

1. **Model Caching**: Pre-pull models in your container images
2. **Health Checks**: Configure proper health checks for Ollama pods
3. **Resource Limits**: Set appropriate resource requests/limits
4. **Autoscaling**: Use HPA based on model serving latency
5. **Monitoring**: Track model inference time and throughput
6. **Fallback**: Consider OpenAI as a fallback for high-load scenarios

## References

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Model Library](https://ollama.ai/library)
- [Llama 3.1 Model Card](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B)
- [Nomic Embed Text](https://huggingface.co/nomic-ai/nomic-embed-text-v1)
