resource "google_secret_manager_secret" "streamlit_secrets_toml" {
  secret_id = "streamlit-secrets-toml"
  replication {
    auto {}
  }
}

resource "random_password" "cookie_secret" {
  length  = 40
  special = false

}

resource "google_secret_manager_secret_version" "streamlit_secrets_toml" {
  secret                 = google_secret_manager_secret.streamlit_secrets_toml.id
  is_secret_data_base64  = true
  secret_data_wo_version = 5
  secret_data_wo         = filebase64("${path.module}/secrets_template.toml")

  # This secret version is a placeholder: ignore when it's disabled after a manual update.
  lifecycle {
    ignore_changes = [enabled]
  }
}

resource "google_secret_manager_secret_iam_member" "client_app_service_account" {
  secret_id = google_secret_manager_secret.streamlit_secrets_toml.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.client_app_service_account.member
}
