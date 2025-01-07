#!/bin/bash

# The user completes these prerequisite commands (Google Cloud Shell sets them up automatically):
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

# Exit if the set_variables script fails.
if [ $? -ne 0 ]; then
  echo "ERROR: The set_variables script failed."
  return 1
fi

# Enable required APIs.
services=(
  "cloudresourcemanager.googleapis.com"
  "iam.googleapis.com"
  "iamcredentials.googleapis.com"
  "serviceusage.googleapis.com"
  "storage.googleapis.com"
)

echo "REQUIRED APIS:"
echo ""
for service in "${services[@]}"; do
  gcloud services list --format="value(config.name)" --filter="config.name=$service" | grep -q $service
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

# Read roles from the roles.txt file
roles_file="${SCRIPT_DIR}/terraform_service_account_roles.txt"
if [ ! -f "$roles_file" ]; then
  echo "Error: roles.txt file not found!"
  return 1
fi

while IFS= read -r role || [ -n "$role" ]; do
  gcloud projects get-iam-policy $PROJECT --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:$TF_VAR_terraform_service_account" | grep -q $role
  if [ $? -ne 0 ]; then
    echo "Granting the $role role to the service account..."
    echo ""
    gcloud projects add-iam-policy-binding $PROJECT --member="serviceAccount:$TF_VAR_terraform_service_account" --role=$role --condition=None
    echo ""
  else
    echo "The service account already has the $role role."
  fi
done < "$roles_file"

echo ""
echo ""

# Grant the caller permission to impersonate the service account if they don't already have it.
user=$(gcloud config list --format='value(core.account)')
echo "SERVICE ACCOUNT IMPERSONATION FOR USER $user:"
echo ""
gcloud iam service-accounts get-iam-policy $TF_VAR_terraform_service_account --format="table(bindings.role)" --flatten="bindings[].members" --filter="bindings.members:$user" --verbosity=error | grep -q "roles/iam.serviceAccountTokenCreator"
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

# Test whether the caller can get an impersonated token for the service account and access objects in the bucket.
# Keep trying until the IAM policy propagates or 1 minute has passed.
echo "IAM POLICY PROPAGATION:"
echo ""
elapsed=0
sleep=10
limit=60
gcloud storage objects list "gs://${BUCKET}/**" --impersonate-service-account=$TF_VAR_terraform_service_account > /dev/null 2>&1
while [ $? -ne 0 ]; do
  echo "Waiting for the IAM policy to propagate..."
  sleep $sleep
  elapsed=$((elapsed + sleep))
  if [ $elapsed -ge $limit ]; then
    echo ""
    echo "ERROR: The caller cannot impersonate the service account and access objects in the bucket after 1 minute."
    echo ""
    return 1
  fi
  gcloud storage objects list "gs://${BUCKET}/**" --impersonate-service-account=$TF_VAR_terraform_service_account > /dev/null 2>&1
done
echo "The caller can impersonate the service account and access objects in the bucket."
echo ""
echo ""


# Initialize the Terraform configuration in the main directory using a subshell.
echo "TERRAFORM MAIN DIRECTORY - INITIALIZE:"
(
cd "$SCRIPT_DIR/../terraform/main"
terraform init -backend-config="bucket=$BUCKET" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" -reconfigure
)
echo ""
echo ""

# Initialize and apply Terraform in the bootstrap directory using a subshell.
echo "TERRAFORM BOOTSTRAP DIRECTORY - INITIALIZE AND APPLY:"
(
cd "$SCRIPT_DIR/../terraform/bootstrap"
terraform init -backend-config="bucket=$BUCKET" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" -reconfigure
terraform apply -auto-approve
)

# Exit if the Terraform apply command fails.
if [ $? -ne 0 ]; then
  echo ""
  echo "ERROR: The Terraform apply command failed."
  echo ""
  return 1
fi

echo ""
echo ""
