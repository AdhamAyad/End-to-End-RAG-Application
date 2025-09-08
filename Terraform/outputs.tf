# 1. User Frontend Service Account
output "cdn_bucket_sa_email" {
  value = module.cdn_bucket_sa.service_account_email
}

# 2. User Cloud Run Service Account
output "user_cloud_run_sa_email" {
  value = module.user_cloud_run_sa.service_account_email
}

# 3. Admin Frontend and Files Storage Service Account
output "admin_bucket_sa_email" {
  value = module.admin_bucket_sa.service_account_email
}

# 4. Admin Cloud Run Service Account
output "admin_cloud_run_sa_email" {
  value = module.admin_cloud_run_sa.service_account_email
}