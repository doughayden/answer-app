output "enabled_services" {
  description = "The enabled service names."
  value       = [for service in google_project_service.project_service : service.service]
}

output "terraform_service_account" {
  description = "The Terraform service account email address."
  value       = var.terraform_service_account
}

output "cloudbuild_service_account" {
  description = "The Cloud Build service account email address."
  value       = google_service_account.cloudbuild_service_account.email
}

output "artifact_registry_tag_namespace" {
  description = "The Artifact Registry Docker repository for Cloud Run."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.cloud_run.name}"
}
