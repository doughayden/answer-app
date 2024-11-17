#!/bin/bash

# The user completes these prerequisite commmands (Google Cloud Shell sets them up automatically):
# gcloud auth login
# gcloud config set project 'my-project-id' # replace 'my-project-id' with your project ID
# [OPTIONAL] gcloud config set compute/region us-central1

# Determine the directory of the script
if [ -n "$BASH_SOURCE" ]; then
  # Bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [ -n "$ZSH_VERSION" ]; then
  # Zsh
  SCRIPT_DIR="$(cd "$(dirname "${(%):-%N}")" && pwd)"
else
  # Fallback for other shells
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

# Set environment variables by sourcing the set_variables script.
echo ""
echo "ENVIRONMENT VARIABLES:"
source "$SCRIPT_DIR/set_variables.sh"

# Enable the Service Usage, IAM, and Service Account Credentials APIs.
services=(
  "serviceusage.googleapis.com"
  "iam.googleapis.com"
  "iamcredentials.googleapis.com"
)

echo "REQUIRED APIS:"
echo ""
for service in "${services[@]}"; do
  gcloud services list --format="value(name)" --filter="name:$service" | grep -q $service
  if [ $? -ne 0 ]; then
    echo "Enabling the $service API..."
    gcloud services enable $service
  else
    echo "The $service API is already enabled."
  fi
done
echo ""
echo ""

# Create a service account for Terraform provisioning if it doesn't exist.
echo "TERRAFORM PROVISIONING SERVICE ACCOUNT:"
echo ""
gcloud iam service-accounts list --format="value(email)" --filter="email:$TF_VAR_terraform_service_account" | grep -q $TF_VAR_terraform_service_account
if [ $? -eq 0 ]; then
  echo "The Terraform service account already exists."
else
  echo "Creating a service account for Terraform provisioning..."
  echo ""
  gcloud iam service-accounts create terraform-service-account --display-name="Terraform Provisioning Service Account" --project=$PROJECT
fi
echo ""
echo ""

# Grant the required IAM roles to the service account if they are not already granted.
echo "TERRAFORM SERVICE ACCOUNT ROLES:"
echo ""
required_roles=(
  "roles/aiplatform.admin"
  "roles/artifactregistry.admin"
  "roles/bigquery.admin"
  "roles/cloudbuild.builds.editor"
  "roles/redis.admin"
  "roles/compute.admin"
  "roles/discoveryengine.admin"
  "roles/dns.admin"
  "roles/resourcemanager.projectIamAdmin"
  "roles/run.admin"
  "roles/iam.securityAdmin"
  "roles/iam.serviceAccountAdmin"
  "roles/iam.serviceAccountUser"
  "roles/serviceusage.serviceUsageAdmin"
  "roles/storage.admin"
  "roles/workflows.admin"
)
for role in "${required_roles[@]}"; do
  gcloud projects get-iam-policy $PROJECT --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:$TF_VAR_terraform_service_account" | grep -q $role
  if [ $? -ne 0 ]; then
    echo "Granting the $role role to the service account..."
    echo ""
    gcloud projects add-iam-policy-binding $PROJECT --member="serviceAccount:$TF_VAR_terraform_service_account" --role=$role --condition=None
    echo ""
else
    echo "The service account already has the $role role."
  fi
done
echo ""
echo ""

# Grant the caller permission to impersonate the service account if they don't already have it.
user=$(gcloud config list --format='value(core.account)')
echo "SERVICE ACCOUNT IMPERSONATION FOR USER $user:"
echo ""
gcloud iam service-accounts get-iam-policy $TF_VAR_terraform_service_account --format="table(bindings.role)" --flatten="bindings[].members" --filter="bindings.members:$user" | grep -q "roles/iam.serviceAccountTokenCreator"
if [ $? -eq 0 ]; then
  echo "The caller already has the roles/iam.serviceAccountTokenCreator role."
else
  echo "Granting the caller permission to impersonate the service account (roles/iam.serviceAccountTokenCreator)..."
  gcloud iam service-accounts add-iam-policy-binding $TF_VAR_terraform_service_account --member="user:${user}" --role="roles/iam.serviceAccountTokenCreator" --condition=None
fi
echo ""
echo ""

# Create a bucket for the Terraform state if it does not already exist.
echo "TERRAFORM STATE BUCKET:"
echo ""
gcloud storage buckets list --format="value(name)" --filter="name:$BUCKET" | grep -q $BUCKET
if [ $? -eq 0 ]; then
  echo "The Terraform state bucket "gs://${BUCKET}" already exists."
else
  echo "Creating a bucket for the Terraform state..."
  echo ""
  gcloud storage buckets create "gs://${BUCKET}" --public-access-prevention --uniform-bucket-level-access --project=$PROJECT
fi
echo ""
echo ""

# Initialize the Terraform configuration in the main directory using a subshell.
echo "TERRAFORM MAIN DIRECTORY - INITIALIZE:"
(
cd $REPO_ROOT/terraform/main
terraform init -backend-config="bucket=$BUCKET" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" -reconfigure
)
echo ""
echo ""

# Initialize and apply Terraform in the boostrap directory using a subshell.
echo "TERRAFORM BOOTSTRAP DIRECTORY - INITIALIZE AND APPLY:"
(
cd $REPO_ROOT/terraform/bootstrap
terraform init -backend-config="bucket=$BUCKET" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" -reconfigure
terraform apply
)
echo ""
