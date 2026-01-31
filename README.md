# 📚 DocRAG - AI-Powered Document Question Answering System

> A production-ready Retrieval-Augmented Generation (RAG) system with multi-tenant support, enabling users to upload documents and ask questions using AI.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🌟 Features

- **🔐 Multi-Tenant Authentication**: Secure user authentication with Supabase (email/password + OAuth)
- **📄 Document Upload**: Support for PDF, TXT, and Markdown files
- **🤖 AI-Powered Q&A**: Ask questions about your documents using Google Gemini 2.5 Flash
- **🔍 Semantic Search**: Vector-based search using Qdrant for accurate retrieval
- **💬 Chat History**: User-specific conversation history persists across sessions
- **🎨 Modern UI**: Clean, responsive interface with dark mode support
- **🏢 Tenant Isolation**: Each user's documents and chats are completely isolated
- **⚡ Real-time Processing**: Fast document chunking and embedding generation
- **📊 Source Citations**: View which document sections answered your questions

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  HTML + Vanilla JS + Supabase Client + LocalStorage         │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     Auth     │  │   Ingestion  │  │    Search    │      │
│  │   (Supabase) │  │  (Chunking + │  │  (Semantic)  │      │
│  │              │  │   Embedding) │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────┬──────────────────┬──────────────────┬──────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   Supabase     │  │     Qdrant     │  │  Gemini API    │
│   (Auth +      │  │  (Vector DB)   │  │  (LLM)         │
│   User Data)   │  │                │  │                │
└────────────────┘  └────────────────┘  └────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - Authentication and user management
- **Qdrant** - Vector database for embeddings
- **Sentence Transformers** - Text embedding generation (`all-MiniLM-L6-v2`)
- **Google Gemini** - AI response generation
- **PyPDF2** - PDF text extraction

### Frontend
- **Vanilla JavaScript** - No framework dependencies
- **Supabase JS Client** - Authentication handling
- **LocalStorage** - User-specific chat persistence
- **CSS3** - Modern styling with dark mode

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/downloads)

You'll also need API keys for:
- **Supabase** - [Create free account](https://supabase.com/)
- **Google Gemini** - [Get API key](https://makersuite.google.com/app/apikey)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/DocRAG.git
cd DocRAG
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key

# Database Configuration (optional - for advanced features)
DATABASE_URL=your_postgresql_connection_string
```

**Getting Supabase Credentials:**
1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Create a new project or select existing
3. Go to Settings → API
4. Copy `URL`, `anon/public key`, `service_role key`
5. Go to Settings → API → JWT Settings → Copy JWT Secret

### 4. Start Qdrant Vector Database

```bash
docker-compose up -d
```

Verify Qdrant is running:
```bash
curl http://localhost:6333/collections
```

### 5. Update Frontend Configuration

Edit `static/js/app.js` (lines 5-6) with your Supabase credentials:

```javascript
this.supabaseUrl = 'YOUR_SUPABASE_URL';
this.supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY';
```

### 6. Run the Application

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 7. Open in Browser

Navigate to [http://localhost:8001](http://localhost:8001)

🎉 **You're ready to go!**

## 📖 Usage Guide

### Creating an Account

1. Click **"Login"** in the top-right corner
2. Switch to **"Sign Up"** tab
3. Enter your name, email, and password
4. Click **"Sign Up"**
5. Check your email for confirmation (if email confirmation is enabled)

### Uploading Documents

1. **Login** to your account
2. Click the **"Upload"** button (📤 icon) in the sidebar
3. Select **"Upload File"** or **"Upload Folder"**
4. Choose your documents (PDF, TXT, or MD files)
5. Wait for processing to complete

**Supported Formats:**
- `.pdf` - PDF documents
- `.txt` - Plain text files
- `.md` - Markdown files

**Processing Steps:**
1. Text extraction (for PDFs)
2. Document chunking (2000 chars with 300 char overlap)
3. Embedding generation using Sentence Transformers
4. Storage in Qdrant vector database

### Asking Questions

1. Type your question in the chat input box
2. Press **Enter** or click **Send** (➤)
3. The AI will:
   - Search your documents using semantic search
   - Retrieve the most relevant passages
   - Generate a comprehensive answer using Gemini AI
   - Show source citations



### Managing Chats

- **New Chat**: Click the ➕ icon to start fresh
- **Switch Chats**: Click on any chat in the history sidebar
- **Delete Chat**: Hover over a chat and click the 🗑️ icon

### Logging Out

Click the **"Logout"** button in the top-right corner. Your chat history will be preserved and restored when you log back in.

## 🔌 API Documentation

### Authentication

All endpoints (except `/health`) require authentication via one of:
- **JWT Token**: `Authorization: Bearer <token>` (for logged-in users)
- **X-Tenant-ID**: `X-Tenant-ID: <tenant_id>` (for demo/testing)

### Endpoints

#### Health Check
```http
GET /health
```
Returns API status and version.

#### Upload Single File
```http
POST /upload-file
Content-Type: multipart/form-data
Authorization: Bearer <token>

Body: file=@document.pdf
```

**Response:**
```json
{
  "message": "Successfully processed document.pdf",
  "document_id": "uuid-here",
  "chunks_processed": 25,
  "chunks_stored": 25
}
```

#### Upload Multiple Files
```http
POST /upload-files
Content-Type: multipart/form-data
Authorization: Bearer <token>

Body: files=@doc1.pdf&files=@doc2.txt
```

**Response:**
```json
{
  "message": "Bulk upload completed: 2 successful, 0 failed",
  "total_files": 2,
  "successful_count": 2,
  "failed_count": 0,
  "results": [...]
}
```

#### Semantic Search (with AI)
```http
POST /search?query=What is machine learning
Authorization: Bearer <token>
```

**Response:**
```json
{
  "query": "What is machine learning",
  "answer": "Machine learning is...",
  "total_results": 5,
  "sources": [
    {
      "score": 0.87,
      "text": "Machine learning is a subset...",
      "document_id": "uuid",
      "filename": "ml_intro.pdf",
      "chunk_index": 3
    }
  ]
}
```

#### Search (authenticated endpoint)
```http
POST /auth/search?query=your question
Authorization: Bearer <token>
```

#### Clear All Documents
```http
DELETE /clear-documents
Authorization: Bearer <token>
```

Deletes all documents for the authenticated user.

#### List Collections (Admin)
```http
GET /collections
```

Returns all Qdrant collections.

## 🏗️ Project Structure

```
DocRAG/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application and routes
│   ├── auth.py                 # Supabase authentication logic
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── chunker.py          # Document chunking
│   │   └── embedder.py         # Embedding generation
│   ├── vectorstore/
│   │   ├── __init__.py
│   │   └── qdrant.py           # Qdrant operations
│   ├── llm/
│   │   ├── __init__.py
│   │   └── gemini_client.py    # Gemini AI integration
│   └── models/
│       ├── __init__.py
│       └── schemas.py          # Pydantic models
├── static/
│   ├── index.html              # Main UI
│   ├── js/
│   │   └── app.js              # Frontend application
│   └── css/
│       └── style.css           # Styling
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Qdrant container config
├── .env.example                # Environment variables template
├── .gitignore
└── README.md
```

## 🔒 Security Features

- **JWT Token Validation**: Tokens verified via Supabase API
- **Tenant Isolation**: User UUID used as tenant_id in Qdrant
- **Row-Level Security**: Supabase RLS policies (configure in Supabase dashboard)
- **No Session Persistence**: Users must login each session (configurable)
- **Secure Password Storage**: Handled by Supabase
- **CORS Protection**: Configure allowed origins in production

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_complete_system.py
```

**Tests include:**
- Health check
- Frontend loading
- Document upload (with demo tenant)
- Semantic search with AI
- Multi-tenant isolation verification

## 📦 Deployment

### Option 1: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t docrag .
docker run -p 8000:8000 --env-file .env docrag
```

### Option 2: Cloud Deployment

**Railway / Render / Fly.io:**
1. Connect your GitHub repository
2. Set environment variables in dashboard
3. Deploy automatically on git push

**Environment Variables to Set:**
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `GEMINI_API_KEY`
- `QDRANT_HOST` (use Qdrant Cloud URL)
- `QDRANT_PORT`

**For Qdrant:**
Use [Qdrant Cloud](https://cloud.qdrant.io/) for production vector database.

## ⚙️ Configuration

### Chunking Strategy

Edit `app/ingestion/chunker.py`:
```python
CHUNK_SIZE = 2000      # Characters per chunk
CHUNK_OVERLAP = 300    # Overlap between chunks
```

### Embedding Model

Edit `app/ingestion/embedder.py`:
```python
model = SentenceTransformer("all-MiniLM-L6-v2")
# Other options:
# - "all-mpnet-base-v2" (better quality, slower)
# - "paraphrase-multilingual-MiniLM-L12-v2" (multilingual)
```

### Search Limit

Edit `app/main.py`:
```python
results = search_embeddings(tenant_id, query_embedding, limit=5)
# Increase limit for more context
```

### AI Model

Edit `app/llm/gemini_client.py`:
```python
model='gemini-2.5-flash'
# Other options:
# - 'gemini-1.5-pro' (more capable, slower)
# - 'gemini-1.5-flash' (faster)
```

## 🐛 Troubleshooting

### Qdrant Connection Failed
```
Error: Connection refused to localhost:6333
```
**Solution:** Start Qdrant using `docker-compose up -d`

### Module Not Found
```
ModuleNotFoundError: No module named 'sentence_transformers'
```
**Solution:** Install dependencies: `pip install -r requirements.txt`

### Supabase Authentication Failed
```
401 Unauthorized
```
**Solution:** Check `.env` file has correct Supabase credentials

### Empty PDF Extraction
```
error: "Could not extract text from PDF"
```
**Solution:** PDF may be scanned/image-based. Use OCR preprocessing.

### Token Expired
```
401: Token expired
```
**Solution:** Logout and login again to get a fresh token

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Code Style:**
- Python: Follow PEP 8
- JavaScript: Use consistent formatting
- Add comments for complex logic
- Write descriptive commit messages




]
