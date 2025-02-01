variable "project_id" {
  description = "The project ID."
  type        = string
}

variable "region" {
  type        = string
  description = "The Compute API default region."
}

variable "additional_regions" {
  type        = list(string)
  description = "Additional regions to deploy the Cloud Run service."
  default     = []
}

variable "iap_sa_member" {
  description = "The IAP service agent member."
  type        = string
}

variable "app_name" {
  description = "The Cloud Run service name."
  type        = string
}

variable "lb_domain" {
  type        = string
  description = "The load balancer domain name."
}

variable "docker_image" {
  description = "The Cloud Run service Docker image."
  type        = map(string)
}

variable "location" {
  type        = string
  description = "The location to create the discovery engine resources."
  default     = "global"
}

variable "dataset_id" {
  description = "The BigQuery dataset ID."
  type        = string
}

variable "table_id" {
  description = "The BigQuery table ID."
  type        = string
}

variable "feedback_table_id" {
  description = "The BigQuery feedback table ID."
  type        = string
}

variable "data_stores" {
  type = map(object({
    data_store_id               = string
    industry_vertical           = optional(string, "GENERIC")
    content_config              = optional(string, "CONTENT_REQUIRED")
    solution_types              = optional(list(string), ["SOLUTION_TYPE_SEARCH"])
    create_advanced_site_search = optional(bool, false)
  }))
  description = "The discoveryengine data stores to provision."
  default     = {}
}

variable "search_engine" {
  type = object({
    search_engine_id  = string
    collection_id     = optional(string, "default_collection")
    industry_vertical = optional(string, "GENERIC")
    search_add_ons    = optional(list(string), ["SEARCH_ADD_ON_LLM"])
    search_tier       = optional(string, "SEARCH_TIER_ENTERPRISE")
    company_name      = string
  })
  description = "The discoveryengine search engine to provision."
}
