-- QueryPilot: a short-lived service user that loads the Olist tables.
-- Run as ACCOUNTADMIN after setup.sql. A ready-to-paste copy with the public
-- key filled in is generated at .secrets/snowflake_loader_user.sql.
--
-- Why a separate user: the agent's user can only read. Loading needs write
-- access, so it gets its own identity with the loader role, and is disabled
-- again as soon as the load finishes (see the last line).

USE ROLE ACCOUNTADMIN;

CREATE USER IF NOT EXISTS querypilot_loader_svc
  TYPE = SERVICE
  DEFAULT_ROLE = querypilot_loader
  DEFAULT_WAREHOUSE = querypilot_wh
  DEFAULT_NAMESPACE = querypilot.olist
  COMMENT = 'QueryPilot data loader; disable when not loading';
ALTER USER querypilot_loader_svc SET RSA_PUBLIC_KEY = '<LOADER_PUBLIC_KEY>';
ALTER USER querypilot_loader_svc SET DISABLED = FALSE;
GRANT ROLE querypilot_loader TO USER querypilot_loader_svc;

-- After `make data-snowflake` succeeds, run this to switch the loader off:
-- ALTER USER querypilot_loader_svc SET DISABLED = TRUE;
