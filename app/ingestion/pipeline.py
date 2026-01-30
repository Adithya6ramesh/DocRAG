from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import generate_embedding

def process_text(text: str):
    """
    Full ingestion pipeline:
    text -> chunks -> embeddings
    """
    chunks = chunk_text(text)

    results = []
    for idx, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk)
        results.append({
            "chunk_index": idx,
            "text": chunk,
            "embedding": embedding
        })

    return results
