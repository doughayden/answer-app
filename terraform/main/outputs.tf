output "project_id" {
  description = "The project ID."
  value       = var.project_id
}

output "lb_ip_address" {
  description = "The load balancer IP address."
  value       = local.config.create_loadbalancer ? module.loadbalancer[0].lb_ip_address : null
}

output "lb_domain" {
  description = "The load balancer domain name."
  value       = local.config.create_loadbalancer ? module.loadbalancer[0].lb_domain : null
}

output "cert_name" {
  description = "The Google-managed encryption certificate name."
  value       = local.config.create_loadbalancer ? module.loadbalancer[0].cert_name : null
}

output "app_service_account" {
  description = "The Cloud Run app service account email address."
  value       = module.answer_app.app_service_account_email
}

output "client_app_service_account" {
  description = "The Cloud Run app service account email address."
  value       = module.answer_app.client_app_service_account_email
}

output "data_store_id" {
  description = "The Agent Builder data store ID."
  value       = module.answer_app.data_store_id
}

output "search_engine_id" {
  description = "The Agent Builder search engine ID."
  value       = module.answer_app.search_engine_id
}

output "docker_image" {
  description = "The Cloud Run service Docker image."
  value       = local.docker_image
}

output "custom_audience" {
  description = "The custom audience to authenticate calls to the Cloud Run service."
  value       = module.answer_app.cloudrun_custom_audiences[0]
}

output "terraform_service_account" {
  description = "The Terraform provisioning service account email address."
  value       = var.terraform_service_account
}

output "client_app_uri" {
  description = "The URI to access the web client application."
  value       = local.config.create_loadbalancer ? "https://${local.lb_domain}/answer-app-client" : module.answer_app.client_service_uri
}
