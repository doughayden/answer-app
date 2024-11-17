resource "google_cloud_run_v2_service" "run_app" {
  name                = var.service_name
  location            = var.region
  deletion_protection = false
  launch_stage        = "GA"
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  custom_audiences = [
    "https://${var.lb_domain}/${var.service_name}",
  ]

  template {
    service_account       = var.service_account
    timeout               = "300s"
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    containers {
      image = var.docker_image

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
      }

      startup_probe {
        timeout_seconds   = 30
        period_seconds    = 180
        failure_threshold = 1
        tcp_socket {
          port = 8080
        }
      }

    }

    scaling {
      min_instance_count = 1
      max_instance_count = 100
    }

  }
}

resource "google_compute_region_network_endpoint_group" "run_app" {
  name                  = var.service_name
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.run_app.name
  }
}

resource "google_compute_backend_service" "run_app" {
  name        = var.service_name
  description = var.service_name

  protocol                        = "HTTPS"
  port_name                       = "http"
  connection_draining_timeout_sec = 0

  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.run_app.id
  }

  # Identity-Aware Proxy (IAP) for external apps requires manual configuration - ignore those changes.
  lifecycle {
    ignore_changes = [iap]
  }
}
