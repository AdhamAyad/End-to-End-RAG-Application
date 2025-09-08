variable "account_id" {
    type = string
}

variable "display_name" {
    type = string
}

variable "project_id" {
    type = string
    description = "Google Cloud project ID"
}

variable "rules" {
    type = list(string)
    default = []
}