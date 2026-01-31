from fastapi import FastAPI, Depends
from app.auth import get_tenant_id, get_current_tenant, get_tenant_id_flexible
from fastapi import UploadFile, File
from typing import List
from app.ingestion.embedder import generate_embedding
from app.ingestion.chunker import chunk_text
from app.ingestion.pipeline import process_text
from app.vectorstore.qdrant import create_collection, store_embeddings, search_embeddings
from app.llm.gemini_client import generate_answer
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
import os

app = FastAPI(title="DocRAG API", description="Document RAG System with Multi-tenant Support")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Qdrant collection on startup
@app.on_event("startup")
async def startup_event():
    """Initialize Qdrant collection on application startup"""
    try:
        create_collection()
        print("✅ Qdrant collection initialized successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize Qdrant collection: {e}")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0"}

# Config endpoint - provides Supabase public config to frontend
@app.get("/api/config")
async def get_config():
    """Return public Supabase configuration for frontend"""
    from app.auth import SUPABASE_URL, SUPABASE_ANON_KEY
    return {
        "supabaseUrl": SUPABASE_URL or "",
        "supabaseAnonKey": SUPABASE_ANON_KEY or ""
    }

# Serve the frontend
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html", media_type="text/html")

@app.get("/api")
def root():
    return {"message": "Document Ingestion Service is running"}

@app.get("/protected")
def protected_route(tenant_id: str = Depends(get_tenant_id)):
    return {
        "message": "You are authenticated",
        "tenant_id": tenant_id
    }
@app.post("/upload-txt")
def upload_txt(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id)
):
    # Check file type
    if not file.filename.endswith(".txt"):
        return {"error": "Only .txt files are supported"}

    # Read file content
    content = file.file.read().decode("utf-8")

    return {
        "tenant_id": tenant_id,
        "filename": file.filename,
        "content_preview": content[:500]  # first 500 chars
    }
@app.post("/embed-test")
def embed_test(
    text: str,
    tenant_id: str = Depends(get_tenant_id)
):
    embedding = generate_embedding(text)

    return {
        "tenant_id": tenant_id,
        "embedding_length": len(embedding),
        "sample_values": embedding[:5]
    }
@app.post("/chunk-test")
def chunk_test(
    text: str,
    tenant_id: str = Depends(get_tenant_id)
):
    chunks = chunk_text(text)

    return {
        "tenant_id": tenant_id,
        "total_chunks": len(chunks),
        "first_chunk_preview": chunks[0][:200]
    }
@app.post("/ingest-test")
def ingest_test(
    text: str,
    tenant_id: str = Depends(get_tenant_id)
):
    results = process_text(text)

    return {
        "tenant_id": tenant_id,
        "total_chunks": len(results),
        "embedding_dim": len(results[0]["embedding"]) if results else 0
    }
@app.post("/upload-files")
async def upload_files_bulk(
    files: List[UploadFile] = File(...),
    tenant_id: str = Depends(get_tenant_id_flexible)
):
    """Bulk upload and process multiple files for the RAG system"""
    results = []
    
    for file in files:
        try:
            if not file.filename:
                results.append({"filename": "unknown", "error": "No file provided"})
                continue
            
            # Check file type
            allowed_types = {'.txt', '.pdf', '.docx', '.md'}
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext not in allowed_types:
                results.append({
                    "filename": file.filename,
                    "error": f"File type {file_ext} not supported. Allowed: {', '.join(allowed_types)}"
                })
                continue
            
            # Process single file (reuse existing logic)
            single_result = await process_single_file(file, file_ext, tenant_id)
            results.append(single_result)
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": f"Failed to process: {str(e)}"
            })
    
    # Calculate summary
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    return {
        "message": f"Bulk upload completed: {len(successful)} successful, {len(failed)} failed",
        "total_files": len(files),
        "successful_count": len(successful),
        "failed_count": len(failed),
        "results": results
    }

async def process_single_file(file: UploadFile, file_ext: str, tenant_id: str):
    """Helper function to process a single file (extracted from upload_file_endpoint)"""
    # Read file content
    content = await file.read()
    
    # Process different file types
    if file_ext == '.txt' or file_ext == '.md':
        text = content.decode('utf-8')
    elif file_ext == '.pdf':
        try:
            import PyPDF2
            import io
            
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Clean up text - remove excessive whitespace
            import re
            text = re.sub(r'\s+', ' ', text).strip()
            
            if not text.strip():
                return {"filename": file.filename, "error": "Could not extract text from PDF"}
        except Exception as e:
            return {"filename": file.filename, "error": f"PDF processing error: {str(e)}"}
    else:
        return {"filename": file.filename, "error": f"File type {file_ext} not implemented"}
    
    # Process the text
    chunks = chunk_text(text)
    embeddings = [generate_embedding(chunk) for chunk in chunks]
    
    # Create document ID
    doc_id = str(uuid.uuid4())
    
    # Store in Qdrant
    embedding_data = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        if embedding:
            embedding_data.append({
                "embedding": embedding,
                "text": chunk,
                "chunk_index": i,
                "filename": file.filename,
                "file_type": file_ext
            })
    
    if embedding_data:
        try:
            store_embeddings(
                tenant_id=tenant_id,
                document_id=doc_id,
                embeddings=embedding_data
            )
        except Exception as e:
            return {"filename": file.filename, "error": f"Storage failed: {str(e)}"}
    
    return {
        "filename": file.filename,
        "document_id": doc_id,
        "chunks_processed": len(chunks),
        "chunks_stored": len(embedding_data)
    }

@app.post("/upload-file")
async def upload_file_endpoint(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id)
):
    """Upload and process a file for the RAG system"""
    try:
        if not file.filename:
            return {"error": "No file provided"}
        
        # Check file type
        allowed_types = {'.txt', '.pdf', '.docx', '.md'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_types:
            return {"error": f"File type {file_ext} not supported. Allowed: {', '.join(allowed_types)}"}
        
        # Read file content
        content = await file.read()
        
        # Process different file types
        if file_ext == '.txt' or file_ext == '.md':
            text = content.decode('utf-8')
        elif file_ext == '.pdf':
            # Extract text from PDF
            try:
                import PyPDF2
                import io
                
                # Create a BytesIO object from the content
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract text from all pages
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                # Clean up text - remove excessive whitespace
                import re
                text = re.sub(r'\s+', ' ', text).strip()
                
                if not text.strip():
                    return {"error": "Could not extract text from PDF. The PDF might be image-based or encrypted."}
                    
            except ImportError:
                return {"error": "PDF processing not available. PyPDF2 not installed."}
            except Exception as e:
                return {"error": f"Error processing PDF: {str(e)}"}
        elif file_ext == '.docx':
            # Add DOCX processing later
            return {"error": f"DOCX processing not yet implemented"}
        else:
            return {"error": f"File processing for {file_ext} not yet implemented"}
        
        # Process the text
        chunks = chunk_text(text)
        embeddings = [generate_embedding(chunk) for chunk in chunks]
        
        # Create document ID
        doc_id = str(uuid.uuid4())
        
        # Store in Qdrant
        stored_count = 0
        embedding_data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding:
                embedding_data.append({
                    "embedding": embedding,
                    "text": chunk,
                    "chunk_index": i,
                    "filename": file.filename,
                    "file_type": file_ext
                })
        
        if embedding_data:
            try:
                store_embeddings(
                    tenant_id=tenant_id,
                    document_id=doc_id,
                    embeddings=embedding_data
                )
                stored_count = len(embedding_data)
            except Exception as e:
                print(f"Storage error: {e}")
                return {"error": f"Failed to store embeddings: {str(e)}"}
        
        return {
            "message": f"Successfully processed {file.filename}",
            "document_id": doc_id,
            "chunks_processed": len(chunks),
            "chunks_stored": stored_count
        }
        
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}

@app.post("/ingest-to-qdrant")
def ingest_to_qdrant(
    text: str,
    tenant_id: str = Depends(get_tenant_id)
):
    try:
        if not text or len(text.strip()) < 50:
            return {"error": "Text too short (minimum 50 characters required)"}

        create_collection()

        document_id = str(uuid.uuid4())
        results = process_text(text)

        if not results:
            return {"error": "No text chunks generated"}

        store_embeddings(
            tenant_id=tenant_id,
            document_id=document_id,
            embeddings=results
        )

        return {
            "message": "Document ingested successfully",
            "tenant_id": tenant_id,
            "document_id": document_id,
            "total_chunks": len(results),
            "text_length": len(text)
        }
    except Exception as e:
        return {"error": f"Ingestion failed: {str(e)}"}
# Supabase Auth Endpoints
@app.post("/auth/ingest-to-qdrant")
def auth_ingest_to_qdrant(
    text: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """Supabase authenticated document ingestion"""
    try:
        if not text or len(text.strip()) < 50:
            return {"error": "Text too short (minimum 50 characters required)"}

        create_collection()

        document_id = str(uuid.uuid4())
        results = process_text(text)

        if not results:
            return {"error": "No text chunks generated"}

        store_embeddings(
            tenant_id=tenant_id,
            document_id=document_id,
            embeddings=results
        )

        return {
            "message": "Document ingested successfully",
            "tenant_id": tenant_id,
            "document_id": document_id,
            "total_chunks": len(results),
            "text_length": len(text)
        }
    except Exception as e:
        return {"error": f"Ingestion failed: {str(e)}"}

@app.post("/auth/search")
def auth_semantic_search(
    query: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """Supabase authenticated semantic search with AI answer generation"""
    try:
        if not query or len(query.strip()) < 1:
            return {"error": "Please enter a question"}
            
        # 1. Embed the query
        query_embedding = generate_embedding(query)
        
        if not query_embedding:
            return {"error": "Failed to generate query embedding"}

        # 2. Search Qdrant with tenant isolation
        results = search_embeddings(
            tenant_id=tenant_id,
            query_vector=query_embedding,
            limit=5
        )

        # 3. Generate AI answer from retrieved context
        ai_answer = ""
        response = []
        if results:
            # Format context for response
            for hit in results:
                response.append({
                    "score": hit.score if hasattr(hit, 'score') else 0.0,
                    "text": hit.payload.get("text", ""),
                    "document_id": hit.payload.get("document_id", ""),
                    "chunk_index": hit.payload.get("chunk_index", 0)
                })
            
            # Generate contextual answer using Gemini
            ai_answer = generate_answer(query, response)
        else:
            ai_answer = f"I couldn't find any relevant information about '{query}' in your uploaded documents. Please make sure you've uploaded documents that contain information about this topic."

        return {
            "tenant_id": tenant_id,
            "query": query,
            "answer": ai_answer,
            "total_results": len(response),
            "sources": response
        }
        
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

# Legacy endpoints (keep existing functionality)
@app.post("/search")
def semantic_search(
    query: str,
    tenant_id: str = Depends(get_tenant_id_flexible)
):
    try:
        if not query or len(query.strip()) < 1:
            return {"error": "Please enter a question"}
            
        # 1. Embed the query
        query_embedding = generate_embedding(query)
        
        if not query_embedding:
            return {"error": "Failed to generate query embedding"}

        # 2. Search Qdrant
        results = search_embeddings(
            tenant_id=tenant_id,
            query_vector=query_embedding,
            limit=5
        )

        # 3. Generate AI answer from retrieved context
        ai_answer = ""
        response = []
        if results:
            # Format context for response
            for hit in results:
                response.append({
                    "score": hit.score if hasattr(hit, 'score') else 0.0,
                    "text": hit.payload.get("text", ""),
                    "document_id": hit.payload.get("document_id", ""),
                    "chunk_index": hit.payload.get("chunk_index", 0)
                })
            
            # Generate contextual answer using Gemini
            ai_answer = generate_answer(query, response)
        else:
            ai_answer = f"I couldn't find any relevant information about '{query}' in your uploaded documents. Please make sure you've uploaded documents that contain information about this topic."

        return {
            "tenant_id": tenant_id,
            "query": query,
            "answer": ai_answer,
            "total_results": len(response),
            "sources": response
        }
        
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

@app.delete('/clear-documents')
async def clear_documents(tenant_id: str = Depends(get_tenant_id)):
    '''Clear all documents for the current tenant'''
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Delete all points with this tenant_id
        client = QdrantClient(host='localhost', port=6333)
        
        client.delete(
            collection_name='document_chunks',
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key='tenant_id',
                        match=MatchValue(value=tenant_id)
                    )
                ]
            )
        )
        
        return {
            'message': f'All documents cleared for tenant {tenant_id}',
            'tenant_id': tenant_id
        }
    except Exception as e:
        return {'error': f'Clear failed: {str(e)}'}
