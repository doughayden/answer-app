from enum import Enum
from typing import Any
from urllib.parse import quote

from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
    session_id: str | None = None
    user_pseudo_id: str = ""


class AnswerResponse(BaseModel):
    question: str
    markdown: str
    latency: float
    answer: dict[str, Any]
    session: dict[str, Any] | None = None
    answer_query_token: str


class HealthCheckResponse(BaseModel):
    status: str = "ok"


class EnvVarResponse(BaseModel):
    name: str
    value: str | None


class ClientCitation(BaseModel):
    start_index: int
    end_index: int
    ref_index: int
    content: str
    score: float
    title: str
    citation_index: int | None = None
    uri: str

    def update_citation_index(self, citation_index: int):
        self.citation_index = citation_index

    def get_inline_link(self):
        # Ensure citation_index is an integer before performing the addition
        if self.citation_index is None:
            raise ValueError(
                "citation_index must be set to an integer before calling get_inline_link"
            )

        # Ref: https://www.markdownguide.org/basic-syntax/#adding-titles
        content = self.content.replace('"', "'")
        return f' _[[{self.citation_index}]({self.get_footer_link()} "{content}")]_'

    def get_footer_link(self):
        url = self.uri.replace("gs://", "https://storage.cloud.google.com/")
        url_encoded = quote(url, safe=":/")
        return url_encoded

    def count_chars(self):
        return len(self.get_inline_link())


class UserFeedback(int, Enum):
    THUMBS_UP = 1
    THUMBS_DOWN = 0


class FeedbackRequest(BaseModel):
    answer_query_token: str
    question: str
    answer_text: str
    feedback_value: UserFeedback
    feedback_text: str | None = None


class FeedbackResponse(BaseModel):
    answer_query_token: str
    message: str = "Feedback logged successfully."


class GetSessionResponse(BaseModel):
    sessions: list[dict[str, Any]]
