# 1. User Frontend Service Account
module "cdn_bucket_sa" {
    source = "./modules/service_account_module"
    account_id = "user-cdn-bucket-sa"
    display_name = "User Frontend Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
        "roles/storage.objectViewer"
    ]
}

# 2. User Cloud Run Service Account
module "user_cloud_run_sa" {
    source = "./modules/service_account_module"
    account_id = "user-cloud-run-sa"
    display_name = "User Cloud Run Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
        "roles/redis.viewer",
        "roles/aiplatform.user",
        "roles/artifactregistry.reader",
        "roles/compute.networkUser"
    ]
}

# 3. Admin Frontend and Files Storage Service Account
module "admin_bucket_sa" {
    source = "./modules/service_account_module"
    account_id = "admin-bucket-sa"
    display_name = "Admin Bucket Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
        "roles/pubsub.publisher",
        "roles/storage.objectCreator",
    ]
}

# 4. Admin Cloud Run Service Account
module "admin_cloud_run_sa" {
    source = "./modules/service_account_module"
    account_id = "admin-cloud-run-sa"
    display_name = "Admin Cloud Run Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
        "roles/pubsub.subscriber",
        "roles/pubsub.viewer",
        "roles/aiplatform.user",
        "roles/datastore.user",
        "roles/storage.objectViewer",
        "roles/artifactregistry.reader"
    ]
}

# 5. Chunk Cloud Run Service Account
module "chunk_cloud_run_sa" {
    source = "./modules/service_account_module"
    account_id = "chunk-cloud-run-sa"
    display_name = "Chunk Cloud Run Service Account"
    project_id = var.project_id
    rules = [
        "roles/artifactregistry.reader",
        "roles/run.invoker",
    ]
}

# # Embedding Model and Vector DB / Matching Engine Index Service Account
# module "vertex_sa" {
#     source = "./modules/service_account_module"
#     account_id = "vertex-sa"
#     display_name = "Vertex Service Account"
#     project_id = var.project_id
# }public