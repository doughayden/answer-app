#!/bin/bash

# **** WARNING: THIS SCRIPT DESTROYS ALL RESOURCES IN THE PROJECT *****
# **** AND DELETES YOUR TERRAFORM STATE BUCKET AND SERVICE ACCOUNT ****

# The user completes these prerequisite commands (Google Cloud Shell sets them up automatically):
# gcloud auth login
# gcloud config set project 'my-project-id' # replace 'my-project-id' with your project ID
# [OPTIONAL] gcloud config set compute/region us-central1

# Determine the directory of the script.
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

# Destroy the infrastructure in the main Terraform module using a subshell.
echo "TERRAFORM MAIN DIRECTORY - DESTROY:"
(
cd "$SCRIPT_DIR/../terraform/main"
terraform init -backend-config="bucket=$BUCKET" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" -reconfigure
terraform destroy -auto-approve
)
echo ""
echo ""

# Destroy the infrastructure in the Terraform bootstrap module using a subshell.
echo "TERRAFORM BOOTSTRAP DIRECTORY - DESTROY:"
(
cd "$SCRIPT_DIR/../terraform/bootstrap"
terraform init -backend-config="bucket=$BUCKET" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" -reconfigure
terraform destroy -auto-approve
)
echo ""
echo ""

# Remove the prerequisite bootstrap resources.
source "$SCRIPT_DIR/un_bootstrap.sh"

echo "============================================="
echo "  ***ANSWER-APP SUCCESSFULLY UNINSTALLED***  "
echo ""
