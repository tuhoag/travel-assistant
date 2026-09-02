import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]

# Loads the repo-root .env if present, without overriding vars already set
# in the shell — same convention as pipelines-prefect/flows/hotels_ingest_flow.py.
load_dotenv(REPO_ROOT / ".env")

AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")

PGHOST = os.environ.get("PGHOST", "localhost")
PGPORT = os.environ.get("PGPORT", "5432")
PGDATABASE = os.environ.get("PGDATABASE", "hotels")
# Local dev (docker-compose Postgres): plain credentials, no AWS calls.
PGUSER = os.environ.get("PGUSER")
PGPASSWORD = os.environ.get("PGPASSWORD")
# Production (real RDS): PGUSER/PGPASSWORD are unset, credentials are
# fetched from this Secrets Manager secret at runtime (db.py) instead —
# never stored here or in .env.
HOTELS_DB_SECRET_ARN = os.environ.get("HOTELS_DB_SECRET_ARN")

MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8080"))
