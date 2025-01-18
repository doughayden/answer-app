locals {
  config = yamldecode(file("../../src/answer_app/config.yaml"))
  services = [
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "discoveryengine.googleapis.com",
    "iap.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
  ]
  # bigquery, logging, monitoring, and storage are enabled by default in all new projects
  cloudbuild_iam_roles = ["roles/cloudbuild.builds.builder"]
}

resource "google_project_service" "project_service" {
  for_each           = toset(local.services)
  disable_on_destroy = false
  service            = each.key
}

resource "google_service_account" "cloudbuild_service_account" {
  account_id   = "${local.config.app_name}-cloudbuild"
  description  = "Cloud Build service account for the ${local.config.app_name} service."
  display_name = "${local.config.app_name} Cloud Build"
}

resource "google_project_iam_member" "cloudbuild_service_account" {
  for_each   = toset(local.cloudbuild_iam_roles)
  project    = var.project_id
  role       = each.key
  member     = google_service_account.cloudbuild_service_account.member
  depends_on = [google_project_service.project_service["cloudresourcemanager.googleapis.com"]]
}

resource "google_service_account_iam_member" "cloudbuild_terraform_token_creator" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.terraform_service_account}"
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = google_service_account.cloudbuild_service_account.member
  depends_on         = [google_project_service.project_service["cloudresourcemanager.googleapis.com"]]
}

resource "google_artifact_registry_repository" "cloud_run" {
  repository_id = local.config.app_name
  format        = "DOCKER"
  location      = var.region
  description   = "${local.config.app_name} Cloud Run Docker repository"
  depends_on    = [google_project_service.project_service["artifactregistry.googleapis.com"]]
}
