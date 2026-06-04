import os
import math
import random
import hashlib
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.models import KnowledgeChunk, Document

# Retrieve keys from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Simple setup for third party SDKs if keys exist
if GEMINI_API_KEY:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)

if OPENAI_API_KEY:
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """
    Split text into chunks of clean overlapping text blocks.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
        
    return chunks

def get_embedding(text: str) -> List[float]:
    """
    Generate a 1536-dimensional vector embedding for the text.
    First tries OpenAI, then Gemini, and falls back to a deterministic mock
    embedding generator if no API keys are provided.
    """
    # 1. Try OpenAI if API Key exists
    if OPENAI_API_KEY:
        try:
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding error: {e}, falling back...")

    # 2. Try Gemini if API Key exists
    if GEMINI_API_KEY:
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            # Gemini embedding is typically 768 dimensions, pad to 1536 for schema uniformity
            gemini_emb = result['embedding']
            if len(gemini_emb) < 1536:
                gemini_emb += [0.0] * (1536 - len(gemini_emb))
            return gemini_emb[:1536]
        except Exception as e:
            print(f"Gemini embedding error: {e}, falling back...")

    # 3. Fallback: Deterministic mock embedding generator based on text hash
    # Generates a pseudo-random unit vector based on the text hash seed
    hash_object = hashlib.sha256(text.encode('utf-8'))
    seed = int(hash_object.hexdigest(), 16) % 10**8
    rng = random.Random(seed)
    
    vector = [rng.gauss(0, 1) for _ in range(1536)]
    # Normalize the vector to unit length
    magnitude = math.sqrt(sum(x**2 for x in vector))
    normalized_vector = [x / magnitude for x in vector] if magnitude > 0 else [0.0] * 1536
    
    return normalized_vector

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Calculate the cosine similarity between two float vectors.
    """
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a**2 for a in v1))
    norm_v2 = math.sqrt(sum(b**2 for b in v2))
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def search_workspace_knowledge(
    db: Session,
    workspace_id: int,
    query: str,
    top_k: int = 3
) -> List[Tuple[KnowledgeChunk, float]]:
    """
    Perform a semantic search for similar text chunks in a specific workspace.
    """
    query_vector = get_embedding(query)
    
    # Retrieve all chunks in this workspace
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.workspace_id == workspace_id).all()
    if not chunks:
        return []
        
    scored_chunks = []
    for chunk in chunks:
        # Load embedding from JSON list
        chunk_vector = chunk.embedding
        if not chunk_vector:
            continue
        sim = cosine_similarity(query_vector, chunk_vector)
        scored_chunks.append((chunk, sim))
        
    # Sort descending by similarity score
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return scored_chunks[:top_k]

def generate_ai_response(
    db: Session,
    workspace_id: int,
    query: str,
    context_chunks: List[KnowledgeChunk]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generate an AI response based on query and context chunks.
    Constructs citations and links back to original documents.
    """
    # Create unique set of sources cited
    citations = []
    seen_docs = set()
    
    context_text = ""
    for idx, chunk in enumerate(context_chunks):
        doc = db.query(Document).filter(Document.id == chunk.document_id).first()
        doc_name = doc.name if doc else f"Document_{chunk.document_id}"
        
        context_text += f"\n--- Source: {doc_name} ---\n{chunk.content}\n"
        
        if doc and doc.id not in seen_docs:
            seen_docs.add(doc.id)
            citations.append({
                "document_id": doc.id,
                "document_name": doc.name,
                "snippet": chunk.content[:200] + "..."
            })
            
    # System prompt directing behavior
    system_prompt = (
        "You are Syner Cortex, an advanced enterprise AI consultant assistant.\n"
        "Your goal is to answer the user's questions based on the provided corporate documents context.\n"
        "Rules:\n"
        "1. You must cite your sources when referring to information from the documents. Use [Document Name] format.\n"
        "2. If the context does not contain the answer, say that you cannot find this information in the uploaded workspace documents. "
        "However, provide a helpful general business consulting recommendation based on standard best practices, separating "
        "your document-based answer from your strategic advice.\n"
        "3. Keep the tone professional, objective, and executive-ready.\n"
    )
    
    user_prompt = f"Context Documents:\n{context_text}\n\nUser Question: {query}\n\nAI Response:"

    # 1. Try OpenAI if API Key exists
    if OPENAI_API_KEY:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content, citations
        except Exception as e:
            print(f"OpenAI completion error: {e}, trying Gemini...")

    # 2. Try Gemini if API Key exists
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_prompt
            )
            response = model.generate_content(
                user_prompt,
                generation_config={"temperature": 0.2}
            )
            return response.text, citations
        except Exception as e:
            print(f"Gemini completion error: {e}, falling back...")

    # 3. Offline Heuristic Fallback Response (Mock Engine)
    # This generates a realistic response based on the search queries and matched text
    if not context_chunks:
        fallback_answer = (
            "I could not find any relevant documents in the workspace vault. Please upload documents such as "
            "financial statements, marketing plans, or operational manuals to begin.\n\n"
            "**Strategic Advice:** For general business consulting, it is recommended to establish clear KPIs "
            "across Commercial, Operations, HR, and Finance areas. Please load documents so I can analyze "
            "your specific organizational status."
        )
        return fallback_answer, []
        
    # Analyze query to customize mock output
    main_doc = context_chunks[0]
    main_doc_model = db.query(Document).filter(Document.id == main_doc.document_id).first()
    main_doc_name = main_doc_model.name if main_doc_model else "Vault Document"
    
    snippet = main_doc.content
    if len(snippet) > 400:
        snippet = snippet[:400] + "..."
        
    fallback_answer = (
        f"Based on the workspace document **{main_doc_name}**, the following analysis was identified:\n\n"
        f"\"{snippet}\"\n\n"
        f"Specifically, we have mapped key indicators corresponding to the prompt. "
        f"This indicates that the operations align with the documented parameters in [{main_doc_name}].\n\n"
        f"**Consulting Insights:**\n"
        f"- *Strategic recommendation:* Formulate a mitigation plan to address any potential constraints or gaps "
        f"mentioned in [{main_doc_name}].\n"
        f"- *Immediate actions:* Benchmark these findings against your target KPIs for the current quarter."
    )
    
    return fallback_answer, citations
