# --- Networking: one ALB per service (see deployment plan for the two-ALB-vs-shared tradeoff) ---
# All four ALB-related resources below only exist when enable_alb = true
# (the default, used by agent/frontend). When false (an internal-only
# service like mcp-hotels), none of these are created — the service is
# reached via Cloud Map instead, see aws_service_discovery_service.this.

resource "aws_security_group" "alb" {
  count = var.enable_alb ? 1 : 0

  name_prefix = "${var.name}-alb-"
  description = "Allow inbound HTTP from the internet to the ${var.name} ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "service" {
  name_prefix = "${var.name}-service-"
  # description is ForceNew on this resource — kept identical to the
  # pre-existing text for the enable_alb = true case so this refactor
  # doesn't force-replace agent/frontend's already-running security groups.
  description = var.enable_alb ? "Allow inbound from the ${var.name} ALB only" : "Allow inbound to the ${var.name} service from explicitly allowed security groups (internal-only)"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = var.enable_alb ? [1] : []
    content {
      description     = "From ALB only"
      from_port       = var.container_port
      to_port         = var.container_port
      protocol        = "tcp"
      security_groups = [aws_security_group.alb[0].id]
    }
  }

  dynamic "ingress" {
    for_each = var.enable_alb ? [] : var.allowed_security_group_ids
    content {
      description     = "Internal-only access from an explicitly allowed service"
      from_port       = var.container_port
      to_port         = var.container_port
      protocol        = "tcp"
      security_groups = [ingress.value]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb" "this" {
  count = var.enable_alb ? 1 : 0

  name               = "${var.name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = var.public_subnet_ids
}

resource "aws_lb_target_group" "this" {
  count = var.enable_alb ? 1 : 0

  name        = "${var.name}-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip" # required for awsvpc-mode Fargate tasks

  health_check {
    path                = var.health_check_path
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }
}

resource "aws_lb_listener" "this" {
  count = var.enable_alb ? 1 : 0

  load_balancer_arn = aws_lb.this[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this[0].arn
  }
}

# --- Service discovery (internal-only services only) ---

resource "aws_service_discovery_service" "this" {
  count = var.enable_alb ? 0 : 1

  name = var.name

  dns_config {
    namespace_id = var.service_discovery_namespace_id
    dns_records {
      type = "A"
      ttl  = 10
    }
    routing_policy = "MULTIVALUE"
  }
  # No custom health_check_config — ECS registers/deregisters instances
  # automatically based on task lifecycle, which is enough for a single
  # internal consumer; there's no ALB target group here to attach one to.
}

# --- IAM ---

data "aws_iam_policy_document" "assume_ecs_tasks" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "${var.name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.assume_ecs_tasks.json
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Only created when the service actually has secrets to read.
data "aws_iam_policy_document" "read_secrets" {
  count = length(var.secrets) > 0 ? 1 : 0

  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = values(var.secrets)
  }
}

resource "aws_iam_role_policy" "read_secrets" {
  count  = length(var.secrets) > 0 ? 1 : 0
  name   = "${var.name}-read-secrets"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.read_secrets[0].json
}

resource "aws_iam_role" "task" {
  name               = "${var.name}-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume_ecs_tasks.json
}

resource "aws_iam_role_policy" "task" {
  count  = var.task_role_policy_json != null ? 1 : 0
  name   = "${var.name}-task-policy"
  role   = aws_iam_role.task.id
  policy = var.task_role_policy_json
}

# --- Logs, task definition, service ---

resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/${var.name}"
  retention_in_days = var.log_retention_days
}

resource "aws_ecs_task_definition" "this" {
  family                   = var.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = var.name
      image     = var.image
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = [for k, v in var.environment : { name = k, value = v }]
      secrets     = [for k, v in var.secrets : { name = k, valueFrom = v }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.this.name
          "awslogs-region"        = data.aws_region.current.region
          "awslogs-stream-prefix" = var.name
        }
      }
    }
  ])
}

data "aws_region" "current" {}

resource "aws_ecs_service" "this" {
  name            = var.name
  cluster         = var.cluster_id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [aws_security_group.service.id]
    assign_public_ip = true # public subnets, no NAT Gateway — see var.public_subnet_ids description; needed for image pulls / AWS API calls regardless of enable_alb
  }

  dynamic "load_balancer" {
    for_each = var.enable_alb ? [1] : []
    content {
      target_group_arn = aws_lb_target_group.this[0].arn
      container_name   = var.name
      container_port   = var.container_port
    }
  }

  dynamic "service_registries" {
    for_each = var.enable_alb ? [] : [1]
    content {
      registry_arn = aws_service_discovery_service.this[0].arn
    }
  }

  # Valid even though aws_lb_listener.this has count now: depends_on can
  # reference a counted resource as a whole, and is simply a no-op when
  # that resource's count is 0 (the enable_alb = false case).
  depends_on = [aws_lb_listener.this]
}
