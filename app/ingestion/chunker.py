def chunk_text(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 300
):
    """
    Split text into overlapping chunks
    """
    # Normalize whitespace - fix extra spaces/newlines
    import re
    text = re.sub(r'\s+', ' ', text).strip()
    
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks
