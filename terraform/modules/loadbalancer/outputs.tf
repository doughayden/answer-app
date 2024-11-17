output "lb_ip_address" {
  description = "The load balancer IP address."
  value       = google_compute_global_address.lb_global_address.address
}

output "lb_domain" {
  description = "The load balancer domain name."
  value       = local.lb_domain
}

output "cert_name" {
  description = "The Google-managed encryption certificate name."
  value       = google_compute_managed_ssl_certificate.cert.name
}
