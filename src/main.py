import logging
import os
import time

from fastapi import FastAPI, HTTPException, Query

from model import (
    QuestionRequest,
    AnswerResponse,
    HealthCheckResponse,
    EnvVarResponse,
)
from utils import UtilHandler


logger = logging.getLogger(__name__)

# Initialize a utility handler.
utils = UtilHandler(log_level=os.getenv("LOG_LEVEL", "INFO").upper())

# Create a FastAPI app.
app = FastAPI()


@app.post("/answer", response_model=AnswerResponse)
async def answer(request: QuestionRequest) -> AnswerResponse:
    """Answer a question using the Discovery Engine Answer method."""
    # Start the timer.
    start_time = time.time()

    # Log the request.
    logger.info(f"Received question: {request.question}")
    logger.info(f"Session: {request.session}")

    try:
        # Get an answer to the question.
        response = await utils.answer_query(
            query_text=request.question,
            session=request.session,
        )

        # Convert the response to a dict and add the question as a new key.
        data = response.model_dump(mode="json")
        data["question"] = request.question

        # Log details to BigQuery.
        errors = await utils.bq_insert_row_data(
            data=data,
        )
        if errors:
            logger.error(f"Errors loading to Big Query: {errors}")
            raise HTTPException(status_code=500, detail=str(errors))

        # Log the full time taken to answer the question.
        elapsed_time = time.time() - start_time
        logger.info(f"Returned an answer in {elapsed_time:.2f} seconds")

        return response

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/healthz", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    """Provides a health pulse for Cloud Deployment"""
    return HealthCheckResponse()


@app.get("/get-env-variable", response_model=EnvVarResponse)
def get_env_variable(name: str = Query(...)) -> EnvVarResponse:
    """Return the value of an environment variable.
    Ref: https://cloud.google.com/run/docs/testing/local#cloud-code-emulator_1
    """
    # return {name: os.environ.get(name, f"No variable set for '{name}'")}
    return EnvVarResponse(name=name, value=os.environ.get(name, None))
