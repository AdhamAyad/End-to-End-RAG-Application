# # 1. User Frontend Service Account
# output "cdn_bucket_sa_email" {
#   value = module.cdn_bucket_sa.service_account_email
# }

# # 2. User Cloud Run Service Account
# output "user_cloud_run_sa_email" {
#   value = module.user_cloud_run_sa.service_account_email
# }

# # 3. Admin Frontend and Files Storage Service Account
# output "admin_bucket_sa_email" {
#   value = module.admin_bucket_sa.service_account_email
# }

# # 4. Admin Cloud Run Service Account
# output "admin_cloud_run_sa_email" {
#   value = module.admin_cloud_run_sa.service_account_email
# }

# 5. Chunk Cloud Run EndPoint
output "chunk_cloud_run_endpoint" {
  value = module.chunk_cloud_run.cloud_run_endpoint
}

# 6. Embedding Model EndPoint URL
output "index_endpoint_url" {
  description = "The URL of the Vertex AI Endpoint for embeddings."
  value       = google_vertex_ai_index_endpoint.rag_endpoint.id
}

output "redis_host" {
  value = google_redis_instance.user_memory_store.host
}

output "redis_port" {
  value = google_redis_instance.user_memory_store.port
}

output "user_url" {
  value = module.user_cloud_run.cloud_run_endpoint
}