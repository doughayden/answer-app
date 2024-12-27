#!/bin/bash

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

# Get the cloud run custom audience from the main module outputs.
echo "Getting the custom audience from the main Terraform module output..."
export AUDIENCE=$(
cd $REPO_ROOT/terraform/main
terraform init -backend-config="bucket=terraform-state-${PROJECT}" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" > /dev/null 2>&1
terraform output -raw custom_audience
)
echo ""
echo "AUDIENCE: $AUDIENCE"
echo ""
echo ""
