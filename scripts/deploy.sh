#!/bin/bash

# Exit on any error
set -e

# Verify GEMINI_API_KEY is configured
if [ -z "$GEMINI_API_KEY" ]; then
  echo "Error: GEMINI_API_KEY environment variable is not set."
  echo "Please export GEMINI_API_KEY before running this script, or run it like:"
  echo "  GEMINI_API_KEY=your_api_key_here ./deploy.sh"
  exit 1
fi

# Verify DB_PASSWORD is configured
if [ -z "$DB_PASSWORD" ]; then
  echo "Error: DB_PASSWORD environment variable is not set."
  echo "Please export DB_PASSWORD before running this script, or run it like:"
  echo "  DB_PASSWORD=your_db_password_here ./deploy.sh"
  exit 1
fi

echo "Deploying maggie-service to Google Cloud Run..."

gcloud run deploy maggie-service \
  --source "$(dirname "$0")" \
  --region us-west1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances=ljhenne-joonix-sandbox:us-west1:maggie \
  --set-env-vars="PROJECT_ID=ljhenne-joonix-sandbox,REGION=us-west1,INSTANCE_NAME=maggie,DB_USER=maggie-service,DB_PASSWORD=$DB_PASSWORD,DB_NAME=maggies-nest,GEMINI_API_KEY=$GEMINI_API_KEY"

echo "Deployment complete!"
