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
    resource.null_resource.push_image
    ]
}