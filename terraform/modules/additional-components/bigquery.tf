resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.dataset_name
  location   = "US"
}

resource "google_bigquery_table" "tables" {
  for_each            = local.table_schemas
  dataset_id          = google_bigquery_dataset.dataset.dataset_id
  table_id            = each.key
  schema              = jsonencode(each.value.fields)
  deletion_protection = false
}

locals {
  table_schemas = {
    "ground_truth" = {
      fields = [
        { name = "question_id", type = "STRING", mode = "REQUIRED" },
        { name = "question", type = "STRING", mode = "REQUIRED" },
        { name = "gt_answer", type = "STRING", mode = "REQUIRED" },
        { name = "gt_document_names", type = "STRING", mode = "REPEATED" },
      ]
    },
    "prediction" = {
      fields = [
        { name = "user_id", type = "STRING", mode = "REQUIRED" },
        { name = "prediction_id", type = "STRING", mode = "REQUIRED" },
        { name = "timestamp", type = "TIMESTAMP", mode = "REQUIRED" },
        { name = "system_state_id", type = "STRING", mode = "REQUIRED" },
        { name = "session_id", type = "STRING", mode = "REQUIRED" },
        { name = "question_id", type = "STRING", mode = "REQUIRED" },
        { name = "question", type = "STRING", mode = "REQUIRED" },
        { name = "react_round_number", type = "STRING", mode = "REQUIRED" },
        { name = "response", type = "STRING", mode = "REQUIRED" },
        { name = "retrieved_documents_so_far", type = "STRING", mode = "REQUIRED" },
        { name = "post_filtered_documents_so_far", type = "STRING", mode = "REQUIRED" },
        { name = "retrieved_documents_so_far_content", type = "STRING", mode = "REQUIRED" },
        { name = "post_filtered_documents_so_far_content", type = "STRING", mode = "REQUIRED" },
        { name = "post_filtered_documents_so_far_all_metadata", type = "STRING", mode = "REQUIRED" },
        { name = "confidence_score", type = "INTEGER", mode = "REQUIRED" },
        { name = "response_type", type = "STRING", mode = "REQUIRED" },
        { name = "run_type", type = "STRING", mode = "REQUIRED" },
        { name = "time_taken_total", type = "FLOAT", mode = "REQUIRED" },
        { name = "time_taken_retrieval", type = "FLOAT", mode = "REQUIRED" },
        { name = "time_taken_llm", type = "FLOAT", mode = "REQUIRED" },
        { name = "tokens_used", type = "INTEGER", mode = "REQUIRED" },
        { name = "summaries", type = "STRING", mode = "REQUIRED" },
        { name = "relevance_score", type = "STRING", mode = "REQUIRED" },
        { name = "additional_question", type = "STRING", mode = "NULLABLE" },
        { name = "plan_and_summaries", type = "STRING", mode = "REQUIRED" },
        { name = "original_question", type = "STRING", mode = "NULLABLE" },
        { name = "app_version", type = "STRING", mode = "NULLABLE" },
      ]
    },
    "experiment" = {
      fields = [
        { name = "system_state_id", type = "STRING", mode = "REQUIRED" },
        { name = "session_id", type = "STRING", mode = "REQUIRED" },
        { name = "github_hash", type = "STRING", mode = "REQUIRED" },
        { name = "gcs_bucket_path", type = "STRING", mode = "REQUIRED" },
        { name = "pipeline_parameters", type = "STRING", mode = "REQUIRED" },
        { name = "comments", type = "STRING", mode = "NULLABLE" },
      ]
    },
    "query_evaluation" = {
      fields = [
        { name = "prediction_id", type = "STRING", mode = "REQUIRED" },
        { name = "timestamp", type = "TIMESTAMP", mode = "REQUIRED" },
        { name = "system_state_id", type = "STRING", mode = "REQUIRED" },
        { name = "session_id", type = "STRING", mode = "REQUIRED" },
        { name = "question_id", type = "STRING", mode = "REQUIRED" },
        { name = "react_round_number", type = "STRING", mode = "REQUIRED" },
        { name = "metric_type", type = "STRING", mode = "REQUIRED" },
        { name = "metric_level", type = "STRING", mode = "REQUIRED" },
        { name = "metric_name", type = "STRING", mode = "REQUIRED" },
        { name = "metric_value", type = "FLOAT64", mode = "REQUIRED" },
        { name = "metric_confidence", type = "FLOAT64", mode = "NULLABLE" },
        { name = "metric_explanation", type = "STRING", mode = "NULLABLE" },
        { name = "run_type", type = "STRING", mode = "REQUIRED" },
        { name = "response_type", type = "STRING", mode = "REQUIRED" },
      ]
    },
    "questions" = {
      fields = [
        { name = "question_id", type = "STRING", mode = "REQUIRED" },
        { name = "question", type = "STRING", mode = "REQUIRED" },
        { name = "parent_question_id", type = "STRING", mode = "NULLABLE" },
      ]
    }
  }

}
