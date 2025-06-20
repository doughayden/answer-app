# Known Issues

Common problems and solutions when deploying the Answer App.

## Installation fails service account impersonation

### Problem

During the first installation while the `install.sh` script calls the `bootstrap.sh` script, it fails with the message: "ERROR: The caller cannot impersonate the service account and access objects in the bucket after 1 minute."

Example:
```
IAM POLICY PROPAGATION:

Waiting for the IAM policy to propagate...
Waiting for the IAM policy to propagate...
Waiting for the IAM policy to propagate...
Waiting for the IAM policy to propagate...
Waiting for the IAM policy to propagate...
Waiting for the IAM policy to propagate...

ERROR: The caller cannot impersonate the service account and access objects in the bucket after 1 minute.

ERROR: The bootstrap script failed.
```

The error occurs because the script tests the caller's permission to impersonate the Terraform service account before the IAM policy has fully propagated. The script retries for 1 minute and then fails.

### Solution

Re-run the `install.sh` script after a couple minutes to allow more time for the IAM policy to propagate. You can safely retry the script multiple times to allow more time for propagation.

## Failure to create the Artifact Registry repository

### Problem

When running the `bootstrap` module, Terraform fails to create the Artifact Registry repository.

Example:
```
╷
│ Error: Error creating Repository: googleapi: Error 403: Permission 'artifactregistry.repositories.create' denied on resource '//artifactregistry.googleapis.com/projects/my-project-id/locations/us-central1' (or it may not exist).
│ Details:
│ [
│   {
│     "@type": "type.googleapis.com/google.rpc.ErrorInfo",
│     "domain": "artifactregistry.googleapis.com",
│     "metadata": {
│       "permission": "artifactregistry.repositories.create",
│       "resource": "projects/my-project-id/locations/us-central1"
│     },
│     "reason": "IAM_PERMISSION_DENIED"
│   }
│ ]
│ 
│   with google_artifact_registry_repository.cloud_run,
│   on main.tf line 38, in resource "google_artifact_registry_repository" "cloud_run":
│   38: resource "google_artifact_registry_repository" "cloud_run" {
│ 
╵
```

The error occurs on the first run of the `bootstrap` module due to a race condition between the Artifact Registry API activation and applying the Terraform plan. The API activation can take a few minutes to complete.

### Solution

Rerun the `bootstrap.sh` script or manually re-apply the `bootstrap` module configuration.

## Cloud Build fails with a Cloud Storage 403 permission denied error

### Problem

Cloud Build fails with a `storage.objects.get` access error when trying to access the Google Cloud Storage object after the first run of the `bootstrap` module.

Example:
```
> gcloud builds submit . --config=cloudbuild.yaml --project=$PROJECT --region=$REGION --impersonate-service-account=$TF_VAR_terraform_service_account --verbosity=error --substitutions="_RUN_TYPE=apply"
Creating temporary archive of 25 file(s) totalling 650.8 KiB before compression.
Uploading tarball of [.] to [gs://my-project-id_cloudbuild/source/1732724661.794156-c07691d9db7449499595855914578017.tgz]
ERROR: (gcloud.builds.submit) INVALID_ARGUMENT: could not resolve source: googleapi: Error 403: run-app-cloudbuild@my-project-id.iam.gserviceaccount.com does not have storage.objects.get access to the Google Cloud Storage object. Permission 'storage.objects.get' denied on resource (or it may not exist)., forbidden
```

The error can occur shortly after setting up a new project with the `bootstrap` module for the first time. It's a race condition where the Cloud Build service account IAM role bindings have not yet propagated.

### Solution

Rerun the Cloud Build job to resolve the error.

## Error creating a DataStore (named DataStore being deleted)

### Problem

When re-running the Terraform configuration after deleting the DataStore, the following error occurs:

```
╷
│ Error: Error creating DataStore: googleapi: Error 400: DataStore projects/.../locations/global/collections/default_collection/dataStores/cymbal-bank-data-store is being deleted, please wait for deletion to complete before recreating with the same ID. The deletion could take a couple of hours.
│ 
│   with module.answer_app.google_discovery_engine_data_store.layout_parser_data_store["answer-app-default"],
│   on ../modules/answer-app/discoveryengine.tf line 1, in resource "google_discovery_engine_data_store" "layout_parser_data_store":
│    1: resource "google_discovery_engine_data_store" "layout_parser_data_store" {
│ 
╵
```

### Solution

Wait for the DataStore deletion to complete (can take several hours) or use a different DataStore ID in your configuration.

## Errors adding users to Identity-Aware Proxy

### Problem

"Policy updated failed" errors occur when adding users to Identity-Aware Proxy due to organizational policies.

### Solution

Check if your organization has the [Domain restricted sharing Org policy](https://cloud.google.com/resource-manager/docs/organization-policy/restricting-domains#example_error_message) enabled. You may need to request an exception or use users from allowed domains.

## Errors reading or editing Terraform resources

### Problem

Permission errors when trying to read or modify Terraform-managed resources.

### Solution

Ensure your user account has the necessary IAM roles and that service account impersonation is configured correctly. Re-run the bootstrap script if needed.

## The Search Agent refuses to answer questions

### Problem

The Vertex AI Search Agent returns responses indicating it cannot answer questions about the imported documents.

### Solution

- Verify that documents have been properly imported into the DataStore
- Check that the Search App is configured correctly
- Ensure the Discovery Engine API is enabled
- Review the document import logs for any errors

## Failure to remove regional backends

### Problem

When destroying resources, Terraform may fail to remove regional backend services due to dependencies.

### Solution

Manually remove the backend services from the load balancer configuration in the Google Cloud Console, then re-run `terraform destroy`.