resource "aws_db_subnet_group" "hotels" {
  name       = "travel-assistant-hotels"
  subnet_ids = aws_subnet.public[*].id
}

resource "aws_security_group" "postgres" {
  name   = "travel-assistant-postgres"
  vpc_id = aws_vpc.this.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Dev-only: lets the Prefect ingestion flow run from a laptop.
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.dev_ingress_cidr]
  }

  ingress {
    description     = "mcp-hotels service"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.mcp_hotels.security_group_id]
  }
}

resource "aws_db_instance" "hotels" {
  identifier        = "travel-assistant-hotels"
  engine            = "postgres"
  instance_class    = "db.t4g.micro" # smallest Postgres-compatible burstable instance
  allocated_storage = 20
  storage_type      = "gp3"

  db_name                     = "hotels"
  username                    = "hotels_admin"
  manage_master_user_password = true # RDS creates/rotates the secret in Secrets Manager

  db_subnet_group_name   = aws_db_subnet_group.hotels.name
  vpc_security_group_ids = [aws_security_group.postgres.id]
  # true: without a public IP/DNS route, the security group's ingress rule
  # has nothing to gate — no path can reach the instance at all, from a
  # laptop or otherwise. Actual access control is the SG rule above (scoped
  # to var.dev_ingress_cidr) plus the real password in Secrets Manager, not
  # network placement.
  publicly_accessible = true

  skip_final_snapshot = true # demo project — no need to retain a snapshot on destroy
}
