locals {
  app_project_iam_roles = toset([
    "roles/aiplatform.user",
    "roles/bigquery.dataEditor",
    "roles/bigquery.user",
    "roles/discoveryengine.admin",
    "roles/gkemulticloud.telemetryWriter",
    "roles/storage.objectUser",
  ])

  client_app_project_iam_roles = toset([
    "roles/gkemulticloud.telemetryWriter",
    # "roles/run.invoker",
  ])

  answer_app_run_invoker_members = toset([
    google_service_account.client_app_service_account.member,
  ])

  run_app_env = {
    LOG_LEVEL = "INFO"
  }

  run_app_client_env = {
    LOG_LEVEL = "INFO"
    AUDIENCE  = google_cloud_run_v2_service.run_app[var.region].custom_audiences[0]
  }

  regions = toset(concat([var.region], var.additional_regions))
}
