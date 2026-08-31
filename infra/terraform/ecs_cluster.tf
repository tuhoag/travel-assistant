# One cluster shared by every Fargate service — an ECS cluster is just a
# logical grouping (no dedicated capacity billed on its own), so splitting
# services across multiple clusters would only add naming overhead.
resource "aws_ecs_cluster" "this" {
  name = "travel-assistant"
}
