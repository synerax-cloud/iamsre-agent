#!/bin/bash
# Ollama Models Setup Script
# Downloads required models for AI SRE Agent

set -e

echo "🤖 AI SRE Agent - Ollama Model Setup"
echo "===================================="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Ollama is running
check_ollama() {
    echo -e "${BLUE}Checking Ollama service...${NC}"
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Ollama is not accessible at http://localhost:11434${NC}"
        echo "Please ensure Ollama is running:"
        echo "  - Docker Compose: docker-compose up -d ollama"
        echo "  - Local install: ollama serve"
        return 1
    fi
}

# Pull a model
pull_model() {
    local model=$1
    local description=$2
    
    echo ""
    echo -e "${BLUE}Pulling model: ${model}${NC}"
    echo "Description: ${description}"
    echo ""
    
    if docker ps | grep -q ai-sre-ollama; then
        # Pull via Docker
        docker exec -it ai-sre-ollama ollama pull "${model}"
    else
        # Pull locally
        ollama pull "${model}"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully pulled ${model}${NC}"
    else
        echo -e "${YELLOW}⚠ Failed to pull ${model}${NC}"
        return 1
    fi
}

# List installed models
list_models() {
    echo ""
    echo -e "${BLUE}Installed models:${NC}"
    if docker ps | grep -q ai-sre-ollama; then
        docker exec -it ai-sre-ollama ollama list
    else
        ollama list
    fi
}

# Main installation
main() {
    # Check Ollama availability
    if ! check_ollama; then
        echo ""
        echo "Please start Ollama first, then run this script again."
        exit 1
    fi
    
    echo ""
    echo "This script will download the following models:"
    echo "  1. llama3.1:8b (~4.7GB) - Main LLM for reasoning"
    echo "  2. nomic-embed-text (~137MB) - Embedding model for RAG"
    echo ""
    echo "Total download size: ~5GB"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    # Pull main LLM
    pull_model "llama3.1:8b" "Main LLM - 8B parameter model for general reasoning"
    
    # Pull embedding model
    pull_model "nomic-embed-text" "Embedding model for RAG and semantic search"
    
    # Show installed models
    list_models
    
    echo ""
    echo -e "${GREEN}✓ Model installation complete!${NC}"
    echo ""
    echo "You can now start the AI SRE Agent:"
    echo "  docker-compose up -d"
    echo ""
    echo "To use different models, see: docs/OLLAMA.md"
    echo ""
    echo "Optional models you might want:"
    echo "  ollama pull mistral:7b        # Faster alternative"
    echo "  ollama pull llama3.1:70b      # Higher quality (requires GPU)"
    echo "  ollama pull codellama:13b     # Better for code analysis"
}

# Run main function
main
