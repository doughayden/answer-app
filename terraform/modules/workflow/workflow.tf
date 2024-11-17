resource "google_workflows_workflow" "document_ingestion" {
  name            = "doc-ingestion-workflow"
  description     = "Workflow to ingest documets to the Agent Builder Data Store"
  service_account = var.service_account
  source_contents = file("${path.module}/workflow.yaml")
  user_env_vars = {
    AUDIENCE         = var.audience
    COMPANY_NAME     = var.company_name
    DATA_STORE_ID    = var.data_store_id
    LB_DOMAIN        = var.lb_domain
    LOCATION         = var.location
    SEARCH_ENGINE_ID = var.search_engine_id
  }
}
