# Execute Terraform to apply infrastructure-only changes to the `bootstrap` or `main` module.

[← Back to README](../../README.md)

Applying the resources from the `bootstrap` module is a one-time setup for a new project. You can re-run it, for example, to add or enable additional APIs to support future development. You can apply infrastructure-only changes to the `main` module to update cloud resources without rebuilding the Docker images (and without using Cloud Build). If you don't provide docker image names as input variables, the `main` retrieves the last-deployed Docker images from the module state and reuses them in the Cloud Run services.

1. Source the `set_variables.sh` script to configure the shell environment (provides variables including `PROJECT` and `BUCKET`). Refer to the [Prerequisites](../installation/prerequisites.md) section for details on configuring the `gcloud` CLI.
```sh
source scripts/set_variables.sh # change the path if necessary
```

2. Initialize the Terraform `main` or `bootstrap` module using a [partial backend configuration](https://developer.hashicorp.com/terraform/language/settings/backends/configuration#partial-configuration).
    - See the [Terraform Backends](terraform.md#terraform-backends) section for more information.
    - You might need to [reconfigure the backend](terraform.md#reconfiguring-a-backend) if you've already initialized the module.
```sh
cd terraform/main # or cd terraform/bootstrap, change the path if necessary
terraform init -backend-config="bucket=$BUCKET" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" -reconfigure
```

3. Apply the Terraform configuration to provision the cloud resources.
```sh
terraform apply
```
