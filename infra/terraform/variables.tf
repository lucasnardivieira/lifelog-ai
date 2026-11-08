variable "project_id" {
  description = "GCP project id"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "southamerica-east1"
}
