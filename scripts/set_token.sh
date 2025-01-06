#!/bin/bash

# Get an impersonated ID token with the cloud run custom audience from the Terraform provisioning service account.
echo "Getting an impersonated ID token with the custom audience..."
export TOKEN=$(gcloud auth print-identity-token --impersonate-service-account=$TF_VAR_terraform_service_account --audiences=$AUDIENCE --verbosity=error)

# Exit if the token is not set.
if [ -z "$TOKEN" ]; then
  echo "ERROR: The token is not set."
  return 1
fi

echo ""
echo "TOKEN environment variable set."
echo ""
echo ""
