variable "service_name" {
  description = "Cloud Run service name"
  type        = string
}

variable "region" {
  description = "Cloud Run region"
  type        = string
}

variable "image" {
  description = "Container image"
  type        = string
}

variable "port" {
  description = "Container port"
  type        = number
  default     = 8080
}

variable "service_account_email" {
  description = "Service account email to run Cloud Run service"
  type        = string
}

variable "auth" {
  description = "Authentication type: public or private"
  type        = string
  default     = "private"
}

variable "by_req" {
  description = "Billing type: request or instance"
  type        = bool
  default     = true
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 3
}

variable "ingress" {
  description = "Ingress type: internal or all"
  type        = string
  default     = "INGRESS_TRAFFIC_INTERNAL_ONLY"
}