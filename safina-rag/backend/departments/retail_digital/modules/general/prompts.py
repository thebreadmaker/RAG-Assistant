from typing import List, Dict

def build_rag_prompt(query: str, chunks: List[Dict]) -> str:
    """Build RAG prompt with retrieved context"""
    
    # Format context
    context_parts = []
    for i, chunk in enumerate(chunks[:3], 1):
        source = chunk["metadata"].get("source", "Unknown")
        text = chunk["text"]
        context_parts.append(f"[Source {i}: {source}]\n{text}")
    
    context = "\n\n".join(context_parts)
    
    prompt = f"""You are a helpful banking assistant for NCBA Bank's Retail Digital Lending department.

Use ONLY the information provided below to answer the question. If the information is not in the context, say so clearly.

CONTEXT:
{context}

QUESTION: {query}

INSTRUCTIONS:
1. Answer based ONLY on the provided context
2. Be concise and direct (2-3 sentences)
3. If the answer is not in the context, say "I don't have information about that in the provided documents"
4. Use professional banking language
5. Do NOT make up information

ANSWER:"""
    
    return prompt