# Rollbacks

[← Back to README](../../README.md)

## Option 1: Use the Cloud Console to switch Cloud Run service traffic to a different revision

**THIS WILL CHANGE STATE OUTSIDE OF TERRAFORM CONTROL**

- Navigate to the Cloud Run service in the Cloud Console.
- Click the 'Revisions' tab.
- Click 'MANAGE TRAFFIC'.
- Select the target revision and traffic percentage (100% to rollback completely to another revision).
- Click 'SAVE'.

## Option 2: Rollback to a different Docker image using Terraform

- Identify the rollback target Docker image.
- Pass the target image name and tag to the `docker_image` [input variable](https://developer.hashicorp.com/terraform/language/values/variables#assigning-values-to-root-module-variables) in the `main` root module.
    - Use a `.tfvars` file, the `-var` command line argument, or the `TF_VAR_` [environment variable](https://developer.hashicorp.com/terraform/language/values/variables#environment-variables).
- Apply the Terraform configuration to update the Cloud Run service to the rollback target.

### Example: select an image by digest or tag from Artifact Registry.

1. Source the `set_variables.sh` script to configure the shell environment (provides variables including `PROJECT` and `BUCKET`). Refer to the [Prerequisites](../installation/prerequisites.md) section for details on configuring the `gcloud` CLI.
```sh
source scripts/set_variables.sh # change the path if necessary
```

2. Initialize the Terraform `main` module configuration with the remote state by passing required arguments to the [partial backend configuration](https://developer.hashicorp.com/terraform/language/settings/backends/configuration#partial-configuration).
    - See the [Terraform Backends](terraform.md#terraform-backends) section for more information.
    - You might need to [reconfigure the backend](terraform.md#reconfiguring-a-backend) if you've already initialized the module.
```sh
cd terraform/main # change the path if necessary
terraform init -backend-config="bucket=$BUCKET" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" -reconfigure
```

3. Set the Terraform input environment variable `TF_VAR_docker_image` to the target image names.
    - The variable value is a JSON object with key-value pairs for each service name and corresponding image name.
    - Don't include spaces or line breaks in the JSON string when setting this environment variable.
    - This example uses the tag Terraform adds to image names corresponding to the Cloud Build ID.
    - You can also use the image digest, e.g., `us-central1-docker.pkg.dev/my-project-id/answer-app/answer-app@sha256:4f2092b926b7e9dc30813e819bb86cfa7d664eede575539460b4a68bbd4981e1`.
```sh
export TF_VAR_docker_image='{"answer-app":"us-central1-docker.pkg.dev/my-project-id/answer-app/answer-app:50bde371-76f8-452a-8a17-9b63273f13e0"}'
```

- Apply the Terraform configuration to update the Cloud Run service to the target image.
```sh
terraform apply
```
