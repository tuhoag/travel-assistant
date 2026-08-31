output "url" {
  description = "Public HTTP URL of the service, via its ALB."
  value       = "http://${aws_lb.this.dns_name}"
}

output "alb_dns_name" {
  value = aws_lb.this.dns_name
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
