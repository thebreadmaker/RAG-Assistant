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
        # NEW: Analyze query first
        from core.query_analyzer import analyzer
        analysis = analyzer.analyze(request.query)
        logger.info(f"Query analysis: type={analysis['query_type']}, synthesis={analysis['requires_synthesis']}")
        
        # Route query
        logger.debug("Classifying query...")
        query_info = router.classify_query(request.query)
        logger.info(f"Query type: {query_info.get('type')}")
        
        # Handle customer-specific queries (EXISTING CODE)
        if query_info['type'] == 'customer_specific':
            customer_id = query_info['customer_id']
            
            if not customer_id:
                logger.warning(f"⚠️ Query classified as customer_specific but no customer ID found")
                logger.info(f"Falling back to general query processing")
                query_info['type'] = 'general'
            else:
                # ... existing customer-specific code ...
                logger.info(f"Processing customer-specific query")
                logger.info(f"🧑 Customer ID: {customer_id}")
                eligibility = processor.check_eligibility(customer_id)
                logger.info(f"✅ Eligibility status: {eligibility.get('status')}")
                answer = lfa_generator.generate(eligibility, request.query)
                
                logger.info(f"✅ Query processed successfully (customer_specific)")
                return QueryResponse(
                    answer=answer,
                    metadata=eligibility,
                    query_info=query_info
                )
        
        # NEW: Handle synthesis queries
        if analysis['requires_synthesis'] and analysis['customer_ids']:
            logger.info(f"Processing synthesis query")
            
            # Step 1: Get relevant policies
            logger.debug(f"Retrieving policy chunks...")
            filters = {"doc_type": "policy"} if analysis['topics'] else None
            policy_chunks = retriever.retrieve(request.query, filters=filters)
            logger.info(f"Retrieved {len(policy_chunks)} policy chunks")
            
            # Step 2: Synthesize customer data + policies
            from core.synthesis import get_synthesis_engine
            engine = get_synthesis_engine()
            
            synthesis_result = engine.synthesize(
                query=request.query,
                customer_ids=analysis['customer_ids'],
                topics=analysis['topics'],
                policy_chunks=policy_chunks
            )
            
            logger.info(f"Synthesis: customer_data={synthesis_result['has_customer_data']}, policies={synthesis_result['has_policy_data']}")
            
            # Step 3: Generate answer with synthesis context
            logger.debug(f"Generating synthesis answer...")
            from departments.retail_digital.modules.general.prompts import build_synthesis_prompt
            
            prompt = build_synthesis_prompt(
                query=request.query,
                context=synthesis_result['context']
            )
            
            # Call LLM
            from departments.retail_digital.modules.general.generator import generator
            response_text = generator._call_llm(prompt)
            answer = generator._clean_response(response_text)
            
            logger.info(f"✅ Synthesis query processed")
            return QueryResponse(
                answer=answer,
                metadata={
                    "query_type": "synthesis",
                    "customer_count": synthesis_result['customer_count'],
                    "policy_count": synthesis_result['policy_count'],
                    "sources": [c["metadata"]["source"] for c in policy_chunks[:3]]
                },
                query_info=query_info
            )
        
        # Handle general queries (EXISTING CODE)
        if query_info['type'] == 'general':
            logger.info(f"Processing general query with RAG")
            
            # Retrieve relevant documents
            logger.debug(f"Retrieving relevant documents...")
            chunks = retriever.retrieve(request.query)
            logger.info(f"✅ Retrieved {len(chunks)} chunks")
            
            # Generate answer
            logger.debug(f"Generating RAG answer...")
            result = rag_generator.generate(request.query, chunks)
            logger.info(f"✅ RAG answer generated - Confidence: {result.get('confidence')}")
            
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
        
        # Fallback (EXISTING CODE)
        logger.warning(f"⚠️ Unknown query type, using fallback response")
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