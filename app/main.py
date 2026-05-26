import asyncio
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.inference import get_inference_engine, SystemInferenceEngine
from app.cache import get_cache_manager, DiagnosticCacheManager

app = FastAPI(title="Hyperswitch AI Host Engine (Streaming Optimized)")

class DiagnosticRequest(BaseModel):
    error_log: str = Field(..., description="The raw JSON telemetry log.")
    context: str | None = Field(default=None, description="Optional cluster state metrics.")

@app.post("/v1/diagnose")
async def process_diagnostics(
    payload: DiagnosticRequest, 
    ai_engine: SystemInferenceEngine = Depends(get_inference_engine),
    cache: DiagnosticCacheManager = Depends(get_cache_manager)
):
    try:
        # Check cache pool first
        cached_result = cache.get_cached_analysis(payload.error_log)
        if cached_result:
            # If cached, return a mock generator stream instantly so the interface contract stays uniform
            async def stream_cache():
                yield f"[CACHE HIT]\n{cached_result}"
            return StreamingResponse(stream_cache(), media_type="text/event-stream")

        # Create an async generator that yields tokens live from the background worker thread
        async def token_stream_generator():
            loop = asyncio.get_event_loop()
            # Construct the model's iterator inside our thread offloader
            token_iterator = ai_engine.stream_telemetry_log(payload.error_log, payload.context)
            
            full_response = ""
            while True:
                # Safely pull the next token from the thread without blocking the main event loop
                token = await loop.run_in_executor(None, next, token_iterator, None)
                if token is None:
                    break
                full_response += token
                yield token
            
            # Once the stream finishes completely, asynchronously seed the Redis cache background ring
            cache.set_cached_analysis(payload.error_log, full_response)

        return StreamingResponse(token_stream_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming System Interruption: {str(e)}")