#!/usr/bin/env bash
# EC2 (Ubuntu 22.04) setup script. Run as the ubuntu user after SSH-ing in.
# NOTE: written and syntax-checked here, not run against a live AWS account.
set -euo pipefail

echo "Installing Docker + Compose plugin..."
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker "$USER"

echo "Cloning project and starting stack..."
git clone <your-repo-url> visioninspect-ai
cd visioninspect-ai
export JWT_SECRET="$(openssl rand -hex 32)"
export CORS_ORIGINS="https://your-domain.example"
sudo docker compose -f deploy/docker-compose.prod.yml up -d --build

echo "Done. Point your domain's A record at this instance's public IP, then set up TLS (e.g. certbot) separately."
