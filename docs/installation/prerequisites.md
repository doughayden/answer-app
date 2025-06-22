# Deployment Prerequisites

[← Back to README](../../README.md)

- Your Google user account must be a [Project Owner](https://cloud.google.com/iam/docs/roles-overview#legacy-basic) in the target Google Cloud project.
- Choose one of the following options to install and configure [Terraform](https://developer.hashicorp.com/terraform) and the [`gcloud` CLI](https://cloud.google.com/sdk/gcloud) for your development environment:
    - Follow the instructions in [OPTION 1](#option-1-deploying-from-google-cloud-shell) to configure deployment using [Google Cloud Shell](https://cloud.google.com/shell/docs/using-cloud-shell).
    - Follow the instructions in [OPTION 2](#option-2-deploying-outside-of-google-cloud-shell) to configure deployment from your local terminal.

## OPTION 1: Deploying from Google Cloud Shell

Use [Cloud Shell](https://cloud.google.com/shell/docs/using-cloud-shell) for a convenient environment with `gcloud` and `terraform` pre-installed. Your user account (`core.account`) and default project (`core.project`) should already be set in the Cloud Shell environment.

1. Select your target deployment project in the [Cloud Console](https://console.cloud.google.com/projectselector2/home/dashboard).
2. [Open Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell) and confirm your `gcloud` configuration.
```sh
gcloud config list --format=yaml
```
Example output:
```yaml
accessibility:
  screen_reader: 'True'
component_manager:
  disable_update_check: 'True'
compute:
  gce_metadata_read_timeout_sec: '30'
core:
  account: project-owner@example.com
  disable_usage_reporting: 'False'
  project: my-project-id
metrics:
  environment: devshell
```

3. Optionally, set the default compute region (`compute.region`). The helper script will default to `us-central1` if your `gcloud` configuration does not specify a region.
    - Agree to enable the `compute.googleapis.com` API if prompted.
```sh
gcloud config set compute/region 'region' # replace with your preferred region, e.g. us-central1
```

4. Set any other [configuration values](https://cloud.google.com/sdk/gcloud/reference/config/set) as needed.

5. Consider using Personal Access Tokens (PATs) to [clone the repo](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token) as an alternative to managing SSH keys in Cloud Shell.

## OPTION 2: Deploying outside of Google Cloud Shell

1. Install [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli).
2. Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
3. Authenticate.
```sh
gcloud auth login
```

4. Set the target deployment project as your default.
```sh
gcloud config set project 'my-project-id' # replace with your project ID
```

5. Configure [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials) for local development.
```sh
gcloud auth application-default login
```

6. Optionally, set the default compute region (`compute.region`). The helper script will default to `us-central1` if your `gcloud` configuration does not specify a region.
    - Agree to enable the `compute.googleapis.com` API if prompted.
```sh
gcloud config set compute/region 'region' # replace with your preferred region, e.g. 'us-central1'
```

7. [Clone the repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) and open a terminal session in the repo root directory.
