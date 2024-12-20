resource "google_storage_bucket" "staging_bucket" {
  name                        = "${var.app_name}-staging-${var.project_id}"
  location                    = var.region
  force_destroy               = true
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
}
