from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.orchestration import run_support_agent
from backend.app.support_response import SupportResponse
from backend.app.vector_store import SearchResult


class SupportRequest(BaseModel):
    query: str


class SourceModel(BaseModel):
    text: str
    source: str
    chunk_id: str
    distance: float


class SupportResponseModel(BaseModel):
    answer: str
    sources: list[SourceModel]
    has_usable_context: bool
    retrieval_confidence: str
    confidence_reason: str
    should_escalate: bool
    escalation_reason: str | None

app = FastAPI(title="AI Customer Support Agent")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "AI Customer Support Agent backend is running."}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/support", response_model=SupportResponseModel)
def support(request: SupportRequest) -> SupportResponseModel:
    response: SupportResponse = run_support_agent(request.query)
    return SupportResponseModel(
        answer=response.answer,
        sources=[
            SourceModel(
                text=source.text,
                source=source.source,
                chunk_id=source.chunk_id,
                distance=source.distance,
            )
            for source in response.sources
        ],
        has_usable_context=response.has_usable_context,
        retrieval_confidence=response.retrieval_confidence,
        confidence_reason=response.confidence_reason,
        should_escalate=response.should_escalate,
        escalation_reason=response.escalation_reason,
    )
