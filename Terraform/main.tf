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