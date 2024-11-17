output "data_store_id" {
  description = "The Agent Builder data store ID."
  value       = { for k, v in google_discovery_engine_data_store.layout_parser_data_store : k => v.data_store_id }
}

output "search_engine_id" {
  description = "The Agent Builder search engine ID."
  value       = google_discovery_engine_search_engine.search_engine.engine_id
}
