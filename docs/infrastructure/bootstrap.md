# Bootstrap

[← Back to README](../../README.md)

The `bootstrap.sh` script automates the `gcloud` and `terraform` commands required to prepare the project.

## What Bootstrap Does

- Source the `set_variables.sh` script to configure the shell environment, including [Terraform environment variables](https://developer.hashicorp.com/terraform/language/values/variables#environment-variables). (Used automatically by later Terraform commands.).
- Enable the Service Usage, IAM, and Service Account Credentials APIs.
- Create a service account for Terraform provisioning.
- Grant the required [IAM roles](https://cloud.google.com/iam/docs/understanding-roles) to the service account.
- Prepare [Service Account Impersonation](https://cloud.google.com/iam/docs/service-account-impersonation) for the caller's user account.
- Create a Terraform [remote state](https://developer.hashicorp.com/terraform/language/state/remote) bucket.
- Initialize the Terraform `bootstrap` module and apply to provision resources required for the main module:
  - Project APIs.
  - Cloud Build service account.
  - Artifact Registry repository.
  - IAM role bindings for the Cloud Build service account:
      - Project IAM policy: Cloud Build Service Account (`roles/cloudbuild.builds.builder`) role.
      - Terraform service account IAM policy: Service Account Token Creator (`roles/iam.serviceAccountTokenCreator`) role.

## Running Bootstrap

Source the `bootstrap.sh` script to set your shell variables and run the Terraform commands:

```sh
source scripts/bootstrap.sh # change the path if necessary
```

## Un-Bootstrap

<span style="color: red;">**WARNING: THIS WILL DELETE YOUR TERRAFORM STATE**</span>

The `un_bootstrap.sh` script automates `gcloud` commands to remove these project resources created by the `bootstrap` script. It does not disable any APIs. 
- Terraform state bucket
- Terraform service account project role bindings
- Terraform service account resource

## Running Un-Bootstrap

Source the `un_bootstrap.sh` script to remove the resources:

```sh
source scripts/un_bootstrap.sh # change the path if necessary
```
