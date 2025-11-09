from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.schemas import QueryRequest, QueryResponse, HealthResponse
from core.router import router
from core.cache import cache
from departments.retail_digital.modules.lfa.processor import processor
from departments.retail_digital.modules.lfa.response import generator as lfa_generator

# Import RAG components
from departments.retail_digital.modules.general.retriever import retriever
from departments.retail_digital.modules.general.generator import generator as rag_generator

app = FastAPI(title="NCBA Safina RAG API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    redis_ok = cache.health_check()
    
    ollama_ok = True
    try:
        import requests
        from core.config import get_settings
        settings = get_settings()
        resp = requests.get(f"{settings.ollama_host}/api/tags", timeout=3)
        ollama_ok = resp.status_code == 200
    except:
        ollama_ok = False
    
    return {
        "status": "healthy" if (redis_ok and ollama_ok) else "degraded",
        "redis": redis_ok,
        "ollama": ollama_ok
    }

@app.post("/api/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        # Route query
        query_info = router.classify_query(request.query)
        
        # Handle customer-specific queries
        if query_info['type'] == 'customer_specific':
            customer_id = query_info['customer_id']
            
            if not customer_id:
                raise HTTPException(400, "Could not extract customer ID")
            
            # Check eligibility
            eligibility = processor.check_eligibility(customer_id)
            
            # Generate response
            answer = lfa_generator.generate(eligibility, request.query)
            
            return QueryResponse(
                answer=answer,
                metadata=eligibility,
                query_info=query_info
            )
        
        # Handle general queries with RAG
        elif query_info['type'] == 'general':
            # Retrieve relevant documents
            chunks = retriever.retrieve(request.query)
            
            # Generate answer
            result = rag_generator.generate(request.query, chunks)
            
            return QueryResponse(
                answer=result["answer"],
                metadata={
                    "sources": result["sources"],
                    "confidence": result["confidence"],
                    "num_chunks": result.get("num_chunks", 0)
                },
                query_info=query_info
            )
        
        # Fallback
        return QueryResponse(
            answer="I'm not sure how to help with that. Please ask about customer eligibility or general policies.",
            metadata={},
            query_info=query_info
        )
    
    except FileNotFoundError as e:
        raise HTTPException(500, f"Data file not found: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Internal error: {str(e)}")

@app.post("/api/ingest")
async def ingest_documents():
    """Endpoint to trigger document ingestion"""
    try:
        from departments.retail_digital.modules.general.ingester import ingester
        ingester.ingest_all()
        
        from core.vector_manager import VectorManager
        vm = VectorManager("retail_digital")
        count = vm.count()
        
        return {
            "status": "success",
            "message": f"Ingested documents successfully. Total chunks: {count}"
        }
    except Exception as e:
        raise HTTPException(500, f"Ingestion error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    from core.config import get_settings
    settings = get_settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)