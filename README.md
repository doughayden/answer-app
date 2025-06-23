# Answer App

![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-623CE4?style=flat&logo=terraform&logoColor=white)

A production-ready Retrieval-Augmented Generation (RAG) server that uses [Vertex AI Search](https://cloud.google.com/generative-ai-app-builder/docs/introduction) and the [Discovery Engine API](https://cloud.google.com/generative-ai-app-builder/docs/reference/rest) to serve the **Answer method** - a [conversational search experience](https://cloud.google.com/generative-ai-app-builder/docs/answer) with generative answers grounded on document data.

- 🤖 **Fully-managed RAG pipeline**: Stateful multi-turn conversational search with generative answers
- ⚡ **Production-capable performance**: Autoscaling, concurrency, and regional redundancy via multiple Cloud Run services
- 🔗 **Integration flexibility**: Authenticated external HTTPS endpoint using Google-managed TLS
- 📊 **Resource observability**: Single-pane-of-glass Cloud Monitoring dashboard with customizable metrics and alerts
- 🔍 **Explainable and debuggable results**: Investigate generative answers using the full RAG pipeline results logged to BigQuery
- 📈 **Data-driven LLM-ops**: Tune the conversational search agent using question/answer pairs labelled with user feedback
- 🛡️ **Identity-Aware Proxy**: Secure access control
- 👤 **Google OAuth**: Personalized sessions with user authentication
- 🚀 **Automated deployments**: One-click install and uninstall with Terraform and Cloud Build

## Architecture

![Application Architecture](assets/answer_app.png)

- The [Global External Application Load Balancer](https://cloud.google.com/load-balancing/docs/https) provides planet-scale availability
- The [load balancer backend service](https://cloud.google.com/load-balancing/docs/backend-service) interfaces with regional [serverless network endpoint group backends](https://cloud.google.com/load-balancing/docs/backend-service#serverless_network_endpoint_groups) composed of [Cloud Run](https://cloud.google.com/run/docs/overview/what-is-cloud-run) services
    - Zonal failover: Cloud Run services [replicate](https://cloud.google.com/run/docs/resource-model#services) across multiple zones within a [Compute region](https://cloud.google.com/run/docs/locations) to prevent outages for a single zonal failure
    - [Autoscaling](https://cloud.google.com/run/docs/about-instance-autoscaling): add/remove instances to match demand and maintain a minimum instance count for high availability
    - [Concurrency](https://cloud.google.com/run/docs/about-concurrency): instances process multiple requests simultaneously
    - [Regional redundancy](https://cloud.google.com/run/docs/multiple-regions): services can span multiple regions to optimize latency and optionally deliver higher availability in case of regional outages.
- The Vertex AI Search [Search App and Data Store](https://cloud.google.com/generative-ai-app-builder/docs/create-datastore-ingest) automate document preparation for semantic search and retrieval
- The [Conversational Search Service](https://cloud.google.com/generative-ai-app-builder/docs/reference/rpc/google.cloud.discoveryengine.v1#conversationalsearchservice) (the interface for the Answer method) uses Gemini-based [answer generation models](https://cloud.google.com/generative-ai-app-builder/docs/answer-generation-models) to power grounded generative answers
- The application asynchronously writes the full session data and user feedback responses to [BigQuery](https://cloud.google.com/bigquery/docs/introduction) for offline analysis

## Quick Start

### Prerequisites

- Google Cloud Project with Owner permissions
- [Terraform](https://developer.hashicorp.com/terraform) and [`gcloud` CLI](https://cloud.google.com/sdk/gcloud) installed

See detailed [deployment prerequisites →](docs/installation/prerequisites.md)

### Installation

1. **Configure OAuth** for user authentication  
   📖 [Complete OAuth setup guide →](docs/installation/oauth-setup.md)

2. **Deploy the application**
   ```sh
   source scripts/install.sh
   ```

3. **Enable Vertex AI Agent Builder** in the Cloud Console and import your documents

4. **Configure Identity-Aware Proxy** to secure access

📖 [View complete installation guide →](docs/installation/deployment.md)

## Documentation

### Installation & Deployment
- [✅ Prerequisites](docs/installation/prerequisites.md) - Environment setup
- [🔐 OAuth Setup Guide](docs/installation/oauth-setup.md) - Step-by-step OAuth client configuration
- [📋 Deployment](docs/installation/deployment.md) - Deployment and Post-deployment steps

### Development
- [🧪 Development Guide](docs/development/development.md) - Local development, testing, and Docker usage
- [📖 API Reference](docs/development/api-configuration.md) - Answer method configuration options
- [🏷️ Version Management](docs/development/version-management.md) - Automated semantic release and versioning

### Infrastructure
- [🏗️ Terraform Overview](docs/infrastructure/terraform.md) - General Terraform patterns and best practices (reusable)
- [🚀 Bootstrap Process](docs/infrastructure/bootstrap.md) - Initial project setup and service accounts
- [☁️ Cloud Build Automation](docs/infrastructure/cloud-build.md) - Automated deployments and CI/CD
- [🔄 Rollbacks](docs/infrastructure/rollbacks.md) - Rolling back deployments and managing revisions
- [⚙️ Infrastructure Changes](docs/infrastructure/cloud_infra_changes.md) - Applying infrastructure-only changes
- [🛠️ Helper Scripts](docs/infrastructure/helper-scripts.md) - Automation scripts reference

### Troubleshooting
- [❗ Known Issues](docs/troubleshooting/known-issues.md) - Common problems and solutions

## Uninstall

Remove all resources:
```sh
source scripts/uninstall.sh
```

## Development

This project uses:
- **Python 3.13+** with **Poetry** for dependency management
- **FastAPI** backend with an example **Streamlit** frontend
- **Terraform** for infrastructure as code
- **pytest** for testing

📖 [Full development guide →](docs/development/development.md)

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
│   ├── infrastructure/      # Infrastructure documentation
│   ├── development/         # Development & API docs
│   └── troubleshooting/     # Known issues & solutions
├── scripts/                 # Automation scripts
├── tests/                   # Unit tests
└── assets/                  # Documentation screenshots
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
