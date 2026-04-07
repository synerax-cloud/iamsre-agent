output "instance_name" {
  description = "The name of the Cloud SQL instance"
  value       = google_sql_database_instance.instance.name
}

output "instance_connection_name" {
  description = "The connection name of the Cloud SQL instance"
  value       = google_sql_database_instance.instance.connection_name
}

output "instance_self_link" {
  description = "The self link of the Cloud SQL instance"
  value       = google_sql_database_instance.instance.self_link
}

output "private_ip_address" {
  description = "The private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.instance.private_ip_address
  sensitive   = true
}

output "public_ip_address" {
  description = "The public IP address of the Cloud SQL instance"
  value       = length(google_sql_database_instance.instance.ip_address) > 0 ? google_sql_database_instance.instance.ip_address[0].ip_address : null
  sensitive   = true
}

output "database_names" {
  description = "List of database names"
  value       = [for db in google_sql_database.databases : db.name]
}

output "user_names" {
  description = "List of user names"
  value       = [for user in google_sql_user.users : user.name]
}

output "replica_instance_names" {
  description = "List of replica instance names"
  value       = [for replica in google_sql_database_instance.replica : replica.name]
}

output "replica_connection_names" {
  description = "List of replica connection names"
  value       = [for replica in google_sql_database_instance.replica : replica.connection_name]
}
