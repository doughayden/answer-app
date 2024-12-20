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

variable "docker_image" {
  description = "The API Cloud Run service Docker image."
  type        = map(string)
  nullable    = true
  default     = null
}
