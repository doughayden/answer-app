import logging
import os

from fastapi import FastAPI

from model import Question, StructuredResponse
from utils import UtilHandler


logger = logging.getLogger(__name__)

# Initialize a utility handler.
utils = UtilHandler(log_level=os.getenv("LOG_LEVEL", "INFO").upper())

# Create a FastAPI app.
app = FastAPI()


@app.post("/answer", response_model=StructuredResponse)
async def answer(request: Question) -> StructuredResponse:
    """Answer a question using the Discovery Engine Answer method."""
    # Get an answer to the question.
    response = await utils.answer_query_sample(
        query_text=request.question,
    )

    # Convert the response to a dict and add the question as a new key.
    data = response.model_dump(mode="json")
    data["question"] = request.question

    # Log details to BigQuery.
    errors = await utils.bq_insert_row_data(
        data=data,
    )
    if errors:
        logger.error(f"Errors: {errors}")

    return response


@app.get("/healthz")
def health_check() -> dict:
    """Provides a health pulse for Cloud Deployment"""
    return {"status": "ok"}


@app.get("/get-env-variable")
def get_env_variables(name: str) -> dict:
    """Return the value of an environment variable.
    Ref: https://cloud.google.com/run/docs/testing/local#cloud-code-emulator_1
    """
    return {name: os.environ.get(name, f"No variable set for '{name}'")}
