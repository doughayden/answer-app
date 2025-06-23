# Development Guide

[← Back to README](../../README.md)

## Unit Tests

Run `pytest` using `poetry`. The test suite is designed to run in any environment without requiring Google Cloud credentials or authentication setup.

**NOTE**: The tests will fail if you've used the [helper scripts](../infrastructure/helper-scripts.md#configuration-scripts) to set the environment variables. Open a new shell session with a clean environment to run the tests.

### Test Features

- **Zero external dependencies**: Tests run without requiring Google Cloud credentials or environment variables
- **Comprehensive auth mocking**: All `google.auth.default()` calls are intercepted during pytest collection
- **Coverage**: Complete test coverage for all major components
- **CI/CD ready**: Tests pass consistently in GitHub Actions and local environments

### Setup

1. [Install Poetry](https://python-poetry.org/docs/#installation)

2. [Install dependencies](https://python-poetry.org/docs/basic-usage/#installing-dependencies).
```sh
cd answer-app # the root of the repository where the pyproject.toml file is located - change the path if necessary
poetry install
```

### Running Tests

Run the tests.
```sh
poetry run pytest
```

Optionally run `pytest` with `coverage` and view the report.
```sh
poetry run coverage run -m pytest
poetry run coverage report -m
```

## Continuous Integration

The project uses [GitHub Actions](../../.github/workflows/release.yml) for automated testing and releases with a split workflow design:

### Workflow Structure

- **Test Job**: Runs on all pushes and pull requests to `main` branch
  - Executes full test suite
  - Validates code quality and functionality
  - No authentication required due to comprehensive mocking
  
- **Release Job**: Runs only on pushes to `main` branch (not on PRs)
  - Uses Python Semantic Release for automated versioning
  - Prevents failed workflow runs on feature branch PRs
  - Automatically generates changelogs and version bumps

### Benefits

- **Clean PR workflows**: No failed semantic-release runs on feature branches
- **Consistent testing**: All tests pass without external dependencies
- **Automated versioning**: Conventional commits trigger appropriate version bumps
- **Zero maintenance**: No credential management needed for CI environment

## Local Development

### Prerequisites

- Complete the [deployment prerequisites](../installation/prerequisites.md) steps to configure `gcloud`.
- Set [environment variables](../infrastructure/helper-scripts.md#environment-variables-set):
```sh
source scripts/set_variables.sh # change the path if necessary
```
- Install Poetry and the project dependencies (see [Unit Tests](#unit-tests)).
- Ensure the `client_secret` JSON file downloaded from the [OAuth web client](../installation/oauth-setup.md#2-create-an-oauth-client) is in the [`.streamlit/secrets`](../../.streamlit/secrets) directory.
- Write a local `.streamlit/secrets/secrets.toml` file (ignored by the local .gitignore) by running the [`write_secrets`](../../pyproject.toml#project.scripts) script with `poetry`.
```sh
poetry run write_secrets
```

### Run with Poetry

#### Answer App Backend

The service will listen on local port 8888.
```sh
poetry run uvicorn main:app --app-dir src/answer_app --reload --host localhost --port 8888
```

#### Client (call local backend)

With the environment variables set using the [`set_variables.sh` script](../infrastructure/helper-scripts.md#configuration-scripts), the `client` app automatically gets an impersonated ID token for the Terraform service account on behalf of the user and sets the target audience for requests to `localhost:8888`.

To solve unexpected communication issues, restart a fresh shell session to clear the environment, then re-source the `set_variables.sh` script.

```sh
poetry run streamlit run src/client/streamlit_app.py 
```

#### Client (call deployed backend)

Use the [`set_audience.sh`](../infrastructure/helper-scripts.md#testing-scripts) script to set the target audience to the deployed backend URL.

```sh
source scripts/set_audience.sh # change the path if necessary
poetry run streamlit run src/client/streamlit_app.py
```

### Build with Docker

#### Answer App Backend

Uses the `Dockerfile` in the `src/answer_app` directory:
```sh
docker build -t local-answer-app:0.2.0 -f ./src/answer_app/Dockerfile . # change image name and tag as needed
```

#### Client

Uses the `Dockerfile` in the `src/client` directory:
```sh
docker build -t local-answer-app-client:0.2.0 -f ./src/client/Dockerfile . # change image name tag as needed
```

### Run with Docker

- `--rm`: (remove) remove the container when it exits.
- `-v`: (volume) mount the host's `gcloud` configuration directory to the container's `/root/.config/gcloud` directory to allow the app to use [Application Default Credentials](https://stackoverflow.com/questions/38938216/pass-google-default-application-credentials-in-local-docker-run) for authentication.
- `-e`: (environment) set container environment variables for the [Google Cloud project](https://stackoverflow.com/questions/74866327/oserror-whilst-trying-to-run-a-python-app-inside-a-docker-container-using-appl), log level, target service account, and audience.
- `-p`: (port) map the container's port 8080 to the host's port 8888 (specify port mapping as `-p <host-port>:<container-port>`).
- The `$PROJECT` and `$TF_VAR_terraform_service_account` environment variables will already be set after you ran the [`set_variables.sh`](#prerequisites) script.

#### Answer App Backend (call deployed backend)

Map container port 8080 to localhost:8888
```sh
docker run --rm -v $HOME/.config/gcloud:/root/.config/gcloud \
-e GOOGLE_CLOUD_PROJECT=$PROJECT \
-e LOG_LEVEL=DEBUG \
-p 8888:8080 local-answer-app:0.2.0 # change image name and tag as needed
```

#### Client (call local backend)

Map container port 8080 to localhost:8080 and call the **LOCAL** `answer-app` service at localhost:8888
```sh
docker run --rm -v $HOME/.config/gcloud:/root/.config/gcloud \
-e GOOGLE_CLOUD_PROJECT=$PROJECT \
-e LOG_LEVEL=DEBUG \
-e "TF_VAR_terraform_service_account=$TF_VAR_terraform_service_account" \
-p 8080:8080 local-answer-app-client:0.2.0 # change env vars and image name and tag as needed
```

Open your Chrome browser to `http://localhost:8080`.
```sh
open -a "/Applications/Google Chrome.app" http://localhost:8080
```

#### Client (call deployed backend)

Map container port 8080 to localhost:8080 and call the **DEPLOYED** `answer-app` service at `https://app.mydomain.com/answer-app`

- To target the deployed `answer-app` backend service, set the `AUDIENCE` environment variable to the custom audience for the `answer-app` service (see [Helper Scripts](../infrastructure/helper-scripts.md#testing-scripts) `set_audience.sh`).
- **NOTE**: You may want to unset the `AUDIENCE` environment variable after testing the deployed service if you want to continue local-only testing.
```sh
source scripts/set_audience.sh # change the path if necessary
docker run --rm -v $HOME/.config/gcloud:/root/.config/gcloud \
-e GOOGLE_CLOUD_PROJECT=$PROJECT \
-e LOG_LEVEL=DEBUG \
-e "TF_VAR_terraform_service_account=$TF_VAR_terraform_service_account" \
-e "AUDIENCE=$AUDIENCE" \
-p 8080:8080 local-answer-app-client:0.2.0 # change env vars and image name and tag as needed
```

Open your browser to `http://localhost:8080`.
```sh
open -a "/Applications/Google Chrome.app" http://localhost:8080
```

### Debug a Container

Open a `sh` shell in the container image.
```sh
docker run --entrypoint /bin/sh --rm -it local-answer-app-client:0.2.0 
```
