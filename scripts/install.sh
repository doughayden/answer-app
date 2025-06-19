#!/bin/bash

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

# Source the bootstrap script to prepare the target project.
source "$SCRIPT_DIR/bootstrap.sh"

# Exit if the bootstrap script fails.
if [ $? -ne 0 ]; then
  echo "ERROR: The bootstrap script failed."
  return 1
fi

# Ensure the Cloud Build service account has the necessary permissions.
echo "IAM POLICY PROPAGATION - CLOUD BUILD SERVICE ACCOUNT:"
cloudbuild_sa_email=$(
    cd "$SCRIPT_DIR/../terraform/bootstrap"
    terraform init -backend-config="bucket=terraform-state-${PROJECT}" -backend-config="impersonate_service_account=$TF_VAR_terraform_service_account" > /dev/null 2>&1
    terraform output -raw cloudbuild_service_account
)
echo ""
echo "Service Account: $cloudbuild_sa_email"
echo ""

# Verify the Cloud Builder role in the project policy.
echo "Project IAM policy: Cloud Builder role..."
echo ""
elapsed=0
sleep=10
limit=180
# gcloud iam service-accounts get-iam-policy $cloudbuild_sa_email --format=json | jq -r '.bindings[] | select(.role == "roles/cloudbuild.builds.builder") | .members[]' | grep -q $cloudbuild_sa_email > /dev/null 2>&1
gcloud projects get-iam-policy $PROJECT --format=json | jq -r '.bindings[] | select(.role == "roles/cloudbuild.builds.builder") | .members[]' | grep -q $cloudbuild_sa_email > /dev/null 2>&1
while [ $? -ne 0 ]; do
  echo "Waiting for the IAM policy to propagate..."
  sleep $sleep
  elapsed=$((elapsed + sleep))
  if [ $elapsed -ge $limit ]; then
    echo ""
    echo "ERROR: The Cloud Build service account does not have the necessary permissions."
    return 1
  fi
  gcloud projects get-iam-policy $PROJECT --format=json | jq -r '.bindings[] | select(.role == "roles/cloudbuild.builds.builder") | .members[]' | grep -q $cloudbuild_sa_email > /dev/null 2>&1
done
echo "The Cloud Build service account has the Cloud Builder role on the project IAM policy."
echo ""
echo ""

# Verify the Service Account Token Creator role in the Terraform Service Account IAM policy.
echo "Terraform Service Account IAM policy: Service Account Token Creator role..."
echo ""
elapsed=0
sleep=10
limit=60
gcloud iam service-accounts get-iam-policy $TF_VAR_terraform_service_account --format=json | jq -r '.bindings[] | select(.role == "roles/iam.serviceAccountTokenCreator") | .members[]' | grep -q $cloudbuild_sa_email > /dev/null 2>&1
while [ $? -ne 0 ]; do
  echo "Waiting for the IAM policy to propagate..."
  sleep $sleep
  elapsed=$((elapsed + sleep))
  if [ $elapsed -ge $limit ]; then
    echo ""
    echo "ERROR: The Cloud Build service account does not have the necessary permissions."
    return 1
  fi
  gcloud iam service-accounts get-iam-policy $TF_VAR_terraform_service_account --format=json | jq -r '.bindings[] | select(.role == "roles/iam.serviceAccountTokenCreator") | .members[]' | grep -q $cloudbuild_sa_email > /dev/null 2>&1
done
echo "The Cloud Build service account has the Service Account Token Creator role on the Terraform service account IAM policy."
echo ""
echo ""

# Sleep to allow the IAM policy changes to propagate.
echo "Sleeping to allow the IAM policy changes to propagate..."
echo "Press any key to skip waiting and continue immediately."
echo ""

sleep=3
elapsed=0
limit=90

while [ $elapsed -lt $limit ]; do
  printf "\rSleeping... $((limit - elapsed)) seconds remaining. Press any key to continue." 
  
  # Read with timeout (non-blocking)
  if read -t $sleep -n 1; then
    printf "\n\nContinuing at user request.\n"
    echo ""
    break
  fi
  
  elapsed=$((elapsed + sleep))
done

# Only print "Done" if we completed the full wait
if [ $elapsed -ge $limit ]; then
  echo -e "\nDone."
fi

# Deploy the answer-app services.
echo "DEPLOYING THE ANSWER-APP SERVICES WITH CLOUD BUILD:"
echo ""
(
cd "$SCRIPT_DIR/.."
gcloud builds submit . --config=cloudbuild.yaml --project=$PROJECT --region=$REGION --substitutions="_RUN_TYPE=apply"
)

# Exit if the Cloud Build deployment fails.
if [ $? -ne 0 ]; then
  echo "ERROR: The Cloud Build deployment failed."
  return 1
fi

echo ""
echo ""

echo "==========================================="
echo "  ***ANSWER-APP SUCCESSFULLY INSTALLED***  "
echo ""
