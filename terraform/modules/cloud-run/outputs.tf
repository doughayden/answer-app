output "docker_image" {
  description = "The Cloud Run service Docker image."
  value       = google_cloud_run_v2_service.run_app.template.0.containers.0.image
}

output "service_id" {
  description = "The Cloud Run service ID."
  value       = google_cloud_run_v2_service.run_app.id
}

output "service_name" {
  description = "The Cloud Run service name. Also names the serverless NEG and backend service."
  value       = var.service_name
}

output "cloudrun_backend_service_id" {
  description = "The Cloud Run backend service ID."
  value       = google_compute_backend_service.run_app.id
}

output "cloudrun_custom_audiences" {
  description = "The list of custom audiences to authenticated calls to the Cloud Run service."
  value       = google_cloud_run_v2_service.run_app.custom_audiences
}
