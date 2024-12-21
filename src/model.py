from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
    session: str | None = None


class SelectedReferences(BaseModel):
    chunk: str
    content: str
    relevance_score: float
    document: str
    # struct_data: dict[str, Any]


class AnswerResponse(BaseModel):
    answer: str
    references: list[SelectedReferences]
    latency: float


class HealthCheckResponse(BaseModel):
    status: str = "ok"


class EnvVarResponse(BaseModel):
    name: str
    value: str | None
