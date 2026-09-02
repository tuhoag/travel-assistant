# Private DNS namespace for internal-only services (no public ALB) to
# register themselves in and be reachable from other services in the VPC —
# e.g. mcp-hotels, reached by the agent at
# travel-assistant-mcp-hotels.internal.travel-assistant.local.
resource "aws_service_discovery_private_dns_namespace" "internal" {
  name = "internal.travel-assistant.local"
  vpc  = aws_vpc.this.id
}
