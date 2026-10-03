"""Snowflake backend: the same Olist tables, in a cloud warehouse.

The agent signs in as a read-only SERVICE user with an RSA key pair (no
password). Read-only is enforced by Snowflake itself (the role has only
USAGE and SELECT), and Snowflake also enforces the 30s statement timeout.
"""
import os
from functools import lru_cache

import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.errors import ProgrammingError

from backend.warehouse.base import QUERY_TIMEOUT_S, QueryResult, QueryTimeoutError, TableInfo, Warehouse

load_dotenv()

SAMPLE_ROWS = 3
# Snowflake error codes for a statement that was cancelled for running too long.
TIMEOUT_ERRNOS = {604, 630}


def connect(user: str, key_file: str, role: str):
    """Open a Snowflake connection with key-pair auth, using settings from .env."""
    return snowflake.connector.connect(
        account=_require("SNOWFLAKE_ACCOUNT"),
        user=user,
        private_key_file=key_file,
        role=role,
        warehouse=_require("SNOWFLAKE_WAREHOUSE"),
        database=_require("SNOWFLAKE_DATABASE"),
        schema=_require("SNOWFLAKE_SCHEMA"),
        login_timeout=30,
    )


def _require(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise ValueError(f"{var} is not set. Add it to your .env file.")
    return value
