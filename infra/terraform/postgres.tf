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
  # No ingress yet — added by the MCP server step via aws_security_group_rule,
  # once the MCP server's own security group exists to reference.
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
  publicly_accessible    = false

  skip_final_snapshot = true # demo project — no need to retain a snapshot on destroy
}
