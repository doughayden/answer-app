import logging
import os
import time

from fastapi import FastAPI, HTTPException, Query

from answer_app.model import (
    QuestionRequest,
    AnswerResponse,
    HealthCheckResponse,
    EnvVarResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from answer_app.utils import sanitize, UtilHandler


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
    logger.info(f"Received question: {sanitize(request.question)}")
    request_session_id = request.session_id or "None"
    logger.info(f"Received session_id: {sanitize(request_session_id)}")

    try:
        # Get an answer to the question.
        response = await utils.answer_query(
            query_text=request.question,
            session_id=request.session_id,
        )

        # Dump the response model to a dictionary for loading to BigQuery.
        data = response.model_dump()

        # Log details to BigQuery.
        errors = await utils.bq_insert_row_data(
            data=data,
        )
        if errors:
            logger.error(f"Errors loading to Big Query: {errors}")
            raise HTTPException(status_code=500, detail=str(errors))

        # Log the full time taken to answer the question.
        elapsed_time = time.time() - start_time
        logger.info(f"Returned an answer in {elapsed_time:.2f} seconds.")

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
    return EnvVarResponse(name=name, value=os.environ.get(name, None))


@app.post("/feedback", response_model=FeedbackResponse)
async def log_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Log feedback from the user."""
    # Log the request.
    logger.info(f"Received answer_query_token: {sanitize(request.answer_query_token)}")
    logger.info(f"Received feedback: {sanitize(request.feedback_value.name)}")
    if request.feedback_text:
        logger.info(f"Received feedback text: {sanitize(request.feedback_text)}")

    # Dump the feedback model to a dictionary for loading to BigQuery.
    data = request.model_dump()

    # Add the feedback name to the data dictionary.
    data["feedback_name"] = request.feedback_value.name

    # Log the feedback to BigQuery.
    errors = await utils.bq_insert_row_data(data=data, feedback=True)

    if errors:
        logger.error(f"Errors loading to Big Query: {errors}")
        raise HTTPException(status_code=500, detail=str(errors))

    return FeedbackResponse(answer_query_token=request.answer_query_token)
