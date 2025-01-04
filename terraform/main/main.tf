data "terraform_remote_state" "main" {
  backend = "gcs"
  config = {
    bucket                      = "terraform-state-${var.project_id}"
    impersonate_service_account = var.terraform_service_account
    prefix                      = "main"
  }
  workspace = terraform.workspace
}

locals {
  # Load the configuration file.
  config = yamldecode(file("../../src/backend/config.yaml"))

  # Use the load balancer domain name from the configuration file if it is set.
  # Otherwise, get the domain name from the load balancer module output.
  lb_domain = coalesce(local.config.loadbalancer_domain, try(module.loadbalancer[0].lb_domain, null))

  # Read the Docker image name from an input variable.
  # Otherwise, use the existing image and get the name from the remote state output.
  docker_image = coalesce(var.docker_image, try(data.terraform_remote_state.main.outputs.docker_image, null))
}

module "loadbalancer" {
  source          = "../modules/loadbalancer"
  count           = local.config.create_loadbalancer ? 1 : 0
  project_id      = var.project_id
  lb_domain       = local.config.loadbalancer_domain
  default_service = module.answer_app.cloudrun_client_backend_service_id
  backend_services = [
    {
      paths   = ["/${module.answer_app.service_name}/*"]
      service = module.answer_app.cloudrun_backend_service_id
    },
    {
      paths   = ["/${module.answer_app.client_service_name}", "/${module.answer_app.client_service_name}/*"]
      service = module.answer_app.cloudrun_client_backend_service_id
    },
  ]
}

# Get the Identity-Aware Proxy (IAP) Service Agent from the google-beta provider.
resource "google_project_service_identity" "iap_sa" {
  provider = google-beta
  service  = "iap.googleapis.com"
}

module "answer_app" {
  source        = "../modules/answer-app"
  project_id    = var.project_id
  region        = var.region
  iap_sa_member = google_project_service_identity.iap_sa.member
  app_name      = local.config.app_name
  lb_domain     = local.lb_domain
  docker_image  = local.docker_image
  location      = local.config.location
  dataset_id    = local.config.dataset_id
  table_id      = local.config.table_id

  data_stores = {
    "${local.config.app_name}-default" = {
      data_store_id = local.config.data_store_id
    }
  }
  search_engine = {
    search_engine_id = local.config.search_engine_id
    company_name     = local.config.customer_name
  }
}

# module "workflow" {
#   source           = "../modules/workflow"
#   project_id       = var.project_id
#   audience         = module.answer_app.cloudrun_custom_audiences[0]
#   company_name     = local.config.customer_name
#   data_store_id    = local.config.data_store_id
#   lb_domain        = local.lb_domain
#   location         = local.config.location
#   search_engine_id = local.config.search_engine_id
# }
