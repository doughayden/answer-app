locals {
  config = yamldecode(file("../../src/config.yaml"))
}

resource "google_project_service" "project_service" {
  for_each           = toset(var.services)
  disable_on_destroy = false
  service            = each.key
}

resource "google_service_account" "cloudbuild_service_account" {
  account_id   = "${local.config.app_name}-cloudbuild"
  description  = "Cloud Build service account for the ${local.config.app_name} service."
  display_name = "${local.config.app_name} Cloud Build"
}

resource "google_project_iam_member" "cloudbuild_service_account" {
  for_each = toset(var.cloudbuild_iam_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.cloudbuild_service_account.email}"
}

resource "google_service_account_iam_member" "cloudbuild_terraform_token_creator" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.terraform_service_account}"
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.cloudbuild_service_account.email}"
}

resource "google_storage_bucket" "staging_bucket" {
  name                        = "${local.config.app_name}-staging-${var.project_id}"
  location                    = "US"
  force_destroy               = true
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
}

resource "google_artifact_registry_repository" "cloud_run" {
  repository_id = local.config.app_name
  format        = "DOCKER"
  location      = var.region
  description   = "${local.config.app_name} Cloud Run Docker repository"
}
