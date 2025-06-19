# Vertex AI Agent Builder Answer App

A production-ready conversational search application that leverages [Vertex AI Agent Builder](https://cloud.google.com/generative-ai-app-builder/docs/introduction) and the [Discovery Engine API](https://cloud.google.com/generative-ai-app-builder/docs/reference/rest) to serve a [conversational search experience](https://cloud.google.com/generative-ai-app-builder/docs/answer) with generative answers grounded on document data.

## Why Use This?

- **Fully-managed conversational search**: Uses the [Answer method](https://cloud.google.com/generative-ai-app-builder/docs/reference/rpc/google.cloud.discoveryengine.v1#conversationalsearchservice) for stateful multi-turn conversational search with generative answers
- **Production-capable performance**: Autoscaling, concurrency, and regional redundancy via multiple Cloud Run services
- **Integration flexibility**: Authenticated external HTTPS endpoint for 3rd party systems (using Google-managed TLS)
- **Resource observability**: Single-pane-of-glass Cloud Monitoring dashboard with customizable metrics and alerts
- **Explainable and debuggable results**: Investigate generative answers using the full RAG pipeline results logged to BigQuery
- **Data-driven LLM-ops**: Tune the conversational search agent using question/answer pairs labelled with user feedback
- **Identity-Aware Proxy**: Secure access control
- **Automated deployments**: One-click install and uninstall with Terraform and Cloud Build

## Architecture

![Application Architecture](assets/answer_app.png)

- Client requests reach the application through the [Cloud Load Balancer](https://cloud.google.com/load-balancing/docs/https)
- The [backend service](https://cloud.google.com/load-balancing/docs/backend-service) interfaces with regional [serverless network endpoint groups](https://cloud.google.com/load-balancing/docs/backend-service#serverless_network_endpoint_groups) composed of [Cloud Run](https://cloud.google.com/run/docs/overview/what-is-cloud-run) services
- [Vertex AI Agent Builder](https://cloud.google.com/generative-ai-app-builder/docs/introduction) provides the [Search App and Data Store](https://cloud.google.com/generative-ai-app-builder/docs/create-datastore-ingest) for document search and retrieval
- The application asynchronously writes log data and user feedback responses to [BigQuery](https://cloud.google.com/bigquery/docs/introduction) for offline analysis

## Quick Start

### Prerequisites

- Google Cloud Project with Owner permissions
- [Terraform](https://developer.hashicorp.com/terraform) and [`gcloud` CLI](https://cloud.google.com/sdk/gcloud) installed

See detailed [deployment prerequisites →](docs/installation/deployment.md#prerequisites)

### Installation

1. **Configure OAuth consent screen** for user authentication  
   📖 [Complete OAuth setup guide →](docs/installation/oauth-setup.md)

2. **Deploy the application**
   ```sh
   source scripts/install.sh
   ```
   📖 [Detailed deployment guide →](docs/installation/deployment.md)

3. **Enable Vertex AI Agent Builder** in the Cloud Console and import your documents

4. **Configure Identity-Aware Proxy** to secure access

📖 [View complete installation guide →](docs/installation/deployment.md)

## Documentation

### Installation & Deployment
- [📋 Prerequisites & Deployment](docs/installation/deployment.md) - Environment setup and deployment steps
- [🔐 OAuth Setup Guide](docs/installation/oauth-setup.md) - Step-by-step OAuth consent screen configuration

### Development
- [🧪 Development Guide](docs/reference/development.md) - Local development, testing, and Docker usage
- [📖 API Reference](docs/reference/api-configuration.md) - Answer method configuration options
- [🛠️ Helper Scripts](docs/reference/helper-scripts.md) - Automation scripts reference

### Infrastructure
- [🏗️ Terraform Overview](docs/terraform/overview.md) - General Terraform patterns and best practices (reusable)
- [🚀 Bootstrap Process](docs/terraform/bootstrap.md) - Initial project setup and service accounts
- [☁️ Cloud Build Automation](docs/terraform/cloud-build.md) - Automated deployments and rollbacks

### Troubleshooting
- [❗ Known Issues](docs/troubleshooting/known-issues.md) - Common problems and solutions

## Uninstall

Remove all resources:
```sh
source scripts/uninstall.sh
```

## Development

This project uses:
- **Python 3.13+** with Poetry for dependency management
- **FastAPI** backend with **Streamlit** frontend
- **Terraform** for infrastructure as code
- **pytest** for testing

```sh
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run locally
poetry run uvicorn main:app --app-dir src/answer_app --reload --host localhost --port 8888
poetry run streamlit run src/client/streamlit_app.py
```

📖 [Full development guide →](docs/reference/development.md)

## Repository Structure

```
answer-app/
├── src/
│   ├── answer_app/          # FastAPI backend service
│   ├── client/              # Streamlit frontend application
│   └── package_scripts/     # Helper scripts (OAuth secrets)
├── terraform/
│   ├── bootstrap/           # Initial project setup
│   ├── main/                # Main infrastructure deployment
│   └── modules/             # Reusable Terraform modules
├── docs/                    # Modular documentation
│   ├── installation/        # Setup guides
│   ├── terraform/           # Infrastructure documentation
│   ├── reference/           # Development & API docs
│   └── troubleshooting/     # Known issues & solutions
├── scripts/                 # Automation scripts
├── tests/                   # Unit tests
└── assets/                  # Documentation screenshots
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.