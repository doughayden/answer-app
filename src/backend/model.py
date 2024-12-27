from urllib.parse import quote

from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
    session_id: str | None = None


class AnswerResponse(BaseModel):
    question: str
    markdown: str
    latency: float
    answer: dict
    session: dict | None
    answer_query_token: str | None


class HealthCheckResponse(BaseModel):
    status: str = "ok"


class EnvVarResponse(BaseModel):
    name: str
    value: str | None


class ClientCitation(BaseModel):
    title: str
    score: float
    start_index: int
    end_index: int
    chunk_index: int
    link: str

    def get_inline_link(self):
        return f"_[[{self.chunk_index+1}]({self.get_footer_link()})]_"

    def get_footer_link(self):
        url = self.link.replace("gs://", "https://storage.cloud.google.com/")
        url_encoded = quote(url, safe=":/")
        return url_encoded

    def count_chars(self):
        return len(self.get_inline_link())
