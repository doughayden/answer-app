output "doc_ingestion_workflow_update_time" {
  description = "The timestamp of when the workflow was last updated."
  value       = google_workflows_workflow.document_ingestion.update_time
}

output "doc_ingestion_workflow_env_vars" {
  description = "The document ingestion workflow environment variables."
  value       = google_workflows_workflow.document_ingestion.user_env_vars
}

output "workflow_service_account_email" {
  description = "The Workflow service account email address."
  value       = google_service_account.doc_ingestion_workflow.email
}
