resource "google_service_account" "app_service_account" {
  account_id   = var.app_name
  description  = "${var.app_name} service-attached service account."
  display_name = "${var.app_name} Service Account"
}

resource "google_project_iam_member" "app_service_account" {
  for_each = local.app_project_iam_roles
  project  = var.project_id
  role     = each.key
  member   = google_service_account.app_service_account.member
}

resource "google_service_account" "client_app_service_account" {
  account_id   = "${var.app_name}-client"
  description  = "${var.app_name}-client service-attached service account."
  display_name = "${var.app_name}-client Service Account"
}

resource "google_project_iam_member" "client_app_service_account" {
  for_each = local.client_app_project_iam_roles
  project  = var.project_id
  role     = each.key
  member   = google_service_account.client_app_service_account.member
}

# Allow the IAP Service Agent to invoke Cloud Run services.
resource "google_project_iam_member" "iap_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = var.iap_sa_member
}

# Maintain an authoritative policy of Run Invoker principals on each answer-app regional service.
resource "google_cloud_run_v2_service_iam_binding" "answer_app_run_invoker" {
  for_each = local.regions
  name     = google_cloud_run_v2_service.run_app[each.value].name
  role     = "roles/run.invoker"
  members  = local.answer_app_run_invoker_members
}
