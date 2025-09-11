module "chunk_cloud_run" {
  source                = "./modules/cloud_run_module/"
  service_name          = "chunk-cloud-run"
  region                = var.region
  image                 = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images_repo.repository_id}/chunk-image:v1"
  port                  = 8080
  service_account_email = module.chunk_cloud_run_sa.service_account_email
  auth                  = "private"
  by_req                = true
  min_instances         = 0
  max_instances         = 3
  ingress               = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  depends_on            = [
    module.chunk_cloud_run_sa,
    null_resource.push_image
    ]
}

resource "google_redis_instance" "user_memory_store" {
  name           = "user-memory-store"
  tier           = "STANDARD_HA"
  memory_size_gb = 5
  region         = var.region
  redis_version  = "REDIS_6_X"
  authorized_network = google_compute_network.rag_vpc.id
  transit_encryption_mode = "DISABLED"  
  depends_on = [ google_compute_subnetwork.rag_subnet ]
}

module "user_cloud_run" {
  source                = "./modules/cloud_run_module/"
  service_name          = "user-cloud-run"
  region                = var.region
  image                 = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images_repo.repository_id}/user-backend:v1"
  port                  = 8080
  service_account_email = module.user_cloud_run_sa.service_account_email
  auth                  = "public"
  by_req                = true
  min_instances         = 0
  max_instances         = 3
  ingress               = "INGRESS_TRAFFIC_ALL"
  vpc_connector = google_vpc_access_connector.cloud_run_connector.id
  depends_on            = [
    module.user_cloud_run_sa,
    null_resource.push_user_backend_image,
    module.chunk_cloud_run,
    google_redis_instance.user_memory_store,
    google_vpc_access_connector.cloud_run_connector,
    google_vertex_ai_index_endpoint.rag_endpoint
    ]
}