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

module "subscription_sa" {
    source = "./modules/service_account_module"
    account_id = "subscription-sa"
    display_name = "Subscription Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
    ]
}

# module "cdn_bucket_sa" {
#     source = "./modules/service_account_module"
#     account_id = "user-cdn-bucket-sa"
#     display_name = "User Frontend Service Account"
#     project_id = var.project_id
#     rules = [
#         "roles/run.invoker",
#         "roles/storage.objectViewer"
#     ]
# }