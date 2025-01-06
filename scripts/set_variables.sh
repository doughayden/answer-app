#!/bin/bash

# The user completes these prerequisite commands (Google Cloud Shell sets them up automatically):
# gcloud auth login
# gcloud config set project 'my-project-id' # replace 'my-project-id' with your project ID
# [OPTIONAL] gcloud config set compute/region us-central1

# Confirm the user configured Application Default Credentials.
gcloud auth application-default print-access-token > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "ERROR: No valid Application Default Credentials found. Run 'gcloud auth application-default login'."
  return 1
fi

# Set the PROJECT variable.
export PROJECT=$(gcloud config list --format='value(core.project)')

# Get the default compute region from gcloud.
region=$(gcloud config list --format='value(compute.region)')

# Set the REGION variable and the default gcloud compute.region attribute to us-central1 if it is unset.
if [ -z "$region" ]; then
  export REGION="us-central1"
  gcloud config set compute/region $REGION

# Use the default gcloud compute.region attribute if it is set.
else
  export REGION=$region
fi

# Set the BUCKET variable for Terraform remote state storage.
export BUCKET="terraform-state-${PROJECT}"

# Set the project_id and terraform_service_account Terraform input variables.
export TF_VAR_project_id=$PROJECT
export TF_VAR_terraform_service_account="terraform-service-account@${PROJECT}.iam.gserviceaccount.com"

# Display the environment variables.
echo ""
echo "PROJECT: $PROJECT"
echo "REGION: $REGION"
echo "BUCKET: $BUCKET"
echo "TF_VAR_project_id: $TF_VAR_project_id"
echo "TF_VAR_terraform_service_account: $TF_VAR_terraform_service_account"
echo ""
echo ""
