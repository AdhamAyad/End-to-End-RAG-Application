resource "google_service_account" "service_account_module" {
  account_id   = var.account_id
  display_name = var.display_name
}

resource "google_project_iam_member" "service_account_roles" {
  for_each = toset(var.rules)
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.service_account_module.email}"
}
