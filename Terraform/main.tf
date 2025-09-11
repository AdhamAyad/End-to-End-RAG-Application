# Artifact Registry Repository and Push Images
resource "google_artifact_registry_repository" "images_repo" {
  location      = var.region
  repository_id = "images-repo"
  description   = "Docker images for Cloud Run services"
  format        = "DOCKER"
}

resource "null_resource" "push_image" {
  provisioner "local-exec" {
    command = <<EOT
      gcloud auth configure-docker ${var.region}-docker.pkg.dev -q

      docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images_repo.repository_id}/chunk-image:v1 ../Chunk_Function/
      docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images_repo.repository_id}/chunk-image:v1
    EOT
    interpreter = ["bash", "-c"]
  }

  depends_on = [google_artifact_registry_repository.images_repo]
}

resource "null_resource" "push_user_backend_image" {
  provisioner "local-exec" {
    command = <<EOT
      gcloud auth configure-docker ${var.region}-docker.pkg.dev -q

      docker build \
      --build-arg CHUNK_URL=${module.chunk_cloud_run.cloud_run_endpoint} \
      --build-arg VECTOR_DB_ENDPOINT=${google_vertex_ai_index_endpoint.rag_endpoint.id} \
      --build-arg MEMORY_STORE_HOST=${google_redis_instance.user_memory_store.host} \
      --build-arg MEMORY_STORE_PORT=${google_redis_instance.user_memory_store.port} \
      -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images_repo.repository_id}/user-backend:v1 ../Users_Backend/
      
      docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images_repo.repository_id}/user-backend:v1
    EOT
    interpreter = ["bash", "-c"]
  }

  depends_on = [
    google_artifact_registry_repository.images_repo,

  ]
}

# Vector DB / Matching Engine Index
resource "google_vertex_ai_index" "rag_index" {
  display_name        = "rag_index_01"
  region              = var.region
  index_update_method = "BATCH_UPDATE"
  metadata {
    config {
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
      dimensions                  = 1536
      approximate_neighbors_count = 100
      shard_size                  = "SHARD_SIZE_SMALL"
    }
  }
}

resource "google_vertex_ai_index_endpoint" "rag_endpoint" {
  display_name = "rag-index-endpoint"
  region       = var.region
  depends_on = [ google_vertex_ai_index.rag_index ]
}

resource "google_vertex_ai_index_endpoint_deployed_index" "rag_deployed" {
  deployed_index_id = "rag_index_01"
  index_endpoint = google_vertex_ai_index_endpoint.rag_endpoint.id
  index          = google_vertex_ai_index.rag_index.id
  dedicated_resources {
  machine_spec {
    machine_type = "e2-standard-2"
  }
  min_replica_count = 1
  max_replica_count = 1
 }
}