from fastapi import FastAPI, Depends
from app.auth import get_tenant_id
from fastapi import UploadFile, File
from app.ingestion.embedder import generate_embedding
from app.ingestion.chunker import chunk_text
from app.ingestion.pipeline import process_text
from app.vectorstore.qdrant import create_collection, store_embeddings, search_embeddings
import uuid



app = FastAPI()

@app.get("/")
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
@app.post("/search")
def semantic_search(
    query: str,
    tenant_id: str = Depends(get_tenant_id)
):
    try:
        if not query or len(query.strip()) < 3:
            return {"error": "Query too short (minimum 3 characters required)"}
            
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

        # 3. Format response
        response = []
        if results:
            for hit in results:
                response.append({
                    "score": hit.score if hasattr(hit, 'score') else 0.0,
                    "text": hit.payload.get("text", ""),
                    "document_id": hit.payload.get("document_id", ""),
                    "chunk_index": hit.payload.get("chunk_index", 0)
                })

        return {
            "tenant_id": tenant_id,
            "query": query,
            "total_results": len(response),
            "results": response
        }
        
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}
