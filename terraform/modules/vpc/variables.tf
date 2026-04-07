variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "network_name" {
  description = "The name of the network"
  type        = string
}

variable "region" {
  description = "The region for the network"
  type        = string
}

variable "subnets" {
  description = "The list of subnets to create"
  type = list(object({
    subnet_name              = string
    subnet_ip                = string
    subnet_region            = string
    private_ip_google_access = optional(bool, true)
  }))
}

variable "secondary_ranges" {
  description = "Secondary IP ranges for subnets"
  type = map(list(object({
    range_name    = string
    ip_cidr_range = string
  })))
  default = {}
}
