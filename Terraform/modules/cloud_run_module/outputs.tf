output "cloud_run_endpoint" {
  value = google_cloud_run_v2_service.cloud_run_module.uri
}