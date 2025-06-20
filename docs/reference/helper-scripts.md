# Helper Scripts

Shell scripts in the `scripts/` directory automate common tasks.

## Deployment Scripts

- **`install.sh`**: Deploy the resources for the `answer-app` service. (Combines other scripts to set up the project and deploy the resources.)
- **`bootstrap.sh`**: Prepare the target deployment project. (Used by the `install.sh` script.)
- **`uninstall.sh`**: Remove the `answer-app` resources from the project. (Combines other scripts to remove the resources and clean up the project.)
- **`un_bootstrap.sh`**: Remove the resources created by the `bootstrap.sh` script. (Used by the `uninstall.sh` script.)

## Configuration Scripts

- **`set_variables.sh`**: Set the environment variables for the shell session. (Used by the `bootstrap.sh`, `set_audience.sh`, `un_bootstrap.sh`, and `uninstall.sh` scripts and by Cloud Build.)

### Environment Variables Set:
- `PROJECT`: The Google Cloud project ID
- `REGION`: The default compute region
- `BUCKET`: The staging bucket for Vertex AI Data Store documents
- `TF_VAR_project_id`: The Google Cloud project ID for Terraform. (Automatically read by Terraform.)
- `TF_VAR_terraform_service_account`: The Terraform service account email address. (Automatically read by Terraform.)

## Testing Scripts

- **`test_endpoint.sh`**: Test the `answer-app` endpoint with a `curl` request.
- **`set_audience.sh`**: Set the custom audience used to call the `answer-app` service. (Used by the `test_endpoint.sh` script.)
- **`set_token.sh`**: Set the ID token used to call the `answer-app` service. (Used by the `test_endpoint.sh` script.)

## Configuration Files

- **`terraform_service_account_roles.txt`**: The IAM roles granted to the Terraform service account. (Used by the `bootstrap.sh` script.)