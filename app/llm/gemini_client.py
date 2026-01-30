import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini - using new google.genai package
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = None

try:
    from google import genai
    if GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("✓ Gemini AI client loaded successfully (new google.genai)")
    else:
        print("Warning: GEMINI_API_KEY not set. Answer generation will use fallback.")
except ImportError:
    print("Warning: google-genai not installed. Using fallback answer generation.")
except Exception as e:
    print(f"Warning: Gemini initialization failed: {e}. Using fallback answer generation.")

def generate_answer(query: str, context_chunks: list) -> str:
    """Generate contextual answer using Gemini or fallback"""
    if client and GEMINI_API_KEY:
        try:
            # Combine context chunks
            context = "\n\n".join([
                f"[Document {i+1}]: {chunk['text']}" 
                for i, chunk in enumerate(context_chunks)
            ])
            
            # Create prompt
            prompt = f"""Based on the following document excerpts, provide a comprehensive and accurate answer to the user's question.

Context:
{context}

Question: {query}

Instructions:
- Answer based solely on the provided context
- If the context doesn't contain enough information, say so clearly
- Cite which document section supports your answer
- Be concise but thorough

Answer:"""

            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            print(f"Gemini generation error: {e}")
            # Fall through to simple fallback
    
    # Simple fallback when Gemini is not available
    if context_chunks and len(context_chunks) > 0:
        best_match = context_chunks[0]
        return f"Based on your uploaded documents, here's what I found:\n\n{best_match['text']}\n\n(Note: Using fallback response. Set GEMINI_API_KEY for AI-generated answers.)"
    else:
        return f"I couldn't find any relevant information about '{query}' in your uploaded documents. Please make sure you've uploaded documents that contain information about this topic."

def generate_summary(text: str, max_length: int = 200) -> str:
    """Generate document summary using Gemini or simple truncation"""
    if client and GEMINI_API_KEY:
        try:
            prompt = f"""Summarize the following text in {max_length} characters or less:

{text}

Summary:"""
            
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            return response.text[:max_length]
            
        except Exception as e:
            print(f"Summary generation error: {e}")
    
    # Fallback to simple truncation
    return text[:max_length] + ("..." if len(text) > max_length else "")