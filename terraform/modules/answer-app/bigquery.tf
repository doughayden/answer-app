resource "google_bigquery_dataset" "answer_app" {
  dataset_id = var.dataset_id
  location   = "US"
}

resource "google_bigquery_table" "conversations" {
  dataset_id          = google_bigquery_dataset.answer_app.dataset_id
  deletion_protection = false
  schema              = file("${path.module}/schema.json")
  table_id            = var.table_id
  time_partitioning {
    type          = "DAY"
    expiration_ms = 2592000000
  }
}

resource "google_bigquery_table" "feedback" {
  dataset_id          = google_bigquery_dataset.answer_app.dataset_id
  deletion_protection = false
  schema              = file("${path.module}/schema_feedback.json")
  table_id            = var.feedback_table_id
  time_partitioning {
    type          = "DAY"
    expiration_ms = 2592000000
  }
}