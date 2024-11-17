variable "project_id" {
  description = "The project ID."
  type        = string
}

variable "terraform_service_account" {
  type        = string
  description = "The Terraform provisioning service account email address."
}

variable "region" {
  type        = string
  description = "The Compute API deafult region."
  default     = "us-central1"
}

variable "zone" {
  type        = string
  description = "The Compute API default zone."
  default     = "us-central1-a"
}

variable "vpc_subnet_cidr" {
  type        = string
  description = "The VPC subnetwork CIDR."
  default     = "10.0.0.0/24"
}

variable "docker_image" {
  description = "The API Cloud Run service Docker image."
  type        = string
  nullable    = true
  default     = null
}
