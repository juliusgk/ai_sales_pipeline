#!/usr/bin/env bash
# Deploy AI Sales Pipeline to a fresh Ubuntu VM.
#
# Usage:
#   1. SSH into your VM
#   2. Clone the repo: git clone https://github.com/juliusgk/ai_sales_pipeline.git
#   3. cd ai_sales_pipeline
#   4. chmod +x scripts/deploy.sh && ./scripts/deploy.sh
#
# Prerequisites: Ubuntu 22.04+ with sudo access.

set -euo pipefail

echo "========================================="
echo " AI Sales Pipeline — Deployment Script"
echo "========================================="

# ---- 1. Install Docker if not present ----
if ! command -v docker &>/dev/null; then
    echo "[1/6] Installing Docker..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker "$USER"
    echo "Docker installed. You may need to log out and back in for group changes."
else
    echo "[1/6] Docker already installed."
fi

# ---- 2. Create .env file if missing ----
if [ ! -f .env ]; then
    echo "[2/6] Creating .env file..."
    cp .env.example .env

    # Generate random secrets
    API_KEY=$(openssl rand -hex 32)
    SECRET_KEY=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -hex 16)

    sed -i "s/changeme-generate-a-strong-key/$API_KEY/" .env
    sed -i "s/changeme-generate-a-secret-key/$SECRET_KEY/" .env
    sed -i "s/DB_PASSWORD=changeme/DB_PASSWORD=$DB_PASSWORD/" .env
    # Update DATABASE_URL with the new password
    sed -i "s|sales_user:changeme@|sales_user:$DB_PASSWORD@|" .env

    echo "   .env created with generated secrets."
    echo "   API_KEY: $API_KEY"
    echo "   (Save this — you need it to access the API and dashboard)"
else
    echo "[2/6] .env already exists, skipping."
fi

# ---- 3. Update Caddyfile with domain ----
echo "[3/6] Caddy configuration..."
if grep -q "your-domain.com" Caddyfile; then
    echo "   WARNING: Caddyfile still has 'your-domain.com' placeholder."
    echo "   Edit Caddyfile and replace with your actual domain or IP."
    echo "   For testing without a domain, replace 'your-domain.com' with ':80'"
fi

# ---- 4. Build and start services ----
echo "[4/6] Building and starting services..."
docker compose build
docker compose up -d db
echo "   Waiting for PostgreSQL to be ready..."
sleep 5

docker compose up -d ollama api dashboard caddy
echo "   All services starting..."
sleep 5

# ---- 5. Pull Ollama models ----
echo "[5/6] Pulling AI models (this may take a few minutes)..."
docker compose exec -T ollama ollama pull llama3:8b || echo "   WARNING: Failed to pull llama3:8b. Run manually: docker compose exec ollama ollama pull llama3:8b"
docker compose exec -T ollama ollama pull nomic-embed-text || echo "   WARNING: Failed to pull nomic-embed-text. Run manually: docker compose exec ollama ollama pull nomic-embed-text"

# ---- 6. Run database migrations ----
echo "[6/6] Running database migrations..."
docker compose exec -T api alembic upgrade head || echo "   WARNING: Migrations failed. The DB might not have the vector extension yet. Try: docker compose exec api alembic upgrade head"

echo ""
echo "========================================="
echo " Deployment complete!"
echo "========================================="
echo ""
echo " Dashboard: https://your-domain.com (or http://VM_IP:8501)"
echo " API docs:  https://your-domain.com/docs (or http://VM_IP:8000/docs)"
echo " Health:    https://your-domain.com/health"
echo ""
echo " Your API key is in .env — you need it for all API calls."
echo ""
echo " Next steps:"
echo "   1. Edit Caddyfile with your domain"
echo "   2. Point your domain's DNS to this VM's IP"
echo "   3. docker compose restart caddy"
echo "   4. Access the dashboard!"
echo "========================================="
