# Single-node, small-instance OpenSearch domain with a public endpoint —
# access is controlled entirely by the IAM resource policy below (SigV4),
# not network placement or a security group. Only the agent's task role and
# whoever runs `terraform apply` (assumed to be the same identity used to
# run the ingestion pipeline locally) can actually call it; anyone else's
# request is rejected with a 403 regardless of network reachability.

data "aws_iam_policy_document" "opensearch_access" {
  statement {
    actions   = ["es:*"]
    resources = ["arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/travel-assistant/*"]
    principals {
      type        = "AWS"
      identifiers = [module.agent.task_role_arn, data.aws_caller_identity.current.arn]
    }
  }
}

resource "aws_opensearch_domain" "travel_assistant" {
  domain_name    = "travel-assistant"
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type  = "t3.small.search" # smallest instance type that supports OpenSearch 2.x
    instance_count = 1                 # single node — no zone_awareness, cheapest viable setup for a demo
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 10
  }

  access_policies = data.aws_iam_policy_document.opensearch_access.json
}
