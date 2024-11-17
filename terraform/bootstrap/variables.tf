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
  description = "The Compute API default region."
  default     = "us-central1"
}

variable "services" {
  type        = list(string)
  description = "The Google Cloud APIs to enable."
}

variable "cloudbuild_iam_roles" {
  type        = list(string)
  description = "The Cloud Build service account IAM roles."
}
