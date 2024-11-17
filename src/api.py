import logging
import os
import yaml

from fastapi import FastAPI
import google.auth

from model import QuestionModel, AnswerModel
from discoveryengine_utils import answer_query_sample


# Setup default logging and create a named logger.
logging.basicConfig(level=logging.DEBUG)
logger: logging.Logger = logging.getLogger(__name__)

# Load variables from the config.yaml file.
with open("config.yaml", "r") as file:
    config: dict = yaml.safe_load(file)

# Add the project ID to the config dictionary from Application Default Credentials.
config["project_id"] = google.auth.default()[1]
logger.info(f" config: {config}")

# Create a FastAPI app.
app = FastAPI()


@app.post("/answer", response_model=AnswerModel)
def answer(request: QuestionModel) -> AnswerModel:
    """ """
    # Get variables and log them.
    project_id: str = google.auth.default()[1]
    logger.debug(f"project_id: {project_id}")

    answer_query_response = answer_query_sample(
        query_text=request.question,
        project_id=project_id,
        location=config["location"],
        engine_id=config["search_engine_id"],
    )
    return AnswerModel(answer=answer_query_response.answer.answer_text)


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
