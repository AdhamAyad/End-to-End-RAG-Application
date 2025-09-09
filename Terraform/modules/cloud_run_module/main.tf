resource "google_cloud_run_v2_service" "cloud_run_module" {
  name     = var.service_name
  location = var.region
  deletion_protection = false

  template {
    containers {
      image = var.image
      ports {
        container_port = var.port
      }
      resources {
        cpu_idle = var.by_req
      }
    }

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    service_account = var.service_account_email
    
  }

  ingress = var.ingress

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_service_iam_member" "public_access" {
  count    = var.auth == "public" ? 1 : 0
  service  = google_cloud_run_v2_service.cloud_run_module.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
