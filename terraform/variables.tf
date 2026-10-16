variable "aws_region" {
  description = "Region for all project resources."
  type        = string
  default     = "ap-southeast-2"
}

variable "sts_region" {
  description = "Optional identity-endpoint region override; does not move infrastructure."
  type        = string
  default     = null
}

variable "aws_account_id" {
  description = "Expected account ID; prevents accidentally deploying to another account."
  type        = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "Use the 12-digit account ID returned by aws sts get-caller-identity."
  }
}

variable "project_name" {
  description = "Prefix for resource names."
  type        = string
  default     = "teamdesk"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,25}$", var.project_name))
    error_message = "Use 3–26 lowercase letters, numbers, or hyphens, starting with a letter."
  }
}

variable "availability_zones" {
  description = "Two standard availability zones in the selected region."
  type        = list(string)
  default     = ["ap-southeast-2a", "ap-southeast-2b"]
  validation {
    condition     = length(distinct(var.availability_zones)) == 2 && length(var.availability_zones) == 2
    error_message = "Provide exactly two different availability zones."
  }
}

variable "kubernetes_version" {
  description = "EKS version in standard support; check availability before changing."
  type        = string
  default     = "1.35"
}

variable "node_instance_type" {
  description = "Two c7i-flex.large nodes provide 4 vCPUs and 8 GiB total; verify Free plan eligibility in the chosen region."
  type        = string
  default     = "c7i-flex.large"
}

variable "api_allowed_cidrs" {
  description = "Public Kubernetes API callers; authentication and EKS access policies still apply. Public access supports GitHub-hosted deployment runners."
  type        = list(string)
  default     = ["0.0.0.0/0"]
  validation {
    condition     = length(var.api_allowed_cidrs) > 0 && alltrue([for cidr in var.api_allowed_cidrs : can(cidrnetmask(cidr))])
    error_message = "Provide at least one valid IPv4 CIDR."
  }
}
