"""Shared test setup."""
import os

# Tests must never send traces to LangSmith, whatever .env says. load_dotenv()
# does not override variables that are already set, so this wins.
os.environ["LANGSMITH_TRACING"] = "false"
