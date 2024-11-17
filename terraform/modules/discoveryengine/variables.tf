# variable "discovery_engines" {
#   type = map(object({
#     industry_vertical           = optional(string, "GENERIC")
#     content_config              = optional(string, "CONTENT_REQUIRED")
#     location                    = optional(string, "global")
#     solution_types              = optional(list(string), ["SOLUTION_TYPE_SEARCH"])
#     create_advanced_site_search = optional(bool, false)
#     data_store_id               = string
#     search_add_ons              = optional(list(string), ["SEARCH_ADD_ON_LLM"])
#     search_tier                 = optional(string, "SEARCH_TIER_ENTERPRISE")
#     search_engine_id            = string
#     collection_id               = optional(string, "default_collection")
#     company_name                = string
#   }))
#   description = "The discovery engine data store and search engine to provision."
#   default     = {}
# }

variable "location" {
  type        = string
  description = "The location to create the discovery engine resources."
  default     = "global"
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