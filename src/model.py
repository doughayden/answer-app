from pydantic import BaseModel


class Question(BaseModel):

    question: str
    # session: str = "-"


class SelectedReferences(BaseModel):

    chunk: str
    content: str
    relevance_score: float
    document: str
    # struct_data: dict[str, Any]


class StructuredResponse(BaseModel):

    answer: str
    references: list[SelectedReferences]
    latency: float
