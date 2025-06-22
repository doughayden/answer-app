# Automate Deployments with Cloud Build

[← Back to README](../../README.md)

Use [`gcloud builds submit`](https://cloud.google.com/build/docs/running-builds/submit-build-via-cli-api) with [build config files](https://cloud.google.com/build/docs/configuring-builds/create-basic-configuration) to plan and deploy project resources.

## 1. Set Configuration Values

Verify/Change parameters as needed in `config.yaml`:
- [`config.yaml`](../../src/answer_app/config.yaml)
- Refer to [Connect Cloud Run services to an existing load balancer](#connect-cloud-run-services-to-an-existing-load-balancer) for configuration requirements when using a Load Balancer managed outside of this Terraform configuration.

## 2. Set Environment Variables

Source the `set_variables.sh` script to configure the shell environment.

```sh
source scripts/set_variables.sh # change the path if necessary
```

## 3. Build & Push Docker Images and Apply Terraform

Use `gcloud` to submit the build from the repository root directory as the build context.

- **[OPTIONAL]** Omit the `_RUN_TYPE=apply` substitution to run a plan-only build and review the Terraform changes before applying.

```sh
cd /path/to/git-repo-root # replace with the local system path to the git repository root directory
gcloud builds submit . --config=cloudbuild.yaml --project=$PROJECT --region=$REGION --substitutions="_RUN_TYPE=apply"
```

- Review the build logs in the [Cloud Build History](https://cloud.google.com/build/docs/view-build-results) to verify the build and deployment status.

## Connect Cloud Run Services to an Existing Load Balancer

Edit and verify these files to connect the Cloud Run services to an existing load balancer:

### [`config.yaml: create_loadbalancer`](../../src/answer_app/config.yaml)

Set `create_loadbalancer = false`

### [`config.yaml: loadbalancer_domain`](../../src/answer_app/config.yaml)

Set `loadbalancer_domain` to the name of your existing domain.

### [`cloudrun.tf`](../../terraform/modules/answer-app/cloudrun.tf#L87)

- Ensure the Terraform `cloud-run` module resource `google_compute_backend_service.run_app` argument [`load_balancing_scheme`](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_backend_service#load_balancing_scheme) matches the existing [load balancer type](https://cloud.google.com/load-balancing/docs/backend-service).
  - Use `load_balancing_scheme = "EXTERNAL_MANAGED"` for the Global external Application Load Balancer.
  - Use `load_balancing_scheme = "EXTERNAL"` for the Classic Application Load Balancer.
- Cloud Run services will use the load balancer domain in the custom audience for authentication.
- You must connect the backend services to the existing load balancer outside of this repo's Terraform configuration.
