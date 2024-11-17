variable "service_name" {
  description = "The Cloud Run service name."
  type        = string
}

variable "project_id" {
  description = "The project ID."
  type        = string
}

variable "region" {
  type        = string
  description = "The Compute API default region."
}

variable "lb_domain" {
  type        = string
  description = "The load balancer domain name."
}

variable "service_account" {
  description = "The Cloud Run service-attached service account email address."
  type        = string
}

variable "docker_image" {
  description = "The Cloud Run service Docker image."
  type        = string
}
