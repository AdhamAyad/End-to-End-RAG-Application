resource "google_storage_bucket" "admin_files_bucket" {
  name          = var.admin_bucket_name
  location      = var.region                   
  storage_class = "STANDARD"
  force_destroy = true
  public_access_prevention    = "enforced"

  lifecycle_rule {
    action {
      type          = "SetStorageClass"
      storage_class = "ARCHIVE"
    }
    condition {
      age = 1
    }
  }      

  versioning {
    enabled = false
  }
  uniform_bucket_level_access = true
}