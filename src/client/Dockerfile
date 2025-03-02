FROM python:3.13-bookworm AS builder

RUN pip install poetry==2.0.0

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

FROM python:3.13-slim-bookworm AS runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY src/client ./client
COPY .streamlit .streamlit

EXPOSE 8080

ENTRYPOINT ["streamlit", "run", "client/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
