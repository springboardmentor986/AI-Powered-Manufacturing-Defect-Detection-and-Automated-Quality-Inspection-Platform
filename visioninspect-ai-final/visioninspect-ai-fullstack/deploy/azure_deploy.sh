#!/usr/bin/env bash
# Azure App Service (Linux, container-based) deployment script.
# NOTE: written and syntax-checked here, not run against a live Azure subscription.
set -euo pipefail

RESOURCE_GROUP="visioninspect-rg"
LOCATION="eastus"
PLAN="visioninspect-plan"
BACKEND_APP="visioninspect-backend"
FRONTEND_APP="visioninspect-frontend"
ACR_NAME="visioninspectacr"

az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
az acr create --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" --sku Basic
az acr login --name "$ACR_NAME"

docker build -t "$ACR_NAME.azurecr.io/visioninspect-backend:latest" ../backend
docker build -t "$ACR_NAME.azurecr.io/visioninspect-frontend:latest" ../frontend
docker push "$ACR_NAME.azurecr.io/visioninspect-backend:latest"
docker push "$ACR_NAME.azurecr.io/visioninspect-frontend:latest"

az appservice plan create --name "$PLAN" --resource-group "$RESOURCE_GROUP" --is-linux --sku B1

az webapp create --resource-group "$RESOURCE_GROUP" --plan "$PLAN" --name "$BACKEND_APP" \
  --deployment-container-image-name "$ACR_NAME.azurecr.io/visioninspect-backend:latest"
az webapp create --resource-group "$RESOURCE_GROUP" --plan "$PLAN" --name "$FRONTEND_APP" \
  --deployment-container-image-name "$ACR_NAME.azurecr.io/visioninspect-frontend:latest"

az webapp config appsettings set --resource-group "$RESOURCE_GROUP" --name "$BACKEND_APP" \
  --settings JWT_SECRET="$(openssl rand -hex 32)" CORS_ORIGINS="https://$FRONTEND_APP.azurewebsites.net"
az webapp config appsettings set --resource-group "$RESOURCE_GROUP" --name "$FRONTEND_APP" \
  --settings NEXT_PUBLIC_API_URL="https://$BACKEND_APP.azurewebsites.net"

echo "Done. Apps at https://$FRONTEND_APP.azurewebsites.net and https://$BACKEND_APP.azurewebsites.net"
