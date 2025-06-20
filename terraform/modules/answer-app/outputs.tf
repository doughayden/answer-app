output "bigquery_dataset_id" {
  description = "The BigQuery dataset ID."
  value       = google_bigquery_dataset.answer_app.dataset_id
}

output "bigquery_table_id" {
  description = "The BigQuery tables."
  value       = google_bigquery_table.conversations.table_id
}

output "bigquery_feedback_table_id" {
  description = "The BigQuery feedback table."
  value       = google_bigquery_table.feedback.table_id
}

output "service_name" {
  description = "The Cloud Run service name. Also names the serverless NEG and backend service."
  value       = google_cloud_run_v2_service.run_app[var.region].name
}

output "cloudrun_backend_service_id" {
  description = "The Cloud Run backend service ID."
  value       = google_compute_backend_service.run_app.id
}

output "cloudrun_custom_audiences" {
  description = "The list of custom audiences to authenticate calls to the Cloud Run service."
  value       = google_cloud_run_v2_service.run_app[var.region].custom_audiences
}

output "client_service_id" {
  description = "The Cloud Run service ID."
  value       = google_cloud_run_v2_service.run_app_client.id
}

output "client_service_name" {
  description = "The Cloud Run service name. Also names the serverless NEG and backend service."
  value       = google_cloud_run_v2_service.run_app_client.name
}

output "cloudrun_client_backend_service_id" {
  description = "The Cloud Run backend service ID."
  value       = google_compute_backend_service.run_app_client.id
}

output "client_service_uri" {
  description = "The URL to access the web client application."
  value       = google_cloud_run_v2_service.run_app_client.uri
}

output "data_store_id" {
  description = "The Agent Builder data store ID."
  value       = { for k, v in google_discovery_engine_data_store.layout_parser_data_store : k => v.data_store_id }
}

output "search_engine_id" {
  description = "The Agent Builder search engine ID."
  value       = google_discovery_engine_search_engine.search_engine.engine_id
}

output "app_service_account_email" {
  description = "The app service-attached service account email address."
  value       = google_service_account.app_service_account.email
}

output "app_service_account_member" {
  description = "The app service-attached service account member."
  value       = google_service_account.app_service_account.member
}

output "client_app_service_account_email" {
  description = "The app service-attached service account email address."
  value       = google_service_account.client_app_service_account.email
}

output "client_app_service_account_member" {
  description = "The app service-attached service account member."
  value       = google_service_account.client_app_service_account.member
}

output "streamlit_secrets_toml_id" {
  description = "The Streamlit secrets.toml Secret Manager secret ID."
  value       = google_secret_manager_secret.streamlit_secrets_toml.id
}
