# output "cdn_bucket_sa_email" {
#   value = module.cdn_bucket_sa.service_account_email
# }

# output "user_cloud_run_sa_email" {
#   value = module.user_cloud_run_sa.service_account_email
# }

# output "admin_bucket_sa_email" {
#   value = module.admin_bucket_sa.service_account_email
# }

# output "admin_cloud_run_sa_email" {
#   value = module.admin_cloud_run_sa.service_account_email
# }

output "chunk_cloud_run_endpoint" {
  value = module.chunk_cloud_run.cloud_run_endpoint
}

output "user_url" {
  value = module.user_cloud_run.cloud_run_endpoint
}

output "admin_url" {
  value = module.admin_cloud_run.cloud_run_endpoint
}

output "user_frontend_url" {
  value = module.user_frontend_cloud_run.cloud_run_endpoint
}

# output "index_endpoint_url" {
#   description = "The URL of the Vertex AI Endpoint for embeddings."
#   value       = google_vertex_ai_index_endpoint.rag_endpoint.id
# }

# output "redis_host" {
#   value = google_redis_instance.user_memory_store.host
# }

# output "redis_port" {
#   value = google_redis_instance.user_memory_store.port
# }

# output "index_endpoint" {
#   value = google_vertex_ai_index_endpoint.rag_endpoint.name
# }