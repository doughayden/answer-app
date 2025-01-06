#!/bin/bash

# ***** WARNING: THIS WILL DELETE YOUR TERRAFORM STATE BUCKET AND SERVICE ACCOUNT *****

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

echo ""
echo "REMOVING BOOTSTRAP RESOURCES"
echo "==========================="
echo ""

# Set environment variables by sourcing the set_variables script.
echo ""
echo "ENVIRONMENT VARIABLES:"
source "$SCRIPT_DIR/set_variables.sh"

# Exit if the set_variables script fails.
if [ $? -ne 0 ]; then
  echo "ERROR: The set_variables script failed."
  return 1
fi

# Delete the Terraform state bucket.
echo "TERRAFORM STATE BUCKET:"
echo ""
gcloud storage buckets list --format="value(name)" --filter="name:$BUCKET" | grep -q $BUCKET
if [ $? -eq 0 ]; then
    echo "Deleting the Terraform state bucket..."
    echo ""
    gsutil rm -r gs://$BUCKET
else
    echo "The Terraform state bucket does not exist."
fi
echo ""
echo ""


# Remove the Terraform service account from the project IAM role bindings.
echo "TERRAFORM PROVISIONING SERVICE ACCOUNT ROLES:"
echo ""

# Read the roles from the roles.txt file.
roles_file="${SCRIPT_DIR}/terraform_service_account_roles.txt"
if [ ! -f "$roles_file" ]; then
  echo "Error: roles.txt file not found!"
  return 1
fi

while IFS= read -r role; do
  gcloud projects get-iam-policy $PROJECT --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:$TF_VAR_terraform_service_account" | grep -q $role
  if [ $? -eq 0 ]; then
    echo "Removing the $role role from the Terraform service account..."
    echo ""
    gcloud projects remove-iam-policy-binding $PROJECT --role=$role --member="serviceAccount:$TF_VAR_terraform_service_account"
    echo ""
  else
    echo "The $role role is not granted to the Terraform service account."
  fi
done < "$roles_file"
echo ""
echo ""


# Delete the Terraform service account.
echo "TERRAFORM PROVISIONING SERVICE ACCOUNT:"
echo ""
gcloud iam service-accounts list --format="value(email)" --filter="email:$TF_VAR_terraform_service_account" | grep -q $TF_VAR_terraform_service_account
if [ $? -eq 0 ]; then
    echo "Deleting the Terraform service account..."
    echo ""
    gcloud iam service-accounts delete $TF_VAR_terraform_service_account --quiet
else
    echo "The Terraform service account does not exist."
fi
echo ""
echo ""

