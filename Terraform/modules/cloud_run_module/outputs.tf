output "cloud_run_endpoint" {
  value = google_cloud_run_v2_service.cloud_run_module.uri
}

# output "chunk_cloud_run_internal_url" {
#   value       = "http://${google_cloud_run_v2_service.cloud_run_module.name}.${var.region}.internal"
#   description = "Internal URL for VPC-connected Cloud Run service"
# }