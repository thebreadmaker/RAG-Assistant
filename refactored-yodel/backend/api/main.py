from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.schemas import QueryRequest, QueryResponse, HealthResponse
from core.router import router
from core.cache import cache
from core.logger import logger
from departments.retail_digital.modules.lfa.processor import processor
from departments.retail_digital.modules.lfa.response import generator as lfa_generator

# Import RAG components
from departments.retail_digital.modules.general.retriever import retriever
from departments.retail_digital.modules.general.generator import generator as rag_generator

app = FastAPI(title="Refactored YodeL API", version="2.0.0")

# Logging middleware for all HTTP requests/responses
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client}")
        logger.debug(f"   Headers: {dict(request.headers)}")
        
        # Try to log body for POST requests
        try:
            if request.method == "POST":
                body = await request.body()
                if body:
                    logger.debug(f"   Request body: {body.decode()}")
                # Re-wrap body for actual processing
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
        except Exception as e:
            logger.debug(f"   Could not read body: {str(e)}")
        
        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Exception during request {request.method} {request.url.path}: {str(e)}", exc_info=True)
            raise
        
        # Log response
        duration = time.time() - start_time
        logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s")
        
        return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    logger.debug("🏥 Health check requested")
    
    redis_ok = cache.health_check()
    logger.debug(f"   Redis status: {'✅ OK' if redis_ok else '❌ FAILED'}")
    
    ollama_ok = True
    try:
        import requests
        from core.config import get_settings
        settings = get_settings()
        resp = requests.get(f"{settings.ollama_host}/api/tags", timeout=3)
        ollama_ok = resp.status_code == 200
        logger.debug(f"   Ollama status: {'✅ OK' if ollama_ok else '❌ FAILED'} (status: {resp.status_code})")
    except Exception as e:
        ollama_ok = False
        logger.error(f"   Ollama check failed: {str(e)}", exc_info=True)
    
    status = "healthy" if (redis_ok and ollama_ok) else "degraded"
    logger.info(f"🏥 Health check complete: {status}")
    
    return {
        "status": status,
        "redis": redis_ok,
        "ollama": ollama_ok
    }

@app.post("/api/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    logger.info(f"🔍 Query received: '{request.query}'")
    
    try:
        # Route query
        logger.debug("   Classifying query...")
        query_info = router.classify_query(request.query)
        logger.info(f"   Query type: {query_info.get('type')}")
        
        # Handle customer-specific queries
        if query_info['type'] == 'customer_specific':
            customer_id = query_info['customer_id']
            
            # If no customer ID was extracted, fallback to general query
            if not customer_id:
                logger.warning(f"   ⚠️ Query classified as customer_specific but no customer ID found")
                logger.info(f"   Falling back to general query processing")
                # Treat as general query instead
                query_info['type'] = 'general'
            else:
                logger.info(f"   Processing customer-specific query")
                logger.info(f"   🧑 Customer ID: {customer_id}")
                
                # Check eligibility
                logger.debug(f"   Checking eligibility for customer {customer_id}...")
                eligibility = processor.check_eligibility(customer_id)
                logger.info(f"   ✅ Eligibility status: {eligibility.get('status')}")
                
                # Generate response
                logger.debug(f"   Generating LFA response...")
                answer = lfa_generator.generate(eligibility, request.query)
                logger.debug(f"   Generated response: {answer[:100]}..." if len(answer) > 100 else f"   Generated response: {answer}")
                
                logger.info(f"✅ Query processed successfully (customer_specific)")
                return QueryResponse(
                    answer=answer,
                    metadata=eligibility,
                    query_info=query_info
                )
        
        # Handle general queries with RAG
        if query_info['type'] == 'general':
            logger.info(f"   Processing general query with RAG")
            
            # Retrieve relevant documents
            logger.debug(f"   Retrieving relevant documents...")
            chunks = retriever.retrieve(request.query)
            logger.info(f"   ✅ Retrieved {len(chunks)} chunks")
            
            # Generate answer
            logger.debug(f"   Generating RAG answer...")
            result = rag_generator.generate(request.query, chunks)
            logger.info(f"   ✅ RAG answer generated - Confidence: {result.get('confidence')}")
            
            logger.info(f"✅ Query processed successfully (general/RAG)")
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
        logger.warning(f"   ⚠️ Unknown query type, using fallback response")
        return QueryResponse(
            answer="I'm not sure how to help with that. Please ask about customer eligibility or general policies.",
            metadata={},
            query_info=query_info
        )
    
    except FileNotFoundError as e:
        logger.error(f"❌ Data file not found: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Data file not found: {str(e)}")
    except HTTPException as e:
        logger.error(f"❌ HTTP Exception: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"❌ Internal error: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Internal error: {str(e)}")

@app.post("/api/ingest")
async def ingest_documents():
    """Endpoint to trigger document ingestion"""
    logger.info("📥 Ingest documents requested")
    
    try:
        from departments.retail_digital.modules.general.ingester import ingester
        
        logger.debug("   Starting document ingestion...")
        ingester.ingest_all()
        logger.info("   ✅ Document ingestion completed")
        
        logger.debug("   Counting total chunks...")
        from core.vector_manager import VectorManager
        vm = VectorManager("retail_digital")
        count = vm.count()
        logger.info(f"   📊 Total chunks in vector store: {count}")
        
        logger.info(f"✅ Ingestion successful")
        return {
            "status": "success",
            "message": f"Ingested documents successfully. Total chunks: {count}"
        }
    except Exception as e:
        logger.error(f"❌ Ingestion error: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Ingestion error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    from core.config import get_settings
    settings = get_settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)