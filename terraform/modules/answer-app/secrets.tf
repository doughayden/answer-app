resource "google_secret_manager_secret" "streamlit_secrets_toml" {
  secret_id = "streamlit-secrets-toml"
  replication {
    auto {}
  }
}

ephemeral "random_password" "cookie_secret" {
  length           = 44
  special          = true
  override_special = "-_"
}

resource "google_secret_manager_secret_version" "streamlit_secrets_toml" {
  secret                 = google_secret_manager_secret.streamlit_secrets_toml.id
  secret_data_wo_version = 1
  secret_data_wo         = <<-EOT
  [auth]
  redirect_uri = "https://${var.lb_domain}/oauth2callback"
  cookie_secret = "${ephemeral.random_password.cookie_secret.result}"

  [auth.google]
  client_id = "${local.client_secret_data.web.client_id}"
  client_secret = "${local.client_secret_data.web.client_secret}"
  server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
  client_kwargs = { "access_type" = "online", "prompt" = "select_account" }
  EOT
}

resource "google_secret_manager_secret_iam_member" "client_app_service_account" {
  secret_id = google_secret_manager_secret.streamlit_secrets_toml.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.client_app_service_account.member
}
