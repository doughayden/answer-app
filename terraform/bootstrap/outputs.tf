output "enabled_services" {
  description = "The enabled service names."
  value       = [for service in google_project_service.project_service : service.service]
}

output "cloudbuild_service_account" {
  description = "The Cloud Build service account email address."
  value       = google_service_account.cloudbuild_service_account.email
}

output "staging_bucket" {
  description = "The document staging bucket."
  value       = google_storage_bucket.staging_bucket.name
}

output "artifact_registry_tag_namesapce" {
  description = "The Artifact Registry Docker repository for Cloud Run."
  value       = "us-central1-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.cloud_run.name}"
}
