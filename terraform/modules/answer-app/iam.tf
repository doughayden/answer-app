locals {
  app_iam_roles = [
    "roles/aiplatform.user",
    "roles/bigquery.dataEditor",
    "roles/bigquery.user",
    "roles/discoveryengine.admin",
    "roles/gkemulticloud.telemetryWriter",
    "roles/storage.objectUser",
  ]
}

resource "google_service_account" "app_service_account" {
  account_id   = var.app_name
  description  = "${var.app_name} service-attached service account."
  display_name = "${var.app_name} Service Account"
}

resource "google_project_iam_member" "app_service_account" {
  for_each = toset(local.app_iam_roles)
  project  = var.project_id
  role     = each.key
  member   = google_service_account.app_service_account.member
}

# Allow the IAP Service Agent to invoke Cloud Run services.
resource "google_project_iam_member" "iap_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = var.iap_sa_member
}
