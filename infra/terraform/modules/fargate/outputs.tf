output "url" {
  description = "Public HTTP URL of the service, via its ALB. null when enable_alb = false (no public ALB exists)."
  value       = var.enable_alb ? "http://${aws_lb.this[0].dns_name}" : null
}

output "alb_dns_name" {
  description = "null when enable_alb = false (no public ALB exists)."
  value       = var.enable_alb ? aws_lb.this[0].dns_name : null
}

output "service_discovery_name" {
  description = "The Cloud Map service name this service is registered under. null when enable_alb = true (no service discovery registration)."
  value       = var.enable_alb ? null : aws_service_discovery_service.this[0].name
}

output "service_name" {
  value = aws_ecs_service.this.name
}

output "cluster_id" {
  value = var.cluster_id
}

output "task_role_arn" {
  description = "ARN of the task role — what the application code itself runs as (e.g. for Bedrock/OpenSearch IAM auth), as opposed to the execution role."
  value       = aws_iam_role.task.arn
}

output "security_group_id" {
  description = "The service's own security group, for scoping other resources' access to exactly this service (e.g. an OpenSearch domain's ingress rule)."
  value       = aws_security_group.service.id
}
