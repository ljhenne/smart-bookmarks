#!/bin/bash

# Exit on any error
set -e

echo "Deleting maggie-service from Google Cloud Run..."

gcloud run services delete maggie-service \
  --region us-west1 \
  --quiet

echo "Teardown complete! Service removed."
