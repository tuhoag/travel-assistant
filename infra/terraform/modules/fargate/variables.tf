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
  description = "Optional IAM policy JSON attached to the task role — for permissions the *application code* needs at runtime (e.g. bedrock:InvokeModel, OpenSearch access), as opposed to the execution role, which only pulls the image and reads secrets."
  type        = string
  default     = null
}
