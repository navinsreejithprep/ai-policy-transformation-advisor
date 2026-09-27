from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import analysis, documents, health
from .config import settings
from .rag.ingest import seed_demo_knowledge_base_if_empty
from .services import kb_meta
from .utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        result = seed_demo_knowledge_base_if_empty(Path(settings.knowledge_base_path))
        if result:
            kb_meta.mark_indexed()
            logger.info(
                "seeded demo knowledge base documents=%d chunks=%d errors=%d",
                result["documents"],
                result["chunks"],
                len(result["errors"]),
            )
    except Exception as exc:
        # Never block startup on seeding failure — the app is still usable without a KB.
        logger.error("demo knowledge base seeding failed: %s", exc)
    yield


app = FastAPI(title="AI Policy & Transformation Advisor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled error path=%s error=%s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})


app.include_router(health.router)
app.include_router(documents.router)
app.include_router(analysis.router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
