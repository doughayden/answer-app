# Global IP address.
resource "google_compute_global_address" "lb_global_address" {
  name         = "load-balancer-global-address"
  address_type = "EXTERNAL"
}

# HTTPS resources.
resource "google_compute_global_forwarding_rule" "https_redirect" {
  name                  = "load-balancer-global-forwarding-rule-https"
  target                = google_compute_target_https_proxy.https_redirect.id
  port_range            = "443-443"
  ip_address            = google_compute_global_address.lb_global_address.address
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

resource "google_compute_target_https_proxy" "https_redirect" {
  name             = "load-balancer-target-https-proxy"
  url_map          = google_compute_url_map.lb_url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.cert.id]
}

locals {
  lb_domain = coalesce(var.lb_domain, "${google_compute_global_address.lb_global_address.address}.sslip.io")
}

resource "random_id" "certificate" {
  byte_length = 4
  prefix      = "lb-cert-"

  keepers = {
    # Ensure a new id is generated when the domain changes
    # ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_managed_ssl_certificate#example-usage---managed-ssl-certificate-recreation
    # ref: https://github.com/hashicorp/terraform-provider-google/issues/5356
    domain = local.lb_domain
  }
}

resource "google_compute_managed_ssl_certificate" "cert" {
  name = random_id.certificate.hex

  lifecycle {
    create_before_destroy = true
  }

  managed {
    domains = [local.lb_domain]
  }
}

# URL Map.
resource "google_compute_url_map" "lb_url_map" {
  name            = "load-balancer-url-map"
  default_service = var.default_service

  host_rule {
    hosts        = [local.lb_domain]
    path_matcher = "lb-path-matcher"
  }

  path_matcher {
    default_service = var.default_service
    name            = "lb-path-matcher"

    dynamic "path_rule" {
      for_each = var.backend_services

      content {
        paths   = path_rule.value.paths
        service = path_rule.value.service
        route_action {
          url_rewrite {
            path_prefix_rewrite = path_rule.value.path_prefix_rewrite
          }
        }
      }
    }
  }
}
