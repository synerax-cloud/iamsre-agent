output "service_account_emails" {
  description = "Map of service account emails"
  value       = { for k, sa in google_service_account.service_accounts : k => sa.email }
}

output "service_account_names" {
  description = "Map of service account names"
  value       = { for k, sa in google_service_account.service_accounts : k => sa.name }
}

output "service_account_unique_ids" {
  description = "Map of service account unique IDs"
  value       = { for k, sa in google_service_account.service_accounts : k => sa.unique_id }
}
