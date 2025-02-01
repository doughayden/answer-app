locals {
  run_app_env = {
    LOG_LEVEL = "INFO"
  }
  run_app_client_env = {
    LOG_LEVEL = "INFO"
    AUDIENCE  = google_cloud_run_v2_service.run_app[var.region].custom_audiences[0]
  }
  regions = concat([var.region], var.additional_regions)
}

resource "google_cloud_run_v2_service" "run_app" {
  for_each            = toset(local.regions)
  name                = var.app_name
  location            = each.value
  deletion_protection = false
  launch_stage        = "GA"
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  custom_audiences = [
    "https://${var.lb_domain}/${var.app_name}",
  ]

  template {
    service_account       = google_service_account.app_service_account.email
    timeout               = "300s"
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    containers {
      image = var.docker_image[var.app_name]

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
        # true = Request-based billing, false = instance-based billing
        # https://cloud.google.com/run/docs/configuring/billing-settings#setting
        cpu_idle = true
      }

      startup_probe {
        timeout_seconds   = 30
        period_seconds    = 180
        failure_threshold = 1
        tcp_socket {
          port = 8080
        }
      }

      dynamic "env" {
        for_each = local.run_app_env
        content {
          name  = env.key
          value = env.value
        }
      }

    }

    # Explicitly set the concurrency (defaults to 80 for CPU >= 1).
    max_instance_request_concurrency = 100

    scaling {
      # Set min_instance_count to 1 or more in production to avoid cold start latency.
      min_instance_count = 1
      max_instance_count = 100
    }

  }
}

resource "google_compute_region_network_endpoint_group" "run_app" {
  for_each              = toset(local.regions)
  name                  = var.app_name
  network_endpoint_type = "SERVERLESS"
  region                = each.value
  cloud_run {
    service = google_cloud_run_v2_service.run_app[each.value].name
  }
}

resource "google_compute_backend_service" "run_app" {
  name        = var.app_name
  description = var.app_name

  protocol                        = "HTTPS"
  port_name                       = "http"
  connection_draining_timeout_sec = 0

  load_balancing_scheme = "EXTERNAL_MANAGED"

  dynamic "backend" {
    for_each = toset(local.regions)
    content {
      group = google_compute_region_network_endpoint_group.run_app[backend.key].id
    }
  }

  # Identity-Aware Proxy (IAP) for external apps requires manual configuration - ignore those changes.
  lifecycle {
    ignore_changes = [iap]
  }
}

resource "google_cloud_run_v2_service" "run_app_client" {
  name                = "${var.app_name}-client"
  location            = var.region
  deletion_protection = false
  launch_stage        = "GA"
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account       = google_service_account.client_app_service_account.email
    timeout               = "300s"
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    containers {
      image = var.docker_image["${var.app_name}-client"]

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
        # true = Request-based billing, false = instance-based billing
        # https://cloud.google.com/run/docs/configuring/billing-settings#setting
        cpu_idle = true
      }

      startup_probe {
        timeout_seconds   = 30
        period_seconds    = 180
        failure_threshold = 1
        tcp_socket {
          port = 8080
        }
      }

      dynamic "env" {
        for_each = local.run_app_client_env
        content {
          name  = env.key
          value = env.value
        }
      }

    }

    # Explicitly set the concurrency (defaults to 80 for CPU >= 1).
    max_instance_request_concurrency = 100

    scaling {
      min_instance_count = 1
      max_instance_count = 100
    }

  }
}

resource "google_compute_region_network_endpoint_group" "run_app_client" {
  name                  = "${var.app_name}-client"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.run_app_client.name
  }
}

resource "google_compute_backend_service" "run_app_client" {
  name        = "${var.app_name}-client"
  description = "${var.app_name}-client"

  protocol                        = "HTTPS"
  port_name                       = "http"
  connection_draining_timeout_sec = 0

  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.run_app_client.id
  }

  # Identity-Aware Proxy (IAP) for external apps requires manual configuration - ignore those changes.
  lifecycle {
    ignore_changes = [iap]
  }
}
