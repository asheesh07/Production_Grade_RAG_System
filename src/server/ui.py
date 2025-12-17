# ui.py
"""
UI-facing API layer.

Responsibilities:
- Accept and validate client requests
- Translate HTTP -> internal service calls
- Apply caching at request boundaries
- Return UI-safe responses

NO AI logic lives here.
"""

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from core.logging import get_logger
from cache import (
    get_cached_response,
    set_cached_response,
)

logger = get_logger(__name__)

router = APIRouter()


# -------------------------------------------------
# Request / Response Schemas
# -------------------------------------------------
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    session_id: Optional[str] = Field(
        None, description="Optional session identifier"
    )


class ChatResponse(BaseModel):
    answer: str
    source: str = "rag"


# -------------------------------------------------
# Chat Endpoint
# -------------------------------------------------
@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with RAG system",
)
async def chat(request: Request, payload: ChatRequest):
    """
    Main chat endpoint.

    Flow:
    - Validate input
    - Check response cache
    - Call RAG pipeline
    - Cache and return response
    """

    query = payload.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    cache = request.app.state.cache
    rag_pipeline = request.app.state.rag_pipeline

    # -------------------------
    # Cache lookup
    # -------------------------
    cached_answer = get_cached_response(cache, query)
    if cached_answer:
        logger.info("Cache hit for query")
        return ChatResponse(answer=cached_answer)

    # -------------------------
    # RAG pipeline invocation
    # -------------------------
    try:
        answer = await rag_pipeline.run(query)
    except Exception as e:
        logger.error(
            "RAG pipeline execution failed",
            extra={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response",
        )

    # -------------------------
    # Cache response
    # -------------------------
    set_cached_response(
        cache=cache,
        prompt=query,
        response=answer,
        ttl=300,  # 5 minutes
    )

    return ChatResponse(answer=answer)


# -------------------------------------------------
# File Upload Endpoint
# -------------------------------------------------
@router.post(
    "/upload",
    summary="Upload document for ingestion",
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Upload document for ingestion.

    This endpoint:
    - validates file
    - delegates ingestion to pipeline
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file",
        )

    rag_pipeline = request.app.state.rag_pipeline

    try:
        await rag_pipeline.ingest(file)
    except Exception as e:
        logger.error(
            "Document ingestion failed",
            extra={"filename": file.filename, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest document",
        )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status": "success",
            "filename": file.filename,
        },
    )



@router.get(
    "/status",
    summary="Service status for UI",
)
async def status_endpoint(request: Request):
    """
    Lightweight UI-facing status endpoint.
    """

    rag_pipeline = request.app.state.rag_pipeline

    return {
        "service": "rag-backend",
        "pipeline_ready": rag_pipeline is not None,
    }
