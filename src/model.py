from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
    session_id: str | None = None


class AnswerResponse(BaseModel):
    question: str
    answer: dict
    latency: float
    session: dict | None
    answer_query_token: str | None


class HealthCheckResponse(BaseModel):
    status: str = "ok"


class EnvVarResponse(BaseModel):
    name: str
    value: str | None
