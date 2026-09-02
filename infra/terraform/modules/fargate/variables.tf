variable "name" {
  description = "Service name, used to derive resource names (ALB, log group, task family, etc)."
  type        = string
}

variable "image" {
  description = "Full container image reference, e.g. \"tuhoag/travel-assistant-agent:latest\"."
  type        = string
}

variable "container_port" {
  description = "Port the container listens on."
  type        = number
}

variable "health_check_path" {
  description = "Path the ALB target group polls for health."
  type        = string
  default     = "/health"
}

variable "cpu" {
  description = "Fargate task CPU units (256 = 0.25 vCPU)."
  type        = string
  default     = "256"
}

variable "memory" {
  description = "Fargate task memory in MiB."
  type        = string
  default     = "512"
}

variable "desired_count" {
  description = "Number of task copies to run."
  type        = number
  default     = 1
}

variable "vpc_id" {
  description = "VPC to deploy the ALB and service into."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet ids for the ALB and the Fargate task's ENI (no NAT Gateway — tasks get a public IP directly, per the cost/security tradeoff documented in the deployment plan)."
  type        = list(string)
}

variable "cluster_id" {
  description = "ARN of the shared ECS cluster this service runs on."
  type        = string
}

variable "environment" {
  description = "Plain (non-secret) environment variables for the container."
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Env-var-name -> Secrets Manager secret ARN. Injected via the task definition's secrets block, never as plain environment."
  type        = map(string)
  default     = {}
}

variable "log_retention_days" {
  description = "CloudWatch log retention for the service's log group."
  type        = number
  default     = 7
}

variable "task_role_policy_json" {
  description = "Optional IAM policy JSON attached to the task role — for permissions the *application code* needs at runtime (e.g. bedrock:InvokeModel, OpenSearch access), as opposed to the execution role, which only pulls the image and reads secrets. Content only; whether it's attached at all is controlled separately by enable_task_role_policy, since this value may be unknown at plan time (e.g. derived from a data source that references a resource with pending changes) and an unknown value can't drive a resource's count."
  type        = string
  default     = null
}

variable "enable_task_role_policy" {
  description = "Whether to attach task_role_policy_json to the task role. Must be a literal true/false set by the caller — never derived from a resource attribute, which could be unknown at plan time and break the count argument this drives."
  type        = bool
  default     = false
}

variable "enable_alb" {
  description = "false for an internal-only service (no public ALB, not internet-reachable) — registered in Cloud Map for service discovery instead. true (default) preserves the existing public-ALB behavior."
  type        = bool
  default     = true
}

variable "allowed_security_group_ids" {
  description = "Security groups allowed to reach the service directly on container_port. Only used when enable_alb = false (when true, ingress is scoped to the ALB's own security group instead)."
  type        = list(string)
  default     = []
}

variable "service_discovery_namespace_id" {
  description = "Cloud Map private DNS namespace to register the service in. Required when enable_alb = false."
  type        = string
  default     = null
}
