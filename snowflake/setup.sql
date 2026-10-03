-- QueryPilot: one-time Snowflake setup.
-- Run as ACCOUNTADMIN in a Snowsight worksheet (select all, then Run All).
-- A ready-to-paste copy with your public key filled in is generated at
-- .secrets/snowflake_setup.sql (not committed).
--
-- Creates:
--   querypilot_wh       X-Small warehouse, suspends after 60s idle, 30s statement timeout
--   querypilot_monitor  hard monthly credit cap on that warehouse
--   querypilot.olist    database and schema for the Olist tables
--   querypilot_loader   role that can create and load tables (granted to you)
--   querypilot_reader   read-only role: SELECT only (the agent's role)
--   querypilot_agent    service user for the agent, key-pair login, no password

USE ROLE ACCOUNTADMIN;
SET my_user = CURRENT_USER();

-- Cost control: at most 5 credits a month (an X-Small warehouse uses 1 per running hour).
CREATE RESOURCE MONITOR IF NOT EXISTS querypilot_monitor
  WITH CREDIT_QUOTA = 5 FREQUENCY = MONTHLY START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 80 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND_IMMEDIATE;

CREATE WAREHOUSE IF NOT EXISTS querypilot_wh
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 60                    -- stop billing after 60 idle seconds
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  STATEMENT_TIMEOUT_IN_SECONDS = 30;   -- guardrail 5, enforced by Snowflake itself
ALTER WAREHOUSE querypilot_wh SET RESOURCE_MONITOR = querypilot_monitor;

CREATE DATABASE IF NOT EXISTS querypilot;
CREATE SCHEMA IF NOT EXISTS querypilot.olist;

-- Loader role: used once by you (browser login) to load the Olist tables.
CREATE ROLE IF NOT EXISTS querypilot_loader;
GRANT USAGE ON WAREHOUSE querypilot_wh TO ROLE querypilot_loader;
GRANT USAGE ON DATABASE querypilot TO ROLE querypilot_loader;
GRANT USAGE, CREATE TABLE, CREATE STAGE ON SCHEMA querypilot.olist TO ROLE querypilot_loader;
GRANT ROLE querypilot_loader TO USER IDENTIFIER($my_user);

-- Reader role: guardrail 1. SELECT on the Olist tables and nothing else.
CREATE ROLE IF NOT EXISTS querypilot_reader;
GRANT USAGE ON WAREHOUSE querypilot_wh TO ROLE querypilot_reader;
GRANT USAGE ON DATABASE querypilot TO ROLE querypilot_reader;
GRANT USAGE ON SCHEMA querypilot.olist TO ROLE querypilot_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA querypilot.olist TO ROLE querypilot_reader;
GRANT SELECT ON FUTURE TABLES IN SCHEMA querypilot.olist TO ROLE querypilot_reader;

-- The agent's user: a SERVICE user (no password, no interactive login),
-- signing in with an RSA key pair. Only the public key is stored here.
CREATE USER IF NOT EXISTS querypilot_agent
  TYPE = SERVICE
  DEFAULT_ROLE = querypilot_reader
  DEFAULT_WAREHOUSE = querypilot_wh
  DEFAULT_NAMESPACE = querypilot.olist
  COMMENT = 'QueryPilot agent, read-only';
ALTER USER querypilot_agent SET RSA_PUBLIC_KEY = '<AGENT_PUBLIC_KEY>';
ALTER USER querypilot_agent SET STATEMENT_TIMEOUT_IN_SECONDS = 30;
GRANT ROLE querypilot_reader TO USER querypilot_agent;

-- Check: the agent's role should list only USAGE and SELECT privileges.
SHOW GRANTS TO ROLE querypilot_reader;
