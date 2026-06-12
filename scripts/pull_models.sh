#!/usr/bin/env bash
# Pull required Ollama models for the AI Sales Pipeline.
# Run this after `docker compose up -d ollama` on first setup.

set -euo pipefail

echo "=== Pulling Llama 3 8B (LLM for chat, ~4.7 GB) ==="
docker compose exec ollama ollama pull llama3:8b

echo ""
echo "=== Pulling nomic-embed-text (embeddings, ~274 MB) ==="
docker compose exec ollama ollama pull nomic-embed-text

echo ""
echo "=== Models ready! ==="
docker compose exec ollama ollama list
