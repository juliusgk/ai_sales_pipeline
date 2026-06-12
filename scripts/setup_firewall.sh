#!/usr/bin/env bash
# Set up UFW firewall — only allow SSH and HTTPS.
# Run once after deploying to the VM.

set -euo pipefail

echo "Setting up firewall..."

sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (for Caddy ACME challenge / redirect)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

echo "Firewall active. Only SSH (22), HTTP (80), and HTTPS (443) are open."
sudo ufw status verbose
