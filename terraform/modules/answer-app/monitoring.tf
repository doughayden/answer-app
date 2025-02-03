resource "google_monitoring_dashboard" "answer_app_dashboard" {
  dashboard_json = templatefile(
    "${path.module}/dashboard.json",
    {
      project_id      = var.project_id,
      service_name    = google_cloud_run_v2_service.run_app[var.region].name,
    }
  )
}
