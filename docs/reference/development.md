# Development Guide

## Unit Tests

Run `pytest` using `poetry`.

**NOTE**: The tests will fail if you've used the [helper scripts](helper-scripts.md) to set the environment variables. Open a new shell session with a clean environment to run the tests.

### Setup

1. [Install Poetry](https://python-poetry.org/docs/#installation)

2. [Install dependencies](https://python-poetry.org/docs/basic-usage/#installing-dependencies).
```sh
cd answer-app # the root of the repository where this README and the pyproject.toml file is located - change the path if necessary
poetry install
```

### Running Tests

3. Run the tests.
```sh
poetry run pytest
```

4. Optionally run `pytest` with `coverage` and view the report.
```sh
poetry run coverage run -m pytest
poetry run coverage report -m
```

## Local Development

### Setup

- Complete the [deployment prerequisites](../installation/deployment.md#prerequisites) steps to configure `gcloud`.
- Set environment variables:
```sh
source scripts/set_variables.sh # change the path if necessary
```
- Install Poetry and the project dependencies (see [Unit Tests](#unit-tests)).
- Ensure the `client_secret` JSON file downloaded from the [OAuth web client](../installation/oauth-setup.md#2-create-an-oauth-client) is in the `.streamlit/secrets` directory.
- Write a local `.streamlit/secrets/secrets.toml` file (ignored by the local .gitignore) by running the `write_secrets` script with `poetry`.
    ```sh
    poetry run write_secrets
    ```

### Run with Poetry

#### Answer App Backend

The service will listen on local port 8888.
```sh
poetry run uvicorn main:app --app-dir src/answer_app --reload --host localhost --port 8888
```

#### Client Frontend

With the environment variables set using the [`set_variables.sh` script](../terraform/bootstrap.md), the `client` app automatically gets and impersonated ID token for the Terraform service account on behalf of the user and sets the target audience for requests to `localhost:8888`.

To solve unexpected communication issues, restart a fresh shell session to clear the environment, then re-source the `set_variables.sh` script.

```sh
poetry run streamlit run src/client/streamlit_app.py 
```

### Build with Docker

#### Answer App Backend

Uses the `Dockerfile` in the src/answer_app directory:
```sh
docker build -t local-answer-app:0.1.0 -f ./src/answer_app/Dockerfile . # change image name and tag as needed
```

#### Client Frontend

Uses a `Dockerfile` in the `src/client` directory:
```sh
docker build -t local-answer-app-client:0.1.0 -f ./src/client/Dockerfile . # change image name tag as needed
```

### Run with Docker

- Use `--rm` to remove the container when it exits.
- Use `-v` to mount the host's `gcloud` configuration directory to the container's `/root/.config/gcloud` directory to allow the app to use [Application Default Credentials](https://stackoverflow.com/questions/38938216/pass-google-default-application-credentials-in-local-docker-run) for authentication.
- Use `-e` to set container environment variables for the [Google Cloud project](https://stackoverflow.com/questions/74866327/oserror-whilst-trying-to-run-a-python-app-inside-a-docker-container-using-appl), log level, target service account, and audience.
- Use `-p` to map the container's port 8080 to the host's port 8888 or 8080 (specify port mapping as `-p <host-port>:<container-port>`).
- The `$PROJECT` and `$TF_VAR_terraform_service_account` environment variables will already be set after you ran the [`set_variables.sh`](../terraform/bootstrap.md) script.

#### Answer App Backend (call deployed backend)

```sh
docker run --rm -v ~/.config/gcloud:/root/.config/gcloud -e GOOGLE_CLOUD_PROJECT=$PROJECT -e LOG_LEVEL=DEBUG -e TF_VAR_terraform_service_account=$TF_VAR_terraform_service_account -e TARGET_AUDIENCE="https://answer-app-hash-uc.a.run.app" -p 8888:8080 local-answer-app:0.1.0
```

#### Client (call local backend)

```sh
docker run --rm -v ~/.config/gcloud:/root/.config/gcloud -e GOOGLE_CLOUD_PROJECT=$PROJECT -e LOG_LEVEL=DEBUG -e TF_VAR_terraform_service_account=$TF_VAR_terraform_service_account -e TARGET_AUDIENCE="http://host.docker.internal:8888" -p 8080:8080 local-answer-app-client:0.1.0
```

#### Client (call deployed backend)

```sh
docker run --rm -v ~/.config/gcloud:/root/.config/gcloud -e GOOGLE_CLOUD_PROJECT=$PROJECT -e LOG_LEVEL=DEBUG -e TF_VAR_terraform_service_account=$TF_VAR_terraform_service_account -e TARGET_AUDIENCE="https://answer-app-hash-uc.a.run.app" -p 8080:8080 local-answer-app-client:0.1.0
```

### Debug a Container

```sh
docker run --rm -it --entrypoint=/bin/bash local-answer-app:0.1.0
```