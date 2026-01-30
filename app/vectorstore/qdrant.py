from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib

client = QdrantClient(
    host="localhost", 
    port=6333,
    timeout=30,
    prefer_grpc=False,
    check_compatibility=False
)

COLLECTION_NAME = "document_chunks"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2

def create_collection():
    collections = client.get_collections().collections
    if COLLECTION_NAME not in [c.name for c in collections]:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )

def store_embeddings(tenant_id: str, document_id: str, embeddings: list):
    try:
        if not embeddings:
            raise ValueError("No embeddings provided")
            
        points = []

        for item in embeddings:
            # Validate embedding item
            if not isinstance(item, dict) or 'embedding' not in item:
                continue
                
            # Create a proper unique ID using hash for better compatibility
            point_id = hashlib.md5(f"{document_id}_{item['chunk_index']}".encode()).hexdigest()
            
            # Ensure embedding is a proper list of floats
            vector = item["embedding"]
            if not isinstance(vector, list):
                vector = vector.tolist()
            
            # Validate vector dimensions
            if len(vector) != VECTOR_SIZE:
                print(f"Warning: Vector size {len(vector)} doesn't match expected {VECTOR_SIZE}")
                continue
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "tenant_id": tenant_id,
                        "document_id": document_id,
                        "chunk_index": item["chunk_index"],
                        "text": item["text"]
                    }
                )
            )

        if not points:
            raise ValueError("No valid points to insert")

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        print(f"Successfully stored {len(points)} embeddings")
        
    except Exception as e:
        print(f"Storage error: {e}")
        raise
def search_embeddings(tenant_id: str, query_vector: list, limit: int = 5):
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        import numpy as np
        
        # Validate input
        if not query_vector or not isinstance(query_vector, list):
            raise ValueError("Invalid query vector")
        
        if limit <= 0:
            limit = 5
            
        # Use scroll to get filtered points, then do manual similarity search
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="tenant_id",
                        match=MatchValue(value=tenant_id)
                    )
                ]
            ),
            limit=100,  # Get more results to search through
            with_payload=True,
            with_vectors=True
        )
        
        def cosine_similarity(vec1: list, vec2: list) -> float:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            return np.dot(vec1_np, vec2_np) / (np.linalg.norm(vec1_np) * np.linalg.norm(vec2_np))
        
        # Calculate similarities and sort
        scored_results = []
        for point in results[0]:  # results is tuple (points, next_page_offset)
            if hasattr(point, 'vector') and point.vector:
                similarity = cosine_similarity(query_vector, point.vector)
                scored_results.append((similarity, point))
        
        # Sort by similarity and take top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Format results to match expected structure
        final_results = []
        for score, point in scored_results[:limit]:
            # Create a simple object to match the expected interface
            class SearchResult:
                def __init__(self, score, payload):
                    self.score = score
                    self.payload = payload
            
            final_results.append(SearchResult(score, point.payload))
        
        return final_results
        
    except Exception as e:
        print(f"Search error: {e}")
        return []
