output "app_service_account_email" {
  description = "The app service-attached service account email address."
  value       = google_service_account.app_service_account.email
}

output "app_service_account_member" {
  description = "The app service-attached service account member."
  value       = google_service_account.app_service_account.member
}

output "workflow_service_account_email" {
  description = "The Workflow service account email address."
  value       = google_service_account.doc_ingestion_workflow.email
}