# IAM Module - Service Accounts and Workload Identity Configuration
# Creates service accounts and binds them to Kubernetes service accounts

# Create Google Service Accounts
resource "google_service_account" "service_accounts" {
  for_each = var.service_accounts

  account_id   = each.value.account_id
  display_name = each.value.display_name
  description  = lookup(each.value, "description", null)
  project      = var.project_id
}

# Assign IAM roles to service accounts
resource "google_project_iam_member" "service_account_roles" {
  for_each = {
    for pair in flatten([
      for sa_key, sa in var.service_accounts : [
        for role in sa.roles : {
          key     = "${sa_key}-${role}"
          sa_key  = sa_key
          role    = role
        }
      ]
    ]) : pair.key => pair
  }

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.service_accounts[each.value.sa_key].email}"
}

# Workload Identity bindings
resource "google_service_account_iam_member" "workload_identity_bindings" {
  for_each = var.workload_identity_bindings

  service_account_id = google_service_account.service_accounts[each.value.service_account].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${each.value.namespace}/${each.value.ksa_name}]"
}
