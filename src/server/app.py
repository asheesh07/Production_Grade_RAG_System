from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    cache_client=init_cache(settings)
    app.state.cacheent=cache_client
    
    rag_pipeline=build_pipeline(settings,cache_client)
    app.state.rag_pipeline=rag_pipeline
    
    yield
    
    await cache_client.close()
    
def create_app() -> FastAPI:
    app=FastAPI(
        title="Production-Grade RAG API",
        version="1.0.0",
        description="An API for a production-grade Retrieval-Augmented Generation (RAG) system.",
        lifespan=lifespan
    )
    
    app.include_router(
        health_router,
        prefix="/health",
        tags=["Health"]
    )
    app.include_router(
        ui_router,
        prefix="/api",
        tags=["UI"]
    )
    
    return app
app=create_app()
    
    