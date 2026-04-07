variable "project_id" {
  description = "The project ID"
  type        = string
}

variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
}

variable "service_accounts" {
  description = "Map of service accounts to create"
  type = map(object({
    account_id   = string
    display_name = string
    description  = optional(string)
    roles        = list(string)
  }))
  default = {}
}

variable "workload_identity_bindings" {
  description = "Map of workload identity bindings"
  type = map(object({
    service_account = string
    namespace       = string
    ksa_name        = string
  }))
  default = {}
}
