#!/bin/bash

# Get an impersonated ID token with the cloud run custom audience from the Terraform provisioning service account.
echo "Getting an impersonated ID token with the custom audience..."
export TOKEN=$(gcloud auth print-identity-token --impersonate-service-account=$TF_VAR_terraform_service_account --audiences=$AUDIENCE --verbosity=error)
echo ""
echo "TOKEN environment variable set."
echo ""
echo ""
