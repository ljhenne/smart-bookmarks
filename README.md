# Smart Bookmarks

A polished, AI-powered Chrome Extension and Python Backend that semantically saves and searches your browser bookmarks. This project demonstrates how to use the **Antigravity SDK** to extract structured metadata using Large Language Models (LLMs) and **Google Cloud Platform (GCP)** to store embeddings for semantic search.

## 🏗 Architecture Overview

1. **Chrome Extension (Frontend)**: Built with Vanilla HTML/CSS/TypeScript. Extracts the full HTML and text of your active tab and sends it to the backend.
2. **FastAPI Service (Backend)**: Built with Python. Receives the page data, uses the Antigravity Agent to summarize and categorize the content, generates vector embeddings using Gemini, and stores the data.
3. **Cloud SQL (Database)**: A PostgreSQL database with the `pgvector` extension enabled to perform ultra-fast cosine similarity searches on the bookmark embeddings.
4. **Cloud Run (Hosting)**: The serverless compute platform hosting the FastAPI backend.

## ☁️ GCP Infrastructure Requirements

To deploy this project to Google Cloud, you will need the following resources enabled and configured:

1. **Cloud SQL for PostgreSQL**
   - Must have the `pgvector` extension enabled (`CREATE EXTENSION vector;`).
   - Note your instance connection name (e.g., `project-id:region:instance-name`).
   - Create a database (e.g., `maggies-nest`) and a user.
2. **Cloud Run**
   - Deploys the containerized FastAPI service.
   - Requires environment variables: `PROJECT_ID`, `REGION`, `INSTANCE_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and `GEMINI_API_KEY`.
3. **IAM Permissions**
   - The default compute service account must have the **Cloud SQL Client** role to connect to the database via the Cloud SQL Auth Proxy.
4. **Enabled APIs**
   - Cloud SQL Admin API
   - Generative Language API (for Gemini LLM access)

## 🚀 Local Development Setup

### 1. Backend Service (Python)
Navigate to the `service/` directory and install the dependencies:

```bash
cd service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your local environment variables (ensure `GEMINI_API_KEY` is set):
```bash
export GEMINI_API_KEY="your-gemini-api-key"
export PROJECT_ID="your-project-id"
export REGION="your-region"
export INSTANCE_NAME="your-db-instance"
export DB_USER="your-db-user"
export DB_PASSWORD="your-db-password"
export DB_NAME="your-db-name"
```

Run the server locally:
```bash
fastapi dev main.py
# The server will start on http://localhost:8000
```

### 2. Chrome Extension (TypeScript)
Navigate to the `extension/` directory.

Since this project avoids complex build tools to remain accessible, you only need the TypeScript compiler to build the scripts:

```bash
cd extension
npm install -g typescript
tsc
```
*(You can also use `tsc --watch` to compile as you make changes).*

**To load the extension in Chrome:**
1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** in the top right corner.
3. Click **Load unpacked** and select the `extension/` directory.

## 📦 Deployment

A deployment script is provided to push the backend to Google Cloud Run. 

From the `service/` directory, ensure your variables are set, then run:

```bash
./deploy.sh
```

Ensure the Chrome Extension points to your newly deployed Cloud Run URL instead of `localhost` in `api.ts` before compiling your final extension build.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
