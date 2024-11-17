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
  value       = module.iam.app_service_account_email
}

output "data_store_id" {
  description = "The Agent Builder data store ID."
  value       = module.discovery_engine.data_store_id
}

output "search_engine_id" {
  description = "The Agent Builder search engine ID."
  value       = module.discovery_engine.search_engine_id
}

output "docker_image" {
  description = "The Cloud Run service Docker image."
  value       = module.cloud_run.docker_image
}

output "custom_audience" {
  description = "The custom audience to authenticate calls to the Cloud Run service."
  value       = module.cloud_run.cloudrun_custom_audiences[0]
}

output "terraform_service_account" {
  description = "The Terraform provisioning service account email address."
  value       = var.terraform_service_account
}
