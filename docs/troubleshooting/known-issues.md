# Known Issues

[← Back to README](../../README.md)

Common problems and solutions when deploying the Answer App.

- [Installation fails service account impersonation](#installation-fails-service-account-impersonation)
- [Failure to create the Artifact Registry repository](#failure-to-create-the-artifact-registry-repository)
- [Cloud Build fails with a Cloud Storage 403 permission denied error](#cloud-build-fails-with-a-cloud-storage-403-permission-denied-error)
- [Error creating a DataStore (named DataStore being deleted)](#error-creating-a-datastore-named-datastore-being-deleted)
- [Errors adding users to Identity-Aware Proxy](#errors-adding-users-to-identity-aware-proxy)
- [Errors reading or editing Terraform resources](#errors-reading-or-editing-terraform-resources)
- [The Search Agent refuses to answer questions](#the-search-agent-refuses-to-answer-questions)
- [Failure to remove regional backends](#failure-to-remove-regional-backends)

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

([return to top](#known-issues))

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

([return to top](#known-issues))

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

([return to top](#known-issues))

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

Wait for the DataStore deletion to complete (can take several hours) or use a different DataStore ID in your configuration before re-applying Terraform.

([return to top](#known-issues))

## Errors adding users to Identity-Aware Proxy

### Problem

"Policy updated failed" errors occur when adding users to the Identity-Aware Proxy backend service due to organizational policies.

![Policy update failed](../../assets/drs_error.png)

### Solution

Check if your organization has the [Domain restricted sharing Org policy](https://cloud.google.com/resource-manager/docs/organization-policy/restricting-domains#example_error_message) enabled. You may need to request an exception or use users from allowed domains.

#### Add a policy exception
1. [Edit the policy](https://cloud.google.com/resource-manager/docs/organization-policy/creating-managing-policies#creating_and_editing_policies) to temporarily disable it.
2. Add the members to IAP-protected backend service IAM policy.
3. Re-enable the policy.

([return to top](#known-issues))

## Errors reading or editing Terraform resources

### Problem

Intermittent connectivity errors when trying to read or modify Terraform-managed resources.

Example:
```
│ Error: Error when reading or editing RedisInstance "projects/my-project/locations/us-central1/instances/my-redis-instance": Get "https://redis.googleapis.com/v1/projects/my-project/locations/us-central1/instances/my-redis-instance?alt=json": write tcp [fe80::ca4b:d6ff:fec7:8a11%utun1]:59235->[2607:f8b0:4009:809::200a]:443: write: socket is not connected
│ 
│   with google_redis_instance.default,
│   on redis.tf line 79, in resource "google_redis_instance" "default":
│   79: resource "google_redis_instance" "default" {
│ 
╵
```

### Solution

Retry the operation to clear the error. If the error persists, check your network or VPN connection and try again.

([return to top](#known-issues))

## The Search Agent refuses to answer questions

### Problem

The Vertex AI Search Agent returns responses indicating it cannot answer questions about the imported documents.

#### Symptoms
- The Search agent responds with `"No results could be found. Try rephrasing the search query."` when the query is valid and should be answerable from the data store documents.
- Cloud Run logs do not include citations or references for the answer response.
- The Big Query `answer-app.conversations` table includes `null` values for the `answer.citations`, `answer.references`, or `answer.related_questions` columns.
- The Big Query `answer-app.conversations` table might list some but not all of the documents expected to be returned in the search results.
- The search preview in the Vertex AI Agent Builder console also does not return any results.
- The data store documents appear to be properly imported with no errors in the Vertex AI Agent Builder console.

### Solution

Importing documents using the [refresh options](https://cloud.google.com/generative-ai-app-builder/docs/refresh-data) without first purging the data store in a separate step may result in this issue. The import operation may actually not have imported and indexed the documents properly. [Purge the data store](https://cloud.google.com/generative-ai-app-builder/docs/delete-datastores) and re-import the documents to resolve the issue.

([return to top](#known-issues))

## Failure to remove regional backends

### Problem

Terraform fails to remove the regional backend Network Endpoint Groups connected to the backend service. It will throw a 'resource in use by another resource' error.

### Solution

Apply changes in multiple steps to remove the regional backends:
1. Edit the backend service to include only the default regional backend group.
    - Change the dynamic `group` argument in `terraform/modules/answer-app/cloudrun.tf` (`module.answer-app.google_compute_backend_service.run_app`) from:
    ```
    dynamic "backend" {
      for_each = toset(local.regions)
      content {
        group = google_compute_region_network_endpoint_group.run_app[backend.key].id
      }
    }
    ```
    to:
    ```
    dynamic "backend" {
      for_each = toset(local.regions)
      content {
        group = google_compute_region_network_endpoint_group.run_app[var.region].id
      }
    }
    ```
2. Apply the changes to update the backend service while leaving the `additional_regions` list variable defined in [`config.yaml`](../../src/answer_app/config.yaml) full with the backends you wish to later remove.
3. Remove the regions you want to destroy from the `additional_regions` list variable defined in [`config.yaml`](../../src/answer_app/config.yaml).
4. Apply the changes to remove the regional backend NEGs and their associated Cloud Run Services.
5. Revert the change to the dynamic block `group` argument in `terraform/modules/answer-app/cloudrun.tf` back to:
    ```
    group = google_compute_region_network_endpoint_group.run_app[backend.key].id
    ```
6. Apply the changes to confirm the configuration works.

([return to top](#known-issues))
