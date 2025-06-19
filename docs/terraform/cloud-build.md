# Automate Deployments with Cloud Build

Use [`gcloud builds submit`](https://cloud.google.com/build/docs/running-builds/submit-build-via-cli-api) with [build config files](https://cloud.google.com/build/docs/configuring-builds/create-basic-configuration) to plan and deploy project resources.

## 1. Set Configuration Values

Verify/Change parameters as needed in `config.yaml`:
- [`config.yaml`](../../src/answer_app/config.yaml)
- Refer to [Connect cloud run services to an existing load balancer](#connect-cloud-run-services-to-an-existing-load-balancer) for configuration requirements when using a Load Balancer managed outside of this Terraform configuration.

## 2. Set Environment Variables

Source the `set_variables.sh` script to configure the shell environment if you restarted your shell session or made changes to the environment variables.

- The `bootstrap.sh` script sources this file to set the environment variables and it's not necessary to run it again in the same shell session.

```sh
source scripts/set_variables.sh # change the path if necessary
```

## 3. Build & Push Docker Images and Apply Terraform

Use `gcloud` to submit the build from the `answer-app` root directory (the location of this README file) as the build context.

- **[OPTIONAL]** Omit the `_RUN_TYPE=apply` substitution to run a plan-only build and review the Terraform changes before applying.

```sh
cd /path/to/answer-app # replace with the local system path to the answer-app root directory
gcloud builds submit . --config=cloudbuild.yaml --project=$PROJECT --region=$REGION --substitutions="_RUN_TYPE=apply"
```

- Review the build logs in the [Cloud Build History](https://cloud.google.com/build/docs/view-build-results) to verify the build and deployment status.

## Connect Cloud Run Services to an Existing Load Balancer

Edit and verify these files to connect the Cloud Run services to an existing load balancer:

### [`config.yaml`](../../src/answer_app/config.yaml#L42)

Set `loadbalancer_domain` to your existing domain or `null` to create a new load balancer.

### [`cloudrun.tf`](../../terraform/modules/answer-app/cloudrun.tf#L87)

Configure the network endpoint groups and backend services to connect to your existing load balancer infrastructure.

## Rollbacks

### Option 1: Use the Cloud Console to switch Cloud Run service traffic to a different revision

**THIS WILL CHANGE STATE OUTSIDE OF TERRAFORM CONTROL**

Navigate to Cloud Run in the Console and adjust traffic allocation between revisions.

### Option 2: Rollback to a different Docker image using Terraform

Update your Terraform configuration to point to a previous image version.

#### Example: select an image by digest or tag from Artifact Registry

```sh
# List available images
gcloud artifacts docker images list $REGION-docker.pkg.dev/$PROJECT/answer-app-repo/answer-app --include-tags

# Update Terraform variables to use specific image
export TF_VAR_docker_image='{"answer_app": {"image": "us-central1-docker.pkg.dev/my-project/answer-app-repo/answer-app@sha256:abc123..."}}'
```

## Execute Terraform Infrastructure-Only Changes

To apply infrastructure-only changes to the `bootstrap` or `main` module:

```sh
# Navigate to the specific module directory
cd terraform/bootstrap  # or terraform/main

# Initialize if needed
terraform init

# Plan and apply changes
terraform plan
terraform apply
```